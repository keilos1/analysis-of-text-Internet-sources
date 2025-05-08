from sshtunnel import SSHTunnelForwarder
from pymongo import MongoClient
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict
from text_summarization import summarize_texts_tfidf


def save_unique_articles(self, new_articles, threshold=0.95):
    """
    Сохраняет только уникальные статьи через метод save_article
    """
    if not new_articles:
        return 0
    
    # 1. Суммаризация
    summarized_new = summarize_texts_tfidf(new_articles)
    
    # 2. Загрузка существующих статей
    existing_articles = list(self.articles.find(
        {}, 
        {"title": 1, "summary": 1, "url": 1, "article_id": 1, "_id": 0}
    ))
    
    saved_count = 0
    
    # 3. Для пустой базы - сохраняем все через save_article
    if not existing_articles:
        for article in summarized_new:
            self.save_article(
                article_id=article["article_id"],
                source_id=article.get("source_id", ""),
                title=article["title"],
                url=article["url"],
                publication_date=article.get("publication_date", ""),
                summary=article["summary"],
                text=article.get("text", "")
            )
            saved_count += 1
        return saved_count
    
    # 4. Подготовка данных для сравнения
    existing_texts = [f"{art['title']} {art['summary']}" for art in existing_articles]
    new_texts = [f"{art['title']} {art['summary']}" for art in summarized_new]
    
    vectorizer = TfidfVectorizer()
    existing_matrix = vectorizer.fit_transform(existing_texts)
    new_matrix = vectorizer.transform(new_texts)
    
    # 5. Фильтрация и сохранение через save_article
    for i, article in enumerate(summarized_new):
        # Проверка по URL
        if self.articles.find_one({"url": article["url"]}):
            continue
        
        # Проверка по содержанию
        similarities = cosine_similarity(new_matrix[i], existing_matrix)[0]
        max_similarity = max(similarities) if similarities.size > 0 else 0
        
        if max_similarity < threshold:
            self.save_article(
                article_id=article["article_id"],
                source_id=article.get("source_id", ""),
                title=article["title"],
                url=article["url"],
                publication_date=article.get("publication_date", ""),
                summary=article["summary"],
                text=article.get("text", "")
            )
            saved_count += 1
    
    return saved_count
