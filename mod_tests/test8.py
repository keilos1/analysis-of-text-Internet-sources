import pytest
from unittest.mock import MagicMock, patch
from application.data_storage.database import Database, connect_to_mongo
from pymongo.errors import ConnectionFailure
from sshtunnel import BaseSSHTunnelForwarderError
import datetime


class TestDatabase:
    @pytest.fixture
    def db(self):
        mock_db = MagicMock()
        return Database(mock_db)

    # Тест М35: Сохранение новой статьи
    def test_save_new_article(self, db):
        """Проверка сохранения новой статьи"""
        input_data = {
            "article_id": "art123",
            "source_id": "src456",
            "title": "Новый парк в Петрозаводске",
            "url": "https://example.com/news1",
            "publication_date": datetime.datetime(2025, 5, 18),
            "summary": "Открытие нового парка",
            "text": "Полный текст о парке...",
            "categories": ["Новости"],
            "district": "Центр"
        }

        db.save_article(**input_data)

        db.articles.update_one.assert_called_once_with(
            {"article_id": "art123"},
            {"$set": input_data},
            upsert=True
        )

    # Тест М36: Обновление статьи
    def test_update_article(self, db):
        """Проверка обновления существующей статьи"""
        input_data = {
            "article_id": "art123",
            "source_id": "src456",
            "title": "Обновленный заголовок",
            "url": "https://example.com/news1",
            "publication_date": datetime.datetime(2025, 5, 18),
            "summary": "Новое описание",
            "text": "Обновленный текст",
            "categories": ["Новости", "Экология"],
            "district": "Центр"
        }

        db.save_article(**input_data)

        db.articles.update_one.assert_called_once_with(
            {"article_id": "art123"},
            {"$set": input_data},
            upsert=True
        )

    # Тест М37: Неполные данные статьи
    def test_save_incomplete_article(self, db):
        """Проверка обработки неполных данных"""
        with pytest.raises(ValueError):
            db.save_article(
                article_id="art123",
                source_id="src456",
                title=None,  # Обязательное поле отсутствует
                url="https://example.com/news1",
                publication_date=datetime.datetime(2025, 5, 18),
                summary="Описание",
                text="Текст",
                categories=["Новости"],
                district="Центр"
            )

    # Тест М38: Сохранение источника
    def test_save_source(self, db):
        """Проверка сохранения нового источника"""
        input_data = {
            "source_id": "src789",
            "name": "Example News",
            "url": "https://example.com/rss",
            "category": "Новости",
            "district": "Центр",
            "area_of_the_city": "Центральный",
            "last_checked_time": datetime.datetime(2025, 5, 18, 12, 0)
        }

        db.save_source(**input_data)

        db.sources.update_one.assert_called_once_with(
            {"source_id": "src789"},
            {"$set": input_data},
            upsert=True
        )

    # Тест М39: Обновление времени проверки
    def test_update_source_check_time(self, db):
        """Проверка обновления времени проверки источника"""
        new_time = datetime.datetime(2025, 5, 19, 10, 30)
        db.save_source(
            source_id="src789",
            name="Example News",
            url="https://example.com/rss",
            category="Новости",
            district="Центр",
            area_of_the_city="Центральный",
            last_checked_time=new_time
        )

        db.sources.update_one.assert_called_once_with(
            {"source_id": "src789"},
            {"$set": {"last_checked_time": new_time}},
            upsert=True
        )

    # Тест М40: Сохранение дайджеста
    def test_save_daily_digest(self, db):
        """Проверка сохранения дайджеста"""
        input_data = {
            "daily_digest_id": "digest20230520",
            "date": datetime.date(2025, 5, 18),
            "article_id": ["art123", "art456"],
            "category_distribution": {"Новости": 5, "Спорт": 3}
        }

        db.save_daily_digest(**input_data)

        db.daily_digest.update_one.assert_called_once_with(
            {"daily_digest_id": "digest20230520"},
            {"$set": input_data},
            upsert=True
        )

    # Тест М41: Обновление дайджеста
    def test_update_daily_digest(self, db):
        """Проверка обновления дайджеста"""
        db.save_daily_digest(
            daily_digest_id="digest20230520",
            date=datetime.date(2025, 5, 18),
            article_id=["art123", "art456", "art789"],  # Добавлен новый ID
            category_distribution={"Новости": 6, "Спорт": 3}  # Обновлено
        )

        db.daily_digest.update_one.assert_called_once()

    # Тест М42: Получение существующего источника
    def test_get_existing_source(self, db):
        """Проверка получения источника"""
        mock_source = {
            "source_id": "src789",
            "name": "Example News",
            "url": "https://example.com/rss"
        }
        db.sources.find_one.return_value = mock_source

        result = db.get_source("src789")

        assert result == mock_source
        db.sources.find_one.assert_called_once_with(
            {"source_id": "src789"}, {"_id": 0}
        )

    # Тест М43: Получение несуществующего источника
    def test_get_nonexistent_source(self, db):
        """Проверка запроса несуществующего источника"""
        db.sources.find_one.return_value = None

        result = db.get_source("wrong_id")

        assert result is None


class TestMongoConnection:
    # Тест М44: Локальное подключение
    @patch('pymongo.MongoClient')
    def test_local_connection(self, mock_mongo):
        """Проверка локального подключения без SSH"""
        mock_client = MagicMock()
        mock_mongo.return_value = mock_client

        db, tunnel = connect_to_mongo(
            ssh_host=None,
            ssh_port=22,
            ssh_user="user",
            ssh_password="pass",
            mongo_host="localhost",
            mongo_port=27017,
            db_name="test_db"
        )

        assert tunnel is None
        mock_mongo.assert_called_once_with("localhost", 27017)

    # Тест М45: Подключение через SSH
    @patch('sshtunnel.SSHTunnelForwarder')
    @patch('pymongo.MongoClient')
    def test_ssh_connection(self, mock_mongo, mock_tunnel):
        """Проверка подключения через SSH"""
        mock_tunnel.return_value.local_bind_port = 3333
        mock_tunnel.return_value.start.return_value = True

        db, tunnel = connect_to_mongo(
            ssh_host="ssh.example.com",
            ssh_port=22,
            ssh_user="user",
            ssh_password="pass",
            mongo_host="mongo.internal",
            mongo_port=27017,
            db_name="test_db"
        )

        assert tunnel is not None
        mock_mongo.assert_called_once_with('127.0.0.1', 3333)

    # Тест М46: Ошибка подключения
    @patch('pymongo.MongoClient')
    def test_connection_failure(self, mock_mongo):
        """Проверка обработки ошибки подключения"""
        mock_mongo.side_effect = ConnectionFailure("Connection failed")

        with pytest.raises(ConnectionFailure):
            connect_to_mongo(
                ssh_host=None,
                ssh_port=22,
                ssh_user="user",
                ssh_password="pass",
                mongo_host="invalid_host",
                mongo_port=27017,
                db_name="test_db"
            )