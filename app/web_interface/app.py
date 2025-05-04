# Команда для старта сервера - uvicorn app:app --host 0.0.0.0 --port 8000
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse, JSONResponse
from pymongo import MongoClient
from sshtunnel import SSHTunnelForwarder
from bson import ObjectId
import json

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# SSH tunnel configuration
ssh_host = '78.36.44.126'
ssh_port = 57381
ssh_user = 'server'
ssh_password = 'tppo'

mongo_host = '127.0.0.1'
mongo_port = 27017

# MongoDB connection setup
def get_mongo_connection():
    tunnel = SSHTunnelForwarder(
        (ssh_host, ssh_port),
        ssh_username=ssh_user,
        ssh_password=ssh_password,
        remote_bind_address=(mongo_host, mongo_port)
    )
    tunnel.start()
    client = MongoClient('127.0.0.1', tunnel.local_bind_port)
    return client, tunnel

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)

# API endpoints
@app.get("/analysis-of-text-Internet-sources")
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/foto.jpg")
async def get_foto():
    return FileResponse("static/foto.jpg")

@app.get("/api/articles")
async def get_all_articles():
    client, tunnel = None, None
    try:
        client, tunnel = get_mongo_connection()
        db = client['newsPTZ']
        articles = list(db.articles.find().limit(20))  # Limit to 20 articles for performance
        return JSONResponse(content=articles, encoder=JSONEncoder)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if client:
            client.close()
        if tunnel:
            tunnel.stop()

@app.get("/api/articles/{article_id}")
async def get_article(article_id: str):
    client, tunnel = None, None
    try:
        client, tunnel = get_mongo_connection()
        db = client['newsPTZ']
        article = db.articles.find_one({"_id": ObjectId(article_id)})
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        return JSONResponse(content=article, encoder=JSONEncoder)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if client:
            client.close()
        if tunnel:
            tunnel.stop()

