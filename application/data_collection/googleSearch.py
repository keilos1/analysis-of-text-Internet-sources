import http.client
import json
from datetime import datetime
from urllib.parse import urlencode
import hashlib
import time

from newspaper import Article  # Импорт newspaper3k


class GoogleNewsCollector:
    def __init__(self, api_key, cx):
        self.api_key = api_key
        self.cx = cx
        self.conn = http.client.HTTPSConnection("customsearch.googleapis.com")

    def generate_article_id(self, url):
        return hashlib.md5(url.encode('utf-8')).hexdigest()

    def fetch_full_text_and_date(self, url):
        try:
            article = Article(url)
            article.download()
            article.parse()

            text = article.text.strip()

            pub_date = article.publish_date
            if pub_date is None:
                pub_date = datetime.now()
            else:
                # Если дата есть, формируем datetime с заполнением 0 для отсутствующих значений времени
                pub_date = datetime(
                    pub_date.year,
                    pub_date.month,
                    pub_date.day,
                    pub_date.hour if pub_date.hour is not None else 0,
                    pub_date.minute if pub_date.minute is not None else 0,
                    pub_date.second if pub_date.second is not None else 0,
                )

            return text, pub_date

        except Exception as e:
            print(f"Не удалось извлечь текст и дату по ссылке {url}: {e}")
            return "", datetime.now()

    def search_news(self, query, source_id="Google search", category="Новости", num=10):
        params = {
            'key': self.api_key,
            'cx': self.cx,
            'q': query,
            'num': num
        }

        query_string = f"/customsearch/v1?{urlencode(params)}"
        self.conn.request("GET", query_string)
        res = self.conn.getresponse()

        if res.status != 200:
            print(f"Ошибка HTTP: {res.status} {res.reason}")
            return []

        data = json.loads(res.read())
        items = data.get('items', [])
        results = []

        for item in items:
            url = item.get('link', '')
            title = item.get('title', '')

            full_text, publication_date = self.fetch_full_text_and_date(url)

            article = {
                "article_id": self.generate_article_id(url),
                "source_id": source_id,
                "title": title,
                "url": url,
                "category": category,
                "publication_date": publication_date,
                "summary": "",  # summary пустой
                "text": full_text,
                "source_type": "google"
            }
            results.append(article)

        return results

    def close(self):
        self.conn.close()


def collect_news(queries, api_key, cx, results_per_query=5, source_id="Google search", category="Новости"):
    collector = GoogleNewsCollector(api_key, cx)
    all_results = []

    for query in queries:
        print(f"Поиск: {query}")
        results = collector.search_news(
            query=query,
            source_id=source_id,
            category=category,
            num=results_per_query
        )
        print(f"Найдено: {len(results)}")
        all_results.extend(results)
        time.sleep(1)

    collector.close()
    return all_results
