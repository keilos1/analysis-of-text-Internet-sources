# Команда для старта сервера - uvicorn app:app --host 0.0.0.0 --port 8000
import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse, JSONResponse
from pymongo import MongoClient
from datetime import datetime, timedelta
import os
from typing import Optional

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Подключение к MongoDB
MONGO_URI = "mongodb://localhost:27017"
client = MongoClient(MONGO_URI)
db = client.newsdb  # Ваша база данных

# API роуты
@app.get("/api/articles")
async def get_articles(category: Optional[str] = None, source: Optional[str] = None):
    query = {}
    if category:
        query["category"] = category
    if source:
        query["source"] = source
    
    articles = list(db.articles.find(query, {'_id': 0}).sort("publication_date", -1).limit(20))
    return JSONResponse(content=articles)

@app.get("/api/articles/{article_id}")
async def get_article(article_id: str):
    article = db.articles.find_one({"_id": article_id}, {'_id': 0})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return JSONResponse(content=article)

@app.get("/api/daily-digest")
async def get_daily_digest():
    one_day_ago = datetime.utcnow() - timedelta(days=1)
    top_articles = list(db.articles.find(
        {"publication_date": {"$gte": one_day_ago}},
        {'_id': 0}
    ).sort("publication_date", -1).limit(5))
    
    return JSONResponse(content={"top_articles": top_articles})

@app.get("/api/search")
async def search_articles(query: str):
    results = list(db.articles.find(
        {
            "$or": [
                {"title": {"$regex": query, "$options": "i"}},
                {"summary": {"$regex": query, "$options": "i"}},
                {"text": {"$regex": query, "$options": "i"}}
            ]
        },
        {'_id': 0}
    ).limit(10))
    
    return JSONResponse(content=results)

# Статические файлы и HTML
@app.get("/analysis-of-text-Internet-sources")
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/foto.jpg")
async def get_foto():
    return FileResponse("static/foto.jpg")

