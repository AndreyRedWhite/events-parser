"""
Данный модуль отвечает за загрузку, парсинг данных с страниц Wiki и за поиск событий по определенным запросам
"""
import datetime
import logging

from dateutil.relativedelta import relativedelta
from bs4 import BeautifulSoup
import requests
import re
from pprint import pprint

from wiki.countries_parser.searcher import search_phrase_in_text
from wiki.requests_config import proxies, headers

# словари с месяцами, для перевода месяцев из одного вида в другой
mounths = {
        "января": "январь",
        "февраля": "февраль",
        "марта": "март",
        "апреля": "апрель",
        "мая": "май",
        "июня": "июнь",
        "июля": "июль",
        "августа": "август",
        "сентября": "сентябрь",
        "октября": "октябрь",
        "ноября": "ноябрь",
        "декабря": "декабрь",

    }

mounths_digits = {
    1: "январь",
    2: "февраль",
    3: "март",
    4: "апрель",
    5: "май",
    6: "июнь",
    7: "июль",
    8: "август",
    9: "сентябрь",
    10: "октябрь",
    11: "ноябрь",
    12: "декабрь"
}

reverse_mounths = {v: k for k, v in mounths.items()}

en_mounth = {
    'января': 'January',
    'февраля': 'February',
    'марта': 'March',
    'апреля': 'April',
    'мая': 'May',
    'июня': 'June',
    'июля': 'July',
    'августа': 'August',
    'сентября': 'September',
    'октября': 'October',
    'ноября': 'November',
    'декабря': 'December'
}

logging.basicConfig(level="INFO")


def clear_text(text: str) -> str:
    """Функция для очистки текста события от ссылок, не-ASCII символов и прочего. На вход подается необработанная
    строка, на выходе - обработанная"""

    cleared_text = re.sub("\[\d{1,2}]", "", text)
    cleared_text = cleared_text.replace('\xa0', "")
    if cleared_text.startswith("— "):
        cleared_text = cleared_text.split("— ")[1]
    if "\n" in cleared_text:
        cleared_text = cleared_text.replace("\n", " ")
    more_clear = re.sub(r'\[\d{1,3}]', "", cleared_text)
    return more_clear


def timedelta_calc(date_1: str, date_2: str) -> int:
    """Функция принимает на вход 2 даты и возвращает количество дней между ними"""
    def parse_rus_date(date_str: str) -> datetime.datetime:
        """Функция для замены месяца на английский и преобразования строки в объект datetime"""
        for rus, eng in en_mounth.items():
            date_str = date_str.replace(rus, eng)
        return datetime.datetime.strptime(date_str, '%d %B %Y')
    date_1 = parse_rus_date(date_1)
    date_2 = parse_rus_date(date_2)
    return abs((date_2 - date_1).days)


def page_getter_before_2006(year: str, save: bool = False) -> str:
    """
    Эта функция получает дату в формате строки '1_июня', генерирует соответствующий URL и извлекает весь HTML-код
    со страницы Википедии. Возвращает строку со всем HTML-кодом этой страницы.
    """
    url = "https://ru.wikipedia.org/wiki/" + year + "_год"
    logging.info(f"getting a page for {year} year")
    res = requests.get(url, headers=headers, proxies=proxies).text
    # Сохраняет страницу для последующего парсинга
    if save:
        with open(f"wiki_{year}.html", "w") as f:
            f.write(res)
    return res


def page_parcer_before_2006(mounth: str, data: str) -> dict:
    """
    функция для парсинга странички WiKi с событиями до 2006 года (там формат 1 год - 1 страница)
    На вход получает строку с месяцем и строку с данными для парсинга. Возвращает словарь вида дата: событие
    """
    soup = BeautifulSoup(data, "lxml")
    mounth = mounths[mounth]
    # ищем события за соответствующий месяц
    res = soup.find("span", id=mounth.capitalize()).find_next("ul")
    events_result = {}

    for li in res.find_all("li", recursive=False):
        day = li.find("a").text

        # обрабатываем вложенные списки, которые есть, когда в какой-то день более 1-го события
        if li.find("ul"):
            events = []
            for subevent in li.find_all("li"):
                text = subevent.get_text()
                cleared_text = clear_text(text)
                events.append(cleared_text)
            events_result.update({day: events})
        else:
            text = "".join(li.get_text().split("—")[1:])
            deleted_links = clear_text(text)
            events_result.update({day: deleted_links})

    return events_result


