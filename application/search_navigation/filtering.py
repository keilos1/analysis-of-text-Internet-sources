import re
from typing import List, Dict, Optional
from enum import Enum

from application.data_collection.sheduler import DataUpdater

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
    NewsCategory.CULTURE: [
        r'\bкультур[а-я]*\b', r'\bмузе[йя]\b', r'\bтеатр[а-я]*\b',
        r'\bвыставк[аи]\b', r'\bконцерт[а-я]*\b', r'\bгалере[яи]\b',
        r'\bарт\b', r'\bхудож[а-я]*\b', r'\bскульптур[а-я]*\b',
        r'\bоркестр[а-я]*\b', r'\bопер[а-я]*\b', r'\bбалет[а-я]*\b',
        r'\bкино\b', r'\bфестивал[яи]\b', r'\bлитератур[а-я]*\b'
    ],
    NewsCategory.SPORT: [
        r'\bспорт[а-я]*\b', r'\bфутбол\b', r'\bхокке[йя]\b',
        r'\bсоревновани[яй]\b', r'\bчемпионат[а-я]*\b', r'\bматч[а-я]*\b',
        r'\bтренер\b', r'\bспортсмен[а-я]*\b', r'\bстадион[а-я]*\b',
        r'\bбаскетбол[а-я]*\b', r'\bволейбол[а-я]*\b', r'\bплавани[ея]\b',
        r'\bлёгк[ая]\sатлетик[а-я]*\b', r'\bтурнир[а-я]*\b', r'\bолимпиад[а-я]*\b',
        r'\bфитнес\b', r'\bзарядк[аи]\b', r'\bтренировк[аи]\b'
    ],
    NewsCategory.TECHNOLOGY: [
        r'\bтехнолог[а-я]*\b', r'\bинноваци[яй]\b', r'\bIT\b',
        r'\bкомпьютер[а-я]*\b', r'\bпрограмм[а-я]*\b', r'\bинтернет[а-я]*\b',
        r'\bгаджет[а-я]*\b', r'\bробот[а-я]*\b', r'\bсмартфон[а-я]*\b',
        r'\bцифров[а-я]*\b', r'\bайти\b', r'\bкод[а-я]*\b',
        r'\bразработк[аи]\b', r'\bстартап[а-я]*\b', r'\bлаборатори[яи]\b',
        r'\bнаук[а-я]*\b', r'\bисследовани[яй]\b'
    ],
    NewsCategory.HOLIDAYS: [
        r'\bпраздник[а-я]*\b', r'\bдень\sгорода\b', r'\bфестивал[яи]\b',
        r'\bкарнавал[а-я]*\b', r'\bсалют[а-я]*\b', r'\bмероприяти[ея]\b',
        r'\bторжеств[а-я]*\b', r'\bюбилей\b', r'\bновый\sгод\b',
        r'\bрождеств[а-я]*\b', r'\bмаслениц[а-я]*\b', r'\bпасх[а-я]*\b',
        r'\bконцерт[а-я]*\b', r'\bшоу\b', r'\bгуляни[яй]\b',
        r'\bнародн[а-я]*\sпраздник\b'
    ],
    NewsCategory.EDUCATION: [
        r'\bобразовани[ея]\b', r'\bшкол[а-я]*\b', r'\bуниверситет[а-я]*\b',
        r'\bстудент[а-я]*\b', r'\bучител[яи]\b', r'\bученик[а-я]*\b',
        r'\bзаняти[яй]\b', r'\bурок[а-я]*\b', r'\bлекци[яи]\b',
        r'\bсесси[яи]\b', r'\bэкзамен[а-я]*\b', r'\bдиплом[а-я]*\b',
        r'\bдетск[а-я]*\sсад\b', r'\bвуз[а-я]*\b', r'\bколледж[а-я]*\b',
        r'\bакадеми[яи]\b', r'\bкурс[а-я]*\b', r'\bрепетитор[а-я]*\b',
        r'\bолимпиад[а-я]*\b'
    ]
}

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
            location = {"city": "Петрозаводск"}
            for district in PETROZAVODSK_DISTRICTS:
                if re.search(rf'\b{re.escape(district)}\b', text, re.IGNORECASE):
                    location["district"] = district
                    break

            # Добавляем обработанную новость
            processed_news.append({
                **news_item,
                "location": location,
                "categories": detected_categories or ["Другое"]
            })

        return processed_news
