from bs4 import BeautifulSoup
import httpx
import re
from datetime import datetime
from typing import List, Dict, Any
import asyncio
import sys

class SocialScraper:
    def __init__(self):
        self.posts_limit = 10
        print("Инициализация SocialScraper...")

    async def collect_social_data(self, sources: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Собираем последние посты из Telegram"""
        posts_dict = {}
        
        print(f"Получено Telegram источников для обработки: {len(sources)}")
        
        if not sources:
            print("Нет Telegram источников для парсинга!")
            return posts_dict

        async with httpx.AsyncClient(
            timeout=30.0,
            headers={"User-Agent": "Mozilla/5.0"}
        ) as client:
            for source in sources:
                source_id = source.get("source_id", "unknown")
                url = source.get("url", "")
                print(f"\nОбрабатываем Telegram источник {source_id} ({url})...")
                
                try:
                    posts = await self._parse_telegram(client, source)
                    if not posts:
                        print(f"Не удалось получить посты для {url}")
                        continue

                    posts_dict[source_id] = posts[:self.posts_limit]
                    print(f"Добавлено постов: {len(posts[:self.posts_limit])}")

                except Exception as e:
                    print(f"Ошибка при обработке {url}: {str(e)}", file=sys.stderr)

        return posts_dict

    def _remove_emojis(self, text: str) -> str:
        """Удаляем эмодзи из текста"""
        emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               u"\U00002500-\U00002BEF"  # chinese char
                               u"\U00002702-\U000027B0"
                               u"\U00002702-\U000027B0"
                               u"\U000024C2-\U0001F251"
                               u"\U0001f926-\U0001f937"
                               u"\U00010000-\U0010ffff"
                               u"\u2640-\u2642"
                               u"\u2600-\u2B55"
                               u"\u200d"
                               u"\u23cf"
                               u"\u23e9"
                               u"\u231a"
                               u"\ufe0f"  # dingbats
                               u"\u3030"
                               "]+", flags=re.UNICODE)
        return emoji_pattern.sub(r'', text)

    def _is_forwarded_message(self, message_element) -> bool:
        """Определяем, является ли сообщение пересланным"""
        if message_element.select_one(".tgme_widget_message_forwarded_from"):
            return True
        
        if message_element.select_one(".tgme_widget_message_forwarded_icon"):
            return True
            
        text_element = message_element.select_one(".tgme_widget_message_text")
        if text_element:
            text = text_element.get_text().lower()
            if "forwarded from" in text or "переслано из" in text:
                return True
        
        return False

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
            
            for msg in soup.select(".tgme_widget_message")[:self.posts_limit*2]:
                try:
                    if self._is_forwarded_message(msg):
                        continue
                        
                    reply = msg.select_one(".tgme_widget_message_reply")
                    reply_info = None
                    
                    if reply:
                        reply_author = reply.select_one(".tgme_widget_message_author_name")
                        reply_text = reply.select_one(".tgme_widget_message_text")
                        
                        reply_info = {
                            "author": reply_author.get_text(strip=True) if reply_author else None,
                            "text": reply_text.get_text("\n", strip=True) if reply_text else None
                        }
                        reply.extract()
                    
                    text_element = msg.select_one(".tgme_widget_message_text")
                    if not text_element:
                        continue
                    
                    full_text = text_element.get_text("\n", strip=True)
                    clean_text = self._remove_emojis(full_text)
                    
                    lines = [line.strip() for line in clean_text.split('\n') if line.strip()]
                    first_line = lines[0] if lines else f"Сообщение из {channel_name}"
                    
                    msg_time = self._extract_telegram_time(msg)
                    link_element = msg.select_one(".tgme_widget_message_date")
                    
                    if not link_element:
                        continue
                        
                    post_data = {
                        "source_id": source.get("source_id", ""),
                        "source_name": f"Telegram-{channel_name}",
                        "title": first_line,
                        "text": clean_text,
                        "url": link_element["href"],
                        "published_at": msg_time,
                        "source_type": "telegram"
                    }
                    
                    if reply_info:
                        post_data["reply_to"] = reply_info
                    
                    posts.append(post_data)
                    
                    if len(posts) >= self.posts_limit:
                        break
                        
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

async def get_social_data(sources: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Получаем посты из Telegram"""
    print("\nЗапуск сбора данных из социальных сетей...")
    scraper = SocialScraper()
    try:
        return await scraper.collect_social_data(sources)
    except Exception as e:
        print(f"Ошибка при сборе социальных данных: {str(e)}")
        return {}