def page_getter_after_2006(mounth: str|int, year: str, save: bool = False) -> str:
    """
    Функция для получения данных со страницы. Получает дату в виде строки в формате '1_июня', создаёт соответствующий
     URL и извлекает весь HTML-код со страницы вики. Возвращает строку со всем HTML-кодом этой страницы.
    """
    if mounths.get(mounth):
        mounth = mounths[mounth]
    elif mounths_digits.get(mounth):
        mounth = mounths_digits[mounth]

    date = f"{mounth}_" + f"{year}" + "_года"
    url = "https://ru.wikipedia.org/wiki/" + date
    logging.info(f"getting a page for {date}")
    res = requests.get(url, headers=headers, proxies=proxies).text
    # Сохраняет страницу для последующего парсинга
    if save:
        with open(f"wiki_{date}.html", "w") as f:
            f.write(res)
    return res


def page_parcer_after_2006(data) -> dict:
    """
    Функция для парсинга событий со страницы Wiki после 2006 года (там формат 1 месяц - 1 страница).
    На вход получает строку со всем html кодом, возвращает словарь вида дата: событие. Функция учитывает различные,
    неструктурированные, неправильно сформатированные варианты страниц в Wiki.
    """
    logging.info(f"executing function 'page_parcer_after_2006'")
    result = {}
    mounth_regex = "января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря"
    soup = BeautifulSoup(data, "lxml")

    # Если страница содержит стандартный список 'события'
    plain_events = soup.find("span", id="События")

    # Если страница содержит стандартный список 'важнейшие события'
    important_events = soup.find("span", id="Важнейшие_события")

    # Если страница содержит элемент "события", но после которого идет элемент "важнейщие"
    the_most_important = soup.find("span", id="Важнейшие")

    # иногда на странице есть важнейщие события, а остальной список помечен тегом "Все_события"
    all_events_span = soup.find("span", id="Все_события")

    # Поиск событий на нормальной странице, где есть элемент "события" и далее идет список этих событий
    if plain_events and not the_most_important:
        events = plain_events.find_next("ul")
        for li in events.find_all("li", recursive=False):

            # regex для поиска дат
            date_regex = re.compile(
                f"(^\d+ ({mounth_regex}) — \d+ ({mounth_regex})|^\d+ ({mounth_regex})|^\d+—\d+ ({mounth_regex}))")
            srch = date_regex.search(li.get_text())
            if srch:
                day = srch.group(1)

            events = []
            if li.find("ul"):
                for sub_li in li.find("ul").find_all("li", recursive=False):

                    text = sub_li.get_text().replace("[нет в источнике]", "")
                    cleared_text = clear_text(text)
                    events.append(cleared_text)
                    if srch:
                        result.update({day: events})
            elif not li.find("ul"):
                # clearing a result from artefacts
                text = li.get_text().replace("[нет в источнике]", "")
                cleared_text = clear_text(text)
                # adds a result to list
                events.append(cleared_text)
                # adding a found event to result dict
                if srch:
                    result.update({day: events})

        # иногда список на странице может быть разбит на несколько такими элементами, как table
        _next_ul = plain_events.find_next("ul")
        if _next_ul:
            table_ul = _next_ul.find_next("table")
            if table_ul:
                next_ul = table_ul.find_next("ul")
                if next_ul:
                    for li in next_ul.find_all("li", recursive=False):

                        # regex для поиска дат
                        date_regex = re.compile(
                            f"(^\d+ ({mounth_regex}) — \d+ ({mounth_regex})|^\d+ ({mounth_regex})|^\d+—\d+ ({mounth_regex}))")
                        srch = date_regex.search(li.get_text())
                        if srch:
                            day = srch.group(1)

                        events = []
                        if li.find("ul"):
                            for sub_li in li.find("ul").find_all("li", recursive=False):

                                text = sub_li.get_text().replace("[нет в источнике]", "")
                                cleared_text = clear_text(text)
                                events.append(cleared_text)
                                if srch:
                                    result.update({day: events})
                        elif not li.find("ul"):
                            # clearing a result from artefacts
                            text = li.get_text().replace("[нет в источнике]", "")
                            cleared_text = clear_text(text)
                            # adds a result to list
                            events.append(cleared_text)
                            # adding a found event to result dict
                            if srch:
                                result.update({day: events})

        return result

    # если на странице есть "Важнейшие события" и "Все события"

    # поиск событий внутри списка "важные события"
    elif important_events:
        events = important_events.find_next("ul")
        for li in events.find_all("li", recursive=False):
            # regex для поиска дат
            date_regex = re.compile(
                f"(^\d+ ({mounth_regex}) — \d+ ({mounth_regex})|^\d+ ({mounth_regex})|^\d+—\d+ ({mounth_regex}))")
            srch = date_regex.search(li.get_text())
            if srch:
                day = srch.group(1)

            events = []
            if li.find("ul"):
                for sub_li in li.find("ul").find_all("li", recursive=False):
                    text = sub_li.get_text().replace("[нет в источнике]", "")

                    # очищаем текст от артефактов
                    cleared_text = clear_text(text)
                    events.append(cleared_text)
                    if srch:
                        result.update({day: events})

            elif not li.find("ul"):
                text = li.get_text().replace("[нет в источнике]", "")
                # очищаем текст от артефактов
                cleared_text = clear_text(text)
                # Добавляем результат в список
                events.append(cleared_text)
                # Добавляем найденное событие в словарь результатов.
                if srch:
                    result.update({day: events})

        # поиск событий внутри списка "все события", если такой есть
        all_events = soup.find("span", id="Все_события")
        if all_events:
            events = all_events.find_next("ul")
            for li in events.find_all("li", recursive=False):
                # regex для поиска дат
                date_regex = re.compile(
                    f"(^\d+ ({mounth_regex}) — \d+ ({mounth_regex})|^\d+ ({mounth_regex})|^\d+—\d+ ({mounth_regex}))")
                srch = date_regex.search(li.get_text())
                if srch:
                    day = srch.group(1)

                events = []
                if li.find("ul"):
                    for sub_li in li.find("ul").find_all("li"):
                        text = sub_li.get_text().replace("[нет в источнике]", "")

                        # очищаем текст от артефактов
                        cleared_text = clear_text(text)
                        events.append(cleared_text)
                        if srch:
                            result.update({day: events})
                elif not li.find("ul"):
                    text = li.get_text().replace("[нет в источнике]", "")
                    # очищаем текст от артефактов
                    cleared_text = clear_text(text)
                    # adds a result to list
                    events.append(cleared_text)
                    # adding a found event to result dict
                    if srch:
                        result.update({day: events})

    # если страница состоит из span="важнейщие" и "все события {месяц} {год}"
    elif the_most_important:
        # обрабатываем список важнейщих событий
        events = the_most_important.find_next("ul")
        for li in events.find_all("li", recursive=False):
            # regex для поиска дат
            date_regex = re.compile(
                f"(^\d+ ({mounth_regex}) — \d+ ({mounth_regex})|^\d+ ({mounth_regex})|^\d+—\d+ ({mounth_regex}))")
            srch = date_regex.search(li.get_text())
            if srch:
                day = srch.group(1)

            events = []
            if li.find("ul"):
                for sub_li in li.find("ul").find_all("li", recursive=False):
                    text = sub_li.get_text().replace("[нет в источнике]", "")

                    # очищаем текст от артефактов
                    cleared_text = clear_text(text)
                    events.append(cleared_text)
                    if srch:
                        result.update({day: events})
            elif not li.find("ul"):
                text = li.get_text().replace("[нет в источнике]", "")
                # очищаем текст от артефактов
                cleared_text = clear_text(text)
                # adds a result to list
                events.append(cleared_text)
                # adding a found event to result dict
                if srch:
                    result.update({day: events})

        # обрабатываем список "все события {месяц} {год}"
        date_mounth, date_year = soup.find("span", class_="mw-page-title-main").text.split()[0:2]
        date_id = f"Все_события_{reverse_mounths[date_mounth.lower()]}_{date_year}_года"
        events_in_mounth = soup.find("span", id=date_id)
        if events_in_mounth:
            events = events_in_mounth.find_next("ul")
            for li in events.find_all("li", recursive=False):
                # regex для поиска дат
                date_regex = re.compile(
                    f"(^\d+ ({mounth_regex}) — \d+ ({mounth_regex})|^\d+ ({mounth_regex})|^\d+—\d+ ({mounth_regex}))")
                srch = date_regex.search(li.get_text())
                if srch:
                    day = srch.group(1)

                events = []
                if li.find("ul"):
                    for sub_li in li.find("ul").find_all("li"):
                        text = sub_li.get_text().replace("[нет в источнике]", "")

                        # очищаем текст от артефактов
                        cleared_text = clear_text(text)
                        events.append(cleared_text)
                        if srch:
                            result.update({day: events})
                elif not li.find("ul"):
                    text = li.get_text().replace("[нет в источнике]", "")
                    # очищаем текст от артефактов
                    cleared_text = clear_text(text)
                    # adds a result to list
                    events.append(cleared_text)
                    # adding a found event to result dict
                    if srch:
                        result.update({day: events})

        # вместо тега "все события {месяц} {год}" страница может просто содержать тег "все события"
        # all_events = soup.find("span", id="Все_события")
        if all_events_span:
            events = all_events_span.find_next("ul")
            for li in events.find_all("li", recursive=False):
                # regex для поиска дат
                date_regex = re.compile(
                    f"(^\d+ ({mounth_regex}) — \d+ ({mounth_regex})|^\d+ ({mounth_regex})|^\d+—\d+ ({mounth_regex}))")
                srch = date_regex.search(li.get_text())
                if srch:
                    day = srch.group(1)

                events = []
                if li.find("ul"):
                    for sub_li in li.find("ul").find_all("li", recursive=False):
                        text = sub_li.get_text().replace("[нет в источнике]", "")

                        # очищаем текст от артефактов
                        cleared_text = clear_text(text)
                        events.append(cleared_text)
                        if srch:
                            result.update({day: events})
                elif not li.find("ul"):
                    text = li.get_text().replace("[нет в источнике]", "")
                    # очищаем текст от артефактов
                    cleared_text = clear_text(text)
                    # adds a result to list
                    events.append(cleared_text)
                    # adding a found event to result dict
                    if srch:
                        result.update({day: events})
    return result


