from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse, JSONResponse
from bson import ObjectId, json_util
from pymongo import MongoClient
import json
import sys

# Добавляем корень проекта в PYTHONPATH
sys.path.append("../")

from data_storage.database import Database

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Локальные настройки подключения
MONGO_HOST = 'localhost'  # или '127.0.0.1'
MONGO_PORT = 27017
DB_NAME = 'newsPTZ'

def get_db_connection():
    """Создает и возвращает подключение к базе данных"""
    client = MongoClient(host=MONGO_HOST, port=MONGO_PORT)
    db = client[DB_NAME]
    return Database(db), None  # Возвращаем None вместо tunnel

def parse_json(data):
    return json.loads(json_util.dumps(data))

# Главная страница
@app.get("/analysis-of-text-Internet-sources")
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Статическое изображение
@app.get("/foto.jpg")
async def get_foto():
    return FileResponse("static/foto.jpg")

# API для получения последних новостей
@app.get("/api/latest-news")
async def get_latest_news():
    db, _ = get_db_connection()  # Игнорируем второй аргумент (tunnel)
    try:
        articles = list(db.articles.find().sort("publication_date", -1).limit(10))
        return parse_json(articles)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения новостей: {str(e)}")

# API для получения новостей по категории
@app.get("/api/category/{category}")
async def get_category_news(category: str):
    db, _ = get_db_connection()
    try:
        articles = list(db.articles.find({"category": category}).sort("publication_date", -1).limit(10))
        return parse_json(articles)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения новостей категории: {str(e)}")

# API для получения новостей по источнику
@app.get("/api/source/{source}")
async def get_source_news(source: str):
    db, _ = get_db_connection()
    try:
        articles = list(db.articles.find({"source_id": source}).sort("publication_date", -1).limit(10))
        source_info = db.get_source(source)

        result = []
        for article in articles:
            article_data = parse_json(article)
            if source_info:
                article_data['source_info'] = parse_json(source_info)
            result.append(article_data)

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения новостей источника: {str(e)}")

# API для получения полной статьи
@app.get("/api/article/{article_id}")
async def get_article(article_id: str):
    db, _ = get_db_connection()
    try:
        # Пробуем найти по ObjectId
        try:
            article = db.articles.find_one({"_id": ObjectId(article_id)})
        except:
            article = None

        # Если не нашли, пробуем найти по article_id
        if not article:
            article = db.articles.find_one({"article_id": article_id})

        if not article:
            raise HTTPException(status_code=404, detail="Статья не найдена")

        # Получаем информацию об источнике
        source_info = None
        if 'source_id' in article:
            source_info = db.get_source(article['source_id'])

        result = parse_json(article)
        if source_info:
            result['source_info'] = parse_json(source_info)

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статьи: {str(e)}")

# API для поиска новостей
@app.get("/api/search")
async def search_news(query: str):
    db, _ = get_db_connection()
    try:
        articles = list(db.articles.find({
            "$or": [
                {"title": {"$regex": query, "$options": "i"}},
                {"text": {"$regex": query, "$options": "i"}},
                {"summary": {"$regex": query, "$options": "i"}}
            ]
        }).sort("publication_date", -1).limit(20))

        # Добавляем информацию об источниках
        results = []
        for article in articles:
            article_data = parse_json(article)
            if 'source_id' in article:
                source_info = db.get_source(article['source_id'])
                if source_info:
                    article_data['source_info'] = parse_json(source_info)
            results.append(article_data)

        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка поиска: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)