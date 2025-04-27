# data_collection/social_scraper.py
from bs4 import BeautifulSoup
import httpx
import re
from datetime import datetime, timedelta
from typing import List, Dict
from pymongo import MongoClient

class SocialScraper:
    def __init__(self, db_uri: str = "mongodb://localhost:27017/newsPTZ"):
        self.client = MongoClient(db_uri)
        self.db = self.client.news_db
        self.time_threshold = datetime.now() - timedelta(hours=24)  # Фильтр по времени

    def get_social_sources(self) -> List[Dict]:
        """Получаем URL соцсетей из MongoDB"""
        return list(self.db.sources.find({
            "$or": [
                {"url": {"$regex": "vk.com", "$options": "i"}},
                {"url": {"$regex": "t.me", "$options": "i"}}
            ],
            "category": "social_media"
        }))

    async def parse_recent_posts(self) -> List[Dict]:
        """Парсим только посты за последние 24 часа"""
        sources = self.get_social_sources()
        recent_posts = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            for source in sources:
                try:
                    if "vk.com" in source["url"]:
                        posts = await self._parse_vk(client, source)
                    elif "t.me" in source["url"]:
                        posts = await self._parse_telegram(client, source)

                    # Фильтруем по времени
                    filtered_posts = [
                        post for post in posts
                        if post["published_at"] > self.time_threshold
                    ]
                    recent_posts.extend(filtered_posts)

                except Exception as e:
                    print(f"Ошибка парсинга {source['url']}: {str(e)}")

        return recent_posts

    async def _parse_vk(self, client: httpx.AsyncClient, source: Dict) -> List[Dict]:
        """Парсинг постов VK за последние 24 часа"""
        try:
            group_id = re.search(r'vk\.com/([^/]+)', source["url"]).group(1)
            response = await client.get(
                f"https://vk.com/{group_id}",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            soup = BeautifulSoup(response.text, "html.parser")

            posts = []
            for post in soup.select(".wall_item"):
                post_time = self._extract_vk_time(post)
                if post_time > self.time_threshold:
                    posts.append({
                        "source_id": str(source["_id"]),
                        "title": f"Новость из VK-{group_id}",
                        "content": post.select_one(".wall_post_text").get_text("\n", strip=True),
                        "url": f"https://vk.com{post.select_one('.post_link')['href']}",
                        "published_at": post_time,
                        "source_type": "vk"
                    })
            return posts

        except Exception as e:
            print(f"Ошибка парсинга VK: {str(e)}")
            return []

    def _extract_vk_time(self, post_element) -> datetime:
        """Извлекаем реальное время публикации из VK"""
        time_element = post_element.select_one(".rel_date")
        if time_element and 'time' in time_element.attrs:
            return datetime.fromtimestamp(int(time_element['time']))
        return datetime.now()

    async def _parse_telegram(self, client: httpx.AsyncClient, source: Dict) -> List[Dict]:
        """Парсинг Telegram за последние 24 часа"""
        try:
            channel_name = re.search(r't\.me/([^/]+)', source["url"]).group(1)
            response = await client.get(
                f"https://t.me/s/{channel_name}",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            soup = BeautifulSoup(response.text, "html.parser")

            posts = []
            for msg in soup.select(".tgme_widget_message"):
                msg_time = self._extract_telegram_time(msg)
                if msg_time > self.time_threshold:
                    posts.append({
                        "source_id": str(source["_id"]),
                        "title": f"Новость из Telegram-{channel_name}",
                        "content": msg.select_one(".tgme_widget_message_text").get_text("\n", strip=True),
                        "url": msg.select_one(".tgme_widget_message_date")["href"],
                        "published_at": msg_time,
                        "source_type": "telegram"
                    })
            return posts

        except Exception as e:
            print(f"Ошибка парсинга Telegram: {str(e)}")
            return []

    def _extract_telegram_time(self, message_element) -> datetime:
        """Извлекаем точное время публикации из Telegram"""
        time_element = message_element.select_one("time[datetime]")
        if time_element:
            return datetime.strptime(
                time_element["datetime"],
                "%Y-%m-%dT%H:%M:%S%z"
            ).replace(tzinfo=None)
        return datetime.now()

    def save_to_db(self, posts: List[Dict]):
        """Сохраняем только новые посты"""
        existing_urls = {p["url"] for p in self.db.social_posts.find({}, {"url": 1})}
        new_posts = [p for p in posts if p["url"] not in existing_urls]

        if new_posts:
            self.db.social_posts.insert_many(new_posts)
            print(f"Добавлено {len(new_posts)} новых постов")

    def close(self):
        self.client.close()

