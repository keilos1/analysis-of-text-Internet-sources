import pytest
from datetime import datetime
from application.data_collection.googleSearch import GoogleNewsCollector
from unittest.mock import MagicMock, patch


class TestGoogleNewsCollector:
    @pytest.fixture
    def collector(self):
        return GoogleNewsCollector(api_key="test_key", cx="test_cx")

    # Тест М1 и М2 - generate_article_id()
    def test_generate_article_id_positive(self, collector):
        """Проверка генерации ID для валидного URL"""
        url = "https://example.com/news/1"
        result = collector.generate_article_id(url)
        assert len(result) == 32
        assert result == "8d9b5e7e0f3e3e3e3e3e3e3e3e3e3e3"

    def test_generate_article_id_empty(self, collector):
        """Проверка обработки пустого URL"""
        result = collector.generate_article_id("")
        assert len(result) == 32

    # Тест М3 и М4 - fetch_full_text_and_date()
    @patch('newspaper.Article')
    def test_fetch_full_text_valid_url(self, mock_article, collector):
        """Проверка извлечения данных с рабочей страницы"""
        # Настройка мока
        mock_article.return_value.download.return_value = None
        mock_article.return_value.parse.return_value = None
        mock_article.return_value.text = "Пример текста статьи"
        mock_article.return_value.publish_date = datetime(2025, 5, 1)

        text, date = collector.fetch_full_text_and_date("http://valid.url")
        assert text == "Пример текста статьи"
        assert date == datetime(2025, 5, 1)

    @patch('newspaper.Article', side_effect=Exception("Error"))
    def test_fetch_full_text_invalid_url(self, mock_article, collector):
        """Проверка обработки битой страницы"""
        text, date = collector.fetch_full_text_and_date("http://invalid.url")
        assert text == ""
        assert isinstance(date, datetime)

    # Тест М5 и М6 - search_news()
    @patch('http.client.HTTPSConnection')
    def test_search_news_success(self, mock_conn, collector):
        """Проверка успешного поиска новостей"""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps({
            'items': [{'link': 'url1', 'title': 'title1'}] * 5
        }).encode('utf-8')

        mock_conn.return_value.getresponse.return_value = mock_response

        results = collector.search_news("новости Петрозаводска", num=5)
        assert len(results) == 5
        assert all('title' in item for item in results)

    @patch('http.client.HTTPSConnection')
    def test_search_news_rate_limit(self, mock_conn, collector):
        """Проверка обработки превышения лимита запросов"""
        mock_response = MagicMock()
        mock_response.status = 429
        mock_conn.return_value.getresponse.return_value = mock_response

        results = collector.search_news("запрос")
        assert results == []