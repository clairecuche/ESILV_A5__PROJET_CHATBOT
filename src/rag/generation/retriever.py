from typing import List, Dict, Tuple
from ..embeddings.embeddings_generator import EmbeddingsGenerator
from src.rag.vectorstore.vector_store import VectorStore

class Retriever:
    """
    Système de récupération intelligent pour RAG
    """
    
    def __init__(
        self,
        vector_store: VectorStore,
        embeddings_generator: EmbeddingsGenerator,
        top_k: int = 5,
        similarity_threshold: float = 0.5
    ):
        """
        Args:
            vector_store: Base vectorielle
            embeddings_generator: Générateur d'embeddings
            top_k: Nombre de chunks à récupérer
            similarity_threshold: Seuil minimal de similarité
        """
        self.vector_store = vector_store
        self.embeddings_generator = embeddings_generator
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
    
    def retrieve(self, query: str) -> List[Dict]:
        """
        Récupère les chunks les plus pertinents
        
        Args:
            query: Question de l'utilisateur
            
        Returns:
            Liste de chunks avec métadonnées et scores
        """
        # 1. Générer embedding de la query
        query_embedding = self.embeddings_generator.generate_single_embedding(query)
        
        # 2. Recherche dans la base vectorielle
        results = self.vector_store.search(
            query_embedding=query_embedding.tolist(),
            top_k=self.top_k
        )
        
        # 3. Formater les résultats
        retrieved_chunks = []
        
        if results['documents'] and len(results['documents'][0]) > 0:
            for i in range(len(results['documents'][0])):
                # ChromaDB retourne distance, convertir en similarité
                distance = results['distances'][0][i] if 'distances' in results else 0
                similarity = 1 - distance  # Cosine distance -> similarity
                
                # Filtrer par threshold
                if similarity >= self.similarity_threshold:
                    chunk_data = {
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'similarity_score': round(similarity, 4),
                        'rank': i + 1
                    }
                    retrieved_chunks.append(chunk_data)
        
        print(f"   Retrieved {len(retrieved_chunks)} chunks (threshold: {self.similarity_threshold})")
        return retrieved_chunks
    
    def retrieve_with_reranking(self, query: str) -> List[Dict]:
        """
        Récupération avec re-ranking simple basé sur mots-clés
        """
        chunks = self.retrieve(query)
        
        # Re-rank basé sur présence de mots-clés de la query
        query_keywords = set(query.lower().split())
        
        for chunk in chunks:
            content_lower = chunk['content'].lower()
            keyword_matches = sum(1 for kw in query_keywords if kw in content_lower)
            chunk['keyword_score'] = keyword_matches / len(query_keywords)
            # Score combiné
            chunk['final_score'] = (chunk['similarity_score'] * 0.7 + 
                                   chunk['keyword_score'] * 0.3)
        
        # Trier par score final
        chunks.sort(key=lambda x: x['final_score'], reverse=True)
        
        return chunks