# Фильтрация данных по тематике и местоположению
import re
from typing import List, Dict, Optional
from enum import Enum
import sys
sys.path.append("../")
from data_collection.sheduler import DataUpdater

class NewsCategory(Enum):
    CULTURE = "Культура"
    SPORT = "Спорт"
    TECHNOLOGY = "Технологии"
    HOLIDAYS = "Праздники"
    EDUCATION = "Образование"


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
    NewsCategory.HOLIDAYS: ["праздник", "день города", "фестивал"],
    NewsCategory.EDUCATION: ["образован", "школ", "университет"]
]

class NewsProcessor:
    def __init__(self):
        self.data_updater = DataUpdater()  # Создаем экземпляр DataUpdater

    def process_news(self) -> List[Dict]:
        """
        Получает новости через fetch_news и обрабатывает их:
        - Оставляет только новости о Петрозаводске
        - Добавляет информацию о локации и категориях
        """
        # Получаем сырые новости из источников
        raw_news = self.data_updater.fetch_news()  # Вызываем метод экземпляра
        processed_news = []

        for news_item in raw_news:
            text = news_item.get("text", "")
            title = news_item.get("title", "")
            text_lower = text.lower()

            # Проверка на принадлежность к Петрозаводску
            if not re.search(r'\bПетрозаводск\b', text, re.IGNORECASE):
                continue

            # Определение категорий
            detected_categories = []
            for category, keywords in CATEGORY_KEYWORDS.items():
                if any(keyword in text_lower for keyword in keywords):
                    detected_categories.append(category.value)

            # Определение района
            district = None
            for d in PETROZAVODSK_DISTRICTS:
                if re.search(rf'\b{re.escape(d)}\b', text, re.IGNORECASE):
                    district = d
                    break

            # Выводим информацию в консоль
            print("Title:", title)
            print("Text:", text)
            print("Categories:", detected_categories or ["Другое"])
            print("District:", district or "Не указан")
            print("-" * 50)  # Разделитель между новостями

            # Добавляем обработанную новость
            processed_news.append({
                **news_item,
                "location": {"city": "Петрозаводск", "district": district},
                "categories": detected_categories or ["Другое"]
            })

        return processed_news
