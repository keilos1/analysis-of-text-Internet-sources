from pymongo import MongoClient
import re
from typing import List, Dict, Union


# Подключение к MongoDB
def connect_to_mongodb(uri: str, db_name: str) -> MongoClient:
    client = MongoClient(uri)
    return client[db_name]


# Иерархия локаций Карелии
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


def extract_locations(text: str) -> List[Dict[str, str]]:
    """
    Извлекает локации из текста с учетом иерархии
    Возвращает список словарей с локациями разных уровней
    """
    found_locations = []

    # Проверяем Республику Карелия
    if re.search(r'Карел(ии|ия|ьский)|республ(ика|ике|ики)\s*Карел(ии|ия)', text, re.IGNORECASE):
        found_locations.append({"republic": "Республика Карелия"})

    # Проверяем города республиканского значения
    for city, districts in LOCATION_HIERARCHY["Республика Карелия"]["Города республиканского значения"].items():
        if re.search(rf'\b{re.escape(city)}\b', text, re.IGNORECASE):
            loc = {
                "republic": "Республика Карелия",
                "city": city
            }

            # Проверяем районы города (только для Петрозаводска и Костомукши)
            if isinstance(districts, dict):
                for district_type, district_list in districts.items():
                    for district in district_list:
                        if re.search(rf'\b{re.escape(district)}\b', text, re.IGNORECASE):
                            loc["district_type"] = district_type
                            loc["district"] = district
                            break
            elif isinstance(districts, list):
                for district in districts:
                    if re.search(rf'\b{re.escape(district)}\b', text, re.IGNORECASE):
                        loc["district"] = district
                        break

            found_locations.append(loc)

    # Проверяем районы и их населенные пункты
    for district, settlements in LOCATION_HIERARCHY["Республика Карелия"]["Районы"].items():
        # Проверяем название района
        district_match = re.search(rf'\b{re.escape(district)}\b', text, re.IGNORECASE)

        # Проверяем населенные пункты района
        found_settlements = []
        for settlement in settlements:
            if re.search(rf'\b{re.escape(settlement)}\b', text, re.IGNORECASE):
                found_settlements.append(settlement)

        if district_match or found_settlements:
            loc = {
                "republic": "Республика Карелия",
                "district": district if district_match else None,
                "settlements": found_settlements if found_settlements else None
            }
            found_locations.append(loc)

    return found_locations if found_locations else [{"republic": "Республика Карелия", "other": True}]


def process_news(news_collection, text: str, title: str = "") -> None:
    """
    Обрабатывает новость, извлекает локации и сохраняет в MongoDB
    """
    locations = extract_locations(f"{title} {text}")

    news_doc = {
        "title": title,
        "content": text,
        "locations": locations,
        "timestamp": datetime.datetime.now()
    }

    news_collection.insert_one(news_doc)


def find_news_by_location(collection, location_query: Dict[str, str]) -> List[Dict]:
    """
    Поиск новостей по локации с учетом иерархии
    location_query может содержать: republic, city, district, settlement
    """
    query = {}

    if "republic" in location_query:
        query["locations.republic"] = location_query["republic"]

    if "city" in location_query:
        query["locations.city"] = location_query["city"]

    if "district" in location_query:
        query["$or"] = [
            {"locations.district": location_query["district"]},
            {"locations.district_type": location_query["district"]}
        ]

    if "settlement" in location_query:
        query["locations.settlements"] = location_query["settlement"]

    return list(collection.find(query))


def main():
    # Подключение к базе данных
    uri = "mongodb://localhost:27017/"
    db_name = "karelia_news"
    db = connect_to_mongodb(uri, db_name)
    news_collection = db["news"]

    # Пример обработки новостей
    sample_news = [
        {"title": "Новый парк в Древлянке",
         "content": "В микрорайоне Древлянка Петрозаводска началось строительство нового парка."},
        {"title": "Дороги в Калевальском районе",
         "content": "В Калевальском районе ремонтируют дороги между поселками Калевала и Юшкозеро."},
        {"title": "Развитие туризма в Карелии",
         "content": "Правительство Республики Карелия выделило средства на развитие туристических маршрутов."},
        {"title": "Авария в Костомукше",
         "content": "В городе Костомукша произошло ДТП на улице Горняк."}
    ]

    for news in sample_news:
        process_news(news_collection, news["content"], news["title"])

    # Пример поиска
    print("Новости Петрозаводска:")
    for news in find_news_by_location(news_collection, {"city": "Петрозаводск"}):
        print(f"- {news['title']}")

    print("\nНовости Калевальского района:")
    for news in find_news_by_location(news_collection, {"district": "Калевальский район"}):
        print(f"- {news['title']}")

    print("\nВсе новости Карелии:")
    for news in find_news_by_location(news_collection, {"republic": "Республика Карелия"}):
        print(f"- {news['title']}")


if __name__ == "__main__":
    import datetime

    main()