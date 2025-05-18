import pytest
from bs4 import BeautifulSoup
from application.data_collection.scraper import Scraper
from unittest.mock import patch


class TestScraper:
    @pytest.fixture
    def scraper(self):
        return Scraper()

    # Тест М7: Проверка парсинга RSS ленты
    @patch('feedparser.parse')
    def test_fetch_rss_success(self, mock_parse, scraper):
        """Позитивный тест для fetch_rss с корректным RSS"""
        mock_parse.return_value = {
            'entries': [
                {
                    'title': 'Тестовая новость',
                    'link': 'http://example.com/news1',
                    'description': '<p>Текст новости</p>',
                    'published_parsed': (2025, 5, 1, 12, 0, 0, 0, 0, 0),
                    'category': 'Политика'
                }
            ],
            'bozo': 0
        }

        result = scraper.fetch_rss(
            url="http://valid.rss",
            source_id="test_source",
            base_url="http://example.com"
        )

        assert len(result) == 1
        assert result[0]['title'] == 'Тестовая новость'
        assert result[0]['url'] == 'http://example.com/news1'
        assert result[0]['publication_date'].year == 2023

    # Тест М8: Проверка обработки битого RSS
    @patch('feedparser.parse')
    def test_fetch_rss_failure(self, mock_parse, scraper):
        """Негативный тест для fetch_rss с неработающим RSS"""
        mock_parse.return_value = {'bozo': 1, 'bozo_exception': Exception('Invalid RSS')}

        result = scraper.fetch_rss(
            url="http://invalid.rss",
            source_id="test_source",
            base_url="http://example.com"
        )

        assert result is None

    # Тест М9: Проверка очистки HTML для ptzgovorit.ru
    def test_clean_html_ptzgovorit(self, scraper):
        """Проверка удаления футера ptzgovorit.ru"""
        html_content = """
        <div class="field-name-body">
            <p>Основной текст новости</p>
            <div>Фото: Автор</div>
            <em>© «Петрозаводск говорит»</em>
        </div>
        """

        cleaned = scraper.clean_html(html_content, "https://ptzgovorit.ru/news")

        assert "Основной текст новости" in cleaned
        assert "© «Петрозаводск говорит»" not in cleaned
        assert "Фото: Автор" not in cleaned

    # Тест М10: Проверка обработки пустого контента
    def test_clean_html_empty(self, scraper):
        """Проверка обработки пустой строки"""
        result = scraper.clean_html("", "http://example.com")
        assert result == ""