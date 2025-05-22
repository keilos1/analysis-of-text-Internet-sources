import re
import sys
import asyncio
from pathlib import Path
from typing import List, Dict
from enum import Enum
from setfit import SetFitModel

sys.path.append("../")
from data_collection.sheduler import DataUpdater


class NewsCategory(Enum):
    CULTURE = "Культура"
    SPORT = "Спорт"
    TECHNOLOGY = "Технологии"
    HOLIDAYS = "Праздники"
    EDUCATION = "Образование"
    INCIDENTS = "Происшествия"
    SOCIETY = "Общество"
    OTHER = "Другое"


PETROZAVODSK_DISTRICTS = [
    "Голиковка", "Древлянка", "Зарека", "Ключевая", "Кукковка",
    "Октябрьский", "Первомайский", "Перевалка", "Пески", "Рыбка", "Центр", "Южная площадка"
]


class NewsProcessor:
    def __init__(self):
        self.data_updater = DataUpdater()
        self.petrozavodsk_pattern = re.compile(
            r'\bПетрозаводск(?:а|у|ом|е|ий|ого|ому|им|ом)?\b',
            re.IGNORECASE
        )

        # Получаем абсолютный путь к модели
        model_path = (Path(__file__).parent.parent / "data_processing" / "saved_models" / "setfit_news_classifier").resolve()

        # Проверяем существование пути
        if not model_path.exists():
            raise FileNotFoundError(f"Model directory not found: {model_path}")

        # Преобразуем путь в строку в формате POSIX
        model_path_str = model_path.as_posix()

        # Загрузка обученной модели
        try:
            self.model = SetFitModel.from_pretrained(model_path_str)
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {str(e)}")

    async def process_news(self) -> List[Dict]:
        raw_news = await self.data_updater.fetch_news()
        processed_news = []

        if not raw_news:
            print("Новостей нет")
            return processed_news

        for news_item in raw_news:
            text = news_item.get("text", "")
            if not self.petrozavodsk_pattern.search(text):
                continue

            # Получение категории (как строки, без np.str_)
            label = self.model.predict([text])[0]
            category = str(label)

            # Определение района
            location = {"city": "Петрозаводск"}
            for district in PETROZAVODSK_DISTRICTS:
                if re.search(rf'\b{re.escape(district)}\b', text, re.IGNORECASE):
                    location["district"] = district
                    break

            print("Title:", news_item.get("title", ""))
            print("Text:", text)
            print("Categories:", [category])
            print("District:", location.get("district", "Не указан"))
            print("-" * 50)

            processed_news.append({
                **news_item,
                "location": location,
                "categories": [category]  # Обычная строка
            })

        return processed_news


if __name__ == "__main__":
    async def main():
        processor = NewsProcessor()
        await processor.process_news()

    asyncio.run(main())
