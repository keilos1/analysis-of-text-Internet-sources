# Команда для старта сервера - uvicorn app:app --host 0.0.0.0 --port 8000
# main.py
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pymongo import MongoClient, TEXT
from bson import ObjectId, json_util
from typing import Optional
import json
from datetime import datetime

# Инициализация FastAPI
app = FastAPI()

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение к MongoDB через SSH туннель (в вашем случае)
# В реальном проекте используйте переменные окружения для конфиденциальных данных!
SSH_HOST = '78.36.44.126'
SSH_PORT = 57381
SSH_USER = 'server'
SSH_PASSWORD = 'tppo'

MONGO_HOST = '127.0.0.1'
MONGO_PORT = 27017
MONGO_DB = 'newsPTZ'


def get_mongo_client():
    from sshtunnel import SSHTunnelForwarder
    tunnel = SSHTunnelForwarder(
        (SSH_HOST, SSH_PORT),
        ssh_username=SSH_USER,
        ssh_password=SSH_PASSWORD,
        remote_bind_address=(MONGO_HOST, MONGO_PORT)
    )
    tunnel.start()
    client = MongoClient('127.0.0.1', tunnel.local_bind_port)
    return client, tunnel


# Для упрощения в этом примере будем использовать прямое подключение
# В реальном проекте используйте правильное подключение через SSH туннель
client = MongoClient(f"mongodb://{MONGO_HOST}:{MONGO_PORT}/")
db = client[MONGO_DB]


# Создание текстового индекса для поиска
def create_text_index():
    index_name = "articles_text_search"
    if index_name not in db.articles.index_information():
        db.articles.create_index(
            [("title", TEXT), ("text", TEXT), ("summary", TEXT)],
            name=index_name,
            weights={"title": 3, "text": 2, "summary": 1},
            default_language="russian"
        )


create_text_index()

# Монтирование статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")


# API Endpoints
@app.get("/")
async def read_root():
    return {"message": "NewsPTZ API is running"}


@app.get("/api/articles")
async def get_articles(
        limit: int = Query(5, gt=0, le=100),
        category: Optional[str] = None,
        source: Optional[str] = None
):
    query = {}
    if category:
        query["category"] = category
    if source:
        query["source"] = source

    try:
        articles = list(db.articles.find(query))
        articles.sort(key=lambda x: x.get("publication_date", datetime.min), reverse=True)
        articles = articles[:limit]
        return JSONResponse(json.loads(json_util.dumps(articles)))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/articles/{article_id}")
async def get_article(article_id: str):
    try:
        article = db.articles.find_one({"_id": ObjectId(article_id)})
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        return JSONResponse(json.loads(json_util.dumps(article)))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/search")
async def search_articles(
        query: str = Query(..., min_length=1),
        limit: int = Query(20, gt=0, le=50)
):
    if not query:
        return []

    try:
        results = db.articles.find(
            {"$text": {"$search": query, "$language": "russian"}},
            {"score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})]).limit(limit)

        return JSONResponse(json.loads(json_util.dumps(list(results))))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/categories")
async def get_categories():
    try:
        categories = db.articles.distinct("category")
        return {"categories": categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sources")
async def get_sources():
    try:
        sources = db.articles.distinct("source")
        return {"sources": sources}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Статические файлы и шаблоны
@app.get("/foto.jpg")
async def get_foto():
    return FileResponse("static/foto.jpg")


# Старая главная страница (для совместимости)
@app.get("/analysis-of-text-Internet-sources")
async def legacy_index(request: Request):
    return FileResponse("static/index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


