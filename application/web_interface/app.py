from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse, JSONResponse
from bson import ObjectId, json_util
import json
import sys
from pathlib import Path

# Добавляем корень проекта в PYTHONPATH
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from application.data_storage.database import connect_to_mongo


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Настройки подключения (должны совпадать с теми, что в database.py)
SSH_HOST = '78.36.44.126'
SSH_PORT = 57381
SSH_USER = 'server'
SSH_PASSWORD = 'tppo'
DB_NAME = 'newsPTZ'


def parse_json(data):
    return json.loads(json_util.dumps(data))


def get_db_connection():
    """Создает и возвращает подключение к базе данных"""
    return connect_to_mongo(
        ssh_host=SSH_HOST,
        ssh_port=SSH_PORT,
        ssh_user=SSH_USER,
        ssh_password=SSH_PASSWORD,
        db_name=DB_NAME
    )


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
    db, tunnel = get_db_connection()
    try:
        articles = list(db.articles.find().sort("publication_date", -1).limit(10))
        return parse_json(articles)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения новостей: {str(e)}")
    finally:
        tunnel.close()


# API для получения новостей по категории
@app.get("/api/category/{category}")
async def get_category_news(category: str):
    db, tunnel = get_db_connection()
    try:
        articles = list(db.articles.find({"category": category}).sort("publication_date", -1).limit(10))
        return parse_json(articles)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения новостей категории: {str(e)}")
    finally:
        tunnel.close()


# API для получения новостей по источнику
@app.get("/api/source/{source}")
async def get_source_news(source: str):
    db, tunnel = get_db_connection()
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
    finally:
        tunnel.close()


# API для получения полной статьи
@app.get("/api/article/{article_id}")
async def get_article(article_id: str):
    db, tunnel = get_db_connection()
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
    finally:
        tunnel.close()


# API для поиска новостей
@app.get("/api/search")
async def search_news(query: str):
    db, tunnel = get_db_connection()
    try:
        articles = list(db.articles.find({
            "$or": [
                {"title": {"$regex": query, "$ofptions": "i"}},
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
    finally:
        tunnel.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)