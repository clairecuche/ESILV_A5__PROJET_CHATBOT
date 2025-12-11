from typing import List
from langchain_community.embeddings import HuggingFaceEmbeddings
import numpy as np


DEFAULT_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

class EmbeddingsGenerator:
    """
    Générateur d'embeddings utilisant l'intégration LangChain pour HuggingFace.
    """
    
    def __init__(self, model_name: str = DEFAULT_MODEL_NAME):
        """
        Initialise l'objet Embeddings de LangChain.
        """
        # La classe HuggingFaceEmbeddings gère le chargement du modèle sentence-transformers en interne.
        self.embeddings_model = HuggingFaceEmbeddings(model_name=model_name)
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Génère les embeddings pour une liste de textes en utilisant l'API LangChain."""
        
        # La méthode embed_documents prend une liste de textes et retourne les vecteurs.
        embeddings_list = self.embeddings_model.embed_documents(texts)
        
        return np.array(embeddings_list)
    
    def generate_single_embedding(self, text: str) -> np.ndarray:
        """Génère l'embedding pour un seul texte (typiquement pour la requête)."""

        embedding = self.embeddings_model.embed_query(text)
        return np.array(embedding)
        
