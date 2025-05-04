from bs4 import BeautifulSoup
import httpx
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any

class SocialScraper:
    def __init__(self):
        self.time_threshold = datetime.now() - timedelta(minutes=30)  # Фильтр по времени (последние 30 минут)

    async def collect_social_data(self, sources: List[Dict]) -> Dict[str, List[Dict[str, Any]]]:
        """Собираем данные из социальных сетей за последние 30 минут и возвращаем в виде словаря"""
        posts_dict = {}

        async with httpx.AsyncClient(timeout=30.0) as client:
            for source in sources:
                source_id = source.get("_id", "")
                try:
                    if "vk.com" in source["url"]:
                        posts = await self._parse_vk(client, source)
                    elif "t.me" in source["url"]:
                        posts = await self._parse_telegram(client, source)
                    else:
                        continue

                    # Фильтруем по времени (только последние 30 минут)
                    filtered_posts = [
                        post for post in posts
                        if post["published_at"] > self.time_threshold
                    ]
                    
                    # Добавляем посты в словарь
                    if source_id not in posts_dict:
                        posts_dict[source_id] = []
                    posts_dict[source_id].extend(filtered_posts)

                except Exception as e:
                    print(f"Ошибка парсинга {source['url']}: {str(e)}")

        return posts_dict

    async def _parse_vk(self, client: httpx.AsyncClient, source: Dict) -> List[Dict[str, Any]]:
        """Парсинг постов VK за последние 30 минут"""
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
                        "source_id": source.get("_id", ""),
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
        """Парсинг Telegram за последние 30 минут"""
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
                        "source_id": source.get("_id", ""),
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

async def get_social_data(sources: List[Dict]) -> Dict[str, List[Dict[str, Any]]:
    """Функция для получения данных из социальных сетей (только последние 30 минут)
    Возвращает словарь, где ключи - идентификаторы источников, значения - списки постов"""
    scraper = SocialScraper()
    return await scraper.collect_social_data(sources)
