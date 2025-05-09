from sshtunnel import SSHTunnelForwarder
from pymongo import MongoClient
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict
import sys
sys.path.append("../")
from data_storage.database import connect_to_mongo
from data_storage.database import save_article
from data_processing.text_summarization import summarize_texts_tfidf

# Константы подключения
SSH_HOST = '78.36.44.126'
SSH_PORT = 57381
SSH_USER = 'server'
SSH_PASSWORD = 'tppo'
DB_NAME = 'newsPTZ'

def save_unique_articles(new_articles: List[Dict], threshold: float = 0.95) -> int:
    """
    Сохраняет только уникальные статьи в базу данных.
    Возвращает количество сохраненных статей.
    
    Args:
        new_articles: Список новых статей для сохранения
        threshold: Порог схожести для определения уникальности (0-1)
        
    Returns:
        Количество сохраненных уникальных статей
    """
    if not new_articles:
        return 0
    
    # Подключаемся к базе данных
    db, tunnel = connect_to_mongo(
        ssh_host=SSH_HOST,
        ssh_port=SSH_PORT,
        ssh_user=SSH_USER,
        ssh_password=SSH_PASSWORD,
        db_name=DB_NAME
    )
    
    try:
        # 1. Суммаризация новых статей
        summarized_new = summarize_texts_tfidf(new_articles)
        
        # 2. Загрузка существующих статей из базы
        existing_articles = list(db.articles.find(
            {}, 
            {"title": 1, "summary": 1, "url": 1, "article_id": 1, "_id": 0}
        ))
        
        saved_count = 0
        
        # 3. Если база пуста - сохраняем все статьи
        if not existing_articles:
            for article in summarized_new:
                db.save_article(
                    article_id=article["article_id"],
                    source_id=article.get("source_id", ""),
                    title=article["title"],
                    url=article["url"],
                    publication_date=article.get("publication_date", ""),
                    summary=article["summary"],
                    text=article.get("text", ""),
                    category=article.get("category", ""),
                    district=article.get("district", "")
                )
                saved_count += 1
            return saved_count
        
        # 4. Подготовка данных для сравнения схожести
        existing_texts = [f"{art['title']} {art['summary']}" for art in existing_articles]
        new_texts = [f"{art['title']} {art['summary']}" for art in summarized_new]
        
        vectorizer = TfidfVectorizer()
        existing_matrix = vectorizer.fit_transform(existing_texts)
        new_matrix = vectorizer.transform(new_texts)
        
        # 5. Фильтрация и сохранение уникальных статей
        for i, article in enumerate(summarized_new):
            # Проверка на дубликат по URL
            if db.articles.find_one({"url": article["url"]}):
                continue
            
            # Проверка на схожесть по содержанию
            similarities = cosine_similarity(new_matrix[i], existing_matrix)[0]
            max_similarity = max(similarities) if similarities.size > 0 else 0
            
            if max_similarity < threshold:
                db.save_article(
                    article_id=article["article_id"],
                    source_id=article.get("source_id", ""),
                    title=article["title"],
                    url=article["url"],
                    publication_date=article.get("publication_date", ""),
                    summary=article["summary"],
                    text=article.get("text", ""),
                    category=article.get("category", ""),
                    district=article.get("district", "")
                )
                saved_count += 1
        
        return saved_count
    finally:
        # Обязательно закрываем соединение
        tunnel.close()

def main():
    saved_count = save_unique_articles()
    print(f"Успешно сохранено {saved_count} новых статей")

if __name__ == "__main__":
    main()
