# Полнотекстовый поиск по базе данных
from pymongo import MongoClient, TEXT
from typing import List, Dict
from data_storage.database import db  # Импорт подключения


class NewsSearch:
    def __init__(self, articles_collection=None):
        """
        :param articles_collection: Коллекция articles из MongoDB
        """
        self.articles = articles_collection or db.get_collection("articles")
        self._create_text_index()

    def _create_text_index(self):
        """
        Создание текстового индекса для полей title и summary
        """
        index_name = "articles_text_search"

        # Проверяем существование индекса
        existing_indexes = self.articles.index_information()
        if index_name not in existing_indexes:
            self.articles.create_index(
                [
                    ("title", TEXT),
                    ("summary", TEXT)
                ],
                name=index_name,
                weights={
                    "title": 3,
                    "summary": 1
                },
                default_language="russian"
            )

    def search_news(self, search_query: str, limit: int = 20) -> List[Dict]:
        """
        Выполняет полнотекстовый поиск по новостям
        :param search_query: Поисковый запрос
        :param limit: Лимит результатов
        :return: Список найденных статей
        """
        query = {
            "$text": {
                "$search": search_query,
                "$language": "russian"
            }
        }

        results = self.articles.find(query).sort([
            ("score", {"$meta": "textScore"})
        ]).limit(limit).projection({
            "title": 1,
            "url": 1,
            "source": 1,
            "publication_date": 1,
            "score": {"$meta": "textScore"}
        })

        return list(results)
