# Команда для старта сервера - uvicorn app:app --host 0.0.0.0 --port 8000
import asyncio
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Старая главная страница (теперь по пути /main)
@app.get("/analysis-of-text-Internet-sources")  # Было: @app.get("/")
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/foto.jpg")
async def get_foto():
    return FileResponse("static/foto.jpg")  # Укажите правильный путь