def page_iterator(start: str, finish: str, type_search: str, search_phrase: str, country: str = None, cities: str = None) -> list:
    """
    Функция для управления функциями-парсерами страниц и функциями-поисковиками. Получает на вход следующие параметры:
    :param start: стартовая дата, строка, обязательный параметр;
    :param finish: финальная дата для поиска, строка, обязательный параметр;
    :param type_search: тип поиска, строка, обязательный параметр. Может быть:
     строгий, '1' - в этом случае ищется полное совпадение ключевой строки в каждом событии из
    Wiki, дает 100% совпадения, но может многое пропускать;
    нестрогий, '2' - в этом случае включаются различные функции для так называемой нормализации текста, приведения
    его в исходную форму, стегматизация, лемминг и прочее, дает много false positive результатов, зато с большей
    вероятностью не упустит нужное событие. В данной функции он не используется, а просто передается поискавым функциям;

    :param search_phrase: поисковая фраза, строка, обязательный параметр;
    :param country: страна, строка, служит для улучщения зоны поиска, при использовании к поисковой фразе добавляетются все
    города из словаря с ключем страны, если таковая есть. В строке могут быть несколько стран через пробел, добавлены
    будут все города по всем странам из словаря. В данной функции не используется, а просто передается поисковым функциям.
    Необязательный параметр;

    :param cities: города, строка, содержит город или несколько городов через пробел, используется для улучшения поиска, каждый
    город добавляется к поисковой строке. Необязательный параметр
    """

    result = []
    s_day, s_mounth, s_year = start.split()
    formated_start = datetime.datetime.strptime(f"{s_day} {en_mounth[s_mounth]} {s_year}", "%d %B %Y").date()

    f_day, f_mounth, f_year = finish.split()
    formated_finish = datetime.datetime.strptime(f"{f_day} {en_mounth[f_mounth]} {f_year}", "%d %B %Y").date()

    date_separation_start = datetime.datetime.strptime("1 January 2006", "%d %B %Y").date()
    date_separation_end = datetime.datetime.strptime("1 January 2007", "%d %B %Y").date()

    # 1. interval is before Feb 2006
    if formated_finish.year < date_separation_start.year:
        logging.info("Execute case 1")
        while formated_start < formated_finish:
            page = page_getter_before_2006(str(formated_start.year))
            event_dates = search_for_events_before_2006(page, search_phrase, type_search, country, cities)
            result.extend(event_dates)
            formated_start += relativedelta(years=1)
        return result
    # 2. Interval is after Feb 2006
    elif formated_start.year >= date_separation_end.year:
        logging.info("Execute case 2")
        while formated_start < formated_finish:
            page = page_getter_after_2006(formated_start.month, str(formated_start.year))
            event_dates = new_better_search_after_2006(page, search_phrase, type_search, country, cities)
            result.extend(event_dates)
            formated_start += relativedelta(months=1)
        return result

    # case 3, when time period contains 2006 year:
    elif formated_start.year <= 2006 and formated_finish.year >= 2006:
        logging.info("executing case when start is 2006 and finish isn't")
        while formated_start <= formated_finish:
            print(f"{formated_start=}, {formated_finish=}")
            if formated_start.year < 2006:
                page = page_getter_before_2006(str(formated_start.year))
                event_dates = search_for_events_before_2006(page, search_phrase, type_search, country, cities)
                result.extend(event_dates)
                formated_start += relativedelta(years=1)
            elif formated_start.year == 2006:
                if formated_start.month in [1, 5, 6, 7, 8, 9]:
                    page = page_getter_before_2006(str(formated_start.year))
                    event_dates = search_for_events_before_2006(page, search_phrase, type_search, country, cities)
                    result.extend(event_dates)
                    formated_start += relativedelta(months=1)
                if formated_start.month in [2, 3, 4, 10, 11, 12]:
                    page = page_getter_after_2006(formated_start.month, str(formated_start.year))
                    event_dates = new_better_search_after_2006(page, search_phrase, type_search, country, cities)
                    result.extend(event_dates)
                    formated_start += relativedelta(months=1)
            elif formated_start.year > 2006:
                page = page_getter_after_2006(formated_start.month, str(formated_start.year))
                event_dates = new_better_search_after_2006(page, search_phrase, type_search, country, cities)
                result.extend(event_dates)
                formated_start += relativedelta(months=1)
        return result


