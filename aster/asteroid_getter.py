"""
Модуль для загрузки данных об астероидах с ресурса https://ssd-api.jpl.nasa.gov
"""
from datetime import datetime, timedelta
import requests
from pprint import pprint

headers = {
        "Accept": "*/*",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
}

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


def get_asters(date: str) -> list:
    """
    Функция получает на вход дату, разбирает ее, формирует url для api запроса. получает результат и записывает его в
    список
    :param date: дата, строка
    :return: result, список
    """
    day, month, year = date.split()
    month = months[month]
    input_date = f"{day} {month} {year}"

    date_min = datetime.strptime(input_date, '%d %B %Y').date()
    date_max = date_min + timedelta(days=1)

    url = f"https://ssd-api.jpl.nasa.gov/cad.api?dist-max=0.2&date-min={date_min}&date-max={date_max}&diameter=true&fullname=true&sort=dist"
    res = requests.get(url, headers=headers)
    if res.json()["count"] == 0:
        return []
    elif res.json()["count"] > 0:
        data = res.json()["data"]
        result = []
        for asteroid in data:
            result.append({
                "des": asteroid[0],
                "cd": asteroid[3],
                "dist": asteroid[4],
                "dist_min": asteroid[5],
                "dist_max": asteroid[6]
            })
        result = sort_by_date(result)
        return result


def sort_by_date(objects):
    # Функция для преобразования строки даты в объект datetime
    def parse_date(date_str):
        return datetime.strptime(date_str, '%Y-%b-%d %H:%M')

    # Сортировка списка объектов по ключу 'cd'
    return sorted(objects, key=lambda x: parse_date(x['cd']))


if __name__ == '__main__':
    pprint(get_asters("26 декабря 1970"), width=200)