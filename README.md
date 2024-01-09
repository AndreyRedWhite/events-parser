# Event-Parser

Данный проект позволяет парсить информацию с таких источников, как:

- https://ssd-api.jpl.nasa.gov/ - данные об астероидах
- https://astrologway.ru/2017/02/25/kalendar-zatmeniy-s-1900-po-2050/ - данные о затмениях
- https://www.calend.ru/holidays/ - праздничные дни
- страници из Wiki по дням, месяцам и годам


## Начало работы
Эти инструкции помогут вам запустить копию проекта на вашем локальном компьютере.

##### Предварительные условия
###### Что нужно установить для запуска вашего проекта:

 Python 3.8 или выше
 pip (менеджер пакетов Python)

##### Установка проекта с GitHub
###### Для пользователей с установленным Git

1.Клонирование репозитория
```
git clone https://github.com/AndreyRedWhite/events-parser.git
cd events-parser
```
2.Создание виртуального окружения и установка зависимостей
```
python -m venv venv
# Для Windows
.\venv\Scripts\activate
# Для Unix или MacOS
source venv/bin/activate

pip install -r requirements.txt
```
3.Запуск приложения
```
python main.py
```
###### Для пользователей без Git
1.Скачивание проекта

 - Перейдите на страницу репозитория: https://github.com/AndreyRedWhite/events-parser
 - Нажмите на кнопку Code и выберите Download ZIP.
 - Распакуйте скачанный ZIP-архив.
 
2.Создание виртуального окружения и установка зависимостей
```
python -m venv venv
# Для Windows
.\venv\Scripts\activate
# Для Unix или MacOS
source venv/bin/activate

pip install -r requirements.txt
```

3.Запуск приложения
```
python main.py
```

## Использование

Данный проект позволяет выполнять 2 задачи:
- парсинг событий по определенной дате
- поиск событий в определенный период по ключевым словам

При запуске пользователю предоставляется выбор, необходимо ввести 1 или 2:
```
Выберете действие:
1. Поиск событий по определенной дате
2. Поиск событий в определенный период по ключевым словам
Ваш выбор: 
```
##### Поиск событий по определенной дате
При выборе 1-го варианта необходимо ввести нужную дату в формате `1 июня 2021`:
```
Введите дату в формате "Число Месяц Год", например "13 мая 2021": 1 июня 2021
```
Результат парсинга будет сохранен в директории `results` в виде `result_{{ дата }}.xlsx`

##### Поиск событий в определенный период по ключевым словам
При выборе 2-го варианта, то есть поиска событий по ключевым словам, будет предложено выбрать варианты поиска. Есть такие:
1. Строгий поиск на совпадение поисковой фразы - ищет полное совпадение поисковой фразы и текста события. Дает 100% результат, если поисковая фраза присутствует в переданном виде, но может пропускать события, если какое-то слово в поисковой фразе отличается от текста события.
2. Неточный поиск, использует стемминг и другие методы нормализации, которые уменьшают слова до их корневой формы, сохраняя при этом смысловую нагрузку. При этом поиск может давать False Positive результаты.
```
Выберите вариант поиска:
1. Строгий поиск на совпадение поисковой фразы
2. Неточный поиск, использует стемминг и другие методы нормализации, которые уменьшают слова до их корневой формы, сохраняя при этом смысловую нагрузку. При этом поиск может давать False Positive результаты.
Ваш выбор: 
```
###### Строгий поиск
При выборе 1-го варианта далее необходимо будет ввести поисковую фразу. Нужно вводить ее в таком виде, в котором она должна присутствовать с искомом событии, например "Чемпионат мира"
```
Введите запрос на поиск (например 'Пожар во Франции'): Чемпионат мира
```
Далее необходимо задать интервал для поиска, строго в формате `1 января 2021 - 31 декабря 2021`, то есть 2 даты через пробел и тире. Проект расчитан на опытных пользователей, понимающих, что они делают, обработка ошибок в проект не включена!
```
Введите интервал дат для поиска в формате '1 января 1990 - 31 декабря 2022':
```
После введения нужного диапазона запускаются функции-загрузчики, парсеры и поисковики. Если какие-то даты будут найдены - они будут выведены на экран, а события по ним будут спарсены и сохранены в файл в директории `results` с именем `result_Строгий_поиск_{{ поисковый запрос }}_{интервал дат}}.xlsx`

###### Нестрогий поиск
При выборе неточного поиска далее необходимо будет ввести поисковую фразу. Нужно вводить ключевые слова через пробел, в именительном падеже, без склонений и без союзов, например `пожар кинотеатр`
```
Введите запрос на поиск (например 'Пожар во Франции'): пожар кинотеатр
```
Далее следуют 2 опциональных параметра.
1. Страна - можно указывать одну или несколько стран через пробел, в этом случае по каждой стране из файла wiki/countries_parser/countries.json будет взят список всех городов по стране, если такая есть в этом файле. Далее каждый город будет добавляться к поисковой фразе и полученная фраза будет сравниваться с текстом каждого события. Стоит использовать с осторожностью, нужно отдавать отчет, что каждая страна содержит 50+ городов, то есть поиск будет увеличиваться на такое количество итераций по каждому событию.
2. Город - можно указать один или несколько городов через пробел, в этом случае каждый город будет добавляться к поисковой фразе и полученная фраза будет сравниваться с текстом каждого события.

Можно использовать оба параметра, можно использовать только какой-то один, можно их не использовать совсем (просто нажать `enter` при соответствующем запросе)
```
(опционально) введите одну или несколько стран через пробел для поиска (или просто нажмите Enter, если не хотие): Франция
(опционально) введите один или несколько городов через проблем для поиска (или просто нажмите Enter, если не хотите): Берлин
```

Далее необходимо задать интервал для поиска, строго в формате `1 января 2021 - 31 декабря 2021`, то есть 2 даты через пробел и тире. Проект расчитан на опытных пользователей, понимающих, что они делают, обработка ошибок в проект не включена!
```
Введите интервал дат для поиска в формате '1 января 1990 - 31 декабря 2022':
```
После введения нужного диапазона запускаются функции-загрузчики, парсеры и поисковики. Если какие-то даты будут найдены - они будут выведены на экран, а события по ним будут спарсены и сохранены в файл в директории `results` с именем `result_Неточный_поиск_{{ поисковая фраза }}_{{ страны и города, если использовались }}_{{ интервал дат }}.xlsx`

##### Добавление своих proxy
В директории `wiki` необходимо открыть модуль `requests_config.py`, закоментировать код `proxies=None`, раскоментировать код с словарем proxies, добавив свои прокси в значение ключа https.

```
requests_config.py
proxies = None

# Чтобы использовать ваш прокси, закоментируйте строку выше и раскоментируйте код ниже, заменив строку со значением
# на ваш прокси
#
# proxies = {
#     "https": "http://login:password@123.45.67.8:8000"
# }
```
В этом же файле можно поменять User-Agent на свой, если предоставленный не устраивает.


## Лицензия

MIT

**Free Software, Hell Yeah!**


