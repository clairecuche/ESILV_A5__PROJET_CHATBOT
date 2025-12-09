import os
import logging
from pathlib import Path
from typing import List

from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


def load_all_pdfs_with_langchain(directory_path: str) -> List[Document]:
    """
    Charge tous les PDFs d'un répertoire en utilisant LangChain's DirectoryLoader
    et PyPDFLoader.
    Args:
        directory_path: Chemin du répertoire contenant les fichiers PDF.
    Returns:
        Une liste d'objets Document de LangChain, où chaque élément
        représente généralement une page de PDF.
    """
    if not os.path.isdir(directory_path):
        logger.warning(f"Directory not found: {directory_path}. Returning empty list.")
        return []

    logger.info(f"Using DirectoryLoader to find and load PDFs from: {directory_path}")
    
    # 1. Créer le DirectoryLoader
    loader = DirectoryLoader(
        path=directory_path, 
        glob="**/*.pdf", #trouve tous les PDFs dans le répertoire et ses sous-répertoires
        loader_cls=PyPDFLoader #spécifie le loader à utiliser pour chaque fichier
    )
    
    # 2. Charger les documents
    docs = loader.load()
    
    logger.info(f"Total documents (pages) loaded: {len(docs)}")
    
    return docs
