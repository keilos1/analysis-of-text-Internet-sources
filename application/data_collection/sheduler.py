import re
import sys
from datetime import datetime, timedelta
import asyncio
from bson import ObjectId, json_util
import json

# Добавляем пути до модулей
sys.path.append("../")

# Импорт модулей
from data_collection.scraper import Scraper
from data_collection.socialScraper import SocialScraper, get_social_data
from data_collection.googleSearch import collect_news  # Добавлен импорт Google поиска
from data_storage.database import connect_to_mongo
from config.config import HOST, PORT, SSH_USER, SSH_PASSWORD, DB_NAME, MONGO_HOST, MONGO_PORT, API_KEY, GOOGLE_CX


class DataUpdater:
    def __init__(self):
        self.scraper = Scraper()
        self.social_scraper = SocialScraper()

        # Подключение к БД
        self.db, self.tunnel = connect_to_mongo(
            ssh_host=HOST,
            ssh_port=PORT,
            ssh_user=SSH_USER,
            ssh_password=SSH_PASSWORD,
            mongo_host=MONGO_HOST,
            mongo_port=MONGO_PORT,
            db_name=DB_NAME
        )

        # Загрузка источников
        self.sources = self._get_sources_from_db()

        # API ключи
        self.google_api_key = API_KEY  # ← Укажи свой ключ
        self.google_cx = GOOGLE_CX

    def _get_sources_from_db(self):
        try:
            sources = list(self.db.sources.find())
            return [self._parse_source(source) for source in sources]
        except Exception as e:
            print(f"Ошибка получения источников: {str(e)}")
            return []

    def _parse_source(self, source):
        return {
            "_id": str(source.get("_id")),
            "source_id": source.get("source_id"),
            "name": source.get("name"),
            "url": source.get("url"),
            "category": source.get("category"),
            "district": source.get("district"),
            "area_of_the_city": source.get("area_of_the_city"),
            "last_checked_time": source.get("last_checked_time")
        }

    def _update_source_check_time(self, source_id):
        try:
            self.db.sources.update_one(
                {"source_id": source_id},
                {"$set": {"last_checked_time": datetime.now()}}
            )
            print(f"Обновлено время проверки для источника {source_id}")
        except Exception as e:
            print(f"Ошибка обновления времени проверки: {str(e)}")

    async def _process_social_source(self, source):
        try:
            print(f"\n=== Обрабатываем социальный источник: {source['name']} ({source['url']}) ===")

            social_source = {
                "_id": source.get("_id"),
                "url": source["url"],
                "source_id": source["source_id"],
                "name": source["name"]
            }

            social_data = await get_social_data([social_source])
            articles = []

            if source["source_id"] in social_data:
                for post in social_data[source["source_id"]]:
                    articles.append({
                        "source_id": source["source_id"],
                        "title": post["title"],
                        "text": post["text"],
                        "url": post["url"],
                        "publication_date": post["published_at"],
                        "category": source["category"],
                        "district": source["district"],
                        "area_of_the_city": source["area_of_the_city"],
                        "source_type": post["source_type"]
                    })
                print(f"Найдено {len(articles)} постов")
            else:
                print("Посты не найдены")

            return articles
        except Exception as e:
            print(f"Ошибка при обработке социального источника: {str(e)}")
            return []

    async def fetch_news(self):
        articles_data = []
        social_sources = []
        regular_sources = []
        google_source = None

        for source in self.sources:
            if source["source_id"] == "Google search":
                google_source = source
            elif "vk.com" in source["url"] or "t.me" in source["url"]:
                social_sources.append(source)
            else:
                regular_sources.append(source)

        # Обработка соцсетей
        if social_sources:
            print("\n=== Обработка социальных сетей ===")
            social_articles = await asyncio.gather(
                *[self._process_social_source(source) for source in social_sources]
            )
            for articles in social_articles:
                if articles:
                    articles_data.extend(articles)
                    self._update_source_check_time(articles[0]["source_id"])

        # Обработка RSS
        for source in regular_sources:
            print(f"\n=== Обрабатываем источник: {source['name']} ({source['url']}) ===")
            try:
                if any(ext in source['url'] for ext in ['rss', 'feed', 'xml']):
                    print("Определен RSS источник")
                    articles = self.scraper.fetch_rss(
                        url=source['url'],
                        source_id=source['source_id'],
                        base_url=source['url'].rsplit('/', 1)[0],
                    )
                else:
                    print("Источник не поддерживается (только RSS)")
                    articles = []

                if articles:
                    print(f"Найдено {len(articles)} статей")
                    articles_data.extend(articles)

                self._update_source_check_time(source['source_id'])

            except Exception as e:
                print(f"Ошибка при обработке источника: {str(e)}")
                continue

        # Обработка Google поиска
        if google_source:
            print("\n=== Поиск через Google ===")
            google_queries = [
                "новости Петрозаводска",
                "Петрозаводск происшествия",
                "Петрозаводск экономика",
                "Петрозаводск культура",
                "Петрозаводск политика"
            ]


            google_results = collect_news(google_queries, self.google_api_key, self.google_cx, results_per_query=10)

            for article in google_results:
                article.update({
                    "source_id": google_source["source_id"],
                    "category": google_source["category"],
                    "district": google_source["district"],
                    "area_of_the_city": google_source["area_of_the_city"],
                    "source_type": "google"
                })

            if google_results:
                print(f"Найдено {len(google_results)} новостей через Google")
                articles_data.extend(google_results)
                self._update_source_check_time(google_source["source_id"])
            else:
                print("Google новости не найдены")

        return articles_data

    def __del__(self):
        if hasattr(self, 'tunnel') and self.tunnel:
            self.tunnel.close()
            print("SSH туннель закрыт")


async def main():
    print("=== Запуск сбора новостей ===")
    updater = DataUpdater()
    news = await updater.fetch_news()

    print("\n=== Итоговый отчет ===")
    print(f"Всего собрано статей/постов: {len(news)}")

    if not news:
        print("Нет новых данных.")
        return

    # Разделение по источникам
    google_items = [n for n in news if n.get("source_type") == "google"]
    news_items = [n for n in news if n.get("source_type") not in ["vk", "telegram", "google"]]
    social_items = [n for n in news if n.get("source_type") in ["vk", "telegram"]]

    if news_items:
        print("\n=== Последние 3 новости (RSS и другие сайты) ===")
        for article in news_items[-1:]:
            print(f"\n[{article['source_id']}] {article['title']}")
            print(f"Дата: {article.get('publication_date')}")
            print(f"URL: {article.get('url')}")
            print(f"Текст: {article.get('text', '')[:500]}...")

    if google_items:
        print("\n=== Последние 3 новости из Google ===")
        for article in google_items[-3:]:
            print(f"\n[{article['source_id']}] {article['title']}")
            print(f"Дата: {article.get('publication_date')}")
            print(f"URL: {article.get('url')}")
            print(f"Текст: {article.get('text', '')[:500]}...")

    if social_items:
        print("\n=== Последние 3 поста из соцсетей ===")
        for post in social_items[-1:]:
            print(f"\n[{post['source_id']}] {post['title']}")
            print(f"Дата: {post.get('publication_date')}")
            print(f"URL: {post.get('url')}")
            print(f"Текст: {post.get('text', '')[:500]}...")


if __name__ == "__main__":
    asyncio.run(main())
