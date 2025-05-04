# Команда для старта сервера - uvicorn app:app --host 0.0.0.0 --port 8000
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse, JSONResponse
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId
from datetime import datetime
import os

app = FastAPI()

# Настройки CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение к MongoDB
uri = "mongodb://localhost:27017"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client['newsPTZ']
articles_collection = db['articles']

# Статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# API Endpoints
@app.get("/api/articles")
async def get_articles(limit: int = 5, category: str = None, source: str = None):
    query = {}
    if category:
        query["category"] = category
    if source:
        query["source"] = source

    articles = []
    for article in articles_collection.find(query).limit(limit):
        article["_id"] = str(article["_id"])
        articles.append(article)

    return JSONResponse(content=articles)


@app.get("/api/articles/{article_id}")
async def get_article(article_id: str):
    try:
        article = articles_collection.find_one({"_id": ObjectId(article_id)})
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")

        article["_id"] = str(article["_id"])
        return JSONResponse(content=article)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/search")
async def search_articles(query: str, limit: int = 10):
    try:
        # Простой текстовый поиск (для production лучше использовать Atlas Search)
        regex = {"$regex": query, "$options": "i"}
        search_query = {
            "$or": [
                {"title": regex},
                {"summary": regex},
                {"text": regex}
            ]
        }

        articles = []
        for article in articles_collection.find(search_query).limit(limit):
            article["_id"] = str(article["_id"])
            articles.append(article)

        return JSONResponse(content=articles)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Старая главная страница (теперь по пути /main)
@app.get("/analysis-of-text-Internet-sources")
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/foto.jpg")
async def get_foto():
    return FileResponse("static/foto.jpg")

