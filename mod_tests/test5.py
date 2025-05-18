import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from application.data_processing.duplicate_detection import save_unique_articles, async_main
import numpy as np


class TestDuplicateDetection:
    # Тест М21: Сохранение уникальных статей
    @patch('application.data_processing.duplicate_detection.connect_to_mongo')
    @patch('application.data_processing.duplicate_detection.summarize_texts_tfidf')
    async def test_save_unique_articles_new(self, mock_summarize, mock_connect):
        """Проверка сохранения новых уникальных статей"""
        # Настройка моков
        mock_db = MagicMock()
        mock_db.articles.find.return_value = []
        mock_db.articles.find_one.return_value = None
        mock_connect.return_value = (mock_db, None)

        mock_summarize.return_value = [
            {
                "title": "Новость 1",
                "summary": "Краткое содержание 1",
                "url": "http://example.com/1",
                "text": "Полный текст 1"
            },
            {
                "title": "Новость 2",
                "summary": "Краткое содержание 2",
                "url": "http://example.com/2",
                "text": "Полный текст 2"
            }
        ]

        result = await save_unique_articles(
            [{}, {}])

        assert result == 2
        assert mock_db.articles.insert_one.call_count == 2

    # Тест М22: Отсеивание дубликатов
    @patch('application.data_processing.duplicate_detection.connect_to_mongo')
    @patch('application.data_processing.duplicate_detection.summarize_texts_tfidf')
    @patch('sklearn.feature_extraction.text.TfidfVectorizer')
    @patch('sklearn.metrics.pairwise.cosine_similarity')
    async def test_save_unique_articles_duplicates(self, mock_cosine, mock_vectorizer, mock_summarize, mock_connect):
        """Проверка отсеивания дубликатов"""
        mock_db = MagicMock()
        mock_db.articles.find.return_value = [
            {"title": "Существующая", "summary": "Аналогичное содержание"}
        ]
        mock_connect.return_value = (mock_db, None)

        mock_summarize.return_value = [
            {
                "title": "Новая",
                "summary": "Аналогичное содержание",
                "url": "http://example.com/new",
                "text": "Полный текст"
            }
        ]

        mock_cosine.return_value = np.array([[0.96]])

        result = await save_unique_articles([{}])

        assert result == 0
        mock_db.articles.insert_one.assert_not_called()

    # Тест М23: Обработка пустого списка
    async def test_save_unique_articles_empty(self):
        """Проверка обработки пустого списка статей"""
        result = await save_unique_articles([])
        assert result == 0

    # Тест М24: Обработка ошибок подключения
    @patch('application.data_processing.duplicate_detection.connect_to_mongo')
    async def test_save_unique_articles_connection_error(self, mock_connect):
        """Проверка обработки ошибок подключения"""
        mock_connect.side_effect = Exception("Connection failed")

        result = await save_unique_articles([{"title": "Тест"}])
        assert result == 0

    # Тест для async_main
    @patch('application.data_processing.duplicate_detection.save_unique_articles')
    @patch('application.data_processing.duplicate_detection.summarize_texts_tfidf')
    async def test_async_main_success(self, mock_summarize, mock_save):
        """Проверка успешного выполнения async_main"""
        mock_summarize.return_value = [{"title": "Тест"}]
        mock_save.return_value = 1

        await async_main()
        assert mock_save.called

    @patch('application.data_processing.duplicate_detection.summarize_texts_tfidf')
    async def test_async_main_empty(self, mock_summarize):
        """Проверка async_main с пустым списком статей"""
        mock_summarize.return_value = []

        await async_main()