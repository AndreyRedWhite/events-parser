"""
Модуль для загрузки ресурса с url https://astrologway.ru/2017/02/25/kalendar-zatmeniy-s-1900-po-2050/ и
парсинга данных из него в json
"""
import json

from bs4 import BeautifulSoup
import requests
from pprint import pprint


headers = {
        "Accept": "*/*",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
}

# parce web page, save to file. Don't use after grabing data

# url = "https://astrologway.ru/2017/02/25/kalendar-zatmeniy-s-1900-po-2050/"
#
# res = requests.get(url, headers=headers).text
#
# with open("eclipse.html", "w") as f:
#     f.write(res)


# read file and parce via BS
with open("eclipse.html") as f:
    src = f.read()

soup = BeautifulSoup(src, "lxml")
table = soup.table

rows = table.find_all("tr")

mounths = {
    "янв.": "January",
    "фев.": "February",
    "марта": "March",
    "апр.": "April",
    "мая": "May",
    "июня": "June",
    "июля": "July",
    "авг.": "August",
    "сент.": "September",
    "окт.": "October",
    "нояб.": "November",
    "иояб.": "November",
    "дек.": "December"
}

# data structure
eclipses = {}

# current year variable
current_year = None

# working with table TR data
for row in rows[1:]:
    cells = row.find_all('td')

    # check wheter an year column contains a year
    if cells[0].get_text().strip():
        current_year = cells[0].get_text().strip()
        eclipses[current_year] = {
            "солнечные затмения": [],
            "лунные затмения": []
        }

    # adding eclipse data
    if current_year:
        # check for sun ecliplse for given year
        if cells[1].get_text().strip() and cells[2].get_text().strip() and cells[3].get_text().strip():
            if len(cells[1].get_text().strip().split()) == 2:
                day, mounth = cells[1].get_text().strip().split()
                date = f"{day} {mounths[mounth.lower()]}"
                eclipses[current_year]["солнечные затмения"].append({
                    "дата": date,
                    "затмение": cells[2].get_text().strip(),
                })

        # check for moon ecliplse for given year
        if cells[4].get_text().strip() and cells[5].get_text().strip():
            if len(cells[4].get_text().strip().split()) == 2:
                day, mounth = cells[4].get_text().strip().split()
                date = f"{day} {mounths[mounth.lower()]}"
                eclipses[current_year]["лунные затмения"].append({
                    "дата": date,
                    "затмение": cells[5].get_text().strip(),
                })
            elif len(cells[4].get_text().strip().split()) == 3:
                day, mounth, new_year = cells[4].get_text().strip().split()
                date = f"{day} {mounths[mounth.lower()]}"
                new_year = new_year.strip("()")
                temp_eclipse_moon = {new_year: {"лунные затмения": []}}
                temp_eclipse_moon[new_year]["лунные затмения"].append({
                    "дата": date,
                    "затмение": cells[5].get_text().strip(),
                })
                # eclipses.update(**temp_eclipse_moon)


if __name__ == '__main__':
    # Save data to file
    with open("eclipse.json", "w") as f:
        json.dump(eclipses, f, indent=4, ensure_ascii=False)

    # open file to test functionality
    with open("eclipse.json") as f:
        json_data = json.load(f)

    # choose the year, may add sun or moon eclipse
    year_1990 = json_data["1936"]
    pprint(year_1990, width=200)
