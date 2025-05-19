from typing import List, Dict  # Добавьте этот импорт в начало файла
from sshtunnel import SSHTunnelForwarder
from pymongo import MongoClient
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import sys
import asyncio
from scipy.sparse import vstack


sys.path.append("../")

from data_storage.database import connect_to_mongo
from data_processing.text_summarization import summarize_texts_tfidf
from config.config import HOST, PORT, SSH_USER, SSH_PASSWORD, DB_NAME, MONGO_HOST, MONGO_PORT

async def save_unique_articles(summarized_new: List[Dict], threshold: float = 0.15) -> int:
    if not summarized_new:
        return 0

    db, tunnel = None, None
    try:
        db, tunnel = connect_to_mongo(
            ssh_host=HOST,
            ssh_port=PORT,
            ssh_user=SSH_USER,
            ssh_password=SSH_PASSWORD,
            mongo_host=MONGO_HOST,
            mongo_port=MONGO_PORT,
            db_name=DB_NAME
        )

        valid_articles = []
        for article in summarized_new:
            if not all(key in article for key in ['title', 'url', 'summary']):
                print(f"Пропущена статья с отсутствующими полями: {article.get('article_id', 'без ID')}")
                continue
            article["duplicate_count"] = 0  # инициализация
            valid_articles.append(article)

        if not valid_articles:
            print("Нет валидных статей для обработки")
            return 0

        existing_articles = list(db.articles.find(
            {},
            {"title": 1, "summary": 1, "text": 1, "url": 1, "article_id": 1, "_id": 0}
        ))

        saved_count = 0
        articles_to_save = []  # собираем статьи для финальной записи
        inserted_urls = set()

        def normalize(text):
            return ' '.join(text.lower().split())

        existing_texts = [
            normalize(f"{art.get('title', '')} {art.get('summary', '')} {art.get('text', '')}")
            for art in existing_articles
        ]
        new_texts = [
            normalize(f"{art.get('title', '')} {art.get('summary', '')} {art.get('text', '')}")
            for art in valid_articles
        ]

        vectorizer = TfidfVectorizer()
        combined_texts = existing_texts + new_texts
        combined_matrix = vectorizer.fit_transform(combined_texts)

        existing_matrix = combined_matrix[:len(existing_texts)]
        new_matrix = combined_matrix[len(existing_texts):]

        similarity_with_existing = cosine_similarity(new_matrix, existing_matrix) if existing_texts else None
        similarity_within_new = cosine_similarity(new_matrix)

        for i, article in enumerate(valid_articles):
            try:
                if db.articles.find_one({"url": article["url"]}):
                    continue
                if db.articles.find_one({"title": article["title"], "summary": article["summary"]}):
                    continue

                max_existing_sim = 0
                index_max_sim = None
                if similarity_with_existing is not None:
                    sim_existing = similarity_with_existing[i]
                    if sim_existing.size > 0:
                        max_existing_sim = max(sim_existing)
                        index_max_sim = sim_existing.argmax()

                sim_internal = similarity_within_new[i][:i]
                max_internal_sim = max(sim_internal) if sim_internal.size > 0 else 0
                index_internal_sim = sim_internal.argmax() if sim_internal.size > 0 else None

                # Дубликат существующей статьи → увеличиваем счётчик
                if max_existing_sim >= threshold and index_max_sim is not None:
                    most_similar_article = existing_articles[index_max_sim]
                    db.articles.update_one(
                        {"url": most_similar_article["url"]},
                        {"$inc": {"duplicate_count": 1}}
                    )
                    continue

                # Дубликат уже пройденной новой статьи → увеличиваем счётчик у неё
                if max_internal_sim >= threshold and index_internal_sim is not None:
                    valid_articles[index_internal_sim]["duplicate_count"] += 1
                    continue

                # Статья уникальна → вычисляем её собственный duplicate_count
                duplicate_count = 0
                if similarity_with_existing is not None:
                    duplicate_count += int((similarity_with_existing[i] >= threshold).sum())
                duplicate_count += int((similarity_within_new[i][:i] >= threshold).sum())

                article["duplicate_count"] = duplicate_count

                articles_to_save.append(article)
                inserted_urls.add(article["url"])
                saved_count += 1

            except Exception as e:
                print(f"Ошибка при обработке статьи {article.get('article_id')}: {str(e)}")

        # Финальная запись всех уникальных и обновлённых статей
        for article in articles_to_save:
            try:
                db.articles.replace_one(
                    {"url": article["url"]},
                    article,
                    upsert=True
                )
            except Exception as e:
                print(f"Ошибка при финальной записи статьи {article.get('article_id')}: {str(e)}")

        return saved_count

    except Exception as e:
        print(f"Ошибка в save_unique_articles: {str(e)}")
        return 0

    finally:
        if tunnel:
            tunnel.close()
            print("SSH туннель закрыт")



async def async_main():
    print("="*50)
    print("СИСТЕМА ОБРАБОТКИ И СОХРАНЕНИЯ НОВОСТЕЙ")
    print("="*50)

    try:
        summarized_articles = await summarize_texts_tfidf([])

        if not summarized_articles:
            print("Нет новых статей для обработки")
            return

        print(f"Получено {len(summarized_articles)} новых статей для обработки")

        saved_count = await save_unique_articles(summarized_articles)

        print(f"\nСохранено {saved_count} уникальных статей из {len(summarized_articles)} обработанных")

    except Exception as e:
        print(f"\nОшибка при обработке новостей: {str(e)}")
    finally:
        print("\nРабота программы завершена")

def main():
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
