# Команда для старта сервера - uvicorn app:app --host 0.0.0.0 --port 8000
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

# # Основной backend-сервер на FastAPI
# from fastapi import FastAPI, HTTPException, Query, Request
# from fastapi.middleware.cors import CORSMiddleware
# from pymongo import MongoClient
# from datetime import datetime
# from typing import Optional, List, Dict
# import requests
# from bs4 import BeautifulSoup
# from threading import Thread
# import time
# import schedule
# from bson import ObjectId
# import json
#
# app = FastAPI()
#
# # Настройка CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
#
# # Подключение к MongoDB
# client = MongoClient('mongodb://localhost:27017/')
# db = client['petrozavodsk_news']
# news_collection = db['news']
# digests_collection = db['digests']
#
# # Конфигурация источников новостей
# NEWS_SOURCES = {
#     'news': [
#         {'url': 'https://ptzgovorit.ru/news', 'name': 'Петрозаводск Говорит'},
#         {'url': 'https://rk.karelia.ru/news/', 'name': 'Республика Карелия'}
#     ],
#     'social': [
#         {'url': 'https://vk.com/petrozavodsk', 'name': 'ВКонтакте - Петрозаводск'},
#         {'url': 'https://t.me/petrozavodsk_now', 'name': 'Telegram - Петрозаводск Now'}
#     ]
# }
#
# # Категории новостей
# CATEGORIES = {
#     'culture': 'Культура',
#     'sports': 'Спорт',
#     'tech': 'Технологии',
#     'holidays': 'Праздники',
#     'education': 'Образование'
# }
#
# # Класс для сериализации ObjectId
# class JSONEncoder(json.JSONEncoder):
#     def default(self, o):
#         if isinstance(o, ObjectId):
#             return str(o)
#         return json.JSONEncoder.default(self, o)
#
# # Подсистема веб-интерфейса
# @app.get("/api/content/{category}")
# async def display_content(category: str):
#     """Отображает контент по категориям"""
#     try:
#         if category == 'digest':
#             digest = digests_collection.find_one({'date': datetime.now().strftime('%Y-%m-%d')})
#             if not digest:
#                 raise HTTPException(status_code=404, detail="Digest not found")
#             return JSONEncoder().encode(digest)
#
#         query = {'category': category} if category in CATEGORIES else {'source_type': category}
#         news = list(news_collection.find(query).sort('date', -1).limit(20))
#         return JSONEncoder().encode({'data': news})
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
#
# @app.get("/api/filter")
# async def filter_data_by_category(
#     category: Optional[str] = Query(None),
#     source_type: Optional[str] = Query(None)
# ):
#     """Фильтрует данные по категории"""
#     query = {}
#     if category:
#         query['category'] = category
#     if source_type:
#         query['source_type'] = source_type
#
#     try:
#         news = list(news_collection.find(query).sort('date', -1).limit(20))
#         return JSONEncoder().encode({'data': news})
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
#
# @app.get("/api/search")
# async def search_data(query: str = Query(...)):
#     """Полнотекстовый поиск по базе данных"""
#     try:
#         results = list(news_collection.find(
#             {'$text': {'$search': query}},
#             {'score': {'$meta': 'textScore'}}
#         ).sort([('score', {'$meta': 'textScore'})]).limit(20))
#
#         return JSONEncoder().encode({'data': results})
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
#
# # Подсистема дайджеста
# @app.get("/api/digest")
# async def show_digest():
#     """Отображает сводку дня"""
#     try:
#         today = datetime.now().strftime('%Y-%m-%d')
#         digest = digests_collection.find_one({'date': today})
#
#         if not digest:
#             digest = create_daily_digest()
#             digests_collection.insert_one(digest)
#
#         return JSONEncoder().encode(digest)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
#
# @app.post("/api/digest/update")
# async def update_digest():
#     """Обновляет дайджест"""
#     try:
#         digest = create_daily_digest()
#         digests_collection.update_one(
#             {'date': digest['date']},
#             {'$set': digest},
#             upsert=True
#         )
#         return {"status": "success", "digest": JSONEncoder().encode(digest)}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
#
# # Подсистема сбора данных (те же функции, что и в оригинале)
# def fetch_web_data(source_type):
#     """Выполняет HTTP-запросы для сбора HTML-кода веб-страниц"""
#     sources = NEWS_SOURCES.get(source_type, [])
#     data = []
#
#     for source in sources:
#         try:
#             response = requests.get(source['url'], timeout=10)
#             soup = BeautifulSoup(response.text, 'html.parser')
#
#             if 'ptzgovorit.ru' in source['url']:
#                 articles = soup.find_all('div', class_='news-item')
#                 for article in articles:
#                     title = article.find('h2').text.strip()
#                     link = article.find('a')['href']
#                     date = article.find('time')['datetime']
#                     data.append({
#                         'title': title,
#                         'url': link,
#                         'date': date,
#                         'source': source['name'],
#                         'source_type': source_type,
#                         'raw_content': str(article)
#                     })
#
#         except Exception as e:
#             print(f"Error fetching {source['url']}: {str(e)}")
#
#     return data
#
# def filter_by_location(data, location='Петрозаводск'):
#     """Фильтрует собранные данные по принадлежности к заданной местности"""
#     filtered = []
#     for item in data:
#         if location.lower() in item['title'].lower() or location.lower() in item.get('content', '').lower():
#             filtered.append(item)
#     return filtered
#
# def classify_data(data):
#     """Классифицирует отфильтрованные данные на категории"""
#     classified = []
#     for item in data:
#         category = 'other'
#         content = f"{item['title']} {item.get('content', '')}".lower()
#
#         for cat, keywords in {
#             'culture': ['культура', 'театр', 'музей', 'выставка', 'концерт'],
#             'sports': ['спорт', 'футбол', 'хоккей', 'соревнование', 'турнир'],
#             'tech': ['технологи', 'интернет', 'компьютер', 'гаджет', 'it'],
#             'holidays': ['праздник', 'фестиваль', 'мероприятие', 'день города'],
#             'education': ['образование', 'школа', 'университет', 'студент', 'учитель']
#         }.items():
#             if any(keyword in content for keyword in keywords):
#                 category = cat
#                 break
#
#         item['category'] = category
#         classified.append(item)
#
#     return classified
#
# def update_data():
#     """Автоматическое обновление данных"""
#     print("Starting data update...")
#     for source_type in ['news', 'social']:
#         data = fetch_web_data(source_type)
#         filtered_data = filter_by_location(data)
#         classified_data = classify_data(filtered_data)
#
#         for item in classified_data:
#             news_collection.update_one(
#                 {'url': item['url']},
#                 {'$set': item},
#                 upsert=True
#             )
#
#     print("Data update completed")
#
# # Подсистема обработки и анализа данных (те же функции, что и в оригинале)
# def summarize_text(text):
#     """Формирует краткую сводку для длинных публикаций"""
#     sentences = text.split('.')
#     return '.'.join(sentences[:3]) + '.'
#
# def create_daily_digest():
#     """Создает дайджест с новостями и отзывами"""
#     today = datetime.now().strftime('%Y-%m-%d')
#     start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
#
#     digest = {
#         'date': today,
#         'created_at': datetime.now().isoformat(),
#         'news': {},
#         'top_news': []
#     }
#
#     for category in CATEGORIES:
#         news = list(news_collection.find({
#             'category': category,
#             'date': {'$gte': start_date}
#         }).sort('date', -1).limit(5))
#
#         if news:
#             digest['news'][category] = news
#             digest['top_news'].extend(news[:2])
#
#     for item in digest['top_news']:
#         if 'content' in item:
#             item['summary'] = summarize_text(item['content'])
#
#     return digest
#
# # Подсистема хранения данных
# @app.post("/api/data/save")
# async def save_data(request: Request):
#     """Сохраняет данные в базе данных"""
#     try:
#         data = await request.json()
#         if not data:
#             raise HTTPException(status_code=400, detail="No data provided")
#
#         result = news_collection.insert_one(data)
#         return {"status": "success", "id": str(result.inserted_id)}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
#
# @app.get("/api/data/history")
# async def retrieve_historical_data(
#     start: Optional[str] = Query(None),
#     end: Optional[str] = Query(None)
# ):
#     """Получает исторические данные за выбранный период"""
#     try:
#         query = {}
#         if start:
#             query['date'] = {'$gte': start}
#         if end:
#             query['date'] = {'$lte': end}
#
#         data = list(news_collection.find(query).sort('date', -1))
#         return JSONEncoder().encode({'data': data})
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
#
# # Планировщик для автоматического обновления данных
# def scheduled_update():
#     """Запускает обновление данных по расписанию"""
#     schedule.every(2).hours.do(update_data)
#
#     while True:
#         schedule.run_pending()
#         time.sleep(60)
#
# # Запуск приложения
# if __name__ == '__main__':
#     import uvicorn
#
#     # Создаем текстовый индекс для поиска
#     news_collection.create_index([('title', 'text'), ('content', 'text')])
#
#     # Запускаем фоновый процесс для обновления данных
#     Thread(target=scheduled_update, daemon=True).start()
#
#     # Запускаем FastAPI-приложение
#     uvicorn.run(app, host="0.0.0.0", port=5000)
