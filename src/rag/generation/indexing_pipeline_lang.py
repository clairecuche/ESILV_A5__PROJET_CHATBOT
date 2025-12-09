from src.rag.document_processing.pdf_loader_lang import load_all_pdfs_with_langchain 
from src.rag.document_processing.chunker_lang import OptimalChunker
from src.rag.document_processing.text_cleaner import TextCleaner

from src.rag.vectorstore.vector_store_lang import VectorStoreManager # Votre nouvelle classe FAISS

from pathlib import Path
from typing import List

class IndexingPipeline:
    def __init__(self, pdf_directory: str):
        self.pdf_directory = pdf_directory
        self.text_cleaner = TextCleaner()
        self.chunker = OptimalChunker(chunk_size=500, chunk_overlap=50)
        self.vector_store = VectorStoreManager()
    
    def process_all_pdfs(self):
        """Traite tous les PDFs et les indexe"""
        
        # 1. Extraction et Nettoyage (maintenant combinés)
        print(f"\n> Phase 1: Chargement et nettoyage des PDFs dans {self.pdf_directory}...")
        
        documents_lc = load_all_pdfs_with_langchain(self.pdf_directory) 
        # Application du nettoyage
        for d in documents_lc:
             d.page_content = self.text_cleaner.clean(d.page_content)
        
        print(f"   - {len(documents_lc)} pages chargées et nettoyées (Documents LangChain)")
        
        # 2. Chunking
        print("> Phase 2: Découpage en chunks...")
        all_chunks_lc = self.chunker.chunk_documents(documents_lc)
        print(f"   - {len(all_chunks_lc)} chunks créés au total")
        
        # 3. Indexation
        print("\n> Phase 3: Indexation dans FAISS...")
        
        # L'indexation FAISS crée les embeddings en interne
        self.vector_store.create_and_save_index(all_chunks_lc)
        
        if self.vector_store.vectorstore:
            print(f"\n Indexation terminée. Index sauvegardé localement.")
        else:
            print("\n Indexation échouée.")

