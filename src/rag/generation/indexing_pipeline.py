from src.rag.document_processing.pdf_loader import PDFLoader
from src.rag.document_processing.chunker import OptimalChunker
from src.rag.document_processing.text_cleaner import TextCleaner

from src.rag.embeddings.embeddings_generator import EmbeddingsGenerator
from src.rag.vectorstore.vector_store import VectorStore

from pathlib import Path

class IndexingPipeline:
    def __init__(self, pdf_directory: str):
        self.pdf_directory = pdf_directory
        self.pdf_loader = PDFLoader()
        self.text_cleaner = TextCleaner()
        self.chunker = OptimalChunker(chunk_size=500, chunk_overlap=50)
        self.embeddings_gen = EmbeddingsGenerator()
        self.vector_store = VectorStore()
    
    def process_all_pdfs(self):
        """Traite tous les PDFs et les indexe"""
        pdf_files = list(Path(self.pdf_directory).glob("*.pdf"))
        print(f" {len(pdf_files)} PDFs trouvés")
        
        all_chunks = []
        all_metadatas = []
        
        for pdf_path in pdf_files:
            print(f"\n🔄 Traitement : {pdf_path.name}")
            
            # 1. Extraction (per-page Documents)
            documents = self.pdf_loader.load_pdf(str(pdf_path))

            # 2. Nettoyage - appliquer au contenu de chaque Document
            for d in documents:
                d.content = self.text_cleaner.clean(d.content)

            # 3. Chunking - chunker works on Document objects
            chunks = self.chunker.chunk_documents(documents)
            
            # 4. Métadonnées
            metadatas = [c.metadata for c in chunks]
            
            all_chunks.extend([c.content for c in chunks])
            all_metadatas.extend(metadatas)
            print(f"   ✓ {len(chunks)} chunks créés")
        
        # 5. Génération embeddings
        print(f"\n Génération des embeddings pour {len(all_chunks)} chunks...")
        embeddings = self.embeddings_gen.generate_embeddings(all_chunks)
        
        # 6. Indexation
        print(f" Indexation dans la base vectorielle...")
        self.vector_store.add_documents(all_chunks, embeddings, all_metadatas)
        
        print(f"\n Indexation terminée : {self.vector_store.get_collection_stats()} documents")

# Utilisation
if __name__ == "__main__":
    pipeline = IndexingPipeline(pdf_directory="./data/brochures_esilv")
    pipeline.process_all_pdfs()