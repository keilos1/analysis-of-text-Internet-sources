from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse, JSONResponse
from bson import ObjectId, json_util
from urllib.parse import unquote
from typing import List, Tuple
import json
import sys
from fastapi import FastAPI
import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging

sys.path.append("../")

from data_storage.database import connect_to_mongo
from config.config import HOST, PORT, SSH_USER, SSH_PASSWORD, DB_NAME, SITE_HOST, CHECK_INTERVAL
from data_processing.duplicate_detection import save_unique_articles, async_main

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_duplicate_detection():
    """Обертка для запуска duplicate detection"""
    try:
        logger.info("Запуск проверки дубликатов...")
        await async_main()

        logger.info("Проверка дубликатов завершена")
    except Exception as e:
        logger.error(f"Ошибка при проверке дубликатов: {str(e)}")


def start_scheduler():
    """Запускает планировщик для периодических задач"""
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        lambda: asyncio.run(run_duplicate_detection()),
        trigger=IntervalTrigger(seconds=CHECK_INTERVAL),
        max_instances=1,
        name="duplicate_detection"
    )
    scheduler.start()
    logger.info(f"Планировщик запущен с интервалом {CHECK_INTERVAL} секунд")


@app.on_event("startup")
async def startup_event():
    """Запускается при старте приложения"""
    start_scheduler()
    # Первый запуск сразу после старта
    asyncio.create_task(run_duplicate_detection())


def parse_json(data):
    return json.loads(json_util.dumps(data))


def get_db_connection():
    """Создает и возвращает подключение к базе данных"""
    return connect_to_mongo(
        ssh_host=HOST,
        ssh_port=PORT,
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


# API для получения списка всех источников
@app.get("/api/sources")
async def get_all_sources():
    db, tunnel = get_db_connection()
    try:
        sources = list(db.sources.find({}, {"_id": 0, "source_id": 1, "name": 1, "category": 1}))
        return {"sources": parse_json(sources)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        tunnel.close()

# API для получения последних новостей
@app.get("/api/latest-news")
async def get_latest_news():
    db, tunnel = get_db_connection()
    try:
        articles = list(db.articles.find().sort("publication_date", -1))

        # Добавляем информацию об источниках
        results = []
        for article in articles:
            article_data = parse_json(article)
            if 'source_id' in article:
                source = db.sources.find_one({"source_id": article['source_id']})
                if source:
                    article_data['source_info'] = parse_json(source)
            results.append(article_data)

        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения новостей: {str(e)}")
    finally:
        tunnel.close()

@app.get("/api/sources-by-category/{category}")
async def get_sources_by_category(category: str):
    db, tunnel = None, None
    try:
        db, tunnel = get_db_connection()

        # Декодируем URL-encoded строку
        category_decoded = unquote(category)

        # Для отладки
        print(f"Requested category: '{category_decoded}'")

        # Находим все источники этой категории
        sources = list(db.sources.find({"category": category_decoded}))
        print(f"Found {len(sources)} sources")

        if not sources:
            return JSONResponse(
                status_code=200,
                content={"sources": [], "articles": []}
            )

        # Получаем source_ids для поиска статей
        source_ids = [s["source_id"] for s in sources]

        # Находим статьи этих источников
        articles = list(db.articles.find(
            {"source_id": {"$in": source_ids}},
            {"_id": 1, "title": 1, "summary": 1, "publication_date": 1, "source_id": 1, "categories": 1}
        ).sort("publication_date", -1).limit(100))

        print(f"Found {len(articles)} articles")

        return {
            "sources": parse_json(sources),
            "articles": parse_json(articles)
        }

    except Exception as e:
        print(f"Error in get_sources_by_category: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if tunnel:
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
            source_info = db.sources.find_one({"source_id": article['source_id']})

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
                source_info = db.sources.find_one({"source_id": article['source_id']})
                if source_info:
                    article_data['source_info'] = parse_json(source_info)
            results.append(article_data)

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка поиска: {str(e)}")
    finally:
        tunnel.close()


@app.get("/api/config")
async def get_config():
    return {
        "SITE_HOST": SITE_HOST,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)