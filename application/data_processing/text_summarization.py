import re
from typing import List, Dict, Union

def clean_html(text: str) -> str:
    """Удаляет HTML-теги из текста с помощью регулярного выражения"""
    return re.sub(r'<[^>]+>', '', text)

def summarize_texts_tfidf(data: Union[List[Dict], Dict]) -> Union[List[Dict], Dict]:
    """
    Добавляет суммаризированный текст (2 самых важных предложения) к каждому посту.
    С предварительной очисткой от HTML-тегов.
    """
    news_processor = NewsProcessor()
    filtered_data = news_processor.process_news()

    result = []
    for filtered_item in filtered_data:
        processed_item = filtered_item.copy()
        raw_text = processed_item.get("text", "")
        
        # Очищаем текст от HTML-тегов
        clean_text = clean_html(raw_text)
        processed_item["text"] = clean_text  # Сохраняем очищенный текст
        
        sentences = [sent.text for sent in nlp(clean_text).sents]

        if len(sentences) <= 2:
            processed_item["summary"] = clean_text.strip()
        else:
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform(sentences)
            sentence_scores = tfidf_matrix.sum(axis=1).A1

            top_indices = sentence_scores.argsort()[-2:][::-1]
            summary = ' '.join([sentences[i] for i in sorted(top_indices)])
            processed_item["summary"] = summary.strip()

        result.append(processed_item)

    return result

def print_news_with_summary(news_data: List[Dict]) -> None:
    """Выводит новости с очищенным текстом и суммаризацией"""
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
