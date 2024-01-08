"""
Модуль для реализации неточного поиска
"""
import re
import json

from nltk.stem.snowball import SnowballStemmer
from natasha import (
    Segmenter,
    MorphVocab,
    NewsEmbedding,
    NewsMorphTagger,
    Doc
)
from concurrent.futures import ThreadPoolExecutor, as_completed


# Инициализация стеммера и компонентов Natasha
stemmer = SnowballStemmer("russian")
segmenter = Segmenter()
morph_vocab = MorphVocab()
emb = NewsEmbedding()
morph_tagger = NewsMorphTagger(emb)

file = "wiki/countries_parser/countries.json"
# file = "countries.json"
with open(file, "r", encoding="utf-8") as f:
    cities_by_country = json.load(f)


def normalize_and_stem_text(text: str) -> str:
    "Функция для нормализации текста. Делает страшные вещи, которые я сам не понимаю"
    text = re.sub(r'[^\w\s]', '', text).lower()
    # Лемматизация с помощью Natasha
    doc = Doc(text)
    doc.segment(segmenter)
    doc.tag_morph(morph_tagger)

    for token in doc.tokens:
        token.lemmatize(morph_vocab)

    # Стемминг каждого токена
    stemmed_words = [stemmer.stem(_.lemma) for _ in doc.tokens]
    return ' '.join(stemmed_words)


def search_in_city(normalized_text: str, normalized_phrase: list, city: str) -> bool:
    """
    Функция для поиска совпадения нормализованной поисковой фразы, к которой добавляется строка с городом и
    текстом события
    :param normalized_text: строка с нормализованным текстом события;
    :param normalized_phrase: строка с нормализованной поисковой фразой;
    :param city: строка с городом, который добавляется к нормализованной поисковой фразе
    :return: True или False, если все совпадения найдены
    """
    city_lower = city.lower()
    words_in_text = normalized_text.split()

    if all(word in normalized_text for word in normalized_phrase):
        for word in words_in_text:
            if word.startswith(city_lower):
                return True
    return False


def search_phrase_in_text(text: str, phrase: str, countries: str = None, cities: str = None) -> bool:
    """
    Функция для выполнения поиска ключевой фразы, к которой может добавится город. Использует многопоточность для
    ускорения поиска

    :param text: текст события;
    :param phrase: поисковая строка;
    :param countries: страна или страны через пробел, если передан - выполняется загрузка списка городов по стране
    из json файла
    :param cities: город или города через пробел, если передан - города добавляются к поисковой фразе
    :return: True, если совпадение найдено, False - если нет
    """
    normalized_text = normalize_and_stem_text(text)
    normalized_phrase = normalize_and_stem_text(phrase).split()

    combined_cities = set()

    if countries:
        for country in countries.split():
            country_key = country.capitalize()  # Или другой метод стандартизации названий стран
            if country_key in cities_by_country.keys():
                combined_cities.update(cities_by_country[country_key])

    if cities:
        for city in cities.split():
            combined_cities.add(city)

    # Если ни страны, ни города не предоставлены, проверяем только фразу в тексте
    if not combined_cities:
        words_in_text = normalized_text.split()
        return any(word in words_in_text for word in normalized_phrase)

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(search_in_city, normalized_text, normalized_phrase, city) for city in combined_cities]
        for future in as_completed(futures):
            if future.result():
                return True

        return False


if __name__ == '__main__':
    text = "произошел пожар в Лейпцигском магазине"
    phrase = "пожар"
    country = "Германия Австрия"

    print(search_phrase_in_text(text, phrase, country))
