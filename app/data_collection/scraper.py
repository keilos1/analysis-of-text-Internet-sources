import requests
from bs4 import BeautifulSoup

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

    def parse_articles(self, html, container_tag, title_tag, link_tag, content_tag):
        """Парсим статьи со страницы"""
        soup = BeautifulSoup(html, "html.parser")

        articles = []
        article_containers = soup.find_all(container_tag)

        for container in article_containers:
            title_tag_content = container.find(title_tag)
            link_tag_content = container.find(link_tag)
            content_tag_content = container.find(content_tag)

            # Извлекаем данные статьи
            if title_tag_content and link_tag_content and content_tag_content:
                title = title_tag_content.get_text(strip=True)
                link = link_tag_content.get('href', '')
                summary = content_tag_content.get_text(strip=True)  # Заменили на summary

                # Извлекаем дату (сохраняем как есть)
                publication_date = self.extract_date(soup)

                articles.append({
                    "title": title,
                    "link": link,
                    "summary": summary,  # Используем summary вместо content
                    "publication_date": publication_date
                })

        return articles

    def extract_date(self, soup):
        """Пытаемся извлечь дату из страницы"""
        # Пример поиска мета-тега с датой
        date_meta_tag = soup.find("meta", {"name": "date"})  # Возможно другой атрибут, зависит от страницы
        if date_meta_tag:
            date_str = date_meta_tag.get('content')
            return date_str  # Возвращаем дату как есть, без преобразования

        # Если дата не найдена в мета-тегах, пробуем искать дату в других местах страницы
        # Например, в теге <time>
        date_from_content = soup.find("time")
        if date_from_content:
            return date_from_content.get('datetime', None)

        return None
