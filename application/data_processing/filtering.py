# Фильтрация данных по тематике и местоположению
import re
from typing import List, Dict, Optional
from enum import Enum
import asyncio
import sys

sys.path.append("../")
from data_collection.sheduler import DataUpdater


class NewsCategory(Enum):
    CULTURE = "Культура"
    SPORT = "Спорт"
    TECHNOLOGY = "Технологии"
    HOLIDAYS = "Праздники"
    EDUCATION = "Образование"
    OTHER = "Другое"  # Добавлена новая категория


# Только районы Петрозаводска
PETROZAVODSK_DISTRICTS = [
    "Голиковка", "Древлянка", "Зарека",
    "Ключевая", "Кукковка", "Октябрьский",
    "Первомайский", "Перевалка", "Пески",
    "Рыбка", "Центр", "Южная площадка"
]

CATEGORY_KEYWORDS = {
    NewsCategory.CULTURE: ["культур", "музей", "театр"],
    NewsCategory.SPORT: ["спорт", "футбол", "хоккей"],
    NewsCategory.TECHNOLOGY: ["технолог", "инновац", "IT"],
    NewsCategory.HOLIDAYS: ["праздник", "день города", "фестиваль"],
    NewsCategory.EDUCATION: ["образован", "школ", "университет"]
}


class NewsProcessor:
    def __init__(self):
        self.data_updater = DataUpdater()
        # Регулярное выражение для поиска всех форм слова "Петрозаводск"
        self.petrozavodsk_pattern = re.compile(
            r'\bПетрозаводск(?:а|у|ом|е|ий|ого|ому|им|ом)?\b',
            re.IGNORECASE
        )

    async def process_news(self) -> List[Dict]:
        """
        Получает новости через fetch_news и обрабатывает их:
        - Оставляет только новости о Петрозаводске (с учетом разных форм слова)
        - Добавляет информацию о локации и категориях
        """
        raw_news = await self.data_updater.fetch_news()
        processed_news = []

        # Проверка на отсутствие новостей
        if not raw_news:
            print("Новостей нет")
            return processed_news

        petrozavodsk_news_count = 0

        for news_item in raw_news:
            text = news_item.get("text", "")
            text_lower = text.lower()

            # Проверка на принадлежность к Петрозаводску (все формы слова)
            if not self.petrozavodsk_pattern.search(text):
                continue

            petrozavodsk_news_count += 1

            # Определение категорий
            detected_categories = []
            for category, keywords in CATEGORY_KEYWORDS.items():
                if any(keyword in text_lower for keyword in keywords):
                    detected_categories.append(category.value)

            # Если категории не найдены, добавляем "Другое"
            if not detected_categories:
                detected_categories.append(NewsCategory.OTHER.value)

            # Определение района
            location = {"city": "Петрозаводск"}
            for district in PETROZAVODSK_DISTRICTS:
                if re.search(rf'\b{re.escape(district)}\b', text, re.IGNORECASE):
                    location["district"] = district
                    break

            # Вывод в консоль
            print("Title:", news_item.get("title", ""))
            print("Text:", text)
            print("Categories:", detected_categories)
            print("District:", location.get("district", "Не указан"))
            print("-" * 50)

            processed_news.append({
                **news_item,
                "location": location,
                "categories": detected_categories
            })

        # Проверка, что после фильтрации остались новости
        if petrozavodsk_news_count == 0:
            print("Новостей о Петрозаводске нет")

        return processed_news


if __name__ == "__main__":
    async def main():
        processor = NewsProcessor()
        await processor.process_news()


    asyncio.run(main())