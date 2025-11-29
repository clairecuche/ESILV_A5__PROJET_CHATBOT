# rag/scraper/pdf_loader.py

import os
from pathlib import Path
from typing import List, Dict, Optional
import logging
from dataclasses import dataclass

# PDF processing with PyMuPDF
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """Structure pour stocker un document chargé"""
    content: str
    metadata: Dict
    source: str
    page_number: Optional[int] = None


class PDFLoader:
    """
    Classe pour charger et extraire le texte des PDFs avec PyMuPDF
    """
    
    def __init__(self):
        """Initialise le loader PDF"""
        pass
    
    
    def load_pdf(self, pdf_path: str) -> List[Document]:
        """Charge un PDF et extrait son contenu"""

        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        logger.info(f"Loading PDF: {pdf_path}")
        
        documents = []
        
        try:
            pdf_document = fitz.open(pdf_path)
            
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                text = page.get_text()
                
                # Extraction des métadonnées
                metadata = {
                    "source": pdf_path,
                    "page": page_num + 1,
                    "total_pages": len(pdf_document),
                    "file_name": Path(pdf_path).name
                }
                
                # Ajout des métadonnées du document (première page seulement)
                if page_num == 0 and pdf_document.metadata:
                    metadata.update({
                        "title": pdf_document.metadata.get("title", ""),
                        "author": pdf_document.metadata.get("author", ""),
                        "subject": pdf_document.metadata.get("subject", ""),
                        "creator": pdf_document.metadata.get("creator", "")
                    })
                
                if text.strip():  # Ignorer les pages vides
                    doc = Document(
                        content=text,
                        metadata=metadata,
                        source=pdf_path,
                        page_number=page_num + 1
                    )
                    documents.append(doc)
            
            pdf_document.close()
            logger.info(f"Extracted {len(documents)} pages from {pdf_path}")
            
        except Exception as e:
            logger.error(f"Error loading PDF: {e}")
            raise
        
        return documents
    
    
    def load_directory(self, directory_path: str) -> List[Document]:
        """Charge tous les PDFs d'un répertoire"""
        all_documents = []
        pdf_files = list(Path(directory_path).glob("**/*.pdf"))
        
        logger.info(f"Found {len(pdf_files)} PDF files in {directory_path}")
        
        for pdf_file in pdf_files:
            try:
                docs = self.load_pdf(str(pdf_file))
                all_documents.extend(docs)
            except Exception as e:
                logger.error(f"Failed to load {pdf_file}: {e}")
                continue
        
        logger.info(f"Total documents extracted: {len(all_documents)}")
        return all_documents


def main():
    """Exemple d'utilisation"""
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Exemple 1: Charger un seul PDF
    loader = PDFLoader()
    
    # Remplacer par votre chemin
    pdf_path = "data/pdf/Admission/Apprentissage.pdf"
    
    if os.path.exists(pdf_path):
        documents = loader.load_pdf(pdf_path)
        print(f"\nLoaded {len(documents)} pages")
        print(f"\nFirst page preview:\n{documents[1].content[:500]}...")
        print(f"\nMetadata: {documents[0].metadata}")
    
    # Exemple 2: Charger un répertoire complet
    directory_path = "data/pdf/Admission"
    
    if os.path.exists(directory_path):
        all_docs = loader.load_directory(directory_path)
        print(f"\nTotal documents from directory: {len(all_docs)}")
        print(f"\nFirst document preview:\n{all_docs[2].content[:500]}...")
        print(f"\nMetadata: {all_docs[0].metadata}")


if __name__ == "__main__":
    main()