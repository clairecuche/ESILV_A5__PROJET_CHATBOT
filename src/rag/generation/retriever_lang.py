from typing import List, Dict, Tuple
from src.rag.vectorstore.vector_store_lang import VectorStoreManager 
from langchain_core.documents import Document as LCDocument

class Retriever:
    """
    Système de récupération intelligent pour RAG
    """
    
    def __init__(
        self,
        vector_store_manager: VectorStoreManager, 
        top_k: int = 4, 
        similarity_threshold: float = 0.0 # A modifier selon les besoins
    ):
        """
        Args:
            vector_store_manager: Base vectorielle LangChain (FAISS)
            top_k: Nombre de chunks à récupérer
        """
        self.vector_store = vector_store_manager 
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
    
    def retrieve(self, query: str) -> List[LCDocument]: 
        """
        Récupère les chunks les plus pertinents
        Args:
            query: Question de l'utilisateur
        Returns:
            Liste de Documents LangChain
        """
        # Le VectorStoreManager expose la méthode search(query, top_k)
        retrieved_documents = self.vector_store.search(
            query=query,
            top_k=self.top_k
        )
        
        # A modifier si l'on veut filtrer par similarité
        #  Dans le contexte d'une pipeline LangChain standard, on ne filtre pas par
        # threshold ici car on perdrait la simplicité de l'objet Document.
        # On peut ajouter le score de similarité comme une métadonnée supplémentaire 
        # si le manager le supporte. Pour l'instant, on retourne les documents bruts.
        
        print(f"   Récupération brute de {len(retrieved_documents)} documents (LangChain format)")
        return retrieved_documents
    
    # NOTE: retrieve_with_reranking doit être modifié pour travailler avec 
    # des objets Document LangChain, ce qui complique l'accès/modification
    # des scores et contenus. 
    # Pour la simplicité, l'implémentation de reranking peut être conservée
    # en utilisant le content et en retournant un dictionnaire standard pour la RAGPipeline.

    def retrieve_with_reranking(self, query: str) -> List[Dict]:
        """
        Récupération avec re-ranking simple basé sur mots-clés
        Convertit les Documents LangChain en dictionnaire pour le reranking/pipeline.
        """
        # 1. RETRIEVAL BRUT (retourne des Documents LangChain)
        retrieved_docs_lc = self.retrieve(query)
        
        # 2. CONVERSION ET RE-RANKING
        chunks_for_pipeline = []
        query_keywords = set(query.lower().split())

        for i, doc in enumerate(retrieved_docs_lc):
            # FAISS met le score dans la seconde variable de la méthode search_with_score
            # Pour l'instant on utilise le score de rank brute si l'on ne peut pas l'extraire directement
            # (Si l'on veut le score exact, il faudrait que VectorStoreManager utilise search_with_score)
            
            # Approximation du score (pour conserver la logique de l'utilisateur)
            similarity_score = 1.0 - (i / self.top_k) # Approximation basée sur le rang

            content_lower = doc.page_content.lower()
            keyword_matches = sum(1 for kw in query_keywords if kw in content_lower)
            keyword_score = keyword_matches / max(1, len(query_keywords))
            
            final_score = (similarity_score * 0.7 + keyword_score * 0.3)

            chunk_data = {
                'content': doc.page_content,
                'metadata': doc.metadata,
                'similarity_score': round(similarity_score, 4), # Score VECTEUR (Approximation)
                'keyword_score': round(keyword_score, 4),
                'final_score': round(final_score, 4),
                'rank': i + 1
            }
            chunks_for_pipeline.append(chunk_data)

        # Trier par score final
        chunks_for_pipeline.sort(key=lambda x: x['final_score'], reverse=True)
        
        print(f"   Retrieved {len(chunks_for_pipeline)} chunks après Reranking")
        return chunks_for_pipeline