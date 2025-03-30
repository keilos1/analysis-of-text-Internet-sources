# Интерфейс для работы с MongoDb
from pymongo import MongoClient


class Database:
    def __init__(self, db_name="news_database", host="localhost", port=27017):
        self.client = MongoClient(host, port)
        self.db = self.client[db_name]
        self.articles = self.db.articles
        self.sources = self.db.sources

    def save_article(self, article):
        self.articles.update_one(
            {"url": article["url"]},
            {"$set": article},
            upsert=True
        )

    def get_sources(self):
        return list(self.sources.find({}, {"_id": 0}))
