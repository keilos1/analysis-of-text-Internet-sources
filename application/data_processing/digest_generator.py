# data_processing/digest_generator.py

from datetime import datetime, timedelta
from pymongo.collection import Collection
import sys
sys.path.append("../")
from config.config import HOST, PORT, SSH_USER, SSH_PASSWORD, DB_NAME, MONGO_HOST, MONGO_PORT
from data_storage.database import connect_to_mongo
import logging

logger = logging.getLogger(__name__)


async def digest_generator(top_n: int = 5):
    """
    Формирует дайджест из топ-N статей с наибольшим duplicate_count
    за последние 24 часа и сохраняет их в коллекцию digest.
    """
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

        logger.info("Генерация дайджеста: отбираем статьи с %s", since.isoformat())

        articles = list(db.articles.find(
            {
                "publication_date": {"$gte": since},
                "duplicate_count": {"$gt": 0}
            }
        )
        .sort("duplicate_count", -1)
        .limit(top_n))

        # Перезапись коллекции digest
        db.digest.delete_many({})
        if articles:
            db.digest.insert_many(articles)
            logger.info("Сохранено %d статей в дайджест", len(articles))
        else:
            logger.info("Нет подходящих статей для дайджеста")

    except Exception as e:
        logger.error(f"Ошибка при формировании дайджеста: {str(e)}")

    finally:
        if tunnel:
            tunnel.close()
