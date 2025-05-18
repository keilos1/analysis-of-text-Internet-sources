import pytest
from unittest.mock import MagicMock, patch
from application.data_collection.sheduler import DataUpdater
from datetime import datetime


class TestSheduler:
    @pytest.fixture
    def updater(self):
        return DataUpdater()

    # Тест М11: Проверка загрузки источников из БД
    @patch('application.data_collection.sheduler.DataUpdater._get_sources_from_db')
    def test_get_sources_from_db_success(self, mock_get_sources, updater):
        """Позитивный тест загрузки источников"""
        mock_get_sources.return_value = [
            {
                "_id": "1",
                "source_id": "source1",
                "name": "Тестовый источник",
                "url": "http://test.rss",
                "category": "Новости",
                "last_checked_time": datetime(2025, 5, 1)
            }
        ]

        sources = updater._get_sources_from_db()
        assert len(sources) == 1
        assert sources[0]['source_id'] == "source1"
        assert isinstance(sources[0]['last_checked_time'], datetime)

    # Тест М12: Проверка ошибки подключения
    @patch('application.data_collection.sheduler.DataUpdater._get_sources_from_db')
    def test_get_sources_from_db_failure(self, mock_get_sources, updater):
        """Негативный тест при ошибке подключения"""
        mock_get_sources.return_value = []
        sources = updater._get_sources_from_db()
        assert sources == []

    # Тест М13: Проверка сбора новостей
    @patch('application.data_collection.sheduler.DataUpdater._process_social_source')
    @patch('application.data_collection.scraper.Scraper.fetch_rss')
    @patch('application.data_collection.googleSearch.collect_news')
    def test_fetch_news_success(self, mock_google, mock_rss, mock_social, updater):
        """Позитивный тест сбора новостей"""
        mock_social.return_value = [{
            "source_id": "vk1",
            "title": "Пост ВК",
            "text": "Текст поста",
            "source_type": "vk"
        }]

        mock_rss.return_value = [{
            "source_id": "rss1",
            "title": "RSS новость",
            "text": "Текст новости"
        }]

        mock_google.return_value = [{
            "source_id": "google",
            "title": "Google новость",
            "text": "Текст из Google"
        }]

        updater.sources = [
            {"source_id": "vk1", "url": "https://vk.com", "type": "social"},
            {"source_id": "rss1", "url": "http://test.rss", "type": "rss"},
            {"source_id": "google", "url": "", "type": "google"}
        ]

        news = updater.fetch_news()
        assert len(news) == 3
        assert any(item['source_id'] == 'vk1' for item in news)
        assert any(item['source_id'] == 'rss1' for item in news)
        assert any(item['source_id'] == 'google' for item in news)

    # Тест М14: Проверка отсутствия источников
    def test_fetch_news_no_sources(self, updater):
        """Негативный тест без источников"""
        updater.sources = []
        news = updater.fetch_news()
        assert news == []