def search_for_events_before_2006(data: str, search_phrase: str, type_search: str, country: str, cities: str) -> list:
    """
    Фунуция-поисковик событий внутри данных из Wiki для струкуры страниц до 2006 года.
    :param data: html код страеницы wiki, строка, обязательный параметр
    :param search_phrase: поисковая строка, обязательный параметр
    :param type_search: тип поиска, строгий "1" - ищет полное совпадение поисковой строки внутри текста события,
    дает 100% совпвдения, но может пропустить событие, если поисковая фраза была не полностью идентичка части текста
    события;
    нестрогий "2" - использует техники нормализации текста, может давать false positive результаты, но находит больше
    событий;
    :param country: страна или страны через пробел - строка, передается в фунцию-поисковик для нестрогово поиска;
    :param cities: город или города - строка, передается в функцию-поискових для нестрогово поиска;
    :return: список с датами, внутри которых найдено совпадение с поисковой строкой
    """
    dates = []
    soup = BeautifulSoup(data, "lxml")
    months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь',
              'Декабрь']
    year = soup.find("span", class_="mw-page-title-main").text.split()[0]
    # regex to search for date in this unstructured annoing wiki data
    month_regex = "января|февраля|марта|апреля|мая|июня|июля|сентября|октября|ноября|декабря"
    date_regex = re.compile(
        f"(^\d+ (?:{month_regex})—\d+ (?:{month_regex}))|(^\d+ (?:{month_regex}))|(^\d+—\d+ (?:{month_regex}))")
    for month in months:
        month_span = soup.find('span', id=month)
        if month_span:
            month_ul = month_span.find_next('ul')
            for li in month_ul.find_all('li', recursive=False):
                if li.find('ul'):
                    for sub_li in li.find('ul').find_all('li'):
                        if type_search == "1":
                            if search_phrase.lower() in sub_li.get_text().lower():
                                date = li.find('a').get_text()
                                dates.append(date + " " + year)
                        # Попытка внедрить улучщенный поиск
                        elif type_search == "2":
                            text = sub_li.get_text().lower()
                            if search_phrase_in_text(text=text, phrase=search_phrase, countries=country, cities=cities):
                                date = li.find('a').get_text()
                                dates.append(date + " " + year)

                elif not li.find("ul"):
                    if type_search == "1":
                        if search_phrase.lower() in li.get_text().lower():
                            date = li.find('a').get_text()
                            dates.append(date + " " + year)
                    # попытка внедрить улучшенный поиск
                    elif type_search == "2":
                        text = li.get_text().lower()
                        if search_phrase_in_text(text=text, phrase=search_phrase, countries=country, cities=cities):
                            res = date_regex.search(li.get_text())
                            if res:
                                for gr in res.groups():
                                    if gr:
                                        date = gr
                                        dates.append(date + " " + year)
    return dates


