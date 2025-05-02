import re
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from typing import List, Dict

# Загружаем модель spaCy для русского языка
nlp = spacy.load("ru_core_news_sm")

def summarize_texts_tfidf(data: List[Dict]) -> List[Dict]:
    """
    Добавляет суммаризированный текст (2 самых важных предложения) к каждому посту.
    Использует TF-IDF для определения важности предложений.
    """
    for item in data:
        text = item.get("text", "")
        sentences = [sent.text for sent in nlp(text).sents]  # Разбиваем на предложения с помощью spaCy

        if len(sentences) <= 2:
            item["summary"] = text.strip()
            continue

        # Рассчитываем TF-IDF для каждого предложения
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(sentences)
        sentence_scores = tfidf_matrix.sum(axis=1).A1  # Оценки важности предложений

        # Выбираем 2 предложения с наибольшими оценками
        top_indices = sentence_scores.argsort()[-2:][::-1]
        summary = ' '.join([sentences[i] for i in sorted(top_indices)])

        item["summary"] = summary.strip()

    return data