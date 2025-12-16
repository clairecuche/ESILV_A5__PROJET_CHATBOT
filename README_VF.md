# Chatbot ESILV 🎓

## 🔎 Présentation

**Chatbot ESILV** est un assistant conversationnel conçu pour aider les futurs étudiants et visiteurs à obtenir des informations sur l'école ESILV : programmes, admissions, vie étudiante, contact, etc. Le projet combine :

- Une interface web en **Streamlit** (`app.py`) pour l'interaction utilisateur;
- Un cœur RAG (Retrieval-Augmented Generation) utilisant des documents indexés dans **FAISS** et un LLM local via **Ollama** pour fournir des réponses factuelles et sourcées;
- Un **système d'agents** (Routing / RAG / Formulaire / Interaction) pour gérer les intentions et les flux conversationnels;
- Des outils de scraping et d'indexation pour construire la base de connaissances (PDFs, pages web).

---

## ⚙️ Structure du projet

Arborescence clé :

- `app.py` — Interface Streamlit (UI, gestion des sessions, envoi de messages)
- `src/agents/` — Agents du système :
  - `agent_orchestrateur.py` (AgentSuperviseur) : routage et orchestration des agents
  - `agent_rag.py` : interface RAG (chargement index FAISS, génération)
  - `agent_formulaire.py` : collecte / validation / sauvegarde des contacts
  - `agent_interaction.py` : réponses conversationnelles générales
  - `state_manager.py` : gestion d'état par session
  - `prompts.py` : prompts système centralisés
- `src/rag/` — Pipeline RAG :
  - `document_processing/` : loaders, chunker, nettoyeurs
  - `generation/` : LLM (Ollama), retriever, pipeline RAG, indexing pipeline
  - `vectorstore/` : gestion FAISS via LangChain
- `data/` :
  - `pdf/` — PDFs sources
  - `scraping/` — résultats du scraper (ex: `esilv_scraped_*.json`)
  - `contacts/contacts.json` — registre sauvegardé des demandes de contact
- `vector_store_faiss/` — index FAISS sauvegardé
- `requirements.txt`, `setup.sh`, `README.md` (original), etc.

---

## 💾 Dépendances & Prérequis

