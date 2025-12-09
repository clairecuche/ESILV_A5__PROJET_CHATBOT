from typing import List, Dict, Optional
import re
from src.rag.vectorstore.vector_store_lang import VectorStoreManager 
from langchain_core.documents import Document as LCDocument

class Retriever:
    """
    Système de récupération pour RAG avec reranking hybride optimisé
    """
    
    def __init__(
        self,
        vector_store_manager: VectorStoreManager, 
        top_k: int = 10,
        final_k: int = 4,
        similarity_threshold: float = 0.0,
        # Poids configurables pour le reranking
        weights: Optional[Dict[str, float]] = None
    ):
        """
        Args:
            vector_store_manager: Base vectorielle LangChain (FAISS)
            top_k: Nombre de chunks à récupérer pour le reranking
            final_k: Nombre final de chunks à retourner
            similarity_threshold: Seuil minimum de similarité (0.0-1.0)
            weights: Poids personnalisés {'vector': 0.6, 'lexical': 0.25, ...}
        """
        self.vector_store = vector_store_manager 
        self.top_k = top_k
        self.final_k = final_k
        self.similarity_threshold = similarity_threshold
        
        # Poids par défaut optimisés pour contexte éducatif
        self.weights = weights or {
            'vector': 0.55,    # Sémantique prioritaire mais équilibrée
            'lexical': 0.30,   # Termes exacts importants (noms de cours, profs)
            'density': 0.08,   # Préférence légère pour contenu concentré
            'length': 0.07     # Légère préférence pour réponses complètes
        }
        
        # Validation des poids
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Les poids doivent sommer à 1.0 (actuellement: {total})")
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalise le texte pour améliorer la recherche
        """
        # Suppression de la ponctuation
        text = re.sub(r'[?!.,;:\'\"]+', ' ', text)
        # Suppression des espaces multiples
        text = re.sub(r'\s+', ' ', text)
        # Minuscules et trim
        return text.strip().lower()
    
    def _extract_keywords(self, text: str) -> set:
        """
        Extrait les mots-clés significatifs (>3 caractères)
        Filtre les mots vides courants
        """
        stopwords = {
            'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du',
            'et', 'ou', 'mais', 'dans', 'pour', 'avec', 'sur',
            'est', 'sont', 'a', 'ont', 'the', 'is', 'are', 'to'
        }
        words = self._normalize_text(text).split()
        return {w for w in words if len(w) > 3 and w not in stopwords}
    
    def _calculate_vector_score(self, rank: int) -> float:
        """
        Score basé sur le rang FAISS (décroissance non-linéaire)
        """
        return 1.0 / (1.0 + rank * 0.1)  # Décroissance plus douce
    
    def _calculate_lexical_score(self, query_terms: set, content: str) -> float:
        """
        Score de correspondance lexicale avec pondération TF
        """
        content_lower = content.lower()
        content_words = content_lower.split()
        
        # Comptage des occurrences
        matches = 0
        for term in query_terms:
            # Compte les occurrences partielles (ex: "program" match "programmation")
            term_count = sum(1 for word in content_words if term in word)
            matches += min(term_count, 3)  # Cap à 3 pour éviter sur-pondération
        
        # Normalisation
        max_score = len(query_terms) * 3
        return matches / max_score if max_score > 0 else 0
    
    def _calculate_density_score(self, query_terms: set, content: str) -> float:
        """
        Densité des termes de requête (concentration dans le texte)
        """
        content_words = self._normalize_text(content).split()
        
        # Positions de tous les mots qui matchent un terme
        term_positions = []
        for i, word in enumerate(content_words):
            if any(term in word for term in query_terms):
                term_positions.append(i)
        
        if len(term_positions) < 2:
            return len(term_positions)  # 0 ou 1
        
        # Compacité: ratio du nombre de matches sur l'étendue
        term_positions.sort()
        span = term_positions[-1] - term_positions[0] + 1
        return min(len(term_positions) / span, 1.0)
    
    def _calculate_length_score(self, chunk_length: int, query_length: int) -> float:
        """
        Score de longueur avec courbe gaussienne autour d'une longueur idéale
        """
        # Longueur idéale: 8-15x la requête (entre 40 et 200 mots)
        ideal_min = max(40, query_length * 8)
        ideal_max = max(100, query_length * 15)
        ideal_mid = (ideal_min + ideal_max) / 2
        
        if chunk_length < 15:  # Trop court
            return 0.3
        elif ideal_min <= chunk_length <= ideal_max:  # Zone idéale
            return 1.0
        elif chunk_length < ideal_min:  # Un peu court
            return 0.5 + (chunk_length / ideal_min) * 0.5
        else:  # Trop long (décroissance douce)
            excess = chunk_length - ideal_max
            return max(0.5, 1.0 - (excess / ideal_max) * 0.5)
    
    def retrieve(self, query: str) -> List[LCDocument]: 
        """
        Récupère les chunks les plus pertinents avec recherche vectorielle
        """
        normalized_query = self._normalize_text(query)
        
        retrieved_documents = self.vector_store.search(
            query=normalized_query,
            top_k=self.top_k
        )
        
        print(f"   📝 Requête normalisée: '{normalized_query}'")
        print(f"   🔍 {len(retrieved_documents)} documents récupérés")
        return retrieved_documents

    def retrieve_with_reranking(self, query: str, debug: bool = True) -> List[Dict]:
        """
        Récupération avec re-ranking hybride multi-critères
        
        Args:
            query: Question de l'utilisateur
            debug: Active les logs détaillés
            
        Returns:
            Liste de chunks scorés et triés
        """
        # 1. RETRIEVAL VECTORIEL
        retrieved_docs = self.retrieve(query)
        
        if not retrieved_docs:
            return []
        
        # 2. PRÉPARATION POUR RERANKING
        query_keywords = self._extract_keywords(query)
        query_length = len(query.split())
        
        if debug:
            print(f"\n   🔑 Mots-clés extraits: {query_keywords}")
        
        # 3. SCORING HYBRIDE
        chunks_scored = []
        
        for rank, doc in enumerate(retrieved_docs):
            content = doc.page_content
            chunk_length = len(content.split())
            
            # Calcul des 4 scores
            vector_score = self._calculate_vector_score(rank)
            lexical_score = self._calculate_lexical_score(query_keywords, content)
            density_score = self._calculate_density_score(query_keywords, content)
            length_score = self._calculate_length_score(chunk_length, query_length)
            
            # Score final pondéré
            final_score = (
                vector_score * self.weights['vector'] +
                lexical_score * self.weights['lexical'] +
                density_score * self.weights['density'] +
                length_score * self.weights['length']
            )
            
            # Filtrage par seuil minimal
            if vector_score < self.similarity_threshold:
                continue
            
            # Bonus si le chunk contient TOUS les mots-clés principaux
            if query_keywords and all(
                any(kw in word for word in self._normalize_text(content).split()) 
                for kw in query_keywords
            ):
                final_score *= 1.1  # Boost de 10%
            
            chunk_data = {
                'content': content,
                'metadata': doc.metadata,
                'scores': {
                    'vector': round(vector_score, 4),
                    'lexical': round(lexical_score, 4),
                    'density': round(density_score, 4),
                    'length': round(length_score, 4),
                    'final': round(final_score, 4)
                },
                'chunk_length': chunk_length,
                'initial_rank': rank + 1
            }
            chunks_scored.append(chunk_data)
        
        # 4. TRI ET SÉLECTION FINALE
        chunks_scored.sort(key=lambda x: x['scores']['final'], reverse=True)
        final_chunks = chunks_scored[:self.final_k]
        
        # 5. LOGS
        print(f"   ✅ Reranking: {len(retrieved_docs)} → {len(final_chunks)} chunks")
        
        if debug:
            print(f"\n   📊 Top {len(final_chunks)} chunks:")
            for i, chunk in enumerate(final_chunks, 1):
                s = chunk['scores']
                preview = chunk['content'].replace('\n', ' ')
                print(f"      [{i}] Score: {s['final']:.3f} "
                      f"(V:{s['vector']:.2f} L:{s['lexical']:.2f} "
                      f"D:{s['density']:.2f} Len:{s['length']:.2f})")
                print(f"          {preview}...\n")
        
        return final_chunks
    