import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from application.data_collection.socialScraper import SocialScraper
import re


class TestSocialScraper:
    @pytest.fixture
    def scraper(self):
        return SocialScraper()

    @pytest.fixture
    def telegram_html(self):
        return """
        <div class="tgme_widget_message">
            <div class="tgme_widget_message_text">Тестовый пост в Telegram 🚀</div>
            <time datetime="2023-01-01T12:00:00+00:00"></time>
            <a class="tgme_widget_message_date" href="https://t.me/channel/123"></a>
        </div>
        """

    # Тест М15: Проверка сбора данных из Telegram
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_collect_social_data_success(self, mock_get, scraper, telegram_html):
        """Позитивный тест сбора данных из Telegram"""
        # Настройка моков
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = telegram_html
        mock_get.return_value = mock_response

        sources = [{
            "source_id": "tg_test",
            "url": "https://t.me/test_channel",
            "name": "Test Channel"
        }]

        result = await scraper.collect_social_data(sources)

        assert "tg_test" in result
        assert len(result["tg_test"]) == 1
        assert result["tg_test"][0]["title"] == "Тестовый пост в Telegram"

    # Тест М16: Проверка несуществующего канала
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_collect_social_data_invalid_channel(self, mock_get, scraper):
        """Негативный тест для несуществующего канала"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        sources = [{
            "source_id": "tg_invalid",
            "url": "https://t.me/nonexistent",
            "name": "Nonexistent"
        }]

        result = await scraper.collect_social_data(sources)
        assert result == {}

    # Тест М17: Проверка парсинга поста Telegram
    @pytest.mark.asyncio
    async def test_parse_telegram_success(self, scraper, telegram_html):
        """Позитивный тест парсинга HTML Telegram"""
        mock_client = AsyncMock()
        mock_source = {
            "source_id": "tg_test",
            "url": "https://t.me/test_channel"
        }

        with patch('bs4.BeautifulSoup', return_value=BeautifulSoup(telegram_html, 'html.parser')):
            posts = await scraper._parse_telegram(mock_client, mock_source)

            assert len(posts) == 1
            post = posts[0]
            assert post["title"] == "Тестовый пост в Telegram"
            assert "🚀" not in post["text"]  # Эмодзи должны быть удалены
            assert post["published_at"] == datetime(2025, 5, 1, 12, 0)

    # Тест М18: Проверка битого HTML
    @pytest.mark.asyncio
    async def test_parse_telegram_invalid_html(self, scraper):
        """Негативный тест для битого HTML"""
        mock_client = AsyncMock()
        mock_source = {
            "source_id": "tg_test",
            "url": "https://t.me/test_channel"
        }

        posts = await scraper._parse_telegram(mock_client, mock_source)
        assert posts == []

    # Тест М19: Проверка удаления эмодзи
    def test_remove_emojis(self, scraper):
        """Позитивный тест удаления эмодзи"""
        text = "Привет 🚀 как дела? 😊"
        result = scraper._remove_emojis(text)
        assert "🚀" not in result
        assert "😊" not in result
        assert "Привет как дела?" in result

    # Тест М20: Проверка текста без эмодзи
    def test_remove_emojis_no_emojis(self, scraper):
        """Позитивный тест для текста без эмодзи"""
        text = "Обычный текст без эмодзи"
        result = scraper._remove_emojis(text)
        assert result == text

    # Дополнительный тест для проверки пересланных сообщений
    def test_is_forwarded_message(self, scraper):
        """Проверка определения пересланных сообщений"""
        html = """
        <div class="tgme_widget_message">
            <div class="tgme_widget_message_forwarded_from"></div>
            <div class="tgme_widget_message_text"></div>
        </div>
        """
        soup = BeautifulSoup(html, 'html.parser')
        assert scraper._is_forwarded_message(soup) is True

    # Дополнительный тест для проверки очистки футера
    def test_clean_footer_text(self, scraper):
        """Проверка удаления футера"""
        text = "Текст сообщения\nФактор Новости | Подписаться"
        result = scraper._clean_footer_text(text)
        assert "Фактор Новости" not in result
        assert "Текст сообщения" in result