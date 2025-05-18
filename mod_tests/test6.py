import pytest
from unittest.mock import patch, AsyncMock
from application.data_processing.filtering import NewsProcessor, NewsCategory
import re


class TestNewsFiltering:
    @pytest.fixture
    def processor(self):
        return NewsProcessor()

    # Тест М25: Фильтрация по Петрозаводску
    @pytest.mark.asyncio
    @patch('application.data_collection.sheduler.DataUpdater.fetch_news')
    async def test_filter_petrozavodsk_positive(self, mock_fetch, processor):
        """Проверяет фильтрацию новостей о Петрозаводске"""
        mock_fetch.return_value = [
            {
                "title": "Новость 1",
                "text": "В Петрозаводске открыли новый парк. Мэр города посетил мероприятие.",
                "url": "http://example.com/1"
            },
            {
                "title": "Новость 2",
                "text": "В Москве построили новый стадион",
                "url": "http://example.com/2"
            }
        ]

        result = await processor.process_news()

        assert len(result) == 1
        assert result[0]['title'] == "Новость 1"
        assert "Петрозаводск" in result[0]['text']
        assert result[0]['location']['city'] == "Петрозаводск"

    # Тест М26: Исключение других городов
    @pytest.mark.asyncio
    @patch('application.data_collection.sheduler.DataUpdater.fetch_news')
    async def test_filter_petrozavodsk_negative(self, mock_fetch, processor):
        """Проверяет исключение новостей не о Петрозаводске"""
        mock_fetch.return_value = [
            {
                "title": "Новость из Кондопоги",
                "text": "В Кондопоге прошёл фестиваль.",
                "url": "http://example.com/3"
            }
        ]

        result = await processor.process_news()
        assert len(result) == 0

    # Тест М27: Классификация категорий
    @pytest.mark.asyncio
    @patch('application.data_collection.sheduler.DataUpdater.fetch_news')
    async def test_category_detection(self, mock_fetch, processor):
        """Проверяет автоматическую классификацию"""
        test_cases = [
            {
                "input": {
                    "title": "Спортивная новость",
                    "text": "В Петрозаводске прошёл футбольный матч",
                    "url": "http://example.com/4"
                },
                "expected": ["Спорт"]
            },
            {
                "input": {
                    "title": "Культурное событие",
                    "text": "В музее Петрозаводска новая выставка",
                    "url": "http://example.com/5"
                },
                "expected": ["Культура"]
            }
        ]

        for case in test_cases:
            mock_fetch.return_value = [case["input"]]
            result = await processor.process_news()
            assert result[0]['categories'] == case["expected"]

    # Тест М28: Категория по умолчанию
    @pytest.mark.asyncio
    @patch('application.data_collection.sheduler.DataUpdater.fetch_news')
    async def test_default_category(self, mock_fetch, processor):
        """Проверяет назначение 'Другое' для новостей без категорий"""
        mock_fetch.return_value = [
            {
                "title": "Погода",
                "text": "В Петрозаводске сегодня солнечно",
                "url": "http://example.com/6"
            }
        ]

        result = await processor.process_news()
        assert result[0]['categories'] == ["Другое"]