def new_better_search_after_2006(data, search_phrase, type_search, country, cities):
    """
    Фунуция-поисковик событий внутри данных из Wiki для струкуры страниц после 2006 года.
    :param data: html код страеницы wiki, строка, обязательный параметр
    :param search_phrase: поисковая строка, обязательный параметр
    :param type_search: тип поиска, строгий "1" - ищет полное совпадение поисковой строки внутри текста события,
    дает 100% совпвдения, но может пропустить событие, если поисковая фраза была не полностью идентичка части текста
    события;
    нестрогий "2" - использует техники нормализации текста, может давать false positive результаты, но находит больше
    событий;
    :param country: страна или страны через пробел - строка, передается в фунцию-поисковик для нестрогово поиска;
    :param cities: город или города - строка, передается в функцию-поискових для нестрогово поиска;
    :return: список с датами, внутри которых найдено совпадение с поисковой строкой
    """
    dates = []

    result_dict = page_parcer_after_2006(data)
    for date, events in result_dict.items():
        for item in events:
            if type_search == "1":
                if search_phrase.lower() in item.lower():
                    soup = BeautifulSoup(data, "lxml")
                    year = soup.find("span", class_="mw-page-title-main").text.split()[1]
                    # пополняем список с датами, по которым были найдены совпадения
                    dates.append(date + " " + year)
            elif type_search == "2":
                if search_phrase_in_text(text=item.lower(), phrase=search_phrase, countries=country, cities=cities):
                    # в случае нахождения совпадения по поисковой фразе, ищем год на странице, чтобы добавить его к дате
                    soup = BeautifulSoup(data, "lxml")
                    year = soup.find("span", class_="mw-page-title-main").text.split()[1]
                    # пополняем список с датами, по которым были найдены совпадения
                    dates.append(date + " " + year)
    return dates


