import http.client
import json
from datetime import datetime, timedelta
import time
import hashlib

class GoogleNewsCollector:
    def __init__(self, api_key):
        self.api_key = api_key
        self.conn = None

    def __enter__(self):
        self.conn = http.client.HTTPSConnection("serpapi.webscrapingapi.com")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()

    def generate_article_id(self, url):
        """Генерация уникального ID для статьи на основе URL"""
        return hashlib.md5(url.encode('utf-8')).hexdigest()

    def parse_date(self, date_str):
        """Парсинг даты из различных форматов Google News"""
        try:
            # Пример форматов: "2 дня назад", "5 часов назад", "2024-03-15"
            if 'час' in date_str or 'часов' in date_str:
                hours = int(date_str.split()[0])
                return (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
            elif 'день' in date_str or 'дней' in date_str:
                days = int(date_str.split()[0])
                return (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
            else:
                return datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y-%m-%d %H:%M:%S')
        except:
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def search_news(self, query, num=10, lang='ru'):
        """Выполняет поиск новостей по заданному запросу"""
        params = {
            'engine': 'google',
            'api_key': self.api_key,
            'q': query,
            'tbm': 'nws',
            'num': num,
            'hl': lang,
            'gl': 'ru' if lang == 'ru' else 'us'
        }

        try:
            self.conn.request("GET", f"/v1?{'&'.join(f'{k}={v}' for k, v in params.items())}")
            res = self.conn.getresponse()
            data = json.loads(res.read().decode('utf-8'))

            if 'error' in data:
                print(f"Ошибка для запроса '{query}': {data['error']}")
                return []

            return self.process_results(data.get('news_results', []), query)

        except Exception as e:
            print(f"Ошибка при выполнении запроса: {str(e)}")
            return []

    def process_results(self, news_items, query):
        """Обрабатывает результаты поиска и приводит к единому формату"""
        processed = []

        for item in news_items:
            url = item.get('link') or item.get('url', '')
            if not url:
                continue

            processed.append({
                "article_id": self.generate_article_id(url),
                "source_id": self.generate_source_id(item.get('source', {}).get('name', 'unknown')),
                "title": item.get('title', ''),
                "url": url,
                "category": item.get('category', 'Новости'),
                "publication_date": self.parse_date(item.get('date', '')),
                "summary": item.get('snippet', ''),
                "text": '',  # Полный текст нужно получать отдельно
                "query": query,
                "collected_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })

        return processed

    def generate_source_id(self, source_name):
        """Генерирует ID источника на основе его названия"""
        if not source_name:
            return 'unknown'
        return (source_name.lower()
                .replace(' ', '_')
                .replace('.', '')
                .replace('-', '_')
                .strip('_'))


def collect_news(queries, api_key, results_per_query=10):
    """Основная функция для сбора новостей"""
    all_news = []

    with GoogleNewsCollector(api_key) as collector:
        for query in queries:
            print(f"Собираю новости по запросу: '{query}'")
            news = collector.search_news(query, num=results_per_query)
            all_news.extend(news)
            print(f"Найдено {len(news)} новостей")
            time.sleep(1)  # Пауза между запросами

    return all_news


if __name__ == "__main__":
    # Конфигурация
    API_KEY = "ваш_api_ключ_serpapi"
    QUERIES = ["новости технологий", "искусственный интеллект", "криптовалюта"]
    RESULTS_PER_QUERY = 5

    # Запуск сбора новостей
    news_results = collect_news(QUERIES, API_KEY, RESULTS_PER_QUERY)

    # Сохранение результатов в JSON файл
    with open('google_news_results.json', 'w', encoding='utf-8') as f:
        json.dump(news_results, f, ensure_ascii=False, indent=2)

    print(f"\nВсего собрано {len(news_results)} новостей. Результаты сохранены в google_news_results.json")