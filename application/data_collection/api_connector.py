import feedparser
from bs4 import BeautifulSoup
import re
import hashlib
from datetime import datetime
from urllib.parse import urljoin
import requests


class APIConnector:
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
                full_text = self.clean_html(entry.get("description", ""), url)

                publication_date = self.format_date(entry.get("published_parsed"))

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

    def clean_html(self, html_content, url):
        """Очистка HTML без вложенных <p><p> и лишних тегов для разных источников"""
        if not html_content or isinstance(html_content, list):
            return ""

        soup = BeautifulSoup(html_content, 'html.parser')

        # Удаляем ненужные теги
        for tag in soup(['script', 'style', 'iframe', 'nav', 'footer',
                         'svg', 'noscript', 'figure', 'img', 'a']):
            tag.decompose()

        # Если источник ptzgovorit.ru, то выполняем специфическую очистку
        if "ptzgovorit.ru" in url:
            # Оставляем только основной текст
            body_div = soup.select_one('.field-name-body')
            if body_div:
                # Удаляем нежелательные теги внутри
                for tag in body_div(['script', 'style', 'iframe', 'img', 'a']):
                    tag.decompose()

                # Удаляем подписи вроде "Фото со страницы ..."
                for div in body_div.find_all('div'):
                    if 'Фото' in div.get_text():
                        div.decompose()

                # Очищаем все теги от атрибутов
                for tag in body_div.find_all(True):
                    tag.attrs = {}

                # Разворачиваем ненужные теги
                allowed_tags = ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'blockquote']
                for tag in body_div.find_all(True):
                    if tag.name not in allowed_tags:
                        tag.unwrap()


                # Собираем текст
                html = str(body_div)
        else:
            # Для остальных источников
            # Разворачиваем вложенные <p> (если внутри p есть другие p — удаляем внешний p)
            for outer_p in soup.find_all('p'):
                if outer_p.find('p'):
                    outer_p.unwrap()

            # Чистим пустые и атрибуты
            for tag in soup.find_all(['p', 'blockquote']):
                if not tag.get_text(strip=True):
                    tag.decompose()
                else:
                    tag.attrs = {}

            # Удаляем все неразрешённые теги
            allowed_tags = ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'blockquote']
            for tag in soup.find_all(True):
                if tag.name not in allowed_tags:
                    tag.unwrap()

            # Собираем текст
            contents = soup.body.contents if soup.body else soup.contents
            html = ''.join(str(e) for e in contents)

        # Чистим пробелы и переносы
        html = re.sub(r'>\s+<', '><', html)
        html = re.sub(r'\s*\n\s*', '', html)

        return html.strip()

    def format_date(self, published_parsed):
        """Форматирование даты"""
        months = ["января", "февраля", "марта", "апреля", "мая", "июня",
                  "июля", "августа", "сентября", "октября", "ноября", "декабря"]

        if not published_parsed:
            return None

        return (f"{published_parsed.tm_mday} {months[published_parsed.tm_mon - 1]} {published_parsed.tm_year} "
                f"{published_parsed.tm_hour:02}:{published_parsed.tm_min:02}:{published_parsed.tm_sec:02}")
