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
        print("Инициализация подключения к базе данных...")
        self.db, self.tunnel = connect_to_mongo(
            ssh_host=SSH_HOST,
            ssh_port=SSH_PORT,
            ssh_user=SSH_USER,
            ssh_password=SSH_PASSWORD,
            db_name=DB_NAME
        )
        print("Подключение к базе данных установлено")

    async def collect_social_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Собираем последние 10 постов из социальных сетей"""
        posts_dict = {}

        # Получаем ВСЕ источники из базы данных
        print("Получаем источники из базы данных...")
        sources = list(self.db.sources.find({}))
        print(f"Найдено источников: {len(sources)}")

        if not sources:
            print("В базе нет источников для парсинга!")
            return posts_dict

        async with httpx.AsyncClient(
                timeout=30.0,
                headers={"User-Agent": "Mozilla/5.0"}
        ) as client:
            for source in sources:
                source_id = source.get("source_id", "unknown")
                url = source.get("url", "")
                print(f"\nОбрабатываем источник {source_id} ({url})...")

                try:
                    if "vk.com" in url:
                        print("Определен как VK источник")
                        posts = await self._parse_vk(client, source)
                    elif "t.me" in url:
                        print("Определен как Telegram источник")
                        posts = await self._parse_telegram(client, source)
                    else:
                        print(f"Неизвестный тип источника: {url}")
                        continue

                    if not posts:
                        print(f"Не удалось получить посты для {url}")
                        continue

                    limited_posts = posts[:self.posts_limit]
                    posts_dict[source_id] = limited_posts
                    print(f"Добавлено постов: {len(limited_posts)}")

                except Exception as e:
                    print(f"Ошибка при обработке {url}: {str(e)}", file=sys.stderr)

        return posts_dict

    async def _parse_vk(self, client: httpx.AsyncClient, source: Dict) -> List[Dict[str, Any]]:
        """Парсинг последних постов VK с улучшенными селекторами"""
        try:
            group_id = re.search(r'vk\.com/([^/]+)', source["url"]).group(1)
            print(f"Парсим VK группу: {group_id}")

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "ru-RU,ru;q=0.9"
            }

            response = await client.get(
                f"https://vk.com/{group_id}",
                headers=headers,
                follow_redirects=True
            )

            if response.status_code != 200:
                print(f"Ошибка {response.status_code} при запросе {source['url']}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')

            # Новые селекторы для современного VK
            posts = []
            post_elements = soup.select('.wall_item, ._post, .Post, .post')

            print(f"Найдено элементов-кандидатов: {len(post_elements)}")

            for post in post_elements[:self.posts_limit]:
                try:
                    # 1. Получаем текст поста
                    text_elem = post.select_one('.wall_post_text, .wall_post_content, .Post__text, .pi_text')
                    if not text_elem:
                        continue

                    post_text = text_elem.get_text('\n', strip=True)

                    # 2. Получаем время поста
                    time_elem = post.select_one('time, .rel_date, .post_date, .Post__time')
                    if time_elem and 'datetime' in time_elem.attrs:
                        post_time = datetime.strptime(
                            time_elem['datetime'],
                            "%Y-%m-%dT%H:%M:%S%z"
                        ).replace(tzinfo=None)
                    elif time_elem and 'time' in time_elem.attrs:
                        post_time = datetime.fromtimestamp(int(time_elem['time']))
                    else:
                        post_time = datetime.now()

                    # 3. Получаем ссылку на пост
                    link_elem = post.select_one('a.post_link, a.Post__anchor')
                    post_url = f"https://vk.com{link_elem['href']}" if link_elem else source['url']

                    posts.append({
                        "source_id": source.get("source_id", ""),
                        "source_name": f"VK-{group_id}",
                        "title": f"Новость из VK-{group_id}",
                        "text": post_text,
                        "url": post_url,
                        "published_at": post_time,
                        "source_type": "vk"
                    })

                except Exception as e:
                    print(f"Ошибка обработки поста: {str(e)}")
                    continue

            print(f"Успешно извлечено постов: {len(posts)}")
            return posts

        except Exception as e:
            print(f"Ошибка парсинга VK: {str(e)}")
            return []

    def _extract_vk_time(self, post_element) -> datetime:
        """Извлекаем время публикации из VK"""
        time_element = post_element.select_one(".rel_date")
        if time_element and 'time' in time_element.attrs:
            return datetime.fromtimestamp(int(time_element['time']))
        return datetime.now()

    async def _parse_telegram(self, client: httpx.AsyncClient, source: Dict) -> List[Dict[str, Any]]:
        """Парсинг последних постов Telegram"""
        try:
            channel_name = re.search(r't\.me/([^/]+)', source["url"]).group(1)
            print(f"Парсим Telegram канал: {channel_name}")

            response = await client.get(
                f"https://t.me/s/{channel_name}",
                headers={"User-Agent": "Mozilla/5.0"}
            )

            if response.status_code != 200:
                print(f"Ошибка HTTP {response.status_code} для {source['url']}")
                return []

            soup = BeautifulSoup(response.text, "html.parser")
            posts = []

            for msg in soup.select(".tgme_widget_message")[:self.posts_limit]:
                try:
                    msg_time = self._extract_telegram_time(msg)
                    text_element = msg.select_one(".tgme_widget_message_text")
                    link_element = msg.select_one(".tgme_widget_message_date")

                    if not text_element or not link_element:
                        continue

                    posts.append({
                        "source_id": source.get("source_id", ""),
                        "source_name": f"Telegram-{channel_name}",
                        "title": f"Новость из Telegram-{channel_name}",
                        "text": text_element.get_text("\n", strip=True),
                        "url": link_element["href"],
                        "published_at": msg_time,
                        "source_type": "telegram"
                    })
                except Exception as e:
                    print(f"Ошибка обработки поста Telegram: {str(e)}")
                    continue

            return posts

        except Exception as e:
            print(f"Ошибка парсинга Telegram: {str(e)}")
            return []

    def _extract_telegram_time(self, message_element) -> datetime:
        """Извлекаем время публикации из Telegram"""
        time_element = message_element.select_one("time[datetime]")
        if time_element:
            return datetime.strptime(
                time_element["datetime"],
                "%Y-%m-%dT%H:%M:%S%z"
            ).replace(tzinfo=None)
        return datetime.now()

    def close_connection(self):
        """Закрывает соединение с базой данных"""
        if hasattr(self, 'tunnel'):
            print("Закрытие подключения к базе данных...")
            self.tunnel.stop()


async def get_social_data() -> Dict[str, List[Dict[str, Any]]]:
    """Получаем посты из социальных сетей"""
    print("\nЗапуск сбора данных...")
    scraper = SocialScraper()
    try:
        return await scraper.collect_social_data()
    finally:
        scraper.close_connection()


def print_posts(posts_data: Dict[str, List[Dict[str, Any]]]):
    """Выводим посты в консоль"""
    if not posts_data:
        print("\nНе удалось получить ни одного поста!")
        return

    print("\nРезультаты парсинга:")
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
    """Основная функция"""
    print("=== Запуск скрипта парсинга ===")
    posts_data = await get_social_data()
    print_posts(posts_data)
    print("\n=== Работа завершена ===")


if __name__ == "__main__":
    asyncio.run(main())
