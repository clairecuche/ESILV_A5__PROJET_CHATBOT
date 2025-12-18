import os
import logging
from pathlib import Path
from typing import List

from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

import os
import logging
from pathlib import Path
from typing import List

from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_core.documents import Document as LCDocument # Renommé pour plus de clarté

logger = logging.getLogger(__name__)


class PDFLoader:
    """
    Charge tous les fichiers PDF d'un répertoire en utilisant LangChain's DirectoryLoader
    et PyPDFLoader. Chaque Document de LangChain représente généralement une page de PDF.
    """
    
    def __init__(self, directory_path: str = "data/pdf"):
        """
        Initialise le chargeur de PDF.
        Args:
            directory_path: Chemin du répertoire contenant les fichiers PDF.
        """
        self.directory_path = directory_path
        self.loader = None

    def load_all_pdfs(self) -> List[LCDocument]:
        """
        Charge tous les PDFs d'un répertoire en utilisant LangChain's DirectoryLoader
        et PyPDFLoader.
        Args:
            directory_path: Chemin du répertoire contenant les fichiers PDF.
        Returns:
            Une liste d'objets Document de LangChain, où chaque élément
            représente généralement une page de PDF.
        """
        if not os.path.isdir(self.directory_path):
            logger.warning(f"Directory not found: {self.directory_path}. Returning empty list.")
            return []

        logger.info(f"Using DirectoryLoader to find and load PDFs from: {self.directory_path}")
        
        # 1. Créer le DirectoryLoader
        # Il est créé ici pour s'assurer que le chemin est correct et actuel
        self.loader = DirectoryLoader(
            path=self.directory_path, 
            glob="**/*.pdf", # Trouve tous les PDFs dans le répertoire et ses sous-répertoires
            loader_cls=PyPDFLoader # Spécifie le loader à utiliser pour chaque fichier
        )
        
        # 2. Charger les documents
        docs = self.loader.load()
        
        logger.info(f" Total documents (pages) loaded: {len(docs)}")
                    
        return docs