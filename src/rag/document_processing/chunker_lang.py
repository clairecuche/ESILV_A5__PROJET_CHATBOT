from typing import List
import re
import math

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document 
from pathlib import Path

class OptimalChunker:
    """
    Chunker optimisé pour chatbot RAG.
    Utilise RecursiveCharacterTextSplitter de LangChain pour une découpe intelligente.
    """
    
    def __init__(
        self,
        chunk_size: int = 512,      # Taille cible en tokens
        chunk_overlap: int = 128,   # Overlap en tokens 
    ):

        self.chunk_size_chars = chunk_size * 4
        self.overlap_chars = chunk_overlap * 4
        
        # Utilisation du RecursiveCharacterTextSplitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size_chars,
            chunk_overlap=self.overlap_chars,
            length_function=len,
            separators=[
                "\n\n",      # Paragraphes
                "\n",        # Lignes
                ". ",        # Phrases
                "! ",
                "? ",
                "; ",
                ", ",
                " ",         # Mots
                ""           # Caractères
            ],
            # Conserver le séparateur peut aider le LLM à comprendre la structure
            keep_separator=False 
        )

    def chunk_document(self, document: Document) -> List[Document]:
        """
        Découpe un seul Document LangChain en chunks optimaux.
        Args:
            document: Document LangChain (une page de PDF) à découper.
        Returns:
            Liste de chunks (Documents LangChain).
        """
        chunks = self.text_splitter.split_documents([document])
        
        # Mettre à jour les métadonnées avec les infos de chunking
        total_chunks = len(chunks)
        for i, chunk in enumerate(chunks):
            # Calcul approximatif des tokens
            chunk_len = len(chunk.page_content)
            tokens_approx = math.ceil(chunk_len / 4)
            
            chunk.metadata.update({
                'chunk_id': f"{Path(document.metadata.get('source', 'unknown')).name}-{document.metadata.get('page', 0)}-{i}",
                'chunk_index': i,
                'total_chunks': total_chunks,
                'chunk_size_chars': chunk_len,
                'chunk_tokens_approx': tokens_approx
            })
            chunk.page_content = chunk.page_content.replace('content', 'page_content')
            
        return chunks
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """Chunke une liste de documents LangChain."""
        all_chunks = []
        for doc in documents:
            chunks = self.chunk_document(doc)
            all_chunks.extend(chunks)
        return all_chunks

