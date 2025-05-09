import re
from datetime import datetime
from data_collection.api_connector import APIConnector
from data_collection.scraper import WebScraper


class DataUpdater:
    def __init__(self):
        self.api_connector = APIConnector()
        self.scraper = WebScraper()

        # Пример источников из БД (в реальности нужно получать через self.db.get_source())
        self.sources = [
            {
                "source_id": "stolicaonego",
                "name": "Столица Онего",
                "url": "https://stolicaonego.ru/rss.php",
                "category": "Новости",
                "district": "Республика Карелия",
                "area_of_the_city": "Петрозаводск",
                "last_checked_time": None
            },
            {
                "source_id": "gubdaily",
                "name": "Губернiя Daily",
                "url": "https://gubdaily.ru/feed/",
                "category": "Новости",
                "district": "Республика Карелия",
                "area_of_the_city": "Петрозаводск",
                "last_checked_time": None
            },
            {
                "source_id": "ptzgovorit",
                "name": "Петрозаводск говорит",
                "url": "https://ptzgovorit.ru/rss.xml",
                "category": "Новости",
                "district": "Республика Карелия",
                "area_of_the_city": "Петрозаводск",
                "last_checked_time": None
            }

        ]

    def fetch_news(self):
        articles_data = []

        for source in self.sources:
            print(f"\n=== Обрабатываем источник: {source['name']} ({source['url']}) ===")

            try:
                # Пробуем парсить как RSS
                if any(ext in source['url'] for ext in ['rss', 'feed', 'xml']):
                    print("Определен RSS источник")
                    articles = self.api_connector.fetch_rss(
                        url=source['url'],
                        source_id=source['source_id'],
                        base_url=source['url'].rsplit('/', 1)[0],
                    )
                else:
                    # Парсим как HTML
                    print("Определен HTML источник")
                    html = self.scraper.fetch_page(source['url'])
                    articles = self.scraper.parse_articles(
                        html=html,
                        source_id=source['source_id'],
                        base_url=source['url'].rsplit('/', 1)[0],
                        container_tag="article",
                        title_tag="h2",
                        link_tag="a",
                        content_tag="p",
                        full_text_selector=None
                    ) if html else []

                if articles:
                    print(f"Найдено {len(articles)} статей")
                    for article in articles:
                        articles_data.append(article)
                else:
                    print("Статьи не найдены")

                # Обновляем время последней проверки (в реальности через self.db.save_source())
                source['last_checked_time'] = datetime.now().isoformat()

            except Exception as e:
                print(f"Ошибка при обработке источника: {str(e)}")
                continue

        return articles_data


if __name__ == "__main__":
    print("=== Запуск сбора новостей ===")
    updater = DataUpdater()
    news = updater.fetch_news()
    print(news)

    print("\n=== Итоговый отчет ===")
    print(f"Всего собрано статей: {len(news)}")
    if news:
        print("\nПоследние 3 статьи:")
        for article in news[-3:]:
            print(f"\n[{article['source_id']}] {article['title']}")
            print(f"Дата: {article['publication_date']}")
            print(f"URL: {article['url']}")
            print(f"Текст: {article['text'][:10000]}...")
