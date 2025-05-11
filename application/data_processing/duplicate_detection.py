async def save_unique_articles(new_articles: List[Dict], threshold: float = 0.95) -> int:
    """Сохраняет только уникальные статьи в базу данных."""
    if not new_articles:
        return 0
    
    db, tunnel = None, None
    try:
        db, tunnel = connect_to_mongo(
            ssh_host=HOST,
            ssh_port=PORT,
            ssh_user=SSH_USER,
            ssh_password=SSH_PASSWORD,
            db_name=DB_NAME
        )
        
        summarized_new = await summarize_texts_tfidf(new_articles)
        
        # Добавляем проверку наличия необходимых полей
        valid_articles = []
        for article in summarized_new:
            if not all(key in article for key in ['title', 'url', 'summary']):
                print(f"Пропущена статья с отсутствующими полями: {article.get('article_id', 'без ID')}")
                continue
            valid_articles.append(article)
        
        if not valid_articles:
            print("Нет валидных статей для обработки")
            return 0
            
        existing_articles = list(db.articles.find(
            {}, 
            {"title": 1, "summary": 1, "url": 1, "article_id": 1, "_id": 0}
        ))
        
        saved_count = 0
        
        if not existing_articles:
            for article in valid_articles:
                try:
                    db.articles.insert_one({
                        "article_id": article.get("article_id", ""),
                        "source_id": article.get("source_id", ""),
                        "title": article["title"],
                        "url": article["url"],
                        "publication_date": article.get("publication_date", ""),
                        "summary": article["summary"],
                        "text": article.get("text", ""),
                        "categories": article.get("categories", ["Другое"]),
                        "district": article.get("district", "Не указан")
                    })
                    saved_count += 1
                except Exception as e:
                    print(f"Ошибка при сохранении статьи {article.get('article_id')}: {str(e)}")
            return saved_count
        
        existing_texts = [
            f"{art.get('title', '')} {art.get('summary', '')}" 
            for art in existing_articles
        ]
        new_texts = [
            f"{art['title']} {art['summary']}" 
            for art in valid_articles
        ]
        
        vectorizer = TfidfVectorizer()
        existing_matrix = vectorizer.fit_transform(existing_texts)
        new_matrix = vectorizer.transform(new_texts)
        
        for i, article in enumerate(valid_articles):
            try:
                if db.articles.find_one({"url": article["url"]}):
                    continue
                    
                similarities = cosine_similarity(new_matrix[i], existing_matrix)[0]
                max_similarity = max(similarities) if similarities.size > 0 else 0
                
                if max_similarity < threshold:
                    db.articles.insert_one({
                        "article_id": article.get("article_id", ""),
                        "source_id": article.get("source_id", ""),
                        "title": article["title"],
                        "url": article["url"],
                        "publication_date": article.get("publication_date", ""),
                        "summary": article["summary"],
                        "text": article.get("text", ""),
                        "categories": article.get("categories", ["Другое"]),
                        "district": article.get("district", "Не указан")
                    })
                    saved_count += 1
            except Exception as e:
                print(f"Ошибка при обработке статьи {article.get('article_id')}: {str(e)}")
        
        return saved_count
        
    except Exception as e:
        print(f"Ошибка в save_unique_articles: {str(e)}")
        return 0
    finally:
        if tunnel:
            tunnel.close()
            print("SSH туннель закрыт")


async def async_main():
    print("="*50)
    print("СИСТЕМА ОБРАБОТКИ И СОХРАНЕНИЯ НОВОСТЕЙ")
    print("="*50)
    
    try:
        new_articles = await summarize_texts_tfidf([])
        
        if not new_articles:
            print("Нет новых статей для обработки")
            return
            
        print(f"Получено {len(new_articles)} новых статей для обработки")
        
        saved_count = await save_unique_articles(new_articles)
        
        print(f"\nСохранено {saved_count} уникальных статей из {len(new_articles)} обработанных")
        
    except Exception as e:
        print(f"\nОшибка при обработке новостей: {str(e)}")
    finally:
        print("\nРабота программы завершена")
