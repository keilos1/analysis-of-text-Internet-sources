# Основной backend-сервер
from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from threading import Thread
import time
import schedule

app = Flask(__name__)
CORS(app)  # Разрешаем CORS для всех доменов

# Подключение к MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['petrozavodsk_news']
news_collection = db['news']
digests_collection = db['digests']

# Конфигурация источников новостей
NEWS_SOURCES = {
    'news': [
        {'url': 'https://ptzgovorit.ru/news', 'name': 'Петрозаводск Говорит'},
        {'url': 'https://rk.karelia.ru/news/', 'name': 'Республика Карелия'}
    ],
    'social': [
        {'url': 'https://vk.com/petrozavodsk', 'name': 'ВКонтакте - Петрозаводск'},
        {'url': 'https://t.me/petrozavodsk_now', 'name': 'Telegram - Петрозаводск Now'}
    ]
}

# Категории новостей
CATEGORIES = {
    'culture': 'Культура',
    'sports': 'Спорт',
    'tech': 'Технологии',
    'holidays': 'Праздники',
    'education': 'Образование'
}

# Подсистема веб-интерфейса
@app.route('/api/content/<category>', methods=['GET'])
def display_content(category):
    """Отображает контент по категориям"""
    try:
        if category == 'digest':
            digest = digests_collection.find_one({'date': datetime.now().strftime('%Y-%m-%d')})
            if not digest:
                return jsonify({'error': 'Digest not found'}), 404
            return jsonify(digest)
        
        query = {'category': category} if category in CATEGORIES else {'source_type': category}
        news = list(news_collection.find(query).sort('date', -1).limit(20)
        return jsonify({'data': news})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/filter', methods=['GET'])
def filter_data_by_category():
    """Фильтрует данные по категории"""
    category = request.args.get('category')
    source_type = request.args.get('source_type')
    
    query = {}
    if category:
        query['category'] = category
    if source_type:
        query['source_type'] = source_type
    
    try:
        news = list(news_collection.find(query).sort('date', -1).limit(20))
        return jsonify({'data': news})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search', methods=['GET'])
def search_data():
    """Полнотекстовый поиск по базе данных"""
    query = request.args.get('query')
    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400
    
    try:
        # Используем текстовый индекс MongoDB
        results = list(news_collection.find(
            {'$text': {'$search': query}},
            {'score': {'$meta': 'textScore'}}
        ).sort([('score', {'$meta': 'textScore'})]).limit(20))
        
        return jsonify({'data': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Подсистема дайджеста
@app.route('/api/digest', methods=['GET'])
def show_digest():
    """Отображает сводку дня"""
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        digest = digests_collection.find_one({'date': today})
        
        if not digest:
            # Если дайджеста нет, создаем новый
            digest = create_daily_digest()
            digests_collection.insert_one(digest)
        
        return jsonify(digest)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/digest/update', methods=['POST'])
def update_digest():
    """Обновляет дайджест"""
    try:
        digest = create_daily_digest()
        digests_collection.update_one(
            {'date': digest['date']},
            {'$set': digest},
            upsert=True
        )
        return jsonify({'status': 'success', 'digest': digest})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Подсистема сбора данных
def fetch_web_data(source_type):
    """Выполняет HTTP-запросы для сбора HTML-кода веб-страниц"""
    sources = NEWS_SOURCES.get(source_type, [])
    data = []
    
    for source in sources:
        try:
            response = requests.get(source['url'], timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Пример парсинга (нужно адаптировать под конкретные сайты)
            if 'ptzgovorit.ru' in source['url']:
                articles = soup.find_all('div', class_='news-item')
                for article in articles:
                    title = article.find('h2').text.strip()
                    link = article.find('a')['href']
                    date = article.find('time')['datetime']
                    data.append({
                        'title': title,
                        'url': link,
                        'date': date,
                        'source': source['name'],
                        'source_type': source_type,
                        'raw_content': str(article)
                    })
            
            # Добавьте другие источники по аналогии
            
        except Exception as e:
            print(f"Error fetching {source['url']}: {str(e)}")
    
    return data

def filter_by_location(data, location='Петрозаводск'):
    """Фильтрует собранные данные по принадлежности к заданной местности"""
    filtered = []
    for item in data:
        if location.lower() in item['title'].lower() or location.lower() in item.get('content', '').lower():
            filtered.append(item)
    return filtered

def classify_data(data):
    """Классифицирует отфильтрованные данные на категории"""
    classified = []
    for item in data:
        category = 'other'
        content = f"{item['title']} {item.get('content', '')}".lower()
        
        for cat, keywords in {
            'culture': ['культура', 'театр', 'музей', 'выставка', 'концерт'],
            'sports': ['спорт', 'футбол', 'хоккей', 'соревнование', 'турнир'],
            'tech': ['технологи', 'интернет', 'компьютер', 'гаджет', 'it'],
            'holidays': ['праздник', 'фестиваль', 'мероприятие', 'день города'],
            'education': ['образование', 'школа', 'университет', 'студент', 'учитель']
        }.items():
            if any(keyword in content for keyword in keywords):
                category = cat
                break
        
        item['category'] = category
        classified.append(item)
    
    return classified

def update_data():
    """Автоматическое обновление данных"""
    print("Starting data update...")
    for source_type in ['news', 'social']:
        data = fetch_web_data(source_type)
        filtered_data = filter_by_location(data)
        classified_data = classify_data(filtered_data)
        
        for item in classified_data:
            # Обновляем или добавляем новость
            news_collection.update_one(
                {'url': item['url']},
                {'$set': item},
                upsert=True
            )
    
    print("Data update completed")

# Подсистема обработки и анализа данных
def summarize_text(text):
    """Формирует краткую сводку для длинных публикаций"""
    # Упрощенная реализация - берем первые 3 предложения
    sentences = text.split('.')
    return '.'.join(sentences[:3]) + '.'

def create_daily_digest():
    """Создает дайджест с новостями и отзывами"""
    today = datetime.now().strftime('%Y-%m-%d')
    start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Получаем топ-5 новостей за день по категориям
    digest = {
        'date': today,
        'created_at': datetime.now().isoformat(),
        'news': {},
        'top_news': []
    }
    
    for category in CATEGORIES:
        news = list(news_collection.find({
            'category': category,
            'date': {'$gte': start_date}
        }).sort('date', -1).limit(5))
        
        if news:
            digest['news'][category] = news
            digest['top_news'].extend(news[:2])
    
    # Добавляем сводку
    for item in digest['top_news']:
        if 'content' in item:
            item['summary'] = summarize_text(item['content'])
    
    return digest

# Подсистема хранения данных
@app.route('/api/data/save', methods=['POST'])
def save_data():
    """Сохраняет данные в базе данных"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        result = news_collection.insert_one(data)
        return jsonify({'status': 'success', 'id': str(result.inserted_id)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/history', methods=['GET'])
def retrieve_historical_data():
    """Получает исторические данные за выбранный период"""
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    
    try:
        query = {}
        if start_date:
            query['date'] = {'$gte': start_date}
        if end_date:
            query['date'] = {'$lte': end_date}
        
        data = list(news_collection.find(query).sort('date', -1))
        return jsonify({'data': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Планировщик для автоматического обновления данных
def scheduled_update():
    """Запускает обновление данных по расписанию"""
    schedule.every(2).hours.do(update_data)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    # Создаем текстовый индекс для поиска
    news_collection.create_index([('title', 'text'), ('content', 'text')])
    
    # Запускаем фоновый процесс для обновления данных
    Thread(target=scheduled_update, daemon=True).start()
    
    # Запускаем Flask-приложение
    app.run(debug=True, port=5000)
