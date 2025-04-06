import feedparser
from bs4 import BeautifulSoup
import re
import time


class APIConnector:
    def fetch_rss(self, url):
        feed = feedparser.parse(url)
        if feed.bozo:
            return None  # Ошибка при разборе RSS

        articles = []
        for entry in feed.entries:
            title = entry.title
            link = entry.link
            category = entry.get("category", "Новости")

            # Получаем описание (summary)
            summary = entry.get("summary", "")

            # Извлекаем дату публикации из pubDate
            publication_date = entry.get("published_parsed", None)  # Используем published_parsed, это time.struct_time

            # Получаем местоположение (например, если указано в теге location)
            location = entry.get("location", "Не указано")

            # Чистим HTML в summary
            clean_summary = self.clean_html(summary)

            # Если дата есть, форматируем её
            if publication_date:
                publication_date = self.format_date(publication_date)

            # Добавляем информацию о местоположении и времени
            article = {
                "title": title,
                "link": link,
                "category": category,
                "summary": clean_summary,  # Чистое описание
                "publication_date": publication_date,  # Сохраняем отформатированную дату
                "location": location
            }

            articles.append(article)

        return articles

    def clean_html(self, html_content):
        """Удаляет HTML-теги и ненужные элементы, оставляя только текст"""
        soup = BeautifulSoup(html_content, "html.parser")

        # Удаляем нежелательные элементы
        for tag in soup(["script", "iframe", "style", "blockquote", "noscript"]):
            tag.decompose()

        # Извлекаем только текст
        text = soup.get_text(separator=" ").strip()

        # Убираем неразрывные пробелы (например, '\xa0')
        text = text.replace("\xa0", " ")

        # Убираем дополнительные пробелы, если они есть
        text = re.sub(r'\s+', ' ', text)

        return text

    def format_date(self, published_parsed):
        """Форматирует дату из time.struct_time в строку в формате "день месяц год время"""
        # Словарь месяцев на русском языке
        months = [
            "января", "февраля", "марта", "апреля", "мая", "июня",
            "июля", "августа", "сентября", "октября", "ноября", "декабря"
        ]

        # Форматируем дату
        formatted_date = f"{published_parsed.tm_mday} {months[published_parsed.tm_mon - 1]} {published_parsed.tm_year} {published_parsed.tm_hour:02}:{published_parsed.tm_min:02}:{published_parsed.tm_sec:02}"

        return formatted_date
