# rag/document_processing/pdf_loader.py

import os
from pathlib import Path
from typing import List, Dict, Optional
import logging
from dataclasses import dataclass

from pypdf import PdfReader

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
    Classe pour charger et extraire le texte des PDFs avec pypdf
    """
    
    def __init__(self):
        """Initialise le loader PDF"""
        pass
    
    
    def load_pdf(self, pdf_path: str) -> List[Document]:
        """Charge un PDF et extrait son contenu ainsi que ses métadonnées"""

        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        logger.info(f"Loading PDF: {pdf_path}")
        
        documents = []
        
        try:
            reader = PdfReader(pdf_path)
            num_pages = len(reader.pages)
            
            # Extract overall PDF metadata once
            pdf_info = reader.metadata
            general_metadata = {
                "title": pdf_info.get("/Title", ""),
                "author": pdf_info.get("/Author", ""),
                "subject": pdf_info.get("/Subject", ""),
                "creator": pdf_info.get("/Creator", ""),
                "producer": pdf_info.get("/Producer", ""),
                "creation_date": pdf_info.get("/CreationDate", ""),
                "mod_date": pdf_info.get("/ModDate", ""),
            }
            
            for page_num in range(num_pages):
                page = reader.pages[page_num]
                text = page.extract_text()

                # Extraction simple de tableau
                if text:
                    text = self.extract_tables_from_text(text)
                
                # Metadata for the current page
                page_metadata = {
                    "source": pdf_path,
                    "page": page_num + 1,
                    "total_pages": num_pages,
                    "file_name": Path(pdf_path).name
                }
                
                # Combine general PDF metadata with page-specific metadata
                page_metadata.update(general_metadata)
                
                documents.append(
                    Document(
                        content=text,
                        metadata=page_metadata,
                        source=pdf_path,
                        page_number=page_num + 1
                    )
                )
            
            return documents
            
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}")
            return []
    
    
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
        
        logger.info(f"Total documents extracted (nb page): {len(all_documents)}")
        return all_documents
    
    def extract_tables_from_text(self, text: str) -> str:
        """
        Version simplifiée : détecte et reformate les tableaux basiques
        
        Détecte les lignes avec multiple espaces (colonnes) et les reformate
        avec des séparateurs "|" clairs.
        """
        import re
        
        lines = text.split('\n')
        result = []
        
        for line in lines:
            # Détecter si c'est une ligne de tableau
            # (au moins 2 séparations de 3+ espaces)
            if re.findall(r'\s{3,}', line) and len(re.findall(r'\s{3,}', line)) >= 2:
                # Remplacer espaces multiples par " | "
                formatted = re.sub(r'\s{3,}', ' | ', line.strip())
                result.append(formatted)
            else:
                result.append(line)
        
        return '\n'.join(result)


def main():
    """Exemple d'utilisation"""
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Exemple 1: Charger un seul PDF
    loader = PDFLoader()
    pdf_path = "data\pdf\Autres\Contact_scolarite.pdf"
    
    if os.path.exists(pdf_path):
        documents = loader.load_pdf(pdf_path)
        print(f"\nLoaded {len(documents)} pages")
        print(f"\nFirst page preview:\n{documents[0].content[:2000]}...")
        print(f"\nMetadata: {documents[0].metadata}")
    
    # Exemple 2: Charger un répertoire complet
    directory_path = "data/pdf/Programmes"
    
    if os.path.exists(directory_path):
        all_docs = loader.load_directory(directory_path)
        print(f"\nTotal documents from directory: {len(all_docs)}")
        print(f"\nFirst document preview:\n{all_docs[0].content[:500]}...")
        print(f"\nMetadata: {all_docs[0].metadata}")


if __name__ == "__main__":
    main()