"""
Модуль для загрузки и парсинга данных из Wiki с страницами с днями
"""
from bs4 import BeautifulSoup
import requests
import re
from pprint import pprint

# Заголовки для requests запросов
headers = {
        "Accept": "*/*",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/116.0.0.0 Safari/537.36 "
}


def clear_text(text: str) -> str:
    """Функция для очистки текста от различных артефактов. получает на вход text, возвращает его обработанный вариант"""
    _text = re.sub(r"\[\d+]", "", text)
    del_source = re.sub(r"\[источник не указан \d+ (?:дня|дней)]", "", _text)
    del_fact = re.sub(r'\[значимость факта\?]', "", del_source)
    clear = del_fact.rstrip(".").strip().replace("\xa0", "")
    return clear


def page_getter(date: str, save: bool = False) -> str:
    """
    Эта функция получает дату в формате строки '1_июня', генерирует соответствующий URL и извлекает весь HTML-код
    со страницы Википедии. Возвращает строку со всем HTML-кодом этой страницы.
    :param date: дата, строка;
    :param save: сохранять ли данные в файл или только возвращать.
    """
    url = "https://ru.wikipedia.org/wiki/" + date
    res = requests.get(url, headers=headers).text
    # Сохраняет страницу для последующего парсинга
    if save:
        with open(f"wiki_{date}.html", "w") as f:
            f.write(res)
    return res


def page_parser(data: str, date: str) -> dict:
    """
    Функция-парсер данных со страницы. Забирает международные, национальные, региональные, профессиональные праздники,
    события за XX и XXI века.
    :param data: html код страницы с данными;
    :param date: строка с датой для дальнейшего сохранения полученных данных
    :return: result: словарь с событиями
    """
    soup = BeautifulSoup(data, "lxml")

    # here we parce for international, national, regional and professional holidays
    international = soup.find('span', id='Международные')
    if international:
        international_holidays = international.find_next('ul')

    national = soup.find('span', id='Национальные')
    if national:
        national_holidays = national.find_next('ul')

    regional = soup.find('span', id='Региональные')
    if regional:
        regional_holidays = regional.find_next('ul')

    professional = soup.find("span", id="Профессиональные")
    if professional:
        professional_holidays = professional.find_next("ul")

    # this is the final structure
    result = {date: {"праздники": {"международные": [], "национальные": [], "региональные": [], "профессиональные": []},
                     "события": {"XX век": None, "XXI век": None}}}

    # enrich data for international days
    if international:
        for holiday in international_holidays.find_all('li'):
            text = re.sub(r'\[\d+]', '', holiday.get_text()).replace('\xa0', ' ').strip().rstrip(".")
            cleared_text = clear_text(text)
            result[date]["праздники"]["международные"].append(cleared_text)

    # enrich data for national days
    if national:
        for holiday in national_holidays.find_all('li', recursive=False):

            # here we're searching for child lists inside main list. It happen if one country has 2 or more days
            if holiday.find('ul'):
                country_text = holiday.get_text().split("\n")[0].replace(":", "").replace("\xa0", "")
                # .split(':')[0].replace('\xa0', ' ').strip().rstrip(".").replace("\n", "")
                sub_list = holiday.find('ul')
                for li in sub_list.find_all('li', recursive=False):
                    text = re.sub(r'\[\S{2}]', '', li.get_text()).replace('\xa0', ' ').strip().rstrip(".")
                    cleared_text = clear_text(text)
                    result[date]["праздники"]["национальные"].append(f"{country_text}: {cleared_text}")
                holiday.extract()  # Удаляем обработанный элемент, чтобы избежать повторной обработки

        for holiday in national_holidays.find_all('li', recursive=False):
            text = re.sub(r'\[\d+]', '', holiday.get_text()).replace('\xa0', ' ').strip().rstrip(".")
            cleared_text = clear_text(text)
            result[date]["праздники"]["национальные"].append(cleared_text)

    # enrich data for regional days
    if regional:
        for holiday in regional_holidays.find_all('li'):
            if holiday.find('ul'):
                country_text = holiday.get_text().split(':')[0].replace('\xa0', ' ').strip().rstrip(".").replace(":", "").replace("\xa0", "")
                sub_list = holiday.find('ul')
                for li in sub_list.find_all('li'):
                    sub_holiday_text = re.sub(r'\[\d+]', '', li.get_text()).replace('\xa0', ' ').strip().rstrip(".")
                    cleared_text = clear_text(sub_holiday_text)
                    result[date]["праздники"]["региональные"].append(f"{country_text}: {cleared_text}")
                holiday.extract()  # Удаляем обработанный элемент, чтобы избежать повторной обработки

        for holiday in regional_holidays.find_all('li'):
            text = re.sub(r'\[\d+]', '', holiday.get_text()).replace('\xa0', ' ').strip().rstrip(".")
            cleared_text = clear_text(text)
            result[date]["праздники"]["региональные"].append(cleared_text)

    # enrich data for professional days
    if professional:
        for holiday in professional_holidays.find_all("li"):
            text = re.sub(r'\[\d+]', '', holiday.get_text()).replace('\xa0', ' ').strip().rstrip(".")
            cleared_text = clear_text(text)
            result[date]["праздники"]["профессиональные"].append(cleared_text)

    # here we parce for XX and century events
    xx_result = {}
    xx_events = soup.find("span", id="XX_век").find_next("ul")
    for li in xx_events.find_all("li"):
        year_text = li.get_text()
        year_match = re.match(r'\b(\d{4})\b', year_text)
        if year_match:
            year = year_match.group(1)
            events = []
            if li.find("ul"):
                for sub_event in li.find("ul").find_all("li"):
                    text = sub_event.get_text().replace("\xa0", "").replace("\n", "")
                    cleared_text = clear_text(text)
                    events.append(cleared_text)
            else:
                event_text = year_text.split("—", 1)[1].strip() if "—" in year_text else year_text
                text = event_text.replace("\xa0", "")
                cleared_text = clear_text(text)
                events.append(cleared_text)
                xx_result[year] = events
        else:
            # Пропуск несоответствующих элементов
            continue
    result[date]["события"]["XX век"] = xx_result

    # here we parce for XXI and century events
    xxi_result = {}
    xxi_events = soup.find("span", id="XXI_век").find_next("ul")
    for li in xxi_events.find_all("li"):
        year_text = li.get_text()
        year_match = re.match(r'\b(\d{4})\b', year_text)
        if year_match:
            year = year_match.group(1)
            events = []
            if li.find("ul"):
                for sub_event in li.find("ul").find_all("li"):
                    events.append(sub_event.get_text().replace("\xa0", "").replace("\n", ""))
            else:
                event_text = year_text.split("—", 1)[1].strip() if "—" in year_text else year_text
                events.append(event_text.replace("\xa0", ""))
                xxi_result[year] = events
        else:
            # Пропуск несоответствующих элементов
            continue
    result[date]["события"]["XXI век"] = xxi_result

    return result


