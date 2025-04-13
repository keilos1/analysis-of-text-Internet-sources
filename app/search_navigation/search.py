# search_api.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient, TEXT
from data_storage.database import db  # ваш импорт
from bson import json_util

app = Flask(__name__)
CORS(app)  # Разрешает запросы с других доменов (например, с localhost:3000)

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

@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    if not query:
        return jsonify([])

    results = news_search.search_news(query)
    return json_util.dumps(results)  # BSON-совместимый JSON

if __name__ == '__main__':
    app.run(debug=True)
