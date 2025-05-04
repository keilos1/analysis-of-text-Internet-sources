from sshtunnel import SSHTunnelForwarder
from pymongo import MongoClient
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict

class Database:
    def __init__(self, db):
        self.db = db
        self.articles = self.db.articles

    def find_duplicates(self, threshold=0.95):
        all_articles = list(self.articles.find({}, {"title": 1, "summary": 1, "url": 1, "article_id": 1}))
        if not all_articles:
            return []

        texts = [f"{article.get('title', '')} {article.get('summary', '')}" for article in all_articles]
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(texts)
        duplicates = []
        processed = set()

        for i in range(len(all_articles)):
            if i in processed:
                continue
            duplicates_group = []
            for j in range(i + 1, len(all_articles)):
                similarity = cosine_similarity(tfidf_matrix[i], tfidf_matrix[j])[0][0]
                if similarity >= threshold:
                    duplicates_group.append(all_articles[j])
                    processed.add(j)
            if duplicates_group:
                duplicates_group.insert(0, all_articles[i])  
                duplicates.append(duplicates_group)

        return duplicates

    def save_articles(self, articles):
        existing_duplicates = self.find_duplicates()
        
        for article in articles:
            summary = article.get("summary", "").strip()
            if not any(article.get("summary") == dup[0].get("summary") for dup in existing_duplicates):
                self.db.articles.insert_one(article)

def connect_to_mongo(
    ssh_host: str,
    ssh_port: int,
    ssh_user: str,
    ssh_password: str,
    remote_host: str = '127.0.0.1',
    remote_port: int = 27017,
    db_name: str = 'newsPTZ'
):
    tunnel = SSHTunnelForwarder(
        (ssh_host, ssh_port),
        ssh_username=ssh_user,
        ssh_password=ssh_password,
        remote_bind_address=(remote_host, remote_port)
    )
    tunnel.start()
    client = MongoClient('127.0.0.1', tunnel.local_bind_port)
    db = client[db_name]
    return Database(db), tunnel
