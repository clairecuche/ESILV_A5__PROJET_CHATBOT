# ESILV_A5__PROJET_CHATBOT

<<<<<<< HEAD
Pour scrapper : 
    - Scrapping rapide : python scrapper.py
    - Scrapping complet : python scrapper.py --full

Pour lancer le front : 
    - streamlit run app.py
=======

## Partie RAG : 
1. Installer les dépendances
pip install -r requirements.txt

2. Installer et démarrer Ollama
Téléchargez depuis: https://ollama.ai
ollama serve

Dans un autre terminal:
ollama pull gemma

3. Indexer vos PDFs ESILV
python -m src.rag.main_rag_lang index ./data/pdf/

4. Lancer le chatBot
python -m src.rag.main_rag_lang chat

5. Stats doc
python -m src.rag.main_rag_lang stats


## Structure clé du projet (important files)
- `src/rag/main_rag_lang.py` — point d’entrée CLI (commandes : `index`, `chat`, `stats`).
- `src/rag/generation/indexing_pipeline_lang.py` — Orchestrateur : charge les documents, nettoie, chunke, génère les embeddings et indexe dans la base vectorielle.
- `src/rag/document_processing/pdf_loader_lang.py` — Loader PDF (extraction du texte, retourne des `Document` compatibles LangChain).
- `src/rag/document_processing/text_cleaner.py` — Nettoyage et normalisation du texte extrait.
- `src/rag/document_processing/chunker_lang.py` — Chunker optimisé (basé sur les splitters LangChain) pour produire des passages à indexer.
- `src/rag/embeddings/embeddings_generator_lang.py` — Génération des embeddings (p.ex. SentenceTransformers / HuggingFace).
- `src/rag/vectorstore/vector_store_lang.py` — Interface pour le stockage vectoriel (FAISS/Chroma, adaptation selon configuration).
- `src/rag/generation/retriever_lang.py` — Logique de récupération des passages pertinents depuis la base vectorielle.
- `src/rag/generation/llm_handler.py` — Gestionnaire LLM (ex. Ollama) pour interroger et formater les réponses.
- `src/rag/generation/rag_pipeline.py` — Pipeline RAG combinant `Retriever` + `LLM` pour exécuter une requête complète.
- `requirements.txt` — Liste des dépendances principales (vérifiez `pypdf`, `sentence-transformers`, `faiss-cpu`, `langchain`, etc.)
<     ```

- **Commandes utiles (récapitulatif)**
  - Indexer les PDFs :
    ```powershell
    python -m src.rag.main_rag_lang index ./data/pdf/
    ```
  - Lancer le chat :
    ```powershell
    python -m src.rag.main_rag_lang chat
    ```


>>>>>>> origin/rag
