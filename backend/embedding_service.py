import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Tuple

class EmbeddingService:
    def __init__(self):
        # TF-IDF Vectorizer with n-grams (1, 2) for robust semantic representation
        self.vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))

    def compute_cosine_similarity(self, text_a: str, text_b: str) -> float:
        """
        Computes cosine similarity between two text strings using TF-IDF term vectors.
        Returns a float between 0.0 and 1.0 (representing 0% to 100% similarity).
        """
        if not text_a.strip() or not text_b.strip():
            return 0.0
            
        try:
            tfidf_matrix = self.vectorizer.fit_transform([text_a, text_b])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            # Clip between 0.0 and 1.0
            return float(np.clip(similarity, 0.0, 1.0))
        except Exception as e:
            print(f"Error computing cosine similarity: {e}")
            return 0.0

    def compute_batch_similarity(self, jd_text: str, resume_texts: List[str]) -> List[float]:
        """Computes similarity scores for a list of resumes against a single JD."""
        if not jd_text.strip() or not resume_texts:
            return [0.0] * len(resume_texts)

        try:
            corpus = [jd_text] + resume_texts
            tfidf_matrix = self.vectorizer.fit_transform(corpus)
            jd_vector = tfidf_matrix[0:1]
            resume_vectors = tfidf_matrix[1:]
            
            similarities = cosine_similarity(jd_vector, resume_vectors)[0]
            return [float(np.clip(s, 0.0, 1.0)) for s in similarities]
        except Exception as e:
            print(f"Error computing batch similarity: {e}")
            return [0.0] * len(resume_texts)

# Singleton instance
embedding_service = EmbeddingService()
