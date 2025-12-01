from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List

class EmbeddingsGenerator:
    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        """
        Modèle multilingue recommandé pour français/anglais
        Alternatives: 'all-MiniLM-L6-v2' (anglais uniquement mais plus rapide)
        """
        self.model = SentenceTransformer(model_name)
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Génère les embeddings pour une liste de textes"""
        embeddings = self.model.encode(texts, show_progress_bar=True)
        return embeddings
    
    def generate_single_embedding(self, text: str) -> np.ndarray:
        """Génère l'embedding pour un seul texte"""
        return self.model.encode([text])[0]