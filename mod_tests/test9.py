import pytest
from unittest.mock import MagicMock, patch
from application.search_navigation.filtering import NewsProcessor, NewsCategory, PETROZAVODSK_DISTRICTS


class TestNewsProcessor:
    @pytest.fixture
    def processor(self):
        return NewsProcessor()

    def setup_method(self, method):
        """Мокируем DataUpdater перед каждым тестом"""
        self.mock_updater = MagicMock()
        NewsProcessor.data_updater = self.mock_updater

    # Тест М47: Фильтрация новостей по Петрозаводску (позитивный)
    def test_filter_petrozavodsk_news(self, processor):
        """Проверяет включение новости о Петрозаводске"""
        self.mock_updater.fetch_news.return_value = [
            {"text": "В Петрозаводске состоялся фестиваль", "title": "Фестиваль"}
        ]

        result = processor.process_news()

        assert len(result) == 1
        assert "Петрозаводск" in result[0]["location"]["city"]

    # Тест М48: Отсеивание новостей не о Петрозаводске (позитивный)
    def test_filter_non_petrozavodsk_news(self, processor):
        """Проверяет исключение новости не о Петрозаводске"""
        self.mock_updater.fetch_news.return_value = [
            {"text": "В Москве открыли новый парк", "title": "Парк в Москве"}
        ]

        result = processor.process_news()

        assert len(result) == 0

    # Тест М49: Определение категории "Культура" (позитивный)
    def test_detect_culture_category(self, processor):
        """Проверяет определение категории 'Культура'"""
        self.mock_updater.fetch_news.return_value = [
            {"text": "В музее Петрозаводска новая выставка", "title": "Выставка"}
        ]

        result = processor.process_news()

        assert len(result) == 1
        assert NewsCategory.CULTURE.value in result[0]["categories"]

    # Тест М50: Определение района "Центр" (позитивный)
    def test_detect_center_district(self, processor):
        """Проверяет определение района 'Центр'"""
        self.mock_updater.fetch_news.return_value = [
            {"text": "В центре Петрозаводска пробки", "title": "Пробки"}
        ]

        result = processor.process_news()

        assert len(result) == 1
        assert result[0]["location"]["district"] == "Центр"

    # Тест М51: Обработка новости без категорий (позитивный)
    def test_news_without_categories(self, processor):
        """Проверяет обработку новости без категорий"""
        self.mock_updater.fetch_news.return_value = [
            {"text": "Петрозаводск сегодня", "title": "Новости"}
        ]

        result = processor.process_news()

        assert len(result) == 1
        assert result[0]["categories"] == ["Другое"]

    # Тест М52: Обработка пустого текста (позитивный)
    def test_empty_text_news(self, processor):
        """Проверяет обработку новости с пустым текстом"""
        self.mock_updater.fetch_news.return_value = [
            {"text": "", "title": "Пустая новость"}
        ]

        result = processor.process_news()

        assert len(result) == 0
