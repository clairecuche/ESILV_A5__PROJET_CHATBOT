import chromadb
from typing import List, Dict
import uuid
import os

class VectorStore:
    def __init__(self, persist_directory: str = "./chroma_db"):
        """Initialise ChromaDB avec persistance locale"""
        
        # Créer le dossier
        os.makedirs(persist_directory, exist_ok=True)
        abs_path = os.path.abspath(persist_directory)
        
        print(f" ChromaDB path: {abs_path}")
        
        # CRITIQUE: Utiliser PersistentClient directement
        self.client = chromadb.PersistentClient(
            path=abs_path
        )
        
        # Nom de collection constant
        self.collection_name = "esilv_documents"
        
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        current_count = self.collection.count()
        print(f" Collection '{self.collection_name}' chargée: {current_count} documents existants")
    
    def add_documents(self, chunks: List[str], embeddings, metadatas: List[Dict] = None):
        """Ajoute des documents avec leurs embeddings"""
        if not chunks:
            print("  Aucun chunk à ajouter")
            return
        
        count_before = self.collection.count()
        
        ids = [str(uuid.uuid4()) for _ in range(len(chunks))]
        
        print(f" Ajout de {len(chunks)} chunks...")
        print(f" Avant: {count_before} documents")
        
        # Convertir embeddings si nécessaire
        if hasattr(embeddings, 'tolist'):
            embeddings = embeddings.tolist()
        
        self.collection.add(
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas if metadatas else [{}] * len(chunks),
            ids=ids
        )
        
        count_after = self.collection.count()
        print(f"   Après: {count_after} documents")
        print(f" {count_after - count_before} chunks réellement ajoutés")
    
    def search(self, query_embedding: List[float], top_k: int = 5) -> Dict:
        """Recherche les chunks les plus similaires"""
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        return results
    
    def get_collection_stats(self):
        """Statistiques de la collection"""
        return self.collection.count()
    
    def list_all_documents(self):
        """Liste tous les documents"""
        try:
            all_docs = self.collection.get(limit=100)
            return all_docs
        except Exception as e:
            print(f"Erreur listing: {e}")
            return None