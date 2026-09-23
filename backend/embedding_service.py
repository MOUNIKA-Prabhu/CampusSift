import math
import re
from typing import List, Tuple

try:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except Exception:
    SKLEARN_AVAILABLE = False

class EmbeddingService:
    def __init__(self):
        if SKLEARN_AVAILABLE:
            try:
                self.vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
            except Exception:
                self.vectorizer = None
        else:
            self.vectorizer = None

    def _tokenize(self, text: str) -> List[str]:
        words = re.findall(r'\b[a-zA-Z0-9]+\b', text.lower())
        unigrams = words
        bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words)-1)]
        return unigrams + bigrams

    def _fallback_cosine_similarity(self, text_a: str, text_b: str) -> float:
        tokens1 = self._tokenize(text_a)
        tokens2 = self._tokenize(text_b)
        if not tokens1 or not tokens2:
            return 0.0

        vocab = list(set(tokens1 + tokens2))
        df = {}
        for token in vocab:
            count = (1 if token in tokens1 else 0) + (1 if token in tokens2 else 0)
            df[token] = count

        N = 2
        len1, len2 = len(tokens1), len(tokens2)
        tf1 = {token: tokens1.count(token) / len1 for token in set(tokens1)}
        tf2 = {token: tokens2.count(token) / len2 for token in set(tokens2)}

        v1, v2 = [], []
        for token in vocab:
            idf = math.log((1 + N) / (1 + df[token])) + 1.0
            v1.append(tf1.get(token, 0.0) * idf)
            v2.append(tf2.get(token, 0.0) * idf)

        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))

        if norm1 == 0 or norm2 == 0:
            return 0.0
        return min(max(dot / (norm1 * norm2), 0.0), 1.0)

    def compute_cosine_similarity(self, text_a: str, text_b: str) -> float:
        """
        Computes cosine similarity between two text strings using TF-IDF term vectors.
        Returns a float between 0.0 and 1.0 (representing 0% to 100% similarity).
        """
        if not text_a.strip() or not text_b.strip():
            return 0.0
            
        if SKLEARN_AVAILABLE and self.vectorizer is not None:
            try:
                tfidf_matrix = self.vectorizer.fit_transform([text_a, text_b])
                similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
                return float(np.clip(similarity, 0.0, 1.0))
            except Exception as e:
                print(f"Error computing cosine similarity with sklearn: {e}")

        return self._fallback_cosine_similarity(text_a, text_b)

    def compute_batch_similarity(self, jd_text: str, resume_texts: List[str]) -> List[float]:
        """Computes similarity scores for a list of resumes against a single JD."""
        if not jd_text.strip() or not resume_texts:
            return [0.0] * len(resume_texts)

        if SKLEARN_AVAILABLE and self.vectorizer is not None:
            try:
                corpus = [jd_text] + resume_texts
                tfidf_matrix = self.vectorizer.fit_transform(corpus)
                jd_vector = tfidf_matrix[0:1]
                resume_vectors = tfidf_matrix[1:]
                similarities = cosine_similarity(jd_vector, resume_vectors)[0]
                return [float(np.clip(s, 0.0, 1.0)) for s in similarities]
            except Exception as e:
                print(f"Error computing batch similarity with sklearn: {e}")

        return [self._fallback_cosine_similarity(jd_text, r) for r in resume_texts]

# Singleton instance
embedding_service = EmbeddingService()

