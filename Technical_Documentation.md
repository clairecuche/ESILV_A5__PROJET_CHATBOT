# Presentation – Multi‑Agent System

## 🔎 General Overview

**Chatbot ESILV** is an advanced conversational ecosystem designed to guide prospective students. Unlike a classic linear chatbot, it relies on a **multi‑agent architecture** capable of dynamically switching between:

* **Document retrieval** via a **RAG (Retrieval Augmented Generation)** pipeline;
* **Business process management**, including **contact collection** through a conversational form.

This approach enables more natural, contextual, and action-oriented conversations.

---

## ⚙️ Project Structure

### Main Tree

* `app.py` — Streamlit interface (UI, session management, message sending)

* `src/agents/` — System agents:

  * `agent_orchestrateur.py` (**AgentSupervisor**) : routing and global orchestration
  * `agent_rag.py` : RAG interface (FAISS, retrieval, generation)
  * `agent_formulaire.py` : contact collection, validation, and storage
  * `agent_interaction.py` : general conversational responses
  * `state_manager.py` : session state management
  * `prompts.py` : centralized system prompts

* `src/rag/` — RAG pipeline:

  * `document_processing/` : loaders, chunking, cleaning
  * `generation/` : LLM (Ollama), retriever, RAG pipeline, indexing
  * `vectorstore/` : FAISS management via LangChain

* `data/`:

  * `pdf/` — source PDFs
  * `scraping/` — scraper results (e.g., `esilv_scraped_*.json`)
  * `contacts/contacts.json` — contact request registry

* `vector_store_faiss/` — persisted FAISS index

* `requirements.txt`, `setup.sh`, `README.md`, etc.

---

## 🧭 Agents & Orchestration

The system relies on a small set of specialized agents, **coordinated by the AgentSupervisor**, ensuring conversation coherence.

### 🔁 Global Message Flow

1. The user sends a message via the interface.
2. The **Supervisor** analyzes the session state (active form, history, context).
3. It selects the most relevant agent.
4. The agent handles the request:

   * **RAG**: document retrieval and contextualized response.
   * **Form**: information collection and validation.
   * **Interaction**: simple replies, greetings, clarifications.
5. The response is returned and the session state is updated.

---

## 🤖 Agent Details

### 🧠 AgentSupervisor

`src/agents/agent_orchestrateur.py`

* **Role**: routing, orchestration, and overall supervision
* **Key methods**:

  * `detect_intent_with_llm`
  * `_fallback_keyword_routing`
  * `route()` / `run()`
* **Priority rules**:

  * Active form states (`editing_field`, `awaiting_confirmation`, etc.)
  * `MIXED` intent → RAG response followed by a contact collection proposal

---

### 📚 RAG Agent

`src/agents/agent_rag.py`

* Loading and managing the FAISS index (`VectorStoreManager`)
* Retrieval, reranking, and generation via `RAGPipeline` + `OllamaLLM`
* **MIXED mode**:

  * provides factual response
  * then triggers the form proposal

---

### 📝 Form Agent

`src/agents/agent_formulaire.py`

* Information extraction (regex + heuristics)
* Field validation (email, FR phone)
* Progressive dialogue to complete missing fields
* Explicit confirmation before saving
* Storage in `data/contacts/contacts.json`

**Managed states**:

* `editing_field`
* `awaiting_confirmation`
* `form_completed`

Flow: **extract → validate → complete → confirm → save → reset**

---

### 💬 Interaction Agent

`src/agents/agent_interaction.py`

* Greetings and thanks
* Short responses and clarifications
* Fallback agent when the request is neither RAG nor Form

---

### 🧾 StateManager

`src/agents/state_manager.py`

* Maintains a `ConversationState` per session
* Stores: history, form data, active agent
* Key methods:

  * `get_or_create_session`
  * `update_form_data`
  * `add_to_history`
  * `is_form_active`
  * `get_session_summary`

---

## 🔁 Example Scenario

**User**: "Tell me about the Data program and call me"

1. Intent detection → `MIXED`
2. Routing to **RAG Agent** → sourced response
3. Form activated by Supervisor
4. **Form Agent** collects, validates, and saves contact info

---

## 🔍 Technical Choices & Design

* **RAG**: chunking + `sentence-transformers` embeddings + FAISS
* **Retriever**: hybrid reranking (vector, lexical, density, length)
* **LLM**: Ollama (e.g., `gemma2`) locally
* **Routing**: LLM priority, keyword fallback
* **Form**: robust extraction, strong validation, user confirmation

### 📚 Source Management (RAG Agent)

* Detect explicit citations (`[1]`, `[2]`, …)
* Post-generation cleaning: remove numeric citations and internal URLs
* Filtering:

  * keep **only** valid web URLs (`http(s)://`)
  * exclude local paths (`data/`, `.pdf`)
* Display **📚 Source(s)** section only if relevant

This strategy avoids exposing internal paths and favors verifiable references.

---

## 📁 Useful Scripts & Commands

### Scraping

* Full scraping:

  ```bash
  python data/scrapper.py --full


* Quick Mode:

  ```bash
  python data/scrapper.py
  ```

### RAG Indexing

* Default indexing (PDF + scraping) :

  ```bash
  python -m src.rag.main_rag_lang index
  ```

* Index a custom PDF folder :

  ```bash
  python -m src.rag.main_rag_lang index ./mes_pdfs
  ```

* Index two custom folders:

  ```bash
  python -m src.rag.main_rag_lang index ./mes_pdfs ./mon_scraping
  ```

### Other Commands

* RAG chat in CLI :

  ```bash
  python -m src.rag.main_rag_lang chat
  ```
* FAISS statistics :

  ```bash
  python -m src.rag.main_rag_lang stats
  ```
* Lauch the UI :

  Via docker, see README.md

* Installer les dépendances :

  ```bash
  pip install -r requirements.txt
  ```

---

## 🛠️ For developers

* Prompts : `src/agents/prompts.py`
* Add RAG sources: `data/pdf/` ou `data/scraping/`
* Improve retrieval : ajust `Retriever` weights, `top_k`, `final_k`
* Local Tests :  `if __name__ == "__main__"` blocks available in some modules
