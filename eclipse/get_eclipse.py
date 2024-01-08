"""
Модуль для загрузки из спаршенного json-а с затмениями информации о ближайщих затмениях для переданной даты
"""
import json
import os.path
from datetime import datetime


# Словарь для перевода названий месяцев
months = {
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


def find_nearest_eclipses(input_date: str) -> dict:
    """
    Функция для поиска ближайших затмений. Получает на вход дату для поиска, возвращает словарь с затмениями
    """
    dir_path = os.path.dirname(os.path.realpath(__file__))
    json_path = os.path.join(dir_path, "eclipse.json")

    with open(json_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    day, month, year = input_date.split()
    month = months[month]
    input_date = f"{day} {month} {year}"

    input_date = datetime.strptime(input_date, '%d %B %Y')

    closest_solar_eclipse = None
    closest_lunar_eclipse = None
    min_solar_delta = None
    min_lunar_delta = None

    for year, eclipses in data.items():
        for eclipse in eclipses['солнечные затмения']:
            _eclipse = eclipse["дата"] + " " + year
            eclipse_date = datetime.strptime(_eclipse, '%d %B %Y')
            delta = abs(eclipse_date - input_date)
            if min_solar_delta is None or delta < min_solar_delta:
                min_solar_delta = delta
                new_d, new_m, new_y = eclipse_date.strftime("%d %B %Y").split()
                inv_months = {v: k for k, v in months.items()}
                new_m = inv_months[new_m]

                closest_solar_eclipse = f"{new_d} {new_m} {new_y}"

        for eclipse in eclipses['лунные затмения']:
            eclipse_date = datetime.strptime(eclipse['дата'] + ' ' + year, '%d %B %Y')
            delta = abs(eclipse_date - input_date)
            if min_lunar_delta is None or delta < min_lunar_delta:
                min_lunar_delta = delta
                new_d, new_m, new_y = eclipse_date.strftime("%d %B %Y").split()
                inv_months = {v: k for k, v in months.items()}
                new_m = inv_months[new_m]
                closest_lunar_eclipse = f"{new_d} {new_m} {new_y}"

    return {
        "closest_solar_eclipse": closest_solar_eclipse,
        "days_to_solar_eclipse": min_solar_delta.days,
        "closest_lunar_eclipse": closest_lunar_eclipse,
        "days_to_lunar_eclipse": min_lunar_delta.days
    }


if __name__ == '__main__':

    # Пример использования
    user_input = "21 января 1956"

    result = find_nearest_eclipses(user_input)
    print(result)
