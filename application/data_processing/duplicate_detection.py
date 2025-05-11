from sshtunnel import SSHTunnelForwarder
from pymongo import MongoClient
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict
import sys
import asyncio

sys.path.append("../")

from data_storage.database import connect_to_mongo
from data_processing.text_summarization import summarize_texts_tfidf
from config.config import HOST, PORT, SSH_USER, SSH_PASSWORD, DB_NAME


async def save_unique_articles(new_articles: List[Dict], threshold: float = 0.95) -> int:
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
        ssh_host=HOST,
        ssh_port=PORT,
        ssh_user=SSH_USER,
        ssh_password=SSH_PASSWORD,
        db_name=DB_NAME
    )
    
    try:
        # 1. Суммаризация новых статей (добавляем await)
        summarized_new = await summarize_texts_tfidf(new_articles)
        
        # 2. Загрузка существующих статей из базы
        existing_articles = list(db.articles.find(
            {}, 
            {"title": 1, "summary": 1, "url": 1, "article_id": 1, "_id": 0}
        ))
        
        saved_count = 0
        
        # 3. Если база пуста - сохраняем все статьи
        if not existing_articles:
            for article in summarized_new:
                db.articles.insert_one({
                    "article_id": article["article_id"],
                    "source_id": article.get("source_id", ""),
                    "title": article["title"],
                    "url": article["url"],
                    "publication_date": article.get("publication_date", ""),
                    "summary": article["summary"],
                    "text": article.get("text", ""),
                    "categories": article.get("categories", ["Другое"]),
                    "district": article.get("district", "Не указан")
                })
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
                db.articles.insert_one({
                    "article_id": article["article_id"],
                    "source_id": article.get("source_id", ""),
                    "title": article["title"],
                    "url": article["url"],
                    "publication_date": article.get("publication_date", ""),
                    "summary": article["summary"],
                    "text": article.get("text", ""),
                    "categories": article.get("categories", ["Другое"]),
                    "district": article.get("district", "Не указан")
                })
                saved_count += 1
        
        return saved_count
    finally:
        # Обязательно закрываем соединение
        tunnel.close()

async def async_main():
    """
    Асинхронный основной метод для обработки и сохранения новостей.
    Получает статьи из функции summarize_texts_tfidf и сохраняет уникальные.
    """
    print("="*50)
    print("СИСТЕМА ОБРАБОТКИ И СОХРАНЕНИЯ НОВОСТЕЙ")
    print("="*50)
    
    try:
        # Получаем обработанные новости (добавляем await)
        new_articles = await summarize_texts_tfidf([])
        
        if not new_articles:
            print("Нет новых статей для обработки")
            return
            
        print(f"Получено {len(new_articles)} новых статей для обработки")
        
        # Сохраняем уникальные статьи (добавляем await)
        saved_count = await save_unique_articles(new_articles)
        
        # Выводим результат
        print(f"\nСохранено {saved_count} уникальных статей из {len(new_articles)} обработанных")
        
    except Exception as e:
        print(f"\nОшибка при обработке новостей: {str(e)}")
    finally:
        print("\nРабота программы завершена")

def main():
    """Точка входа для синхронного вызова"""
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
