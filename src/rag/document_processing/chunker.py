# rag/preprocessing/chunker.py

from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
# Import the Document dataclass from the local pdf_loader module.
# Support three invocation modes:
#  - running as a package (python -m rag.document_processing.chunker)
#  - running the module directly as a script (python chunker.py)
#  - running as a top-level package when `rag` is on sys.path
try:
    # Preferred: relative import inside package
    from .pdf_loader import Document
except Exception:
    try:
        # Fallback: local import when running the script directly
        from pdf_loader import Document
    except Exception:
        # Final fallback: absolute package import if rag is on PYTHONPATH
        from rag.document_processing.pdf_loader import Document


class OptimalChunker:
    """
    Chunker optimisé pour chatbot RAG
    Base sur recherches académiques et best practices
    """
    
    def __init__(
        self,
        chunk_size: int = 512,      # en tokens
        chunk_overlap: int = 128,   # 25% overlap
        model_name: str = "gpt-3.5-turbo"  # pour compter tokens
    ):
        """
        Args:
            chunk_size: Taille cible en tokens
            chunk_overlap: Overlap en tokens
            model_name: Modèle pour tokenization
        """
        # Approximation: 1 token ≈ 4 caractères en moyenne
        self.chunk_size_chars = chunk_size * 4
        self.overlap_chars = chunk_overlap * 4
        
        # Splitter avec séparateurs hiérarchiques
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
            keep_separator=True
        )
    
    def chunk_document(self, document: Document) -> List[Document]:
        """
        Découpe un document en chunks optimaux
        
        Args:
            document: Document à chunker
            
        Returns:
            Liste de chunks (Documents)
        """
        # Découper le texte (sécuriser si content est None)
        text_to_split = document.content or ""
        text_chunks = self.text_splitter.split_text(text_to_split)
        
        # Créer les documents
        chunks = []
        for i, chunk_text in enumerate(text_chunks):
            chunk_metadata = document.metadata.copy()
            chunk_metadata.update({
                'chunk_id': i,
                'chunk_index': i,
                'total_chunks': len(text_chunks),
                'chunk_size': len(chunk_text),
                'chunk_tokens_approx': len(chunk_text) // 4
            })
            
            chunk = Document(
                content=chunk_text,
                metadata=chunk_metadata,
                source=document.source,
                page_number=document.page_number
            )
            chunks.append(chunk)
        
        return chunks
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """Chunke une liste de documents"""
        all_chunks = []
        for doc in documents:
            chunks = self.chunk_document(doc)
            all_chunks.extend(chunks)
        return all_chunks
    
# test_chunker_main.py
def main():
    # Exemple de texte brut avec un tableau "linéarisé" comme ton PDF
    sample_text =  """
Titre du Document : Test Chunker

Introduction
-------------
Durant leur scolarité, les étudiants disposent d'un espace de stockage et de partage
sur Onedrive de 1 To. L'association étudiante "DigiTeam" a un partenariat avec
le fabricant MSI permettant des tarifs préférentiels.

Tableau Équipement :
Configuration « confort »   Configuration minimale
Processeur Intel i7 (11e génération ou plus)   Processeur Intel i5 (8e génération ou plus)
Mémoire RAM 32 Go   Mémoire RAM 16 Go
Stockage 512 Go SSD + 1To SATA   Stockage 512 Go
Carte graphique dédiée 4Go   Écran 15" HD
Écran 15" HD   Caméra
Wifi 802.11 g,ac Dual Band

Liste à puces :
- Installation de logiciels essentiels
- Accès aux plateformes pédagogiques
- Suivi des projets collaboratifs

Paragraphe long :
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut 
labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris 
nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit 
esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in 
culpa qui officia deserunt mollit anim id est laborum.

Numérotation :
1. Première étape : préparation du poste
2. Deuxième étape : configuration des accès
3. Troisième étape : vérification des permissions
4. Quatrième étape : finalisation du setup

Section finale :
Ce document sert à tester la robustesse du chunker, notamment sur des textes longs, 
des tableaux linéarisés, des listes et des paragraphes complexes. 
Les sauts de ligne irréguliers et les sections multiples doivent être gérés correctement.
"""

    # Document artificiel
    doc = Document(
        content=sample_text,
        metadata={"source": "test", "page": 1},
        source="generated",
        page_number=1
    )

    # Initialiser le chunker
    chunker = OptimalChunker(
        chunk_size=128,     # petits chunks pour voir la découpe
        chunk_overlap=32
    )

    # Chunker le document
    chunks = chunker.chunk_document(doc)

    print(f"\nNombre total de chunks générés : {len(chunks)}\n")
    print("-----------------------------------------------\n")

    # Afficher les chunks
    for i, c in enumerate(chunks):
        print(f"--- Chunk {i} ---")
        print(f"Longueur (chars) : {len(c.content)}")
        print("Contenu :")
        print(c.content)
        print("Metadata :", c.metadata)
        print("-----------------------------------------------\n")


if __name__ == "__main__":
    main()
