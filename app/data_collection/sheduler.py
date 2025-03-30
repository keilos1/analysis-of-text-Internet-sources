# Планировщик автоматического обновления данных
import schedule
import time
from api_connector import APIConnector
from scraper import WebScraper
from app.config.config import SITES
from app.data_storage.database import Database

class DataUpdater:
    def __init__(self):
        self.db = Database()
        self.api_connector = APIConnector()
        self.scraper = WebScraper()

    def update_data(self):
        sources = self.db.get_sources()
        for source in sources:
            data = None
            if "rss" in source:
                data = self.api_connector.fetch_rss(source["rss"])
            elif "url" in source:
                html = self.scraper.fetch_page(source["url"])
                data = self.scraper.parse_articles(html) if html else None

            if data:
                for article in data:
                    article_doc = {
                        "title": article.get("title"),
                        "url": article.get("link"),
                        "source": source["name"],
                        "publication_date": None,  # MongoDB использует текущую дату по умолчанию
                        "category": source.get("category", ["Новости"]),
                        "summary": article.get("summary", ""),
                        "district": source.get("district", "Неизвестно"),
                        "area_of_the_city": source.get("area_of_the_city", "Неизвестно")
                    }
                    self.db.save_article(article_doc)

    def start_scheduler(self):
        schedule.every(SITES["update_interval"]).minutes.do(self.update_data)
        while True:
            schedule.run_pending()
            time.sleep(1)