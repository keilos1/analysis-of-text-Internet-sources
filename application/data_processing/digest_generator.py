# data_processing/digest_generator.py

from datetime import datetime, timedelta
from pymongo.collection import Collection
import asyncio
import sys
from bson import ObjectId

sys.path.append("../")
from config.config import HOST, PORT, SSH_USER, SSH_PASSWORD, DB_NAME, MONGO_HOST, MONGO_PORT
from data_storage.database import connect_to_mongo
import logging

logger = logging.getLogger(__name__)

async def digest_generator():
    db, tunnel = connect_to_mongo(
        ssh_host=HOST,
        ssh_port=PORT,
        ssh_user=SSH_USER,
        ssh_password=SSH_PASSWORD,
        mongo_host=MONGO_HOST,
        mongo_port=MONGO_PORT,
        db_name=DB_NAME
    )

    try:
        now = datetime.utcnow()
        since = now - timedelta(hours=24)

        logger.info("Генерация дайджеста: статьи за последние 24 часа с duplicate_count > 0")

        # 1. Находим статьи с дубликатами
        primary_articles = list(db.articles.find(
            {
                "publication_date": {"$gte": since},
                "duplicate_count": {"$gt": 0}
            }
        ).sort("duplicate_count", -1).limit(3))

        count_needed = 3 - len(primary_articles)

        # 2. Если не хватает, добираем самые свежие статьи
        if count_needed > 0:
            additional_articles = list(db.articles.find(
                {"publication_date": {"$gte": since}}
            ).sort("publication_date", -1).limit(count_needed))

            # Исключим дубликаты, если вдруг они пересекаются
            existing_ids = {str(a["_id"]) for a in primary_articles}
            for art in additional_articles:
                if str(art["_id"]) not in existing_ids:
                    primary_articles.append(art)
                    if len(primary_articles) == 3:
                        break

        # 3. Сохраняем в digest
        db.daily_digest.delete_many({})

        # Обеспечим уникальные `_id` (если вдруг используется ObjectId())
        digest_docs = [art for art in primary_articles]
        db.daily_digest.insert_many(digest_docs)

        logger.info(f"Дайджест сформирован: {len(digest_docs)} статей")

    except Exception as e:
        logger.error(f"Ошибка при формировании дайджеста: {str(e)}")

    finally:
        if tunnel:
            tunnel.close()


def main():
    asyncio.run(digest_generator())


if __name__ == "__main__":
    main()
