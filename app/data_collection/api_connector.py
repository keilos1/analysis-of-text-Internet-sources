# Подключение к API соцсетей и других источников данных
import requests
import feedparser


class APIConnector:
    def fetch_rss(self, url):
        feed = feedparser.parse(url)
        if feed.bozo:
            return None  # Ошибка при разборе RSS
        return [{"title": entry.title, "link": entry.link, "published": entry.published} for entry in feed.entries]

    def fetch_api(self, url, headers=None):
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        return None