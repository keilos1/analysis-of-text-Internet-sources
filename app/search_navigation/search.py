# search_api.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient, TEXT
from ..data_storage.database import db  # ваш импорт
from bson import json_util
import json

app = FastAPI()

class NewsSearch:
    def __init__(self, articles_collection=None):
        self.articles = articles_collection or db.get_collection("articles")
        self._create_text_index()

    def _create_text_index(self):
        index_name = "articles_text_search"
        existing_indexes = self.articles.index_information()
        if index_name not in existing_indexes:
            self.articles.create_index(
                [("title", TEXT), ("summary", TEXT)],
                name=index_name,
                weights={"title": 3, "summary": 1},
                default_language="russian"
            )

    def search_news(self, search_query: str, limit: int = 20):
        query = {"$text": {"$search": search_query, "$language": "russian"}}
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


news_search = NewsSearch()


@app.get("/api/search")
async def search(query: str = ""):
    if not query:
        return []

    results = news_search.search_news(query)
    # Конвертируем BSON в JSON-совместимый формат
    return json.loads(json_util.dumps(results))


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
