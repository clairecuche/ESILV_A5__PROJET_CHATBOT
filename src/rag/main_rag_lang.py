import sys
from pathlib import Path

# Importer les classes de la nouvelle structure
from src.rag.generation.indexing_pipeline_lang import IndexingPipeline
from src.rag.vectorstore.vector_store_lang import VectorStoreManager # <-- Nouvelle classe FAISS/LangChain

# --- Paramètres globaux de l'index FAISS ---
FAISS_DIR = "vector_store_faiss"
# -------------------------------------------

def index_documents(pdf_directory: str, web_directory: str ):
    """Indexe tous les PDFs en utilisant l'IndexingPipeline FAISS."""
    print("\n INDEXATION DES DOCUMENTS")
    print("="*60)
    
    # 1. L'IndexingPipeline utilise maintenant VectorStoreManager (FAISS)
    pipeline = IndexingPipeline(pdf_directory=pdf_directory, web_data_directory=web_directory)
    pipeline.run_indexing()
    
    print("\n Indexation terminée et sauvegardée localement!")


def run_chat():
    """Lance le chatbot RAG."""
    print("\n LANCEMENT DU CHATBOT RAG")
    print("="*60)
    
    # Importer uniquement les composants LLM, Retriever et RAGPipeline
    from src.rag.generation.retriever_lang import Retriever
    from src.rag.generation.llm_handler import OllamaLLM
    from src.rag.generation.rag_pipeline import RAGPipeline
    
    print(" Chargement des composants...")

    # 1. Chargement de l'index FAISS
    # On utilise le VectorStoreManager pour charger l'index existant.
    vector_store_manager = VectorStoreManager(index_directory=FAISS_DIR)
    if not vector_store_manager.load_index():
        print(f"\n❌ Erreur: Index FAISS non trouvé dans '{FAISS_DIR}'. Veuillez d'abord indexer les documents.")
        return

    # 2. Initialisation du Retriever
    # Le Retriever utilise directement le Manager chargé et n'a plus besoin d'EmbeddingsGenerator.
    retriever = Retriever(
        vector_store_manager=vector_store_manager, # Utilise l'index chargé
        top_k=10,
        final_k=4,
        similarity_threshold=0.0
    )
    
    # 3. Initialisation du LLM (Ollama)
    llm = OllamaLLM(
        model="gemma:latest",
        temperature=0.3,
        max_tokens=1000
    )
    
    # 4. Lancement de la Pipeline RAG
    rag = RAGPipeline(
        retriever=retriever,
        llm=llm
    )
    
    # Lancer le chat interactif
    rag.interactive_chat()


def show_index_stats():
    """Affiche les statistiques de l'index FAISS."""
    print("\n STATISTIQUES DE L'INDEX FAISS")
    print("="*60)
    
    # 1. Utilisation de VectorStoreManager (FAISS)
    vector_store_manager = VectorStoreManager(index_directory=FAISS_DIR)
    
    if not vector_store_manager.load_index():
        print(f"\n❌ Erreur: Index FAISS non trouvé dans '{FAISS_DIR}'.")
        return

    # Récupérer l'objet FAISS interne pour accéder aux statistiques
    faiss_index = vector_store_manager.vectorstore.index
    
    # Nombre total de chunks (taille de la base FAISS)
    total_chunks = faiss_index.ntotal
    print(f" Total de chunks indexés: {total_chunks}")
    
    # Lister les sources (Extraction des métadonnées du DocumentStore de FAISS)
    try:
        # FAISS stocke les documents dans un DocumentStore séparé
        docstore_keys = vector_store_manager.vectorstore.docstore._dict.keys()
        
        # Le nombre de métadonnées extraites sera égal au nombre de chunks
        doc_metadatas = [
            doc.metadata 
            for doc in vector_store_manager.vectorstore.docstore._dict.values()
        ]
        
        if doc_metadatas:
            sources = set(meta.get('source', 'Unknown') for meta in doc_metadatas)
            print(f"\n📚 Documents sources ({len(sources)}):")
            for source in sorted(sources):
                count = sum(1 for meta in doc_metadatas if meta.get('source', 'Unknown') == source)
                print(f"  - {source}: {count} chunks")
        
    except Exception as e:
        print(f"\n  Impossible de lister les sources (erreur: {e}).")
        
    print(f"\n Localisation: ./{FAISS_DIR}/")


def main():
    """Point d'entrée principal"""
    # ... (le corps de main est conservé tel quel)
    if len(sys.argv) < 2:
        print("Usage:")
        print(" python -m src.rag.main_rag index <pdf_directory> # Indexer les PDFs")
        print(" python -m src.rag.main_rag chat # Lancer le chatbot")
        print(" python -m src.rag.main_rag stats # Voir les stats") 
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "index":
        # Dossier PDF optionnel (défaut: data/pdf)
        pdf_directory = sys.argv[2] if len(sys.argv) > 2 else "data/pdf"
        
        # Dossier web optionnel (défaut: data/autres)
        web_directory = sys.argv[3] if len(sys.argv) > 3 else "data/scraping"
        
        print(f"> Indexation:")
        print(f"   - PDFs: {pdf_directory}")
        print(f"   - Web: {web_directory}")
        
        index_documents(pdf_directory, web_directory=web_directory)
    
    elif command == "chat":
        run_chat()

    elif command == "stats": 
        show_index_stats()
    
    else:
        print(f" Commande inconnue: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()