from pymongo import MongoClient
import re

# Подключение к MongoDB
def connect_to_mongodb(uri, db_name):
    client = MongoClient(uri)
    db = client[db_name]
    return db

# Фильтрация текстов по ключевым словам
def filter_by_location(texts, location_keywords):
    filtered_texts = []
    for text in texts:
        if any(keyword in text for keyword in location_keywords):
            filtered_texts.append(text)
    return filtered_texts

# Сохранение данных в MongoDB
def save_to_mongodb(collection, data):
    collection.insert_many(data)

# Поиск новостей по локации
def find_news_by_location(collection, location):
    return list(collection.find({"location": location}))

# Основная функция
def main():
    # Подключение к базе данных
    uri = "mongodb://localhost:27017/"  # Замените на ваш URI
    db_name = "your_database_name"
    db = connect_to_mongodb(uri, db_name)

    # Создание коллекций
    news_collection = db["news"]

    # Пример данных
    texts = [
        "Новость о Петрозаводске",
        "Событие в Первомайском районе",
        "Петрозаводск: новый проект"
    ]

    # Ключевые слова для фильтрации
    location_keywords = ["Петрозаводск", "Первомайский"]

    # Фильтрация текстов
    filtered_texts = filter_by_location(texts, location_keywords)

    # Преобразование отфильтрованных текстов в формат для сохранения
    news_data = [
        {"title": f"Новость {i+1}", "content": text, "location": "Петрозаводск" if "Петрозаводск" in text else "Первомайский"}
        for i, text in enumerate(filtered_texts)
    ]

    # Сохранение данных в MongoDB
    save_to_mongodb(news_collection, news_data)

    # Поиск новостей по Петрозаводску
    petrozavodsk_news = find_news_by_location(news_collection, "Петрозаводск")
    print("Новости по Петрозаводску:", petrozavodsk_news)

if __name__ == "__main__":
    main()
