#Установка необходимых зависимостей. Создание БД и коллекций. Обучение модели.
import os
import subprocess
import sys
from pathlib import Path
import git
import pymongo
from pymongo import MongoClient


def clone_repository(repo_url, target_dir):
    """Клонирует репозиторий из GitHub"""
    print(f"Клонируем репозиторий {repo_url} в {target_dir}")
    if os.path.exists(target_dir):
        print("Директория уже существует, пропускаем клонирование")
        return
    git.Repo.clone_from(repo_url, target_dir)


def install_requirements(requirements_file):
    """Устанавливает зависимости из requirements.txt"""
    print(f"Устанавливаем зависимости из {requirements_file}")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_file])


def setup_mongodb():
    """Настраивает MongoDB: создает базу данных и коллекции"""
    print("Настраиваем MongoDB...")
    try:
        client = MongoClient('mongodb://localhost:27017/')

        # Создаем базу данных
        db = client['text_analysis_db']

        # Создаем коллекции (примерные, нужно уточнить по проекту)
        collections = ['texts', 'models', 'results', 'train_data']
        for col in collections:
            if col not in db.list_collection_names():
                db.create_collection(col)
                print(f"Создана коллекция {col}")

        print("MongoDB настроена успешно")
        return db
    except Exception as e:
        print(f"Ошибка при настройке MongoDB: {e}")
        return None


def train_model(project_dir):
    """Запускает обучение модели"""
    train_script = os.path.join(project_dir, 'train_model.py')
    if not os.path.exists(train_script):
        raise FileNotFoundError(f"Файл {train_script} не найден")

    print(f"Запускаем обучение модели: {train_script}")
    subprocess.check_call([sys.executable, train_script])


def main():
    # Конфигурация
    repo_url = "https://github.com/keilos1/analysis-of-text-Internet-sources"
    project_dir = "analysis-of-text-Internet-sources"
    requirements_file = os.path.join(project_dir, "requirements.txt")

    try:
        # 1. Клонируем репозиторий
        clone_repository(repo_url, project_dir)

        # 2. Устанавливаем зависимости
        if os.path.exists(requirements_file):
            install_requirements(requirements_file)
        else:
            print(f"Файл {requirements_file} не найден, пропускаем установку зависимостей")

        # 3. Настраиваем MongoDB
        setup_mongodb()

        # 4. Запускаем обучение модели
        train_model(project_dir)

        print("Все операции завершены успешно!")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()