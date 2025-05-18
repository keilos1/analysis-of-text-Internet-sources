import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from application.search_navigation.search import NewsSearch, app
from pymongo import MongoClient


class TestNewsSearch:
    @pytest.fixture
    def mock_collection(self):
        """Фикстура для мокирования коллекции articles"""
        collection = MagicMock()
        collection.index_information.return_value = {}
        return collection

    @pytest.fixture
    def news_search(self, mock_collection):
        """Фикстура для тестирования NewsSearch"""
        return NewsSearch(articles_collection=mock_collection)

    @pytest.fixture
    def test_client(self):
        """Фикстура для тестирования FastAPI endpoint"""
        return TestClient(app)

    # Тест М53: Создание текстового индекса
    def test_create_text_index(self, news_search, mock_collection):
        """Проверяет создание текстового индекса с правильными весами"""
        news_search._create_text_index()

        mock_collection.create_index.assert_called_once()
        args, kwargs = mock_collection.create_index.call_args

        # Проверяем поля и веса индекса
        assert args[0] == [("title", "text"), ("text", "text"), ("summary", "text")]
        assert kwargs["weights"] == {"title": 3, "text": 2, "summary": 1}
        assert kwargs["default_language"] == "russian"

    # Тест М54: Поиск по ключевому слову
    def test_search_news_by_keyword(self, news_search, mock_collection):
        """Проверяет поиск по ключевому слову"""
        mock_results = [
            {"title": "Фестиваль в Петрозаводске", "score": 1.5},
            {"title": "Музыкальный фестиваль", "score": 1.2}
        ]
        mock_collection.find.return_value.sort.return_value.limit.return_value = mock_results

        results = news_search.search_news("фестиваль")

        assert len(results) == 2
        assert "фестиваль" in results[0]["title"].lower()
        mock_collection.find.assert_called_once_with({
            "$text": {
                "$search": "фестиваль",
                "$language": "russian"
            }
        })

    # Тест М55: Сортировка по релевантности
    def test_search_results_sorted(self, news_search, mock_collection):
        """Проверяет сортировку результатов по score"""
        mock_results = [
            {"title": "Высокий рейтинг", "score": 2.5},
            {"title": "Средний рейтинг", "score": 1.8},
            {"title": "Низкий рейтинг", "score": 0.5}
        ]
        mock_collection.find.return_value.sort.return_value.limit.return_value = mock_results

        results = news_search.search_news("рейтинг")

        assert results[0]["score"] > results[1]["score"] > results[2]["score"]

    # Тест М56: Ограничение количества результатов
    def test_search_limit_results(self, news_search, mock_collection):
        """Проверяет ограничение количества результатов"""
        mock_collection.find.return_value.sort.return_value.limit.return_value = [{}] * 5

        results = news_search.search_news("Петрозаводск", limit=5)

        assert len(results) == 5
        mock_collection.find.return_value.sort.return_value.limit.assert_called_once_with(5)


class TestSearchAPI:
    # Тест М57: Обработка пустого запроса
    def test_empty_query(self, test_client):
        """Проверяет обработку пустого запроса"""
        response = test_client.get("/api/search?query=")
        assert response.status_code == 200
        assert response.json() == []

    # Тест М58: Формат JSON-ответа
    @patch("application.search_navigation.search.NewsSearch.search_news")
    def test_search_api_response_format(self, mock_search, test_client):
        """Проверяет формат JSON-ответа"""
        mock_search.return_value = [
            {
                "title": "Новости Петрозаводска",
                "url": "http://example.com/news1",
                "score": 1.5,
                "publication_date": "2023-05-20T00:00:00",
                "summary": "Краткое описание",
                "source": "example.com"
            }
        ]

        response = test_client.get("/api/search?query=Петрозаводск")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert all(field in data[0] for field in ["title", "url", "score"])
        assert data[0]["title"] == "Новости Петрозаводска"
