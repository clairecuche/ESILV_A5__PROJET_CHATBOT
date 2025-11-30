# agent_rag.py
from ollama import Client

client = Client()

class AgentRAG:
    def __init__(self):
        self.model = "mistral"

    def rag_search(self, query: str):
        # Placeholder, your friend will implement real RAG
        return ["Document1: ...", "Document2: ..."]

    def run(self, user_message: str):
        docs = self.rag_search(user_message)
        prompt = f"Tu es l'agent RAG. Utilise uniquement ces documents: {docs}. Question: {user_message}"
        response = client.generate(model=self.model, prompt=prompt)
        return response["response"]
