import re
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from typing import List, Dict, Union
from filtering import NewsProcessor


# Загружаем модель spaCy для русского языка
nlp = spacy.load("ru_core_news_sm")


def summarize_texts_tfidf(data: Union[List[Dict], Dict]) -> Union[List[Dict], Dict]:
    """
    Добавляет суммаризированный текст (2 самых важных предложения) к каждому посту.
    Использует TF-IDF для определения важности предложений.
    Перед обработкой вызывает функцию фильтрации (process_news) для получения обработанных данных.
    Всегда работает со списком словарей, полученных после фильтрации.
    """
    # Создаем экземпляр NewsProcessor для вызова функции фильтрации
    news_processor = NewsProcessor()

    # Вызываем функцию фильтрации для получения обработанных данных
    filtered_data = news_processor.process_news()

    # Обрабатываем все отфильтрованные элементы
    result = []
    for filtered_item in filtered_data:
        # Создаем копию элемента, чтобы не изменять исходные данные
        processed_item = filtered_item.copy()
        text = processed_item.get("text", "")
        sentences = [sent.text for sent in nlp(text).sents]

        if len(sentences) <= 2:
            processed_item["summary"] = text.strip()
        else:
            # Рассчитываем TF-IDF для каждого предложения
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform(sentences)
            sentence_scores = tfidf_matrix.sum(axis=1).A1

            # Выбираем 2 предложения с наибольшими оценками
            top_indices = sentence_scores.argsort()[-2:][::-1]
            summary = ' '.join([sentences[i] for i in sorted(top_indices)])
            processed_item["summary"] = summary.strip()

        result.append(processed_item)

    return result


def print_news_with_summary(news_data: List[Dict]) -> None:
    """
    Выводит новости в консоль с суммаризацией и основной информацией
    """
    if not news_data:
        print("Новостей для отображения нет")
        return

    for i, news_item in enumerate(news_data, 1):
        print(f"\nНовость #{i}")
        print("-" * 50)
        print(f"Заголовок: {news_item.get('title', 'Без заголовка')}")
        print(f"Район: {news_item.get('location', {}).get('district', 'Не указан')}")
        print(f"Категории: {', '.join(news_item.get('categories', ['Другое']))}")
        print(f"\nПолный текст:\n{news_item.get('text', 'Текст отсутствует')}")
        print(f"\nСуммаризация (ключевые предложения):\n{news_item.get('summary', 'Не удалось сгенерировать')}")
        print("-" * 50)


def main():
    """
    Основная функция для запуска обработки и вывода новостей
    """
    try:
        # Получаем данные с суммаризацией
        summarized_news = summarize_texts_tfidf([])
        
        # Выводим результат в консоль
        print_news_with_summary(summarized_news)
        
        # Дополнительная информация
        print(f"\nВсего обработано новостей: {len(summarized_news)}")
    except Exception as e:
        print(f"Произошла ошибка при обработке новостей: {str(e)}")


if __name__ == "__main__":
    main()
