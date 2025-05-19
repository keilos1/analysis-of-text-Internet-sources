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
from pytz import timezone
from apscheduler.triggers.cron import CronTrigger

sys.path.append("../")

from data_storage.database import connect_to_mongo
from config.config import HOST, PORT, SSH_USER, SSH_PASSWORD, DB_NAME, SITE_HOST, CHECK_INTERVAL, MONGO_HOST, MONGO_PORT
from data_processing.duplicate_detection import save_unique_articles, async_main
from data_processing.digest_generator import digest_generator

from contextlib import asynccontextmanager


app = FastAPI(lifespan=lifespan)
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
    scheduler = BackgroundScheduler(timezone=timezone("Europe/Moscow"))

    # Задача: удаление дубликатов каждые 30 минут
    scheduler.add_job(
        lambda: asyncio.run(run_duplicate_detection()),
        trigger=IntervalTrigger(minutes=30),  # <-- изменено с seconds=CHECK_INTERVAL
        max_instances=1,
        name="duplicate_detection"
    )

    # Задача: формирование дайджеста каждый день в 12:00 по Москве
    scheduler.add_job(
        lambda: asyncio.run(digest_generator()),
        trigger=CronTrigger(hour=12, minute=0),
        max_instances=1,
        name="daily_digest"
    )

    scheduler.start()
    logger.info("Планировщик запущен")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Запускаем планировщик
    start_scheduler()

    loop = asyncio.get_event_loop()

    # Гарантируем запуск после старта event loop
    loop.call_soon(lambda: asyncio.create_task(run_duplicate_detection()))
    loop.call_soon(lambda: asyncio.create_task(digest_generator()))

    yield




def parse_json(data):
    return json.loads(json_util.dumps(data))


def get_db_connection():
    """Создает и возвращает подключение к базе данных"""
    return connect_to_mongo(
        ssh_host=HOST,          # если пустое - будет локальное подключение
        ssh_port=PORT,
        ssh_user=SSH_USER,
        ssh_password=SSH_PASSWORD,
        mongo_host=MONGO_HOST,  # новый параметр вместо remote_host
        mongo_port=MONGO_PORT,   # новый параметр вместо remote_port
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
        if tunnel:
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
        if tunnel:
            tunnel.close()

@app.get("/api/sources-by-category/{category}")
async def get_sources_by_category(
    category: str,
    offset: int = 0,
    limit: int = 10
):
    if limit > 50:
        limit = 50  # Защита от слишком больших значений

    db, tunnel = get_db_connection()
    try:
        category_decoded = category
        print(f"Requested category: '{category_decoded}'")

        sources = list(db.sources.find({"category": category_decoded}))
        print(f"Found {len(sources)} sources")

        if not sources:
            return JSONResponse(
                status_code=200,
                content={"articles": [], "total": 0}
            )

        source_ids = [s["source_id"] for s in sources]

        # Получаем статьи с пагинацией
        articles = list(db.articles.find(
            {"source_id": {"$in": source_ids}},
            {"_id": 1, "title": 1, "summary": 1, "publication_date": 1, "source_id": 1, "categories": 1}
        )
        .sort("publication_date", -1)
        .skip(offset)
        .limit(limit))

        # Общее количество статей для этой категории
        total = db.articles.count_documents({"source_id": {"$in": source_ids}})

        print(f"Returning {len(articles)} articles (offset={offset}, limit={limit}), total: {total}")

        return {
            "articles": parse_json(articles),
            "total": total
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if tunnel:
            tunnel.close()


# Новый эндпоинт только для статей по категории
@app.get("/api/articles-by-category/{category}")
async def get_articles_by_category(
        category: str,
        skip: int = 0,
        limit: int = 10
):
    db, tunnel = get_db_connection()
    try:
        # Прямой поиск по категории в массиве categories
        query = {"categories": category}

        articles = list(db.articles.find(
            query,
            {
                "_id": 1,
                "title": 1,
                "summary": 1,
                "publication_date": 1,
                "categories": 1,
                "district": 1,
                "image_url": 1
            }
        )
                        .sort("publication_date", -1)
                        .skip(skip)
                        .limit(limit))

        total = db.articles.count_documents(query)

        return {
            "articles": parse_json(articles),
            "total": total
        }

    except Exception as e:
        print(f"Error in get_articles_by_category: {str(e)}")
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
        if tunnel:
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
        if tunnel:
            tunnel.close()


@app.get("/api/config")
async def get_config():
    return {
        "SITE_HOST": SITE_HOST,
    }


@app.get("/api/digest")
async def get_digest():
    db, tunnel = get_db_connection()
    try:
        # Получаем все статьи из коллекции daily_digest, сортированные по убыванию duplicate_count
        articles = list(db.daily_digest.find().sort("duplicate_count", -1))
        return parse_json(articles)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения дайджеста: {str(e)}")
    finally:
        if tunnel:
            tunnel.close()



if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
