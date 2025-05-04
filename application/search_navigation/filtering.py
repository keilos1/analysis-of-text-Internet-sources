# фильтрация данных по категориям и местоположению
# search_navigation/filter.py
import re
import sys
from pathlib import Path
from typing import List, Dict
from enum import Enum

# Добавляем корень проекта в PYTHONPATH для корректных импортов
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# Теперь можно импортировать модули
try:
    from data_collection.sheduler import NewsScheduler
    from search_navigation.search import NewsSearcher
except ImportError as e:
    print(f"Import error: {e}")


    # Создаем заглушки для классов, если модули не найдены
    class NewsScheduler:
        def collect_news(self):
            print("NewsScheduler not implemented - using stub")
            return []


    class NewsSearcher:
        def find_news(self, location_query=None, categories=None):
            print("NewsSearcher not implemented - using stub")
            return []

class NewsCategory(Enum):
    CULTURE = "Культура"
    SPORT = "Спорт"
    TECHNOLOGY = "Технологии"
    HOLIDAYS = "Праздники"
    EDUCATION = "Образование"

LOCATION_HIERARCHY = {
    "Республика Карелия": {
        "Районы": {
            "Беломорский район": ["Беломорск", "Сумский Посад", "Вирандозеро"],
            "Калевальский район": ["Калевала", "Юшкозеро", "Боровой"],
            "Кемский район": ["Кемь", "Рабочеостровск", "Кривой Порог"],
            "Кондопожский район": ["Кондопога", "Гирвас", "Янишполе"],
            "Лахденпохский район": ["Лахденпохья", "Хийтола", "Ихала"],
            "Лоухский район": ["Лоухи", "Чупа", "Пяозерский"],
            "Медвежьегорский район": ["Медвежьегорск", "Повенец", "Пиндуши"],
            "Муезерский район": ["Муезерский", "Ругозеро", "Лендеры"],
            "Олонецкий район": ["Олонец", "Ильинский", "Коткозеро"],
            "Питкярантский район": ["Питкяранта", "Салми", "Ляскеля"],
            "Прионежский район": ["Шуя", "Деревянка", "Мелиоративный"],
            "Пряжинский район": ["Пряжа", "Эссойла", "Колатсельга"],
            "Пудожский район": ["Пудож", "Шальский", "Кривцы"],
            "Сегежский район": ["Сегежа", "Надвоицы", "Валдай"],
            "Сортавальский район": ["Сортавала", "Рускеала", "Хелюля"],
            "Суоярвский район": ["Суоярви", "Поросозеро", "Лоймола"]
        },
        "Города республиканского значения": {
            "Петрозаводск": {
                "Районы Петрозаводска": [
                    "Голиковка", "Древлянка", "Зарека",
                    "Ключевая", "Кукковка", "Октябрьский",
                    "Первомайский", "Перевалка", "Пески",
                    "Рыбка", "Центр", "Южная площадка"
                ]
            },
            "Костомукша": ["Горняк", "Заречный", "Михайловский"]
        }
    }
}

CATEGORY_KEYWORDS = {
    NewsCategory.CULTURE: ["культур", "музей", "театр"],
    NewsCategory.SPORT: ["спорт", "футбол", "хоккей"],
    NewsCategory.TECHNOLOGY: ["технолог", "инновац", "IT"],
    NewsCategory.HOLIDAYS: ["праздник", "день города", "фестивал"],
    NewsCategory.EDUCATION: ["образован", "школ", "университет"]
}


class NewsProcessor:
    def __init__(self):
        self.scheduler = NewsScheduler()
        self.searcher = NewsSearcher()

    def detect_category(self, text: str) -> List[str]:
        detected_categories = []
        text_lower = text.lower()

        for category, keywords in CATEGORY_KEYWORDS.items():
            if any(keyword in text_lower for keyword in keywords):
                detected_categories.append(category.value)

        return detected_categories or ["Другое"]

    def extract_locations(self, text: str) -> List[Dict[str, str]]:
        found_locations = []

        if re.search(r'Карел(ии|ия|ьский)', text, re.IGNORECASE):
            found_locations.append({"republic": "Республика Карелия"})

        for city, districts in LOCATION_HIERARCHY["Республика Карелия"]["Города республиканского значения"].items():
            if re.search(rf'\b{re.escape(city)}\b', text, re.IGNORECASE):
                loc = {"republic": "Республика Карелия", "city": city}

                if isinstance(districts, dict):
                    for district in districts["Районы Петрозаводска"]:
                        if re.search(rf'\b{re.escape(district)}\b', text, re.IGNORECASE):
                            loc["district"] = district
                            break
                elif isinstance(districts, list):
                    for district in districts:
                        if re.search(rf'\b{re.escape(district)}\b', text, re.IGNORECASE):
                            loc["district"] = district
                            break
