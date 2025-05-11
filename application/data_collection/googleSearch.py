import http.client
import json
from datetime import datetime

def google_search(queries, api_key, num=5):
    """Поиск новостей и вывод результатов в консоль."""
    conn = http.client.HTTPSConnection("serpapi.webscrapingapi.com")
    all_results = []

    try:
        for query in queries:
            # Формируем запрос для новостей
            params = {
                'engine': 'google',
                'api_key': api_key,
                'q': query,
                'tbm': 'nws',  # специальный параметр для поиска новостей
                'num': num,
                'hl': 'ru'
            }

            # Выполняем запрос
            conn.request("GET", f"/v1?{'&'.join(f'{k}={v}' for k, v in params.items())}")
            res = conn.getresponse()
            data = json.loads(res.read().decode('utf-8'))

            if 'error' in data:
                print(f"Ошибка для запроса '{query}': {data['error']}")
                continue  # Переходим к следующему запросу

            # Сохраняем новости в массив
            news_results = []
            for item in data.get('news_results', []):
                news_item = {
                    'source_id': item.get('ObjectId'),
                    'url': item.get('url'),
                    'source': item.get('source', {}).get('name'),
                    'category': item.get('category'),
                    'district': item.get('area'),
                    'saved_at': datetime.now()
                }
                news_results.append(news_item)

            all_results.extend(news_results)  # Объединяем результаты всех запросов
            print(f"Найдено {len(news_results)} новостей по запросу '{query}'")

    except Exception as e:
        print(f"Ошибка: {str(e)}")
    finally:
        conn.close()

    return all_results