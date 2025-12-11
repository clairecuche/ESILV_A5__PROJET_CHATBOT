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
        return """Tu es un assistant intelligent spécialisé pour l'école d'ingénieurs ESILV (École Supérieure d'Ingénieurs Léonard de Vinci).

RÈGLES IMPORTANTES:
1. Base ta réponse UNIQUEMENT sur les informations présentes dans le CONTEXTE ci-dessous
2. Si l'information est dans le contexte (même partiellement ou noyée dans un paragraphe), EXTRAIS-LA et formule une réponse claire
3. Réponds de manière directe et précise à la question posée
4. Si l'information est TOTALEMENT absente du contexte, dis: "Je n'ai pas trouvé cette information dans les documents fournis."
5. Ne JAMAIS inventer ou déduire des informations qui ne sont pas explicitement mentionnées
6. Utilise un ton professionnel mais amical
7. Réponds en français

CONTEXTE:
{context}

---

QUESTION: {query}

RÉPONSE:"""
    
    def _format_context(self, chunks: List[Dict]) -> str:
        """
        Formate les chunks récupérés en contexte structuré pour le LLM
        
        Args:
            chunks: Liste de chunks avec leurs métadonnées et scores
            
        Returns:
            Contexte formaté et numéroté
        """
        if not chunks:
            return "Aucun contexte disponible."
        
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            # Récupération des métadonnées
            source = chunk['metadata'].get('source', 'Document inconnu')
            page = chunk['metadata'].get('page', 'N/A')
            
            # Récupération du score final 
            final_score = chunk['scores']['final']
            
            # Nettoyage du contenu
            content = chunk['content'].strip()
            
            # Format clair et structuré
            context_parts.append(
                f"--- DOCUMENT {i} ---\n"
                f"Source: {source} | Page: {page} | Pertinence: {final_score:.2f}\n\n"
                f"{content}\n"
            )
        
        return "\n".join(context_parts)
    
    def query(
        self,
        user_query: str,
        return_sources: bool = True,
        stream: bool = False,
        debug: bool = False
    ) -> Dict:
        """
        Exécute une requête RAG complète
        
        Args:
            user_query: Question de l'utilisateur
            return_sources: Retourner les sources utilisées
            stream: Streaming de la réponse
            debug: Afficher le contexte envoyé au LLM
            
        Returns:
            Dictionnaire avec réponse et métadonnées
        """
        print(f"\n{'='*60}")
        print(f"  Question: {user_query}")
        print(f"{'='*60}\n")
        
        # 1. RETRIEVAL: Récupérer les chunks pertinents
        print("Phase 1: Récupération des documents...")
        retrieved_chunks = self.retriever.retrieve_with_reranking(
            user_query, 
            debug=debug
        )
        
        if not retrieved_chunks:
            return {
                'answer': "Je n'ai trouvé aucune information pertinente pour répondre à votre question.",
                'sources': [],
                'num_chunks_used': 0
            }
        
        # 2. FORMATTING: Créer le contexte structuré
        print("Phase 2: Formatage du contexte...")
        context = self._format_context(retrieved_chunks)
        
        # Debug: afficher le contexte exact envoyé au LLM
        if debug:
            print("\n" + "="*60)
            print("CONTEXTE ENVOYÉ AU LLM:")
            print("="*60)
            print(context)
            print("="*60 + "\n")
        
        # Construire le prompt complet
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
                    'page': chunk['metadata'].get('page', 'N/A'),
                    'final_score': chunk['scores']['final'],
                    'vector_score': chunk['scores']['vector'],
                    'lexical_score': chunk['scores']['lexical'],
                    'preview': chunk['content'][:250] + "..." if len(chunk['content']) > 250 else chunk['content']
                }
                for chunk in retrieved_chunks
            ]
        
        return response
        
    def interactive_chat(self, debug: bool = False):
        """Mode chat interactif"""
        print("\n" + "="*60)
        print("  ESILV Smart Assistant - Mode Chat")
        print("="*60)
        print("Commandes: 'quit' pour quitter, 'debug' pour toggle debug\n")
        
        current_debug = debug
        
        while True:
            user_input = input("  Vous: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("  Au revoir!")
                break
            
            if user_input.lower() == 'debug':
                current_debug = not current_debug
                print(f"  🔧 Debug mode: {'ON' if current_debug else 'OFF'}\n")
                continue
            
            if not user_input:
                continue
            
            # Traiter la requête
            result = self.query(
                user_input, 
                return_sources=False, 
                stream=True,
                debug=current_debug
            )
            
            print(f"\n  📚 {result['num_chunks_used']} chunks utilisés\n")
    