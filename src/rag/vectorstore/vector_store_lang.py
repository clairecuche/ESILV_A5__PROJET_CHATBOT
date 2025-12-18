import os
import logging
from typing import List, Optional
from pathlib import Path
import re

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document as LCDocument

logger = logging.getLogger(__name__)

EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

class VectorStoreManager:
    """
    Gère l'index FAISS de LangChain
    """
    
    def __init__(self, index_directory: str = "vector_store_faiss"):
        """Initialise le manager et charge le modèle d'embeddings."""
        self.index_directory = index_directory
        self.vectorstore: Optional[FAISS] = None
        self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

        # On ne crée le dossier QUE s'il n'existe pas du tout
        if not os.path.exists(self.index_directory):
            os.makedirs(self.index_directory, exist_ok=True)
            logger.info(f"Dossier créé : {os.path.abspath(self.index_directory)}")
    
    
    def create_and_save_index(self, chunks: List[LCDocument]):
        """
        Crée l'index FAISS à partir des chunks (Documents LangChain) et le sauvegarde.
        """
        if not chunks:
            logger.warning("No chunks provided to create the index.")
            return

        logger.info(f"Creating FAISS index from {len(chunks)} documents...")
        self.vectorstore = FAISS.from_documents(chunks, self.embeddings)
        
        # Sauvegarde
        self.vectorstore.save_local(self.index_directory)
        logger.info(f"FAISS index successfully saved to: {self.index_directory}")
        
    
    def load_index(self) -> bool:
        # Vérification robuste des fichiers attendus par FAISS
        faiss_path = os.path.join(self.index_directory, "index.faiss")
        if not os.path.exists(faiss_path):
            logger.error(f"Fichier index.faiss introuvable dans : {self.index_directory}")
            return False
            
        try:
            self.vectorstore = FAISS.load_local(
                self.index_directory, 
                self.embeddings, 
                allow_dangerous_deserialization=True
            )
            logger.info("Index FAISS chargé avec succès.")
            return True
        except Exception as e:
            logger.error(f"Erreur chargement FAISS : {e}")
            return False
            
    
    def search(self, query: str, top_k: int = 4) -> List[LCDocument]:
        """
        Effectue une recherche par similarité (Retrieval) en utilisant l'objet d'embedding.
        """
        if not self.vectorstore:
            logger.error("Vector store not loaded/initialized.")
            return []
        
        # Normalisation de la requête
        normalized_query = re.sub(r'[?!.,;:\'\"]+', ' ', query)
        normalized_query = re.sub(r'\s+', ' ', normalized_query).strip()
        
        results = self.vectorstore.similarity_search(normalized_query, k=top_k)
        return results
