# Интерфейс для работы с MongoDb
from sshtunnel import SSHTunnelForwarder
from pymongo import MongoClient


class Database:
    def __init__(self, db):
        self.db = db
        self.articles = self.db.articles
        self.sources = self.db.sources
        self.daily_digest = self.db.daily_digest

    def save_article(self, article_id, source_id, title, url, publication_date, summary, text):
        article = {
            "article_id": article_id,
            "source_id": source_id,
            "title": title,
            "url": url,
            "publication_date": publication_date,
            "summary": summary,
            "text": text,
            "categories": categories,
            "district": district
        }
        self.articles.update_one(
            {"article_id": article_id},
            {"$set": article},
            upsert=True
        )

    def save_source(self, source_id, name, url, category, district, area_of_the_city, last_checked_time):
        source = {
            "source_id": source_id,
            "name": name,
            "url": url,
            "category": category,
            "district": district,
            "area_of_the_city": area_of_the_city,
            "last_checked_time": last_checked_time
        }
        self.sources.update_one(
            {"source_id": source_id},
            {"$set": source},
            upsert=True
        )

    def save_daily_digest(self, daily_digest_id, date, article_id, category_distribution):
        daily_digest = {
            "daily_digest_id": daily_digest_id,
            "date": date,
            "article_id": article_id,
            "category_distribution": category_distribution
        }
        self.daily_digest.update_one(
            {"daily_digest_id": daily_digest_id},
            {"$set": daily_digest},
            upsert=True
        )

    def get_source(self, source_id):
        source = self.sources.find_one(
            {"source_id": source_id},
            {"_id": 0}
        )
        return source


def connect_to_mongo(
    ssh_host,
    ssh_port,
    ssh_user,
    ssh_password,
    mongo_host,
    mongo_port,
    db_name
):
    if not ssh_host:
        # Локальное подключение без SSH-туннеля
        client = MongoClient(mongo_host, mongo_port)
        db = client[db_name]
        return Database(db), None
    else:
        # Подключение через SSH-туннель
        tunnel = SSHTunnelForwarder(
            (ssh_host, ssh_port),
            ssh_username=ssh_user,
            ssh_password=ssh_password,
            remote_bind_address=(mongo_host, mongo_port)  # используем новые имена
        )
        tunnel.start()
        client = MongoClient('127.0.0.1', tunnel.local_bind_port)
        db = client[db_name]
        return Database(db), tunnel

