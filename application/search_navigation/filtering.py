# Фильтрация данных по тематике и местоположению
import re
from typing import List, Dict
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
    OTHER = "Другое"


# Только районы Петрозаводска
PETROZAVODSK_DISTRICTS = [
    "Голиковка", "Древлянка", "Зарека",
    "Ключевая", "Кукковка", "Октябрьский",
    "Первомайский", "Перевалка", "Пески",
    "Рыбка", "Центр", "Южная площадка"
]

# Улучшенный словарь с регулярными выражениями
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
        self.data_updater = DataUpdater()
        self.petrozavodsk_pattern = re.compile(
            r'\bПетрозаводск(?:а|у|ом|е|ий|ого|ому|им|ом)?\b',
            re.IGNORECASE
        )
        # Предкомпилируем регулярные выражения для производительности
        self.compiled_patterns = {
            category: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
            for category, patterns in CATEGORY_KEYWORDS.items()
        }

    async def process_news(self) -> List[Dict]:
        raw_news = await self.data_updater.fetch_news()
        processed_news = []

        if not raw_news:
            print("Новостей нет")
            return processed_news

        petrozavodsk_news_count = 0

        for news_item in raw_news:
            text = news_item.get("text", "")
            title = news_item.get("title", "")

            # Проверка на принадлежность к Петрозаводску
            if not self.petrozavodsk_pattern.search(text):
                continue

            petrozavodsk_news_count += 1

            # Определение категорий
            detected_categories = []
            for category, patterns in self.compiled_patterns.items():
                if any(pattern.search(text) for pattern in patterns):
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
            print("Title:", title)
            print("Text:", text[:100] + "...")  # Выводим первые 100 символов текста
            print("Categories:", ", ".join(detected_categories))
            print("District:", location.get("district", "Не указан"))
            print("-" * 50)

            processed_news.append({
                "title": title,
                "text": text,
                "location": location,
                "categories": detected_categories,
                "source": news_item.get("source", ""),
                "date": news_item.get("date", "")
            })

        if petrozavodsk_news_count == 0:
            print("Новостей о Петрозаводске нет")

        return processed_news


if __name__ == "__main__":
    async def main():
        processor = NewsProcessor()
        await processor.process_news()


    asyncio.run(main())