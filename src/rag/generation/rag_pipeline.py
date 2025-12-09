from typing import List, Dict, Optional
from src.rag.generation.llm_handler import OllamaLLM
from src.rag.generation.retriever_lang import Retriever

class RAGPipeline:
    """
    Pipeline RAG complet: Retrieval + Generation
    """
    
    def __init__(
        self,
        retriever: Retriever,
        llm: OllamaLLM,
        system_prompt: Optional[str] = None
    ):
        """
        Args:
            retriever: Système de récupération
            llm: Modèle de langage Ollama
            system_prompt: Instructions système personnalisées
        """
        self.retriever = retriever
        self.llm = llm
        
        self.system_prompt = system_prompt or self._default_system_prompt()
    
    def _default_system_prompt(self) -> str:
        """Prompt système par défaut pour ESILV"""
        return """Tu es un assistant intelligent pour l'école d'ingénieurs ESILV.

INSTRUCTIONS:
- Réponds UNIQUEMENT en te basant sur le CONTEXTE fourni
- Sois précis, factuel et professionnel
- Si l'information n'est PAS dans le contexte, dis "Je n'ai pas cette information dans ma base de données"
- Ne JAMAIS inventer d'informations
- Utilise un ton amical mais professionnel
- Réponds en français sauf si la question est en anglais

CONTEXTE:
{context}

QUESTION: {query}

RÉPONSE:"""
    
    def _format_context(self, chunks: List[Dict]) -> str:
        """
        Formate les chunks récupérés en contexte
        Args:
            chunks: Chunks récupérés
        Returns:
            Contexte formaté
        """
        if not chunks:
            return "Aucun contexte disponible."
        
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk['metadata'].get('source', 'Inconnu')
            score = chunk.get('similarity_score', 0)
            content = chunk['content'].strip()
            
            context_parts.append(
                f"[Source {i}: {source} (Score: {score:.2f})]\n{content}\n"
            )
        
        return "\n---\n".join(context_parts)
    
    def query(
        self,
        user_query: str,
        return_sources: bool = True,
        stream: bool = False
    ) -> Dict:
        """
        Execute une requête RAG complète
        
        Args:
            user_query: Question de l'utilisateur
            return_sources: Retourner les sources utilisées
            stream: Streaming de la réponse
            
        Returns:
            Dictionnaire avec réponse et métadonnées
        """
        print(f"\n{'='*60}")
        print(f"  Question: {user_query}")
        print(f"{'='*60}\n")
        
        # 1. RETRIEVAL: Récupérer les chunks pertinents
        print("Phase 1: Récupération des documents...")
        retrieved_chunks = self.retriever.retrieve_with_reranking(user_query)
        
        if not retrieved_chunks:
            return {
                'answer': "Je n'ai trouvé aucune information pertinente pour répondre à votre question.",
                'sources': [],
                'num_chunks_used': 0
            }
        
        # 2. FORMATTING: Créer le prompt
        print("Phase 2: Formatage du contexte...")
        context = self._format_context(retrieved_chunks)
        
        prompt = self.system_prompt.format(
            context=context,
            query=user_query
        )
        
        # 3. GENERATION: Générer la réponse
        print("Phase 3: Génération de la réponse...\n")
        answer = self.llm.generate(prompt, stream=stream)
        
        # 4. FORMAT RESPONSE
        response = {
            'answer': answer.strip(),
            'num_chunks_used': len(retrieved_chunks)
        }
        
        if return_sources:
            response['sources'] = [
                {
                    'source': chunk['metadata'].get('source', 'Inconnu'),
                    'score': chunk.get('similarity_score', 0),
                    'preview': chunk['content'][:200] + "..."
                }
                for chunk in retrieved_chunks
            ]
        
        return response
    
    def interactive_chat(self):
        """Mode chat interactif"""
        print("\n" + "="*60)
        print("  ESILV Smart Assistant - Mode Chat")
        print("="*60)
        print("Tapez 'quit' pour quitter\n")
        
        while True:
            user_input = input("  Vous: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("  Au revoir!")
                break
            
            if not user_input:
                continue
            
            # Traiter la requête
            result = self.query(user_input, return_sources=False, stream=True)
            
            print(f"\n  Chunks utilisés: {result['num_chunks_used']}\n")