def unstructured_page_parcer(result_dict: dict, data: str) -> dict:
    """
    Страницы в Wiki очень неструктурированы, иногда вместо <div>-ов с праздниками там просто список праздников.
    На этот случай результат из предыдущей функции парсинга пропускается через эту функцию, если праздники не были
    найдены - происходит повторный парсинг html кода для поиска обычного списка со всеми праздниками.
    :param result_dict: словарь с данными из функции page_parser();
    :param data: строка с html кодом страницы из Wiki
    :return: result_dict: словарь с событиями, обогащенный событиями из неструктурированного списка
    """
    for date, val in result_dict.items():
        holidays = val["праздники"]
    validate = []
    for _, val in holidays.items():
        validate.append(val)
    if any(validate):
        return result_dict
    else:
        soup = BeautifulSoup(data, "lxml")
        span_start = soup.find("span", id="Праздники_и_памятные_дни")
        span_end = soup.find("span", id="Религиозные")

        holidays_list = span_start.find_next_siblings()
        holidays = []
        for event in holidays_list:
            if event == "\n":
                continue
            elif event == span_end:
                break
            elif event.name == "ul":
                text = event.text
                cleared_text = re.sub(r"\xa0", "", text).rstrip(".")
                holidays.append(cleared_text)
        if not holidays:
            start_span = soup.find("span", id="Праздники_и_памятные_дни")

            # Проверяем, находится ли он внутри элемента h2
            if start_span and start_span.parent.name == 'h2':
                # Ищем следующий элемент ul
                next_ul = start_span.find_next('ul')

                # Проверяем, не встречается ли span с id="stop" до ul
                stop_span = soup.find("span", id="Религиозные")
                if stop_span and stop_span.find_previous('ul') == next_ul:
                    for li in next_ul.find_all("li"):
                        text = li.get_text()
                        cleared_text = clear_text(text)
                        holidays.append(cleared_text)

        result_dict[date]["праздники"]["международные"] = holidays
        return result_dict


def wiki_days(day, mounth):
    """
    Функция для оперирования функциями-загрузчиками и функциями-парсерами данных;
    :param day: строка с днем из даты;
    :param mounth: строка с месяцем из даты
    :return: cleared_result: словарь с событиями по определенной дате
    """
    user_input = f"{day}_{mounth}"
    data = page_getter(user_input, save=False)
    result = page_parser(data, date=user_input)
    cleared_result = unstructured_page_parcer(result, data)
    return cleared_result


if __name__ == '__main__':
    pprint(wiki_days("26", "декабря"), width=200)
