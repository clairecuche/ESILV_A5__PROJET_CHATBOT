import sys

# Import principal de l'indexing pipeline
from src.rag.generation.indexing_pipeline import IndexingPipeline
from src.rag.vectorstore.vector_store import VectorStore

def index_documents(pdf_directory: str):
    """Indexe tous les PDFs ESILV"""
    print("\n INDEXATION DES DOCUMENTS")
    print("="*60)
    pipeline = IndexingPipeline(pdf_directory=pdf_directory)
    pipeline.process_all_pdfs()
    
    print("\n✅ Indexation terminée!")

def run_chat():
    """Lance le chatbot RAG"""
    print("\n LANCEMENT DU CHATBOT RAG")
    print("="*60)
    
    # Import des composants du projet
    from src.rag.embeddings.embeddings_generator import EmbeddingsGenerator
    from src.rag.vectorstore.vector_store import VectorStore
    from src.rag.generation.retriever import Retriever
    from src.rag.generation.llm_handler import OllamaLLM
    from src.rag.generation.rag_pipeline import RAGPipeline

    print(" Chargement des composants...")

    # Initialisation des composants
    embeddings_gen = EmbeddingsGenerator(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    
    vector_store = VectorStore(persist_directory="./chroma_db")
    
    retriever = Retriever(
        vector_store=vector_store,
        embeddings_generator=embeddings_gen,
        top_k=5,
        similarity_threshold=0.4
    )
    
    llm = OllamaLLM(
        model="mistral:latest",
        temperature=0.3,
        max_tokens=1000
    )
    
    rag = RAGPipeline(
        retriever=retriever,
        llm=llm
    )
    
    # Lancer le chat interactif
    rag.interactive_chat()

def show_index_stats():
    """Affiche les statistiques de l'index"""
    print("\n STATISTIQUES DE L'INDEX")
    print("="*60)
    
    vector_store = VectorStore(persist_directory="./chroma_db")
    
    # Nombre total de chunks
    total_chunks = vector_store.get_collection_stats()
    print(f" Total de chunks indexés: {total_chunks}")
    
    # Lister les sources
    collection = vector_store.collection
    all_metadatas = collection.get(include=["metadatas"])
    
    if all_metadatas and all_metadatas['metadatas']:
        sources = set(meta.get('source', 'Unknown') for meta in all_metadatas['metadatas'])
        print(f"\n📚 Documents sources ({len(sources)}):")
        for source in sorted(sources):
            count = sum(1 for meta in all_metadatas['metadatas'] if meta.get('source') == source)
            print(f"  - {source}: {count} chunks")
    
    print(f"\n Localisation: ./chroma_db/")

def main():
    """Point d'entrée principal"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m src.rag.main_rag index <pdf_directory>  # Indexer les PDFs")
        print("  python -m src.rag.main_rag chat                    # Lancer le chatbot")
        print("  python -m src.rag.main_rag stats                   # Voir les stats") 
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "index":
        if len(sys.argv) < 3:
            print(" Spécifiez le dossier des PDFs")
            print("Exemple: python -m src.rag.main_rag index ./data/brochures_esilv")
            sys.exit(1)
        pdf_directory = sys.argv[2]
        index_documents(pdf_directory)
    
    elif command == "chat":
        run_chat()

    elif command == "stats":  
        show_index_stats()
    
    else:
        print(f" Commande inconnue: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
