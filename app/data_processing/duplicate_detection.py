from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict

class DuplicateRemover:

    def __init__(self, articles_collection=None):
        self.articles = articles_collection or db.get_collection("articles")

    def find_duplicates(self, threshold=0.95):
        all_articles = list(self.articles.find({}, {"title": 1, "summary": 1, "url": 1, "_id": 1}))
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


    def remove_duplicates(self, duplicates: List[List[Dict]]):
        for duplicate_group in duplicates:
            for duplicate in duplicate_group[1:]:
                self.articles.delete_one({"_id": duplicate["_id"]})

duplicate_remover = DuplicateRemover()
duplicates = duplicate_remover.find_duplicates()
duplicate_remover.remove_duplicates(duplicates)