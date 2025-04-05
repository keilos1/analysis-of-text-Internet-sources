# data_collection/social_scraper.py
from bs4 import BeautifulSoup
import httpx
import re
from datetime import datetime
from typing import List, Dict
from pymongo import MongoClient


class SocialScraper:
    def __init__(self, db_uri: str = "mongodb://localhost:27017/newsPTZ"):
        self.client = MongoClient(db_uri)
        self.db = self.client.news_db

    def get_social_sources(self) -> List[Dict]:
        """Получаем URL соцсетей из MongoDB"""
        return list(self.db.sources.find({
            "$or": [
                {"url": {"$regex": "vk.com", "$options": "i"}},
                {"url": {"$regex": "t.me", "$options": "i"}}
            ],
            "category": "social_media"
        }))

    async def parse_all_posts(self) -> List[Dict]:
        """Основная функция парсинга"""
        sources = self.get_social_sources()
        all_posts = []

        async with httpx.AsyncClient(timeout=10.0) as client:
            for source in sources:
                if "vk.com" in source["url"]:
                    posts = await self._parse_vk(client, source)
                elif "t.me" in source["url"]:
                    posts = await self._parse_telegram(client, source)

                all_posts.extend(posts)

        return all_posts

    async def _parse_vk(self, client: httpx.AsyncClient, source: Dict) -> List[Dict]:
        """Парсинг постов VK"""
        try:
            group_id = re.search(r'vk\.com/([^/]+)', source["url"]).group(1)
            response = await client.get(
                f"https://vk.com/{group_id}",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            soup = BeautifulSoup(response.text, "html.parser")

            return [{
                "source_id": str(source["_id"]),
                "title": f"Новость из VK-{group_id}",
                "content": post.select_one(".wall_post_text").get_text("\n", strip=True),
                "url": f"https://vk.com{post.select_one('.post_link')['href']}",
                "published_at": datetime.now(),
                "source_type": "vk"
            } for post in soup.select(".wall_item") if post.select_one(".wall_post_text")]
        except Exception as e:
            print(f"Ошибка парсинга VK: {str(e)}")
            return []

    async def _parse_telegram(self, client: httpx.AsyncClient, source: Dict) -> List[Dict]:
        """Парсинг Telegram"""
        try:
            channel_name = re.search(r't\.me/([^/]+)', source["url"]).group(1)
            response = await client.get(
                f"https://t.me/s/{channel_name}",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            soup = BeautifulSoup(response.text, "html.parser")

            return [{
                "source_id": str(source["_id"]),
                "title": f"Новость из Telegram-{channel_name}",
                "content": msg.select_one(".tgme_widget_message_text").get_text("\n", strip=True),
                "url": msg.select_one(".tgme_widget_message_date")["href"],
                "published_at": datetime.now(),
                "source_type": "telegram"
            } for msg in soup.select(".tgme_widget_message") if msg.select_one(".tgme_widget_message_text")]
        except Exception as e:
            print(f"Ошибка парсинга Telegram: {str(e)}")
            return []

    def close(self):
        self.client.close()


