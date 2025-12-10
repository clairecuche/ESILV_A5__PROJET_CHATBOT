from src.rag.document_processing.pdf_loader_lang import load_all_pdfs_with_langchain 
from src.rag.document_processing.chunker_lang import OptimalChunker
from src.rag.document_processing.text_cleaner import TextCleaner

from src.rag.vectorstore.vector_store_lang import VectorStoreManager # Votre nouvelle classe FAISS
from src.rag.document_processing.web_scrapper_loader import WebScraperLoader
from pathlib import Path
from typing import List

class IndexingPipeline:
    def __init__(self, pdf_directory: str, web_data_directory: str = "data/scraping"):
        self.pdf_directory = pdf_directory
        self.web_data_directory = web_data_directory
        self.web_loader = WebScraperLoader(data_folder=web_data_directory)
        self.text_cleaner = TextCleaner()
        self.chunker = OptimalChunker(chunk_size=500, chunk_overlap=50)
        self.vector_store = VectorStoreManager()
    
    def process_all_pdfs1(self):
        """Traite tous les PDFs et les indexe"""
        
        # 1. Extraction et Nettoyage (maintenant combinés)
        print(f"\n> Phase 1: Chargement et nettoyage des PDFs dans {self.pdf_directory}...")
        
        documents_lc = load_all_pdfs_with_langchain(self.pdf_directory) 
        # Application du nettoyage
        for d in documents_lc:
             d.page_content = self.text_cleaner.clean(d.page_content)
        
    def run_indexing(self):
        """Traite tous les PDFs et données web, puis les indexe"""
        
        all_documents_lc = []
        
        # 1. CHARGEMENT DES PDFs
        print(f"\n> Phase 1a: Chargement et nettoyage des PDFs dans {self.pdf_directory}...")
        
        pdf_documents_lc = load_all_pdfs_with_langchain(self.pdf_directory)
        
        # Nettoyage des PDFs
        for doc in pdf_documents_lc:
            doc.page_content = self.text_cleaner.clean(doc.page_content)
        
        print(f"   - {len(pdf_documents_lc)} pages PDF chargées et nettoyées")
        all_documents_lc.extend(pdf_documents_lc)
        
        # 2. CHARGEMENT DES DONNÉES WEB SCRAPÉES 
        print(f"\n> Phase 1b: Chargement des données web scrapées dans {self.web_data_directory}...")
        
        web_documents_lc = self.web_loader.load_all_scraped_data()
        
        # Nettoyage des données web
        for doc in web_documents_lc:
            doc.page_content = self.text_cleaner.clean(doc.page_content)
        
        print(f"   - {len(web_documents_lc)} pages web chargées et nettoyées")
        all_documents_lc.extend(web_documents_lc)
        
        # RÉSUMÉ DU CHARGEMENT
        print(f"\n> Total documents chargés: {len(all_documents_lc)}")
        print(f"   - PDFs: {len(pdf_documents_lc)}")
        print(f"   - Web: {len(web_documents_lc)}")
        
        # 3. CHUNKING
        print("\n> Phase 2: Découpage en chunks...")
        all_chunks_lc = self.chunker.chunk_documents(all_documents_lc)
        print(f"   - {len(all_chunks_lc)} chunks créés au total")
        
        # STATISTIQUES PAR TYPE
        pdf_chunks = [c for c in all_chunks_lc if c.metadata.get('type') != 'web_scraped']
        web_chunks = [c for c in all_chunks_lc if c.metadata.get('type') == 'web_scraped']
        print(f"   - Chunks PDF: {len(pdf_chunks)}")
        print(f"   - Chunks Web: {len(web_chunks)}")
        
        # 4. INDEXATION FAISS
        print("\n> Phase 3: Indexation dans FAISS...")
        
        self.vector_store.create_and_save_index(all_chunks_lc)
        
        if self.vector_store.vectorstore:
            print(f"\nIndexation terminée. Index FAISS sauvegardé localement.")
            print(f"  Total chunks indexés: {len(all_chunks_lc)}")
        else:
            print("\n Indexation échouée.")
