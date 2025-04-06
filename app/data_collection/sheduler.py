import re
from api_connector import APIConnector
from scraper import WebScraper

class DataUpdater:
    def __init__(self):
        self.api_connector = APIConnector()
        self.scraper = WebScraper()
        # self.db = Database()  # Отключено пока не требуется подключение к базе

        # Тестовые источники (заменить на загрузку из базы)
        self.sources = [
            {
                "name": "Столица Онего",
                "url": "https://stolicaonego.ru/rss.php",
                "category": ["Новости"],
                "district": "Республика Карелия",
                "area_of_the_city": "Петрозаводск"
            },
            {
                "name": "Губернiя Daily",
                "url": "https://gubdaily.ru/feed/",
                "category": ["Новости"],
                "district": "Республика Карелия",
                "area_of_the_city": "Петрозаводск"
            }
        ]

    def fetch_news(self):
        articles_data = []

        for source in self.sources:
            print(f"Обрабатываем источник: {source['name']}")

            data = None
            url = source["url"]

            # Пробуем загрузить как RSS
            data = self.api_connector.fetch_rss(url)
            if data:
                print(f"Загружено {len(data)} статей из RSS")
                for article in data:
                    articles_data.append({
                        "title": article.get("title"),
                        "url": article.get("link"),
                        "source": source["name"],
                        "publication_date": article.get("publication_date"),
                        "category": source.get("category", ["Новости"]),
                        "summary": article.get("summary", ""),
                        "district": source.get("district", "Неизвестно"),
                        "area_of_the_city": source.get("area_of_the_city", "Неизвестно")
                    })

            # Если RSS не сработал — парсим HTML
            if not data:
                print("Переходим к парсингу HTML...")
                html = self.scraper.fetch_page(url)
                if html:
                    parsed_articles = self.scraper.parse_articles(
                        html, container_tag="div", title_tag="h2", link_tag="a", content_tag="p"
                    )
                    for article in parsed_articles:
                        # Извлекаем дату, если она есть (в HTML)
                        publication_date = article.get("publication_date", None)

                        articles_data.append({
                            "title": article["title"],
                            "url": article["link"],
                            "source": source["name"],
                            "publication_date": publication_date,  # Сохраняем как есть
                            "category": source.get("category", ["Новости"]),
                            "summary": article["summary"],
                            "district": source.get("district", "Неизвестно"),
                            "area_of_the_city": source.get("area_of_the_city", "Неизвестно")
                        })

        return articles_data


# Тестовый запуск
if __name__ == "__main__":
    updater = DataUpdater()
    news = updater.fetch_news()

    if news:
        print("\nНайденные новости:")
        for article in news:
            print(article)
    else:
        print("Новости не найдены")