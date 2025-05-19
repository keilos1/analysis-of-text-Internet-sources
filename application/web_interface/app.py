from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse, JSONResponse
from bson import ObjectId, json_util
from urllib.parse import unquote
from typing import List, Tuple
import json
import sys
import asyncio
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone
from contextlib import asynccontextmanager

sys.path.append("../")

from data_storage.database import connect_to_mongo
from config.config import HOST, PORT, SSH_USER, SSH_PASSWORD, DB_NAME, SITE_HOST, MONGO_HOST, MONGO_PORT
from data_processing.duplicate_detection import save_unique_articles, async_main
from data_processing.digest_generator import digest_generator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    asyncio.create_task(run_duplicate_detection())
    asyncio.create_task(digest_generator())
    yield

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def start_scheduler():
    scheduler = BackgroundScheduler(timezone=timezone("Europe/Moscow"))

    scheduler.add_job(
        lambda: asyncio.run(run_duplicate_detection()),
        trigger=IntervalTrigger(minutes=30),
        max_instances=1,
        name="duplicate_detection"
    )

    scheduler.add_job(
        lambda: asyncio.run(digest_generator()),
        trigger=CronTrigger(hour=12, minute=0),
        max_instances=1,
        name="daily_digest"
    )

    scheduler.start()
    logger.info("Планировщик запущен")

async def run_duplicate_detection():
    try:
        logger.info("\u0417\u0430\u043f\u0443\u0441\u043a \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0438 \u0434\u0443\u0431\u043b\u0438\u043a\u0430\u0442\u043e\u0432...")
        await async_main()
        logger.info("\u041f\u0440\u043e\u0432\u0435\u0440\u043a\u0430 \u0434\u0443\u0431\u043b\u0438\u043a\u0430\u0442\u043e\u0432 \u0437\u0430\u0432\u0435\u0440\u0448\u0435\u043d\u0430")
    except Exception as e:
        logger.error(f"Ошибка при проверке дубликатов: {str(e)}")

def parse_json(data):
    return json.loads(json_util.dumps(data))

def get_db_connection():
    return connect_to_mongo(
        ssh_host=HOST,
        ssh_port=PORT,
        ssh_user=SSH_USER,
        ssh_password=SSH_PASSWORD,
        mongo_host=MONGO_HOST,
        mongo_port=MONGO_PORT,
        db_name=DB_NAME
    )

@app.get("/analysis-of-text-Internet-sources")
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/foto.jpg")
async def get_foto():
    return FileResponse("static/foto.jpg")

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

@app.get("/api/latest-news")
async def get_latest_news():
    db, tunnel = get_db_connection()
    try:
        articles = list(db.articles.find().sort("publication_date", -1))
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

@app.get("/api/config")
async def get_config():
    return {
        "SITE_HOST": SITE_HOST,
    }

@app.get("/api/digest")
async def get_digest():
    db, tunnel = get_db_connection()
    try:
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