def wiki_years(mounth: str, year: int):
    """
    Функция, отвечающая за вызов функций-загрузчиков html кода и функций-парсеров страниц Wiki. Так как страницы Wiki
    до 2006 года и после 2006 имеют разный формат, нужно использовать разные функции для их обработки.
    :param mounth: месяц, строка;
    :param year: год, строка
    """
    logging.info(f"executing function wiki_years, here is {mounth=}, {year=}")
    if int(year) < 2006:
        res = page_getter_before_2006(year)
        wiki_years_res = page_parcer_before_2006(mounth, res)
        return wiki_years_res
    elif int(year) > 2006:
        res = page_getter_after_2006(mounth, year, save=False)
        wiki_years_res = page_parcer_after_2006(res)
        return wiki_years_res
    elif int(year) == 2006:
        if mounth in ["января", "мая", "июня", "июля", "августа", "сентября"]:
            res = page_getter_before_2006(year)
            wiki_years_res = page_parcer_before_2006(mounth, res)
            return wiki_years_res
        elif mounth in ["февраля", "марта", "апреля", "октября", "ноября", "декабря"]:
            res = page_getter_after_2006(mounth, year, save=False)
            wiki_years_res = page_parcer_after_2006(res)
            return wiki_years_res


if __name__ == '__main__':
    # TESTING FOR DATE AFTER 2006
    res = page_getter_after_2006(mounth="мая",year="2015", save=True)
    result = page_parcer_after_2006(res)
    pprint(result, width=200)

    # TESTING FOR DATE BEFORE 2006
    # res = page_getter_before_2006("1989", save=True)
    # result = page_parcer_before_2006("ноября", res)
    # pprint(result, width=200)
    # with open("wiki_1991.html") as f:
    #     data = f.read()
    # search = "югославская война"
    # print(search_for_events_before_2006(data, search_phrase=search))
