from bs4 import BeautifulSoup
import httpx
import re
from datetime import datetime
from typing import List, Dict, Any
from sshtunnel import SSHTunnelForwarder
from pymongo import MongoClient
import asyncio
import sys
sys.path.append("../")
from data_storage.database import connect_to_mongo

# Константы подключения
SSH_HOST = '78.36.44.126'
SSH_PORT = 57381
SSH_USER = 'server'
SSH_PASSWORD = 'tppo'
DB_NAME = 'newsPTZ'

class SocialScraper:
    def __init__(self):
        self.posts_limit = 10  # Лимит постов для сбора
        # Подключаемся к базе данных
        self.db, self.tunnel = connect_to_mongo(
            ssh_host=SSH_HOST,
            ssh_port=SSH_PORT,
            ssh_user=SSH_USER,
            ssh_password=SSH_PASSWORD,
            db_name=DB_NAME
        )

    async def collect_social_data(self, sources: List[Dict]) -> Dict[str, List[Dict[str, Any]]:
        """Собираем последние 10 постов из социальных сетей и возвращаем в виде словаря"""
        posts_dict = {}

        async with httpx.AsyncClient(timeout=30.0) as client:
            for source in sources:
                source_id = source.get("source_id", "")
                try:
                    if "vk.com" in source["url"]:
                        posts = await self._parse_vk(client, source)
                    elif "t.me" in source["url"]:
                        posts = await self._parse_telegram(client, source)
                    else:
                        continue

                    # Ограничиваем количество постов
                    limited_posts = posts[:self.posts_limit]
                    
                    # Добавляем посты в словарь
                    if source_id not in posts_dict:
                        posts_dict[source_id] = []
                    posts_dict[source_id].extend(limited_posts)

                except Exception as e:
                    print(f"Ошибка парсинга {source['url']}: {str(e)}")

        return posts_dict

    async def _parse_vk(self, client: httpx.AsyncClient, source: Dict) -> List[Dict[str, Any]]:
        """Парсинг последних постов VK"""
        try:
            group_id = re.search(r'vk\.com/([^/]+)', source["url"]).group(1)
            response = await client.get(
                f"https://vk.com/{group_id}",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            soup = BeautifulSoup(response.text, "html.parser")

            posts = []
            for post in soup.select(".wall_item")[:self.posts_limit]:
                post_time = self._extract_vk_time(post)
                posts.append({
                    "source_id": source.get("source_id", ""),
                    "source_name": f"VK-{group_id}",
                    "title": f"Новость из VK-{group_id}",
                    "text": post.select_one(".wall_post_text").get_text("\n", strip=True),
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

    async def _parse_telegram(self, client: httpx.AsyncClient, source: Dict) -> List[Dict[str, Any]]:
        """Парсинг последних постов Telegram"""
        try:
            channel_name = re.search(r't\.me/([^/]+)', source["url"]).group(1)
            response = await client.get(
                f"https://t.me/s/{channel_name}",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            soup = BeautifulSoup(response.text, "html.parser")

            posts = []
            for msg in soup.select(".tgme_widget_message")[:self.posts_limit]:
                msg_time = self._extract_telegram_time(msg)
                posts.append({
                    "source_id": source.get("source_id", ""),
                    "source_name": f"Telegram-{channel_name}",
                    "title": f"Новость из Telegram-{channel_name}",
                    "text": msg.select_one(".tgme_widget_message_text").get_text("\n", strip=True),
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

    def close_connection(self):
        """Закрывает соединение с базой данных и SSH-туннель"""
        if hasattr(self, 'tunnel'):
            self.tunnel.stop()

async def get_social_data(sources: List[Dict]) -> Dict[str, List[Dict[str, Any]]]:
    """Получаем последние 10 постов из социальных сетей"""
    scraper = SocialScraper()
    try:
        return await scraper.collect_social_data(sources)
    finally:
        scraper.close_connection()

def print_posts(posts_data: Dict[str, List[Dict[str, Any]]]):
    """Выводим посты в консоль в удобном формате"""
    for source_id, posts in posts_data.items():
        print(f"\n=== Источник {source_id} ===")
        for i, post in enumerate(posts, 1):
            print(f"\nПост #{i}:")
            print(f"Заголовок: {post.get('title', 'Без заголовка')}")
            print(f"Дата: {post.get('published_at', 'Неизвестно')}")
            print(f"Текст: {post.get('text', 'Без текста')}")
            print(f"Ссылка: {post.get('url', 'Нет ссылки')}")
            print(f"Тип: {post.get('source_type', 'Неизвестно')}")

async def main():
    """Основная функция для выполнения скрипта"""
    # Пример списка источников (можно заменить на получение из базы данных)
    sources = [
        {"source_id": "vk_ptz", "url": "https://vk.com/petrozavodsk"},
        {"source_id": "tg_ptz", "url": "https://t.me/petrozavodsk_now"}
    ]
    
    # Получаем данные
    posts_data = await get_social_data(sources)
    
    # Выводим результаты
    print_posts(posts_data)

if __name__ == "__main__":
    asyncio.run(main())
