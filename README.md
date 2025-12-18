# 🤖 Intelligent Chatbot ESILV - RAG & Form

This project is an intelligent chatbot developed as part of the AI & Data major at ESILV. It combines the power of a local language model (Ollama) with a document knowledge base (RAG) and a data collection system (Form Agent).

## 🌟 Features

* **Intelligent Orchestrator**: Analyzes the user's intent to route to the appropriate agent.
* **RAG Agent (Retrieval Augmented Generation)**: Answers specific questions about ESILV using a FAISS vector database (indexed PDFs).
* **Form Agent**: Collects contact information conversationally and stores it locally.
* **Web Interface**: Modern and responsive chat in HTML/CSS/JS.
* **Fully Local**: Privacy-respecting, no data is sent to the cloud (uses Ollama).

## 🏗️ Technical Architecture

The project is fully containerized with Docker to ensure a smooth installation.

* **Backend**: Flask (Python 3.10)
* **LLM**: Ollama (Default model: gemma2:2b)
* **Vector Store**: FAISS with sentence-transformers embeddings
* **AI Framework**: LangChain
* **Frontend**: HTML5 / CSS3 / JavaScript (Fetch API)

## 🚀 Installation and Startup

### 1. Prerequisites

* Docker Desktop installed and running.
* Ollama installed on your machine (Windows/Mac/Linux).
* Download the required model:

```bash
ollama pull gemma2:2b
```

### 2. Ollama Configuration

For Docker to communicate with Ollama on your host machine, make sure Ollama allows external connections (default on Windows). The project uses the address [http://host.docker.internal:11434](http://host.docker.internal:11434).

### 3. Launching the Project

Clone the repository, navigate to the root, and run:

```bash
docker-compose up --build -d
```

The first build may take a long time (around 20-40 min) as it downloads heavy computation libraries (PyTorch, NVIDIA).

### 4. Access

* **Chatbot**: Open the `index.html` file in your browser.
* **API Healthcheck**: [http://localhost:5000/api/health](http://localhost:5000/api/health)

## 🛠️ Useful Commands (Maintenance)

| Action                          | Command                             |
| ------------------------------- | ------------------------------------ |
| Launch the application          | `docker-compose up -d`               |
| Stop the application            | `docker-compose down`                |
| View logs (AI Engine)           | `docker logs -f esilv-chatbot-api`  |
| Restart after code changes      | `docker-compose restart chatbot-api`|
| Update dependencies             | `docker-compose up --build -d`       |

## 📁 Project Structure

```plaintext
.
├── src/
│   ├── agents/          # Agent logic (Orchestrator, RAG, Form)
│   └── rag/             # Document processing pipeline and FAISS
├── data/
│   ├── contacts/        # Storage of JSON files (Saved contacts)
│   ├── pdf/             # Source documents (Official PDFs)
│   └── pdfs/            # Source documents (From scraping)
├── vector_store_faiss/  # Generated vector index
├── app_streamlit_V1/    # Version 1 of the interface (Archive)
├── chatbot.py           # Flask API entry point
├── index.html           # User interface (Front-end)
├── Dockerfile           # Docker image configuration
├── docker-compose.yml   # Container and volume orchestration
├── Readme.md            # Project documentation
└── requirements.txt     # Python dependencies (Pinned)

```

## 📝 Usage

* Question about the school: "What are the tuition fees?" → The RAG agent will answer.
* Contact: "I want to register" → The Form agent will take over.
* Data verification: Contacts are saved in `data/contacts/contacts.json`.

## ⚠️ Important Notes

* **RAM**: Docker and Ollama consume a significant amount of memory. At least 16 GB of RAM is recommended.
* **Docker Volume**: Contact data and the FAISS index are persistent thanks to Docker volumes; they are not deleted when the container stops.

Author: [Claire CUCHE and Inès DARDE] - ESILV A5 DIA2

