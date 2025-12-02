# agent_interaction.py
from ollama import Client
import logging

logger = logging.getLogger(__name__)
client = Client()

class AgentInteraction:
    def __init__(self):
        self.model = "mistral"

    def run(self, message: str):
        prompt = f"Tu es l'agent d'interaction. Reformule, clarifie et détecte l'intention. Texte: {message}"
        response = client.generate(model=self.model, prompt=prompt)
        return response["response"]
