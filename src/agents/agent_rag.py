from pathlib import Path
import logging

from src.rag.generation.rag_pipeline import RAGPipeline
from src.rag.generation.retriever_lang import Retriever
from src.rag.generation.llm_handler import OllamaLLM
from src.rag.vectorstore.vector_store_lang import VectorStoreManager

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
            self.rag_pipeline = RAGPipeline(retriever=self.retriever, llm=self.llm)

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

            result = self.rag_pipeline.query(user_message, return_sources=True, stream=False, debug=False)

            if not result or not result.get("answer"):
                logger.warning("⚠️ Aucune réponse générée par la pipeline RAG")
                return self._no_answer_response()

            answer = result.get("answer", "")
            sources = result.get("sources", [])

            web_sources = []
            for src in sources:
                src_name = src.get("source", "")
                
                # Convertir Path en string si nécessaire
                if isinstance(src_name, Path):
                    src_name = str(src_name)
                
                # Garder uniquement les URLs web (commence par http:// ou https://)
                if isinstance(src_name, str) and (src_name.startswith('http://') or src_name.startswith('https://')):
                    if src_name not in web_sources:  # Éviter les doublons
                        web_sources.append(src_name)
                        break

            # Format response with web sources only
            response = answer.strip()
            
            # Afficher les sources seulement s'il y a des liens web
            if web_sources:
                response += "\n\n📚 Sources :\n"
                for i, url in enumerate(web_sources, start=1):
                    response += f"{i}. {url}\n"

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