- Python 3.10+ recommandé
- Dépendances Python listées dans `requirements.txt`
- Ollama (serveur LLM local) : https://ollama.ai
- Modèle Ollama recommandé : `gemma2:2b` (ou autre disponible)
- FAISS (cpu ou gpu selon l'environnement)

Installation rapide :

```bash
# Créer et activer un environnement Python
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1

# Installer les dépendances
pip install -r requirements.txt
```

Assurez-vous qu'Ollama est installé et lancé :

```bash
# Lancer le serveur Ollama
ollama serve
# Télécharger le modèle (exemple)
ollama pull gemma2:2b
```

Le script `setup.sh` automatise quelques vérifications et la création de dossiers.

---

## 🚀 Démarrage rapide

1. Indexer les documents (si vous n'avez pas encore d'index FAISS) :

```bash
# Indexe les PDFs et données web (par défaut: data/pdf et data/scraping)
python -m src.rag.main_rag_lang index
```

2. Lancer l'interface Streamlit :

```bash
streamlit run app.py
```

3. Optionnel : tester le RAG seul en mode CLI :

```bash
python -m src.rag.main_rag_lang chat
```

Voir également :

```bash
python -m src.rag.main_rag_lang stats  # stats index FAISS
```

---

## 🧭 Agents & orchestration 🔧

Le système est construit autour d'un petit ensemble d'agents coordonnés par l'**AgentSuperviseur**. Voici comment ils interagissent et quelles règles dirigent le routage :

### Flux d'un message (résumé)

1. L'utilisateur envoie un message via l'interface.
2. Le superviseur vérifie l'état de la session (par ex. formulaire en cours) et choisit l'agent le plus adapté.
3. L'agent sélectionné traite la demande :
   - **RAG** : recherche documentaire et réponse sourcée.
   - **Formulaire** : collecte et validation des coordonnées.
   - **Interaction** : salutations, clarifications et réponses courtes.
4. La réponse est renvoyée à l'utilisateur et l'historique de la session est mis à jour. Si nécessaire, le superviseur peut ensuite déclencher un autre agent (p.ex. lancer la collecte d'un contact).
---

### Agents (détails)

- **AgentSuperviseur** (`src/agents/agent_orchestrateur.py`)
  - Responsabilités : routing, orchestrer l'appel des agents, maintenir le LLM de routing (ChatOllama).
  - Méthodes clés : `detect_intent_with_llm`, `_fallback_keyword_routing`, `route()`, `run()`.
  - Règles importantes :
    - Priorité aux règles liées au formulaire (ex: `editing_field`, `awaiting_confirmation`, formulaire partiel).
    - Si `intent == "mixed"` : prioritise RAG puis déclenche proposition de collecte de contact.

- **Agent RAG** (`src/agents/agent_rag.py`) 
  - Responsabilités : charger l'index FAISS (`VectorStoreManager`), récupérer et reranker les chunks (`Retriever`), formater le contexte et générer la réponse via `RAGPipeline` + `OllamaLLM`.
  - Comportement MIXED : si l'intention est MIXED, renvoie la réponse RAG puis propose d'activer le formulaire pour la collecte des coordonnées.

- **Agent Formulaire** (`src/agents/agent_formulaire.py`)
  - Responsabilités : extraction d'informations (regex + heuristiques), validation des champs (email/téléphone), dialogue pour compléter les champs manquants, confirmation avant sauvegarde, enregistrement dans `data/contacts/contacts.json`.
  - États gérés : `awaiting_confirmation`, `editing_field`, `form_completed`. Vérifie `state_manager.is_form_active(session_id)` pour garder la continuité.
  - Flux : extraire → valider → demander champs manquants → demander confirmation → sauvegarder → réinitialiser.

- **Agent Interaction** (`src/agents/agent_interaction.py`) 💬
  - Responsabilités : salutations, remerciements, clarifications et réponses rapides pour phrases simples (mots-clés). Fallback quand la question n'est ni RAG ni Formulaire.

- **StateManager** (`src/agents/state_manager.py`) 🧾
  - Maintient un `ConversationState` par session (historique, `form_data`, flags, `current_agent`).
  - Méthodes clés : `get_or_create_session`, `update_form_data`, `add_to_history`, `is_form_active`, `get_session_summary`.

---

### Exemple de scénario (séquence)

- Utilisateur : "Parlez-moi du programme Data et appelez-moi"
- 1) Superviseur : `detect_intent_with_llm` → détecte `MIXED` (ou via fallback mots-clés)
- 2) Route vers **RAG** → RAG renvoie une réponse factuelle sourcée
- 3) Superviseur voit `MIXED` → active un formulaire partiel dans la session et envoie : "Puis-je prendre vos coordonnées ?"
- 4) **Agent Formulaire** prend la main, extrait/valide les champs, demande confirmations et sauvegarde le contact

---

### Notes d'implémentation importantes

- Le superviseur enregistre `current_agent` dans la session pour alimenter l'UI (suggestions contextuelles, affichage de l'agent actif).
- Le routing basé LLM apporte précision mais peut être lent ; le fallback mot-clé assure résilience.
- Toutes les modifications d'état passent par `StateManager` pour éviter des incohérences entre agents.

Cette section vise à clarifier le rôle de chaque agent, les règles qui gouvernent le routage et la façon dont une conversation évolue à travers le système.

---

## 🔍 Détails techniques & choix de conception

