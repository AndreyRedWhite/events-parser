"""
Модуль для сбора данных с этого сайта: https://www.calend.ru/holidays/
"""
import logging
from bs4 import BeautifulSoup
import requests


headers = {
        "Accept": "*/*",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/116.0.0.0 Safari/537.36 "
}

logging.basicConfig(level="INFO")


def convert_date_to_url_format(day: str, mounth: str) -> str:
    """
    Данная функция преобразует тектовый формат даты вида 1 Мая в вид 9-1, который потом будет использован
    в генерации url ссылок
    """
    # Словарь для конвертации названий месяцев в их числовые эквиваленты
    month_conversion = {
        "января": "1",
        "февраля": "2",
        "марта": "3",
        "апреля": "4",
        "мая": "5",
        "июня": "6",
        "июля": "7",
        "августа": "8",
        "сентября": "9",
        "октября": "10",
        "ноября": "11",
        "декабря": "12"
    }

    day, month = day, mounth

    # Конвертируем месяц и формируем итоговую строку
    month_number = month_conversion.get(month.lower())
    if month_number:
        return f"{month_number}-{day}"
    else:
        raise ValueError(f"Некорректное название месяца: {month}")


def page_graber(day: str, mounth: str, save=True) -> str:
    """
    Данная функция получает на вход текстовую дату, с помощью другой функции convert_date_to_url_format преобразует
    в правильный формат, добавляет к url и забирает страницу по указанной дате
    """
    url_date = convert_date_to_url_format(day, mounth)
    url = "https://www.calend.ru/holidays/" + url_date

    res = requests.get(url, headers=headers).text
    # Сохраняет страницу для последующего парсинга
    if save:
        with open(f"holiday_{url_date}.html", "w") as f:
            f.write(res)

    return res


def page_parcer(data=None, date=False) -> list:
    """
    Функция для парсинга данных с страницы. На вход получает преобразованную дату, на выходе возвращает
    список с заголовками по указанной дате
    """
    if date:
        with open(f"holiday_{date}.html") as f:
            data = f.read()
            soup = BeautifulSoup(data, "lxml")
            result = soup.find("div", class_="holidays").find_all("span", class_="title")

    elif data:
        soup = BeautifulSoup(data, "lxml")
        result = soup.find("div", class_="holidays").find_all("span", class_="title")

    holidays = []
    for item in result:
        holidays.append(item.text)

    return holidays


def holidays(day: str, month: str) -> list:
    """
    Основная функция для управления функциями-загрузчиками и функциями-парсерами данных
    :param day: день из даты;
    :param month: месяц из переданной даты;
    :return: holidays: списсок с событиями за переданных период
    """
    page = page_graber(day, month, save=False)
    holidays = page_parcer(page)
    return holidays


if __name__ == '__main__':
    holidays("2", "января")
