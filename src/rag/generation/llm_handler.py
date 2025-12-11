import requests
import json

class OllamaLLM:
    """
    Interface pour communiquer avec Ollama
    """
    
    def __init__(
        self,
        model: str = "gemma2:2b",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.3,
        max_tokens: int = 1000
    ):
        """
        Args:
            model: Modèle Ollama (mistral, llama3, gemma, etc.)
            base_url: URL de l'API Ollama
            temperature: Créativité (0-1, bas = factuel)
            max_tokens: Longueur max de la réponse
        """
        self.model = model
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Vérifier qu'Ollama est running
        self._check_ollama_status()
    
    def _check_ollama_status(self):
        """Vérifie qu'Ollama est accessible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                available_models = [m['name'] for m in response.json().get('models', [])]
                print(f"   Ollama connecté. Modèles disponibles: {available_models}")
                
                if self.model not in available_models:
                    print(f"  Modèle '{self.model}' non trouvé. Téléchargez-le avec:")
                    print(f"   ollama pull {self.model}")
            else:
                print("   Ollama non accessible")
        except requests.exceptions.ConnectionError:
            print("   Ollama non démarré. Lancez: ollama serve")
    
    def generate(self, prompt: str, stream: bool = False) -> str:
        """
        Génère une réponse avec Ollama
        Args:
            prompt: Prompt complet avec contexte
            stream: Streaming de la réponse
        Returns:
            Réponse générée
        """
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens
            }
        }
        
        try:
            response = requests.post(url, json=payload, stream=stream)
            print(f"   Statut Ollama: {response.status_code}")
            if stream:
                # Mode streaming
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        json_response = json.loads(line)
                        chunk = json_response.get('response', '')
                        full_response += chunk
                        print(chunk, end='', flush=True)
                print()
                return full_response
            else:
                # Mode non-streaming
                result = response.json()
                return result.get('response', '')
                
        except Exception as e:
            print(f" Erreur Ollama: {e}")
            return f"Erreur: {str(e)}"