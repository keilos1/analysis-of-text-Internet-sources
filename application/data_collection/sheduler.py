import re
import sys
from datetime import datetime, timedelta
import asyncio
from bson import ObjectId, json_util
import json

# Добавляем пути до того как импортируем наши модули
sys.path.append("../")

# Теперь импортируем наши модули
from data_collection.scraper import Scraper  # Переименованный модуль
from data_collection.socialScraper import SocialScraper, get_social_data
from data_storage.database import connect_to_mongo
from config.config import HOST, PORT, SSH_USER, SSH_PASSWORD, DB_NAME, MONGO_HOST, MONGO_PORT


class DataUpdater:
    def __init__(self):
        self.scraper = Scraper()
        self.social_scraper = SocialScraper()

        # Получаем подключение к базе данных
        self.db, self.tunnel = connect_to_mongo(
        ssh_host=HOST,          # если пустое - будет локальное подключение
        ssh_port=PORT,
        ssh_user=SSH_USER,
        ssh_password=SSH_PASSWORD,
        mongo_host=MONGO_HOST,
        mongo_port=MONGO_PORT,
        db_name=DB_NAME
    )

        # Получаем источники из БД
        self.sources = self._get_sources_from_db()

    def _get_sources_from_db(self):
        """Получает список источников из базы данных"""
        try:
            sources = list(self.db.sources.find())
            return [self._parse_source(source) for source in sources]
        except Exception as e:
            print(f"Ошибка получения источников: {str(e)}")
            return []

    def _parse_source(self, source):
        """Преобразует источник из формата MongoDB в словарь"""
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
        """Обновляет время последней проверки источника"""
        try:
            self.db.sources.update_one(
                {"source_id": source_id},
                {"$set": {"last_checked_time": datetime.now()}}
            )
            print(f"Обновлено время проверки для источника {source_id}")
        except Exception as e:
            print(f"Ошибка обновления времени проверки: {str(e)}")

    async def _process_social_source(self, source):
        """Обрабатывает источники из социальных сетей"""
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

        # Разделяем источники на социальные и обычные
        for source in self.sources:
            if "vk.com" in source["url"] or "t.me" in source["url"]:
                social_sources.append(source)
            else:
                regular_sources.append(source)

        # Обрабатываем социальные сети асинхронно
        if social_sources:
            print("\n=== Обработка социальных сетей ===")
            social_articles = await asyncio.gather(
                *[self._process_social_source(source) for source in social_sources]
            )
            for articles in social_articles:
                if articles:
                    articles_data.extend(articles)
                    # self._save_articles(articles)
                    self._update_source_check_time(articles[0]["source_id"])

        # Обрабатываем обычные источники (только RSS)
        for source in regular_sources:
            print(f"\n=== Обрабатываем источник: {source['name']} ({source['url']}) ===")

            try:
                # Парсим только RSS
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
                    for article in articles:
                        articles_data.append(article)
                    # self._save_articles(articles)
                else:
                    print("Статьи не найдены")

                self._update_source_check_time(source['source_id'])

            except Exception as e:
                print(f"Ошибка при обработке источника: {str(e)}")
                continue

        return articles_data

    def __del__(self):
        """Закрывает соединение с БД при уничтожении объекта"""
        if hasattr(self, 'tunnel'):
            self.tunnel.close()
            print("SSH туннель закрыт")


async def main():
    print("=== Запуск сбора новостей ===")
    updater = DataUpdater()
    news = await updater.fetch_news()

    print("\n=== Итоговый отчет ===")
    print(f"Всего собрано статей/постов: {len(news)}")

    if news:
        # Разделяем новости и посты для отчета
        news_items = [n for n in news if n.get("source_type") not in ["vk", "telegram"]]
        social_items = [n for n in news if n.get("source_type") in ["vk", "telegram"]]

        if news_items:
            print("\n=== Последние 3 новости ===")
            for article in news_items[-20:]:
                print(f"\n[{article['source_id']}] {article['title']}")
                print(f"Дата: {article['publication_date']}")
                print(f"URL: {article['url']}")
                print(f"Текст: {article['text'][:10000]}...")

        if social_items:
            print("\n=== Последние 3 поста из соцсетей ===")
            for post in social_items[-3:]:
                print(f"\n[{post['source_id']}] {post['title']}")
                print(f"Дата: {post['publication_date']}")
                print(f"URL: {post['url']}")
                print(f"Текст: {post['text'][:100]}...")


if __name__ == "__main__":
    asyncio.run(main())