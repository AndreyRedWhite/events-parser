"""
Основной модуль для работы с пользователем. Запускает диалог в консоли, в зависимости от выбора выполняет различные
виды парсинга данных
"""
import datetime
import re

from holidays.holiday_parcer import holidays
from wiki.wiki_days_parcer import wiki_days
from wiki.wiki_years_parcer import wiki_years, page_iterator, timedelta_calc, en_mounth, mounths_digits, mounths
from eclipse.get_eclipse import find_nearest_eclipses
from aster.asteroid_getter import get_asters
from exel_sheets.new_clean_exel_operator import book_creater, book_creator_multiple_dates


def user_input():
    """
    Основная функция всего проекта. Запускает диалоговое окно, в завимости от выбора запускает различные парсеры,
    поисковики, сохраняет результат в файл
    """
    choise = int(input("Выберете действие:\n1. Поиск событий по определенной дате"
                       "\n2. Поиск событий в определенный период по ключевым словам\n"
                       "Ваш выбор: "))
    if choise == 1:
        date_input = input("Введите дату в формате \"Число Месяц Год\", например \"13 мая 2021\": ")
        data = single_day(date_input=date_input)
        book_creater(data=data)

    elif choise == 2:
        type_search = input("Выберите вариант поиска:\n1. Строгий поиск на совпадение поисковой фразы\n"
                            "2. Неточный поиск, использует стемминг и другие методы нормализации, которые уменьшают"
                            " слова до их корневой формы, сохраняя при этом смысловую нагрузку. При этом поиск"
                            " может давать False Positive результаты.\nВаш выбор: ")
        search = input("\nВведите запрос на поиск (например 'Пожар во Франции'): ")

        if type_search == "2":
            geo_optional = input("\n(опционально) введите одну или несколько стран через пробел для поиска"
                                 " (или просто нажмите Enter, если не хотие): ")
            city_optional = input("\n(опционально) введите один или несколько городов через проблем для поиска "
                                  "(или просто нажмите Enter, если не хотите): ")
        date_interval = input("\nВведите интервал дат для поиска в формате '1 января 1990 - 31 декабря 2022': ")
        start_date, finish_date = date_interval.split("-")
        if type_search == "1":
            date_list = page_iterator(
                start_date, finish_date, type_search=type_search, search_phrase=search)
        elif type_search == "2":
            date_list = page_iterator(
                start_date, finish_date, search_phrase=search, type_search=type_search, country=geo_optional,
                cities=city_optional)
        if date_list:
            print("были найдены такие даты:")
            print(date_list)
            date_list = filter_dates(start_date, finish_date, date_list)
            print("обработанные даты:")
            print(date_list, end="\n")
            # print("По вашему запросу найдены следующие совпадения:")
            event_list = []
            for each_day in date_list:
                # print(f"Найдено совпадение в следующей дате: {each_day}")
                event_list.append(single_day(each_day))

            # добавим значение timedelta
            for i in range(1, len(event_list)):
                date_1 = event_list[i - 1]['date']
                date_2 = event_list[i]['date']
                event_list[i]['timedelta'] = timedelta_calc(date_1, date_2)
            if type_search == "1":
                book_creator_multiple_dates(event_list, search, date_interval, type_search)
            elif type_search == "2":
                book_creator_multiple_dates(event_list, search, date_interval, type_search, geo_optional, city_optional)
        print("Пока на этом все, спасибо")