- RAG : chunking, embeddings (sentence-transformers) et FAISS pour retrieval rapide
- Retriever : reranking hybride (vector / lexical / density / length) pour sélectionner les meilleurs passages
- LLM : utilisation d'Ollama pour exécuter localement des modèles (ex: gemma2)
- Routing : LLM-based routing en priorité avec fallback mot-clé
- Formulaire : extraction robuste (regex + heuristiques), validation (emails/téléphones FR) et confirmations avant enregistrement
- Gestion des sources (Agent RAG) :
  - L'Agent RAG détecte les sources réellement citées par le LLM en recherchant des **citations explicites** de type `[1]`, `[2]`, etc. (implémenté dans `AgentRAG._extract_used_sources`).
  - Le pipeline RAG (`RAGPipeline.query`) renvoie une liste de sources avec métadonnées (`sources` contenant `source`, `page`, `final_score`, ...). La méthode `_format_sources_for_llm` formate ces éléments pour le prompt envoyé au LLM.
  - Après génération, l'Agent RAG :
    - nettoie la réponse (supprime les citations numériques et URLs intégrées),
    - filtre les sources pour ne **conserver que les URLs web valides** (`http://` / `https://`) et **exclure** les chemins de fichier locaux et les PDFs (pas d'affichage des chemins `data/` ou `.pdf`),
    - n'affiche la section "📚 Source(s)" qu'uniquement s'il y a des liens web pertinents ; sinon aucune source n'est présentée à l'utilisateur.
  - Cette stratégie évite d'exposer des chemins internes et favorise des références web vérifiables et pertinentes.

---

## 📁 Scripts & commandes utiles

- Scraper complet :
  - `python data/scrapper.py --full`  (scraping en profondeur)
  - `python data/scrapper.py` (mode rapide)
- Indexation :
  - `python -m src.rag.main_rag_lang index [pdf_dir] [web_dir]`  
    (Indexe les dossiers spécifiés pour les PDFs et le scraping)
  
  ### Détail de l'indexation :
  - Indexer par défaut (PDF et scraping) :
    ```bash
    python -m src.rag.main_rag_lang index
    ```
    Cette commande indexe les dossiers par défaut : `data/pdf` pour les fichiers PDF et `data/scraping` pour les données de scraping.
    
  - Indexer seulement un dossier PDF personnalisé (le dossier de scraping sera par défaut `data/autres`) :
    ```bash
    python -m src.rag.main_rag_lang index ./mes_pdfs
    ```
    Ici, le dossier `./mes_pdfs` contient tes fichiers PDF.

  - Indexer avec deux dossiers personnalisés (un pour les PDFs et un pour le scraping) :
    ```bash
    python -m src.rag.main_rag_lang index ./mes_pdfs ./mon_scraping
    ```
    Cette commande permet de spécifier un dossier pour les fichiers PDF (`./mes_pdfs`) et un autre pour les données issues du scraping (`./mon_scraping`).

- RAG Chat CLI :
  - `python -m src.rag.main_rag_lang chat`
- Voir stats FAISS :
  - `python -m src.rag.main_rag_lang stats`
- Lancer l'app UI :
  - `streamlit run app.py`
- Installer dépendances :
  - `pip install -r requirements.txt`

---

## ✅ Bonnes pratiques & troubleshooting

- Si `AgentRAG` indique que l'index est manquant → exécutez l'indexation puis relancez l'agent
- Vérifiez qu'Ollama est accessible sur `http://localhost:11434` et que le modèle souhaité est téléchargé
- FAISS : si un GPU est disponible, installez `faiss-gpu` et ajustez les dépendances
- Sauvegarde des contacts : `data/contacts/contacts.json`

---

## 🛠️ Pour les développeurs

- Ajouter / modifier prompts : `src/agents/prompts.py`
- Ajouter sources pour le RAG : déposer PDFs dans `data/pdf/` ou générer via `data/scraping/`
- Pour améliorer la retrieval : ajuster les poids dans `Retriever` ou la taille de `top_k` / `final_k`
- Tests rapides : certains modules incluent des blocs `if __name__ == "__main__"` pour vérifications locales

