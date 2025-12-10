from typing import List, Dict
import re
from src.rag.vectorstore.vector_store_lang import VectorStoreManager 
from langchain_core.documents import Document as LCDocument

class Retriever:
    """
    Système de récupération pour RAG avec reranking hybride
    """
    
    def __init__(
        self,
        vector_store_manager: VectorStoreManager, 
        top_k: int = 10,
        final_k: int = 4,
        similarity_threshold: float = 0.0
    ):
        """
        Args:
            vector_store_manager: Base vectorielle LangChain (FAISS)
            top_k: Nombre de chunks à récupérer pour le reranking
            final_k: Nombre final de chunks à retourner
            similarity_threshold: Seuil minimum de similarité
        """
        self.vector_store = vector_store_manager 
        self.top_k = top_k
        self.final_k = final_k
        self.similarity_threshold = similarity_threshold
    
    def _normalize_query(self, query: str) -> str:
        """
        Normalise la requête pour améliorer la recherche vectorielle
        """
        # Suppression de la ponctuation
        query = re.sub(r'[?!.,;:\'\"]+', ' ', query)
        # Suppression des espaces multiples
        query = re.sub(r'\s+', ' ', query)
        # Trim et minuscules pour la cohérence
        query = query.strip().lower()
        return query
    
    def retrieve(self, query: str) -> List[LCDocument]: 
        """
        Récupère les chunks les plus pertinents
        Args:
            query: Question de l'utilisateur
        Returns:
            Liste de Documents LangChain
        """
        # Normalisation de la requête
        normalized_query = self._normalize_query(query)
        
        retrieved_documents = self.vector_store.search(
            query=normalized_query,
            top_k=self.top_k
        )
        
        print(f"   Requête normalisée: '{normalized_query}'")
        print(f"   Récupération de {len(retrieved_documents)} documents")
        return retrieved_documents

    def retrieve_with_reranking(self, query: str) -> List[Dict]:
        """
        Récupération avec re-ranking hybride amélioré
        Combine: similarité vectorielle + correspondance lexicale + longueur
        """
        # 1. RETRIEVAL VECTORIEL (avec normalisation)
        retrieved_docs_lc = self.retrieve(query)
        
        if not retrieved_docs_lc:
            return []
        
        # 2. RERANKING HYBRIDE
        chunks_scored = []
        # Normalisation pour le reranking aussi
        normalized_query = self._normalize_query(query)
        query_terms = set(normalized_query.split())
        query_length = len(normalized_query.split())
        
        for i, doc in enumerate(retrieved_docs_lc):
            content = doc.page_content
            content_lower = content.lower()
            content_words = content_lower.split()
            
            # Score 1: Similarité vectorielle (basé sur le rang FAISS)
            vector_score = 1.0 - (i / self.top_k)
            
            # Score 2: Correspondance lexicale (termes exacts)
            exact_matches = sum(1 for term in query_terms if term in content_lower)
            lexical_score = exact_matches / len(query_terms) if query_terms else 0
            
            # Score 3: Densité des termes de requête dans le chunk
            term_positions = []
            for term in query_terms:
                for j, word in enumerate(content_words):
                    if term in word:
                        term_positions.append(j)
            
            if len(term_positions) > 1:
                # Compacité: les termes sont-ils proches dans le texte?
                term_positions.sort()
                span = term_positions[-1] - term_positions[0] + 1
                density_score = len(term_positions) / span if span > 0 else 0
            else:
                density_score = lexical_score
            
            # Score 4: Pénalité si chunk trop court ou trop long
            chunk_length = len(content.split())
            ideal_length = max(50, query_length * 10)  # ~10x la requête
            length_ratio = min(chunk_length, ideal_length) / ideal_length
            length_score = length_ratio if chunk_length >= 20 else length_ratio * 0.5
            
            # SCORE FINAL HYBRIDE
            # 50% vecteur, 25% lexical, 15% densité, 10% longueur
            final_score = (
                vector_score * 0.50 +
                lexical_score * 0.25 +
                density_score * 0.15 +
                length_score * 0.10
            )
            
            # Filtrage par threshold
            if vector_score < self.similarity_threshold:
                continue
            
            chunk_data = {
                'content': content,
                'metadata': doc.metadata,
                'vector_score': round(vector_score, 4),
                'lexical_score': round(lexical_score, 4),
                'density_score': round(density_score, 4),
                'length_score': round(length_score, 4),
                'final_score': round(final_score, 4),
                'rank': i + 1
            }
            chunks_scored.append(chunk_data)
        
        # 3. TRI ET SÉLECTION FINALE
        chunks_scored.sort(key=lambda x: x['final_score'], reverse=True)
        final_chunks = chunks_scored[:self.final_k]
        
        print(f"   Reranking: {len(retrieved_docs_lc)} → {len(final_chunks)} chunks finaux")
        
        return final_chunks



## V2 : avec debug 

from typing import List, Dict
import re
from src.rag.vectorstore.vector_store_lang import VectorStoreManager 
from langchain_core.documents import Document as LCDocument

