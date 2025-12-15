from pathlib import Path
import logging
import re

from src.rag.generation.rag_pipeline import RAGPipeline
from src.rag.generation.retriever_lang import Retriever
from src.rag.generation.llm_handler import OllamaLLM
from src.rag.vectorstore.vector_store_lang import VectorStoreManager
from src.agents.prompts import prompts

logger = logging.getLogger(__name__)


class AgentRAG:
    """Agent RAG aligné sur la structure des autres agents.

    Utilise :
    - `VectorStoreManager` pour charger l'index FAISS
    - `Retriever` pour récupérer et reranker les chunks
    - `OllamaLLM` comme interface LLM
    - `RAGPipeline` pour orchestrer retrieval + generation
    """

    def __init__(
        self,
        model: str = "gemma2:2b",
        index_directory: str = "vector_store_faiss",
        top_k: int = 20,
        final_k: int = 5,
        temperature: float = 0.1,
    ):
        self.model = model
        self.index_directory = index_directory
        self.top_k = top_k
        self.final_k = final_k
        self.temperature = temperature

        self.rag_ready = False
        self.rag_pipeline = None
        self.retriever = None
        self.vector_store = None

        try:
            logger.info("🔧 Initialisation Agent RAG...")

            # Load FAISS vector store
            self.vector_store = VectorStoreManager(index_directory=self.index_directory)
            loaded = self.vector_store.load_index()
            if not loaded:
                logger.warning("⚠️ Vectorstore FAISS non trouvé ou non chargé")
                return

            # Init retriever
            self.retriever = Retriever(
                vector_store_manager=self.vector_store,
                top_k=self.top_k,
                final_k=self.final_k,
                similarity_threshold=0.7,
            )

            # Init LLM handler
            self.llm = OllamaLLM(model=self.model, temperature=self.temperature, max_tokens=1000)

            # Create RAG pipeline
            self.rag_pipeline = RAGPipeline(retriever=self.retriever, llm=self.llm, system_prompt=prompts.RAG_SYSTEM_PROMPT)

            self.rag_ready = True
            logger.info("✓ Agent RAG initialisé avec succès")

        except Exception as e:
            logger.error(f"✗ Erreur initialisation Agent RAG: {e}")
            logger.info("💡 Indexez vos PDFs: python -m src.rag.main_rag_lang index ")
            self.rag_ready = False

    def rag_search(self, query: str):
        """Recherche rapide (retourne documents bruts depuis le vectorstore)."""
        if not self.rag_ready or not self.retriever:
            return []

        try:
            docs = self.retriever.retrieve(query)
            logger.info(f"✓ {len(docs)} documents récupérés pour la requête")
            return docs
        except Exception as e:
            logger.error(f"✗ Erreur lors de la recherche RAG: {e}")
            return []
    def _extract_used_sources(self, answer: str, all_sources: list) -> list:
        """
        Extrait les sources réellement citées dans la réponse du LLM.
        
        Stratégie : Se fier UNIQUEMENT aux citations explicites [1], [2], etc.
        """
        used_sources = []
        
        # Méthode 1 : Citations explicites [1], [2], etc.
        citation_pattern = r'\[(\d+)\]'
        citations = re.findall(citation_pattern, answer)

        # 🔥 DEBUG : Afficher ce qui est détecté
        logger.info(f"🔍 Citations détectées dans la réponse : {citations}")
        
        if citations:
            # Mapper les numéros de citation aux sources
            for cite_num in set(citations):
                idx = int(cite_num) - 1  # Les citations commencent à [1]
                if 0 <= idx < len(all_sources):
                    # On ajoute l'objet source complet
                    used_sources.append(all_sources[idx])
            logger.info(f"📌 {len(used_sources)} sources citées explicitement")
        
        # On ne retourne plus de fallback (correspondance de contenu ou top 2)
        # Si le LLM n'a pas cité, used_sources sera vide, ce qui est correct.
        return used_sources

    def _format_sources_for_llm(self, sources: list) -> str:
        """
        Formate les sources pour le prompt LLM avec numéros de citation.
        """
        formatted = []
        for i, src in enumerate(sources, start=1):
            content = src.get("content", "")
            source_name = src.get("source", "inconnu")
            formatted.append(f"[{i}] {content}\nSource: {source_name}")
        return "\n\n".join(formatted)

    def run(self, user_message: str) -> str:
        """Traite une requête utilisateur via la pipeline RAG."""
        if not self.rag_ready or not self.rag_pipeline:
            return (
                "Le système de recherche documentaire n'est pas encore configuré.\n\n"
                "Pour l'activer, indexez vos documents :\n"
                "python -m src.rag.main_rag_lang index \n\n"
                "En attendant, **souhaitez-vous être contacté par un conseiller ?**"
            )

        try:
            logger.info(f"🔍 AgentRAG traitement: {user_message[:120]}")
            
            # 1. Exécution de la requête
            result = self.rag_pipeline.query(
                user_message, 
                return_sources=True, 
                stream=False, 
                debug=False
            )

            if not result or not result.get("answer"):
                logger.warning("⚠️ Aucune réponse générée par la pipeline RAG")
                return self._no_answer_response()

            answer = result.get("answer", "")
            all_sources = result.get("sources", [])

            # 🔥 AMÉLIORATION 1 : Extraire les sources utilisées (seulement celles citées)
            used_sources = self._extract_used_sources(answer, all_sources)

            # 2. Nettoyage de la réponse (supprime les citations [1], [2]...)
            clean_answer = re.sub(r'\[\d+\]', '', answer).strip()
            
            # Si le LLM n'a pas cité, il n'a pas utilisé le contexte, 
            # ou il n'a pas pu répondre. Si sa réponse est vide (ou une 
            # phrase générique non supportée), on utilise la réponse par défaut.
            if not used_sources and clean_answer.lower() in [
                "je n'ai pas cette information dans ma documentation", 
                "je n'ai pas trouvé cette information"
            ]:
                return self._no_answer_response()

            # 3. Filtrer uniquement les URLs web (pour l'affichage final)
            web_sources = []
            for src in used_sources:
                src_name = src.get("source", "")
                
                # Convertir Path en string si nécessaire
                if isinstance(src_name, Path):
                    src_name = str(src_name)
                
                # Garder uniquement les URLs web
                if isinstance(src_name, str) and (
                    src_name.startswith('http://') or src_name.startswith('https://')
                ):
                    if src_name not in web_sources:  # Éviter les doublons
                        web_sources.append(src_name)

            # Format response
            response = clean_answer
            
            # Afficher les sources seulement s'il y a des liens web
            if web_sources:
                response += "\n\n📚 Sources utilisées :\n"
                # Afficher les URLs web uniquement
                for i, url in enumerate(web_sources, start=1):
                    response += f"{i}. {url}\n"
            
            # Si used_sources n'est PAS vide, mais web_sources est vide, 
            # cela signifie qu'il a utilisé des documents internes (PDFs, etc.), 
            # et nous n'affichons rien, ce qui est le comportement souhaité 
            # pour la documentation interne.

            return response

        except Exception as e:
            logger.error(f"✗ Erreur Agent RAG lors du run(): {e}")
            return self._error_response()
        
    def _no_answer_response(self) -> str:
        return (
            "Je n'ai pas trouvé d'informations pertinentes dans ma documentation.\n\n"
            "📞 Souhaitez-vous être contacté par notre équipe pour obtenir plus de détails ?"
        )

    def _error_response(self) -> str:
        return (
            "Désolé, une erreur s'est produite lors de la recherche.\n\n"
            "Pouvez-vous reformuler votre question ou cliquer sur '📞 Je souhaite être contacté' ?"
        )

    def is_ready(self) -> bool:
        return self.rag_ready and self.rag_pipeline is not None

    def get_stats(self) -> dict:
        try:
            return {
                "status": "ready" if self.is_ready() else "not_ready",
                "model": self.model,
                "vectorstore_index": self.index_directory,
                "top_k": self.top_k,
                "final_k": self.final_k,
            }
        except Exception:
            return {"status": "error"}