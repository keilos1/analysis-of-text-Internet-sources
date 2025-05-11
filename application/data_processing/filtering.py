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

# Основы названий районов Петрозаводска (без окончаний) и их полные названия
PETROZAVODSK_DISTRICTS_INFO = [
    ("голиковк", "Голиковка"),
    ("древлянк", "Древлянка"),
    ("зарек", "Зарека"),
    ("ключев", "Ключевая"),
    ("кукковк", "Кукковка"),
    ("октябрьск", "Октябрьский"),
    ("первомайск", "Первомайский"),
    ("перевалк", "Перевалка"),
    ("песк", "Пески"),
    ("рыбк", "Рыбка"),
    ("центр", "Центр"),
    ("южн площадк", "Южная площадка")
]

# Основы названий улиц Петрозаводска и их полные названия
PETROZAVODSK_STREETS_INFO = [
    ("ленин", "Ленина"),
    ("киров", "Кирова"),
    ("антикайнен", "Антикайнена"),
    ("кузьмин", "Кузьмина"),
    ("андропов", "Андропова"),
    ("пушкинск", "Пушкинская"),
    ("маркс", "Маркса"),
    ("энгельс", "Энгельса"),
    ("дзержинск", "Дзержинского"),
    ("гогол", "Гоголя"),
    ("герцен", "Герцена"),
    ("онежск набережн", "Онежская набережная"),
    ("советск", "Советская"),
    ("красноармейск", "Красноармейская"),
    ("заводск", "Заводская"),
    ("ровио", "Ровио"),
    ("шуйск", "Шуйская"),
    ("чапаев", "Чапаева"),
    ("жуковск", "Жуковского")
]

# Основы фамилий мэров Петрозаводска и их полные имена
PETROZAVODSK_MAYORS_INFO = [
    ("катанандов", "Сергей Катанандов"),
    ("демин", "Андрей Демин"),
    ("масляков", "Виктор Масляков"),
    ("левин", "Николай Левин"),
    ("любарск", "Любарский"),
    ("константинович", "Владимир Константинович"),
    ("колыхматов", "Инна Колыхматова")
]

CATEGORY_KEYWORDS = {
    NewsCategory.CULTURE: ["культур", "музе", "театр"],
    NewsCategory.SPORT: ["спорт", "футбол", "хокке"],
    NewsCategory.TECHNOLOGY: ["технолог", "инновац", "it"],
    NewsCategory.HOLIDAYS: ["праздник", "день город", "фестивал"],
    NewsCategory.EDUCATION: ["образова", "школ", "университет"]
}

class NewsProcessor:
    def __init__(self):
        self.data_updater = DataUpdater()
        # Предкомпилированные регулярные выражения для быстрого поиска
        self.petrozavodsk_re = re.compile(r'\bпетрозаводск\b', re.IGNORECASE)
        self.districts_re = self._prepare_regex([base for base, _ in PETROZAVODSK_DISTRICTS_INFO])
        self.streets_re = self._prepare_regex([base for base, _ in PETROZAVODSK_STREETS_INFO])
        self.mayors_re = self._prepare_regex([base for base, _ in PETROZAVODSK_MAYORS_INFO])
        
    def _prepare_regex(self, bases: List[str]) -> re.Pattern:
        """Создает регулярное выражение для поиска основ слов"""
        pattern = r'\b(?:' + '|'.join(bases) + r')\w*'
        return re.compile(pattern, re.IGNORECASE)

    def is_petrozavodsk_related(self, text: str) -> bool:
        """
        Проверяет, относится ли новость к Петрозаводску:
        - упоминание города
        - упоминание районов
        - упоминание улиц
        - упоминание мэров
        """
        text_lower = text.lower()
        
        # Проверка на название города
        if self.petrozavodsk_re.search(text):
            return True
        
        # Проверка районов, улиц и мэров
        return (self.districts_re.search(text_lower) is not None or
                self.streets_re.search(text_lower) is not None or
                self.mayors_re.search(text_lower) is not None)

    async def process_news(self) -> List[Dict]:
        """
        Получает новости через fetch_news и обрабатывает их:
        - Оставляет только новости о Петрозаводске
        - Добавляет информацию о локации и категориях
        """
        raw_news = await self.data_updater.fetch_news()
        processed_news = []

        if not raw_news:
            print("Новостей нет")
            return processed_news

        petrozavodsk_news_count = 0

        for news_item in raw_news:
            text = news_item.get("text", "")
            
            if not self.is_petrozavodsk_related(text):
                continue

            petrozavodsk_news_count += 1
            text_lower = text.lower()

            # Определение категорий
            detected_categories = []
            for category, keywords in CATEGORY_KEYWORDS.items():
                if any(re.search(rf'\b{kw}\w*', text_lower) for kw in keywords):
                    detected_categories.append(category.value)

            # Определение локации
            location = {"city": "Петрозаводск"}
            
            # Поиск района
            district_match = self.districts_re.search(text_lower)
            if district_match:
                matched_base = district_match.group().lower()
                for base, full in PETROZAVODSK_DISTRICTS_INFO:
                    if base in matched_base:
                        location["district"] = full
                        break
            
            # Поиск улицы
            street_match = self.streets_re.search(text_lower)
            if street_match:
                matched_base = street_match.group().lower()
                for base, full in PETROZAVODSK_STREETS_INFO:
                    if base in matched_base:
                        location["street"] = full
                        break
            
            # Поиск мэров
            mentioned_mayors = []
            for match in self.mayors_re.finditer(text_lower):
                matched_base = match.group().lower()
                for base, full in PETROZAVODSK_MAYORS_INFO:
                    if base in matched_base:
                        mentioned_mayors.append(full)
            if mentioned_mayors:
                location["mayors"] = list(set(mentioned_mayors))  # Убираем дубли

            # Вывод в консоль
            print("Title:", news_item.get("title", ""))
            print("Text:", text)
            print("Categories:", detected_categories or ["Другое"])
            print("Location:", location)
            print("-" * 50)

            processed_news.append({
                **news_item,
                "location": location,
                "categories": detected_categories or ["Другое"]
            })

        if petrozavodsk_news_count == 0:
            print("Новостей о Петрозаводске нет")

        return processed_news

if __name__ == "__main__":
    async def main():
        processor = NewsProcessor()
        await processor.process_news()
    
    asyncio.run(main())
