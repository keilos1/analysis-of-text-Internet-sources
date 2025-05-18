import pytest
from unittest.mock import patch, AsyncMock
from application.data_processing.text_summarization import (
    clean_html,
    summarize_texts_tfidf,
    print_news_with_summary
)
import re


class TestTextSummarization:
    # Тест М29: Суммаризация длинного текста
    @pytest.mark.asyncio
    async def test_summarize_long_text(self):
        """Проверяет сокращение длинного текста до 2 ключевых предложений"""

        input_text = (
            "В Петрозаводске состоялось открытие нового парка. "
            "Мэр города лично перерезал ленточку. "
            "Парк расположен в центре города и занимает 5 гектаров. "
            "На территории высажено более 100 деревьев. "
            "Жители уже оценили новое место для отдыха."
        )

        expected_summary_patterns = [
            "открытие нового парка",
            "высажено более 100 деревьев|оценили новое место"
        ]

        result = await summarize_texts_tfidf([{"text": input_text}])
        summary = result[0]["summary"]

        assert len(summary.split('. ')) <= 2
        for pattern in expected_summary_patterns:
            assert re.search(pattern, summary)

    # Тест М30: Обработка короткого текста
    @pytest.mark.asyncio
    async def test_summarize_short_text(self):
        """Проверяет обработку текста из 1-2 предложений"""
        # Входные данные
        input_text = "В Петрозаводске солнечно. Температура +25°C."

        result = await summarize_texts_tfidf([{"text": input_text}])

        assert result[0]["summary"] == input_text
        assert result[0]["text"] == input_text

    # Тест М31: Очистка HTML
    def test_clean_html(self):
        """Проверяет удаление HTML-тегов"""
        # Входные данные
        html_text = (
            '<div class="article"><p>Основной <b>текст</b> новости</p>'
            '<a href="#">Ссылка</a><script>alert();</script></div>'
        )

        expected = "Основной текст новостиСсылка"

        assert clean_html(html_text) == expected

    # Тест М32: Текст без HTML
    def test_clean_html_no_tags(self):
        """Проверяет обработку текста без HTML"""
        plain_text = "Обычный текст без тегов"

        assert clean_html(plain_text) == plain_text

    # Тест М33: Вывод новостей
    @patch('builtins.print')
    def test_print_news_with_summary(self, mock_print):
        """Проверяет форматированный вывод новостей"""
        news_data = [
            {
                "title": "Открытие парка",
                "location": {"district": "Центр"},
                "categories": ["Культура"],
                "text": "Полный текст о парке...",
                "summary": "Открыт новый парк в центре"
            }
        ]

        print_news_with_summary(news_data)

        assert mock_print.call_count >= 5
        output = ''.join([str(call) for call in mock_print.call_args_list])
        assert "Открытие парка" in output
        assert "Центр" in output
        assert "Культура" in output
        assert "Открыт новый парк" in output

    # Тест М34: Пустой список новостей
    @patch('builtins.print')
    def test_print_empty_news(self, mock_print):
        """Проверяет обработку пустого списка новостей"""
        print_news_with_summary([])
        mock_print.assert_called_with("Новостей для отображения нет")

    @pytest.mark.asyncio
    async def test_preserve_original_text(self):
        """Проверяет что оригинальный текст не изменяется"""
        input_text = "<p>Текст <b>с</b> тегами</p>"
        result = await summarize_texts_tfidf([{"text": input_text}])
        assert result[0]["text"] == input_text
        assert "<p>" not in result[0]["summary"] 