def single_day(date_input: str) -> dict:
    """
    Функция для парсинга данных для конкретного дня, используется дальше в итерации по датам
    :param date_input: дата, строка
    :return: словарь с данными
    """
    result = {"date": date_input}

    day, mounth, year = date_input.split()
    # print("-" * 100)

    # holidays from calend.ru
    holidays_list = holidays(day, mounth)
    # print("\nПраздники в этот день (данные с сайта https://www.calend.ru/): ")
    # for item in holidays_list:
    #     print(item)
    result['праздники (данные с calend.ru)'] = holidays_list
    # print("-" * 100)

    # holidays from wiki
    holidays_wiki = wiki_days(day, mounth)
    if any([*holidays_wiki[f"{day}_{mounth}"]["праздники"]]):
        result['Праздничные события (данные Wiki)'] = holidays_wiki[f"{day}_{mounth}"]["праздники"]
    elif not any([*holidays_wiki[f"{day}_{mounth}"]["праздники"]]):
        result['Праздничные события (данные Wiki)'] = holidays_wiki[f"{day}_{mounth}"]["праздники"]

    events_wiki = wiki_years(mounth, year)
    if events_wiki.get(f"{day} {mounth}"):
        if isinstance(events_wiki[f"{day} {mounth}"], str):
            result["события в этот день (данные Wiki)"] = [events_wiki[f"{day} {mounth}"]]
        elif isinstance(events_wiki[f"{day} {mounth}"], list):
            result["события в этот день (данные Wiki)"] = events_wiki[f"{day} {mounth}"]
    elif not events_wiki.get(f"{day} {mounth}"):
        result["события в этот день (данные Wiki)"] = ["События не найдены"]

    result["События за XX век"] = holidays_wiki[f"{day}_{mounth}"]["события"]["XX век"]

    result["События за XXI век"] = holidays_wiki[f"{day}_{mounth}"]["события"]["XXI век"]

    eclipses = find_nearest_eclipses(date_input)
    result["Затмения"] = eclipses
    eclipse_output = f"Ближайшее солнечное затмение: {eclipses['closest_solar_eclipse']}, количество дней " \
                     f"до него: {eclipses['days_to_solar_eclipse']}\nБлижайшее лунное затмение: " \
                     f"{eclipses['closest_lunar_eclipse']}, количество дней до него:" \
                     f" {eclipses['days_to_lunar_eclipse']}"

    # asteroids
    asteroids = get_asters(date_input)
    if asteroids:
        result["астероиды"] = asteroids

    elif not asteroids:
        result['астероиды'] = []

    return result


def convert_date(date_str: str) -> datetime.datetime.date:
    "Функция для перевода строкового представления даты в объект datetime"
    day, mounth, year = date_str.split()
    months = {
        'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
        'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
        'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
    }
    return datetime.datetime(int(year), months[mounth], int(day)).date()


def filter_dates(start_date_str: str, finish_date_str: str, dates: list) -> list:
    """
    функция для обработки списка с датами, который возвращает функция page_iterator() из директории wiki.
    На вход получает стартовую и финишниые даты из запроса пользователей и необработанный список. Возвращает список
    уникальных дат, которые начинаются не раньше стартовой даты.Также делает проверку, если дата пришла в виде
    диапазона вида 1-3 января 2002, добавляет в список все даты из диапазона
    """
    unique_dates = []
    start_date = convert_date(start_date_str)
    finish_date = convert_date(finish_date_str)
    for date_str in dates:

        # проверка, если дата пришла в виде "1-3 Января 2000"
        if len(date_str.split()[0].split("—")) == 2:
            for d in range(int(date_str.split()[0].split("—")[0]), int(date_str.split()[0].split("—")[1]) + 1):
                new_day = f"{d} {' '.join(date_str.split()[1:])}"
                date = convert_date(new_day)
                if start_date <= date <= finish_date and date not in unique_dates:
                    unique_dates.append(new_day)

        # проверка, если дата выглядит в виде '21 января—1 февраля 2000'
        elif re.search(r"(?P<s_d>\d+) (?P<s_m>\S+)—(?P<f_d>\d+) (?P<f_m>\S+) (?P<year>\d+)", date_str):
            # поиск через регулярные выражения этой строки
            result = re.search(r"(?P<s_d>\d+) (?P<s_m>\S+)—(?P<f_d>\d+) (?P<f_m>\S+) (?P<year>\d+)", date_str)
            # берем из этой строки первый и последний день, создаем далее список
            first_day = datetime.datetime.strptime(f"{result['s_d']} {en_mounth[result['s_m'].lower()]} {result['year']}", "%d %B %Y")
            finish_day = datetime.datetime.strptime(f"{result['f_d']} {en_mounth[result['f_m'].lower()]} {result['year']}", "%d %B %Y")

            day_list = [(first_day + datetime.timedelta(days=i)).date() for i in range((finish_day - first_day).days + 1)]
            # сделаем обратный словарь из словаря mounth, приведя в вид 'январь': 'января'
            revers_mounth = {}
            for k, v in mounths.items():
                revers_mounth[v] = k
            # тут получаем список из строковых дат
            formated_list = [f"{day.day} {revers_mounth[mounths_digits[day.month]]} {day.year}" for day in day_list]
            for date_str in formated_list:
                date = convert_date(date_str)
                if start_date <= date <= finish_date and date not in unique_dates:
                    unique_dates.append(date_str)
        # в остальных случаях, когда дата выглядит нормальной, в виде "1 января 2000"
        else:
            date = convert_date(date_str)
            if start_date <= date <= finish_date and date_str not in unique_dates:
                unique_dates.append(date_str)

    return unique_dates


if __name__ == '__main__':
    user_input()
