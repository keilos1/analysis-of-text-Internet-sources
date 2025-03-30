# Модуль для парсинга веб-страниц
from bs4 import BeautifulSoup
import requests


class WebScraper:
    def fetch_page(self, url):
        response = requests.get(url)
        if response.status_code != 200:
            return None
        return response.text

    def parse_articles(self, html, tag="article", class_name=None):
        soup = BeautifulSoup(html, "html.parser")
        articles = soup.find_all(tag, class_=class_name)
        return [article.get_text(strip=True) for article in articles]