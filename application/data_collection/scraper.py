import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import hashlib
from datetime import datetime
import re


class WebScraper:
    def fetch_page(self, url):
        """Получаем HTML-контент страницы по URL"""
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.text
            return None
        except Exception as e:
            print(f"Ошибка при загрузке страницы: {e}")
            return None

    def parse_articles(self, html, source_id, base_url, container_tag, title_tag, link_tag, content_tag,
                       full_text_selector=None):
        """Парсим статьи со страницы и получаем полный текст"""
        soup = BeautifulSoup(html, "html.parser")
        articles = []
        article_containers = soup.find_all(container_tag)

        for container in article_containers:
            try:
                title_tag_content = container.find(title_tag)
                link_tag_content = container.find(link_tag)
                content_tag_content = container.find(content_tag)

                if not (title_tag_content and link_tag_content):
                    continue

                title = title_tag_content.get_text(strip=True)
                relative_link = link_tag_content.get('href', '')
                link = urljoin(base_url, relative_link)
                summary = content_tag_content.get_text(strip=True) if content_tag_content else ""

                # Получаем полный текст статьи если указан селектор
                full_text = self._get_full_text(link, full_text_selector) if full_text_selector else summary
                
                # Удаляем фразу "© «Петрозаводск говорит»" из конца текста
                cleaned_text = self._remove_footer(full_text)

                articles.append({
                    "article_id": hashlib.md5(link.encode()).hexdigest(),
                    "source_id": source_id,
                    "title": title,
                    "url": link,
                    "publication_date": self.extract_date(container) or datetime.now().isoformat(),
                    "summary": summary,
                    "text": cleaned_text,  # Используем очищенный текст
                    "scraped_at": datetime.now().isoformat()
                })

            except Exception as e:
                print(f"Ошибка при парсинге статьи: {e}")
                continue

        return articles

    def _remove_footer(self, text):
        """Удаляет фразу '© «Петрозаводск говорит»' из конца текста"""
        if not text:
            return text
            
        # Удаляем фразу с возможными вариантами оформления
        patterns = [
            r'\s*©\s*«Петрозаводск говорит»\s*$',
            r'\s*©\s*Петрозаводск говорит\s*$',
            r'\s*«Петрозаводск говорит»\s*$'
        ]
        
        for pattern in patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
            
        return text.strip()

    def extract_date(self, container):
        """Извлекаем дату публикации"""
        # Проверяем мета-теги
        for prop in ["date", "article:published_time"]:
            meta = container.find("meta", {"property": prop}) or container.find("meta", {"name": prop})
            if meta and meta.get('content'):
                return meta.get('content')

        # Проверяем тег <time>
        time_tag = container.find("time")
        if time_tag and time_tag.has_attr('datetime'):
            return time_tag['datetime']

        return None

    def _get_full_text(self, article_url, selector):
        """Внутренний метод для получения полного текста статьи"""
        html = self.fetch_page(article_url)
        if not html:
            return ""

        soup = BeautifulSoup(html, 'html.parser')
        content = soup.select_one(selector)
        return content.get_text(strip=True, separator='\n') if content else ""