class Retriever:
    """
    Système de récupération pour RAG avec reranking hybride
    """
    
    def __init__(
        self,
        vector_store_manager: VectorStoreManager, 
        top_k: int = 10,
        final_k: int = 4,
        similarity_threshold: float = 0.0
    ):
        """
        Args:
            vector_store_manager: Base vectorielle LangChain (FAISS)
            top_k: Nombre de chunks à récupérer pour le reranking
            final_k: Nombre final de chunks à retourner
            similarity_threshold: Seuil minimum de similarité
        """
        self.vector_store = vector_store_manager 
        self.top_k = top_k
        self.final_k = final_k
        self.similarity_threshold = similarity_threshold
    
    def _normalize_query(self, query: str) -> str:
        """
        Normalise la requête pour améliorer la recherche vectorielle
        """
        # Suppression de la ponctuation
        query = re.sub(r'[?!.,;:\'\"]+', ' ', query)
        # Suppression des espaces multiples
        query = re.sub(r'\s+', ' ', query)
        # Trim et minuscules pour la cohérence
        query = query.strip().lower()
        return query
    
    def retrieve(self, query: str) -> List[LCDocument]: 
        """
        Récupère les chunks les plus pertinents
        Args:
            query: Question de l'utilisateur
        Returns:
            Liste de Documents LangChain
        """
        # Normalisation de la requête
        normalized_query = self._normalize_query(query)
        
        retrieved_documents = self.vector_store.search(
            query=normalized_query,
            top_k=self.top_k
        )
        
        print(f"   Requête normalisée: '{normalized_query}'")
        print(f"   Récupération de {len(retrieved_documents)} documents")
        return retrieved_documents

    def retrieve_with_reranking(self, query: str) -> List[Dict]:
        """
        Récupération avec re-ranking hybride amélioré
        Combine: similarité vectorielle + correspondance lexicale + longueur
        """
        # 1. RETRIEVAL VECTORIEL (avec normalisation)
        retrieved_docs_lc = self.retrieve(query)
        
        if not retrieved_docs_lc:
            return []
        
        # DEBUG: Afficher les chunks récupérés
        print(f"\n   🔍 DEBUG - Chunks récupérés:")
        for i, doc in enumerate(retrieved_docs_lc[:10]):
            preview = doc.page_content.replace('\n', ' ')
            print(f"      [{i+1}] {preview}...")
        
        # 2. RERANKING HYBRIDE
        chunks_scored = []
        # Normalisation pour le reranking aussi
        normalized_query = self._normalize_query(query)
        query_terms = set(normalized_query.split())
        query_length = len(normalized_query.split())
        
        for i, doc in enumerate(retrieved_docs_lc):
            content = doc.page_content
            content_lower = content.lower()
            content_words = content_lower.split()
            
            # Score 1: Similarité vectorielle (basé sur le rang FAISS)
            vector_score = 1.0 - (i / self.top_k)
            
            # Score 2: Correspondance lexicale (termes exacts)
            exact_matches = sum(1 for term in query_terms if term in content_lower)
            lexical_score = exact_matches / len(query_terms) if query_terms else 0
            
            # Score 3: Densité des termes de requête dans le chunk
            term_positions = []
            for term in query_terms:
                for j, word in enumerate(content_words):
                    if term in word:
                        term_positions.append(j)
            
            if len(term_positions) > 1:
                # Compacité: les termes sont-ils proches dans le texte?
                term_positions.sort()
                span = term_positions[-1] - term_positions[0] + 1
                density_score = len(term_positions) / span if span > 0 else 0
            else:
                density_score = lexical_score
            
            # Score 4: Pénalité si chunk trop court ou trop long
            chunk_length = len(content.split())
            ideal_length = max(50, query_length * 10)  # ~10x la requête
            length_ratio = min(chunk_length, ideal_length) / ideal_length
            length_score = length_ratio if chunk_length >= 20 else length_ratio * 0.5
            
            # SCORE FINAL HYBRIDE
            # 50% vecteur, 25% lexical, 15% densité, 10% longueur
            final_score = (
                vector_score * 0.60 +
                lexical_score * 0.25 +
                density_score * 0.10 +
                length_score * 0.05
            )
            
            # Filtrage par threshold
            if vector_score < self.similarity_threshold:
                continue
            
            chunk_data = {
                'content': content,
                'metadata': doc.metadata,
                'vector_score': round(vector_score, 4),
                'lexical_score': round(lexical_score, 4),
                'density_score': round(density_score, 4),
                'length_score': round(length_score, 4),
                'final_score': round(final_score, 4),
                'rank': i + 1
            }
            chunks_scored.append(chunk_data)
        
        # 3. TRI ET SÉLECTION FINALE
        chunks_scored.sort(key=lambda x: x['final_score'], reverse=True)
        final_chunks = chunks_scored[:self.final_k]
        
        print(f"   Reranking: {len(retrieved_docs_lc)} → {len(final_chunks)} chunks finaux")
        
        # DEBUG: Afficher les scores finaux
        print(f"\n   📊 Scores des chunks finaux:")
        for chunk in final_chunks:
            print(f"      Score: {chunk['final_score']:.3f} (vec:{chunk['vector_score']:.2f} lex:{chunk['lexical_score']:.2f}) | {chunk['content']}...")
        print()
        
        return final_chunks