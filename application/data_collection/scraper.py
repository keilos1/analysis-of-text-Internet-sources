import feedparser
from bs4 import BeautifulSoup
import re
import hashlib
from datetime import datetime
from urllib.parse import urljoin
import requests


class Scraper:
    def fetch_rss(self, url, source_id, base_url):
        """Получаем статьи из RSS с очищенной разметкой"""
        feed = feedparser.parse(url)
        if feed.bozo:
            return None

        articles = []
        for entry in feed.entries:
            try:
                title = entry.title
                link = urljoin(base_url, entry.link)
                article_id = hashlib.md5(link.encode()).hexdigest()

                # Определяем полный текст в зависимости от источника
                full_text = self.clean_html(entry.get("description", ""), url, entry)

                # Преобразуем дату в объект datetime для MongoDB ISODate
                publication_date = None
                if hasattr(entry, 'published_parsed'):
                    pub_parsed = entry.published_parsed
                    publication_date = datetime(
                        pub_parsed.tm_year,
                        pub_parsed.tm_mon,
                        pub_parsed.tm_mday,
                        pub_parsed.tm_hour,
                        pub_parsed.tm_min,
                        pub_parsed.tm_sec
                    )

                articles.append({
                    "article_id": article_id,
                    "source_id": source_id,
                    "title": title,
                    "url": link,
                    "category": entry.get("category", "Новости"),
                    "publication_date": publication_date,
                    "summary": "",
                    "text": full_text,
                })

            except Exception as e:
                print(f"Ошибка при обработке статьи: {e}")
                continue

        return articles

    def clean_html(self, html_content, url, entry=None):
        """Очистка HTML с учетом особенностей разных источников"""
        if not html_content or isinstance(html_content, list):
            return ""

        # Специальная обработка для gubdaily.ru
        if "gubdaily.ru" in url and entry and hasattr(entry, 'content'):
            for item in entry.content:
                if item.get('type') == 'text/html':
                    html_content = item.value
                    break
            else:
                if hasattr(entry, 'content') and entry.content:
                    html_content = entry.content[0].value

        # Очистка для ptzgovorit.ru
        if "ptzgovorit.ru" in url:
            html_content = re.sub(
                r'©\s*<em>«Петрозаводск говорит»</em>',
                '',
                html_content,
                flags=re.IGNORECASE
            )
            html_content = re.sub(
                r'©\s*«Петрозаводск говорит»',
                '',
                html_content,
                flags=re.IGNORECASE
            )

        soup = BeautifulSoup(html_content, 'html.parser')
        html = ""

        # Общая очистка тегов для всех источников
        for tag in soup(['script', 'style', 'iframe', 'nav', 'footer',
                         'svg', 'noscript', 'figure', 'img']):
            tag.decompose()

        for a_tag in soup.find_all('a'):
            a_tag.unwrap()

        # Специфическая обработка для ptzgovorit.ru
        if "ptzgovorit.ru" in url:
            body_div = soup.select_one('.field-name-body')
            if body_div:
                for div in body_div.find_all('div'):
                    if 'Фото' in div.get_text():
                        div.decompose()

                for tag in body_div.find_all(True):
                    tag.attrs = {}

                allowed_tags = ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'blockquote']
                for tag in body_div.find_all(True):
                    if tag.name not in allowed_tags:
                        tag.unwrap()

                for p in body_div.find_all('p'):
                    if not p.get_text(strip=True):
                        p.decompose()

                html = ''.join(str(child) for child in body_div.children)
            else:
                html = str(soup)
        else:
            # Общая очистка для других источников (включая gubdaily)
            for outer_p in soup.find_all('p'):
                if outer_p.find('p'):
                    outer_p.unwrap()

            for tag in soup.find_all(['p', 'blockquote']):
                if not tag.get_text(strip=True):
                    tag.decompose()
                else:
                    tag.attrs = {}

            allowed_tags = ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'blockquote']
            for tag in soup.find_all(True):
                if tag.name not in allowed_tags:
                    tag.unwrap()

            for p in soup.find_all('p'):
                if not p.get_text(strip=True):
                    p.decompose()

            html = ''.join(str(e) for e in (soup.body.contents if soup.body else soup.contents))

        # Финальная очистка
        html = re.sub(r'>\s+<', '><', html)
        html = re.sub(r'\s*\n\s*', '', html)
        return html.strip()