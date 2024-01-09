"""
Модуль содержит заголовки а также возмонжость настроить proxy для запросов к Wiki
"""

headers = {
        "Accept": "*/*",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/116.0.0.0 Safari/537.36 "
}

proxies = None

# Чтобы использовать ваш прокси, закоментируйте строку выше и раскоментируйте код ниже, заменив строку со значением
# на ваш прокси
#
# proxies = {
#     "https": "http://login:password@123.45.67.8:8000"
# }
