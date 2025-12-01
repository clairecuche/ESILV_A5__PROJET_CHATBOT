# agent_superviseur.py
"""
Agent Superviseur - Coordinateur principal du système multi-agents

Rôle :
- Détecte l'intention de l'utilisateur avec un LLM
- Route vers le bon agent (RAG, Formulaire, Interaction)
- Gère l'état conversationnel
- Coordonne les réponses
"""

from agent_rag import AgentRAG
from agent_formulaire import AgentFormulaire
from agent_interaction import AgentInteraction
from state_manager import state_manager
from prompts import prompts
from ollama import Client
import logging
import time

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

# Client Ollama
client = Client()


class AgentSuperviseur:
    """
    Agent coordinateur qui orchestre tous les autres agents
    """
    
    def __init__(self):
        """Initialise tous les agents et la configuration"""
        
        # Initialisation des agents
        logger.info("Initialisation du Superviseur...")
        
        try:
            self.rag = AgentRAG()
            logger.info("Agent RAG initialisé")
        except Exception as e:
            logger.error(f" Erreur init Agent RAG: {e}")
            self.rag = None
        
        try:
            self.form = AgentFormulaire()
            logger.info("Agent Formulaire initialisé")
        except Exception as e:
            logger.error(f"Erreur init Agent Formulaire: {e}")
            self.form = None
        
        try:
            self.interact = AgentInteraction()
            logger.info("Agent Interaction initialisé")
        except Exception as e:
            logger.error(f" Erreur init Agent Interaction: {e}")
            self.interact = None
        
        # Configuration du routing
        self.routing_model = "mistral"  # ou "llama3.2"
        self.routing_temperature = 0.0  # Déterministe pour le routing
        self.routing_max_tokens = 10    # On veut juste un mot
        
        logger.info("Superviseur prêt\n")
    
    def detect_intent_with_llm(self, message: str) -> str:
        """
        Détecte l'intention de l'utilisateur en utilisant un LLM
        
        Cette méthode utilise Ollama pour analyser le message et déterminer
        si l'utilisateur veut :
        - Des informations (RAG)
        - Être contacté (FORMULAIRE)
        - Les deux (MIXED)
        - Autre chose (INTERACTION)
        
        Args:
            message: Le message de l'utilisateur
            
        Returns:
            str: "rag", "formulaire", "mixed", ou "interaction"
        """
        try:
            logger.info(f"Analyse intention du message: '{message[:60]}...'")
            start_time = time.time()
            
            # Construction du prompt complet
            full_prompt = f"""{prompts.ROUTING_SYSTEM_PROMPT}

Message utilisateur à analyser :
{message}

Classification (un seul mot) :"""
            
            # Appel au LLM avec Ollama
            response = client.generate(
                model=self.routing_model,
                prompt=full_prompt,
                options={
                    "temperature": self.routing_temperature,
                    "num_predict": self.routing_max_tokens
                }
            )
            
            elapsed_time = time.time() - start_time
            
            # Extraction de la réponse
            intent_raw = response["response"].strip()
            
            logger.info(f"Réponse brute LLM: '{intent_raw}'")
            logger.info(f"Temps de détection: {elapsed_time:.2f}s")
            
            # Nettoyage et extraction du premier mot
            # Le LLM peut parfois ajouter du texte, on ne veut que le premier mot
            intent_word = intent_raw.upper()
            
            # Enlève les sauts de ligne et prend la première ligne
            intent_word = intent_word.split('\n')[0]
            
            # Prend le premier mot
            intent_word = intent_word.split()[0] if intent_word.split() else ""
            
            # Enlève la ponctuation éventuelle
            intent_word = intent_word.rstrip('.,!?;:')
            
            logger.info(f"Mot extrait: '{intent_word}'")
            
            # Validation et mapping vers les valeurs attendues
            valid_intents = {
                "RAG": "rag",
                "FORMULAIRE": "formulaire",
                "MIXED": "mixed",
                "INTERACTION": "interaction"
            }
            
            if intent_word in valid_intents:
                detected = valid_intents[intent_word]
                logger.info(f"Intent final: {detected.upper()}")
                return detected
            else:
                # Intent non reconnu
                logger.warning(f"Intent invalide '{intent_word}', utilisation du fallback")
                return self._fallback_keyword_routing(message)
        
        except Exception as e:
            logger.error(f"Erreur détection LLM: {e}")
            logger.info("Utilisation du routing par mots-clés (fallback)")
            return self._fallback_keyword_routing(message)
    
    def _fallback_keyword_routing(self, message: str) -> str:
        """
        Routing de secours basé sur des mots-clés si le LLM échoue
        
        Cette méthode est utilisée en fallback si :
        - Ollama ne répond pas
        - Le LLM donne une réponse invalide
        - Une erreur se produit
        
        Args:
            message: Le message utilisateur
            
        Returns:
            str: Intent détecté ("rag", "formulaire", "mixed", ou "interaction")
        """
        logger.info(" Fallback: routing par mots-clés")
        
        msg_lower = message.lower()
        
        # Mots-clés pour RAG (questions sur l'école)
        rag_keywords = [
            "programme", "programmes", "formation", "formations",
            "admission", "admissions", "concours",
            "cours", "matière", "matières",
            "frais", "coût", "coûts", "prix", "tarif",
            "stage", "stages", "alternance",
            "spécialisation", "spécialisations",
            "esilv", "école", "campus",
            "étudiant", "étudiants",
            "diplôme", "diplômes",
            "débouché", "débouchés", "métier", "métiers",
            "quoi", "quel", "quelle", "quels", "quelles",
            "comment", "où", "pourquoi",
            "info", "information", "informations"
        ]
        
        # Mots-clés pour FORMULAIRE (demande de contact)
        form_keywords = [
            "contact", "contacter", "contacté", "contactez",
            "rappel", "rappeler", "rappelez",
            "appel", "appeler", "appelez",
            "brochure", "documentation",
            "inscription", "inscrire", "candidature",
            "rendez-vous", "rdv",
            "email", "mail", "téléphone", "tel",
            "recontacter", "recontacté"
        ]
        
        # Compte les occurrences
        rag_count = sum(1 for keyword in rag_keywords if keyword in msg_lower)
        form_count = sum(1 for keyword in form_keywords if keyword in msg_lower)
        
        logger.info(f"Scores - RAG: {rag_count}, FORM: {form_count}")
        
        # Décision basée sur les scores
        if rag_count > 0 and form_count > 0:
            logger.info("MIXED détecté (mots-clés des deux catégories)")
            return "mixed"
        elif rag_count > 0:
            logger.info("RAG détecté")
            return "rag"
        elif form_count > 0:
            logger.info("FORMULAIRE détecté")
            return "formulaire"
        else:
            logger.info("INTERACTION par défaut")
            return "interaction"
    
    def route(self, message: str, session_id: str) -> str:
        """
        Détermine quel agent doit traiter le message
        
        Prend en compte :
        1. L'état de la session (formulaire en cours ?)
        2. L'intention détectée par le LLM
        3. Les règles métier (ex: formulaire prioritaire si actif)
        
        Args:
            message: Message de l'utilisateur
            session_id: ID de la session
            
        Returns:
            str: "rag", "formulaire", ou "interaction"
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"ROUTING - Session: {session_id[:8]}...")
        logger.info(f"{'='*60}")
        
        # RÈGLE 1 : Si un formulaire est déjà actif, on continue avec
        if state_manager.is_form_active(session_id):
            logger.info("RÈGLE 1: Formulaire en cours → continue avec Form Agent")
            return "formulaire"
        
        # RÈGLE 2 : Détection d'intention avec LLM
        intent = self.detect_intent_with_llm(message)
        
        # RÈGLE 3 : Mapping intention → agent
        if intent == "mixed":
            # Pour MIXED : on commence par RAG, puis on active le formulaire
            logger.info("RÈGLE 3: Intent MIXED → RAG d'abord, formulaire ensuite")
            return "rag"
        
        elif intent == "rag":
            logger.info("RÈGLE 3: Intent RAG → Agent RAG")
            return "rag"
        
        elif intent == "formulaire":
            logger.info("RÈGLE 3: Intent FORMULAIRE → Agent Formulaire")
            return "formulaire"
        
        else:  # interaction
            logger.info("RÈGLE 3: Intent INTERACTION → Agent Interaction")
            return "interaction"
    
    def run(self, message: str, session_id: str) -> str:
        """
        Point d'entrée principal du superviseur
        
        Workflow :
        1. Récupère l'état de la session
        2. Ajoute le message à l'historique
        3. Route vers le bon agent
        4. Exécute l'agent
        5. Sauvegarde la réponse
        6. Retourne la réponse
        
        Args:
            message: Message de l'utilisateur
            session_id: ID de la session Streamlit
            
        Returns:
            str: La réponse générée
        """
        try:
            logger.info(f"\n{'#'*60}")
            logger.info(f"NOUVEAU MESSAGE")
            logger.info(f"   Session: {session_id[:8]}...")
            logger.info(f"   Message: '{message[:100]}...'")
            logger.info(f"{'#'*60}\n")
            
            # 1. Récupère l'état de la session
            session = state_manager.get_or_create_session(session_id)
            
            # 2. Ajoute le message utilisateur à l'historique
            state_manager.add_to_history(session_id, "user", message)
            
            # 3. Détermine quel agent utiliser
            agent_type = self.route(message, session_id)
            
            # 4. Vérifie si c'était MIXED pour gérer l'enchaînement
            intent = self.detect_intent_with_llm(message)
            is_mixed = (intent == "mixed")
            
            # 5. Exécute l'agent approprié
            logger.info(f"\n{'='*60}")
            logger.info(f"EXÉCUTION AGENT: {agent_type.upper()}")
            logger.info(f"{'='*60}\n")
            
            if agent_type == "rag":
                if self.rag is None:
                    response = "Désolé, le service de recherche d'information est temporairement indisponible."
                else:
                    response = self.rag.run(message)
                
                # Si c'était MIXED, ajoute une invitation au formulaire
                if is_mixed:
                    logger.info("Intent MIXED détecté → ajout invitation formulaire")
                    response += "\n\nJe vois que vous souhaitez également être contacté. Pouvons-nous prendre vos coordonnées ?"
                    # Le prochain message sera routé vers le formulaire
            
            elif agent_type == "formulaire":
                if self.form is None:
                    response = "Désolé, le service de contact est temporairement indisponible."
                else:
                    response = self.form.run(message, session_id)
            
            else:  # interaction
                if self.interact is None:
                    response = "Bonjour ! Comment puis-je vous aider ?"
                else:
                    response = self.interact.run(message)
            
            # 6. Sauvegarde la réponse dans l'historique
            state_manager.add_to_history(session_id, "assistant", response)
            
            logger.info(f"\n{'='*60}")
            logger.info(f"RÉPONSE GÉNÉRÉE")
            logger.info(f"   Longueur: {len(response)} caractères")
            logger.info(f"   Aperçu: '{response[:100]}...'")
            logger.info(f"{'='*60}\n")
            
            return response
        
        except Exception as e:
            logger.error(f"\n{'!'*60}")
            logger.error(f"ERREUR CRITIQUE dans run()")
            logger.error(f"   Exception: {type(e).__name__}")
            logger.error(f"   Message: {str(e)}")
            logger.error(f"{'!'*60}\n")
            return "Désolé, une erreur s'est produite. Pouvez-vous reformuler votre demande ?"
    
    def get_statistics(self, session_id: str) -> dict:
        return state_manager.get_session_summary(session_id)


    
