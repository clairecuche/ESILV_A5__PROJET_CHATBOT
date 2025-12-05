from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from src.agents.agent_rag import AgentRAG
from src.agents.agent_formulaire import AgentFormulaire
from src.agents.agent_interaction import AgentInteraction
from src.agents.state_manager import state_manager
from src.agents.prompts import prompts
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)


class AgentSuperviseur:
    def __init__(self):
        logger.info("Initialisation du Superviseur...")
        
        try:
            self.rag = AgentRAG()
            logger.info("Agent RAG initialisé")
        except Exception as e:
            logger.error(f"Erreur init Agent RAG: {e}")
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
            logger.error(f"Erreur init Agent Interaction: {e}")
            self.interact = None
        
        self.llm = ChatOllama(
            model="mistral",
            temperature=0.0,
            num_predict=10
        )
        
        self.routing_prompt = ChatPromptTemplate.from_messages([
            ("system", prompts.ROUTING_SYSTEM_PROMPT),
            ("human", "Message utilisateur à analyser :\n{message}\n\nClassification (un seul mot) :")
        ])
        
        self.routing_chain = self.routing_prompt | self.llm | StrOutputParser()
        
        logger.info("Superviseur prêt\n")
    
    def detect_intent_with_llm(self, message: str) -> str:
        try:
            logger.info(f"Analyse intention du message: '{message[:60]}...'")
            start_time = time.time()
            
            intent_raw = self.routing_chain.invoke({"message": message})
            
            elapsed_time = time.time() - start_time
            logger.info(f"Réponse brute LLM: '{intent_raw}'")
            logger.info(f"Temps de détection: {elapsed_time:.2f}s")
            
            intent_word = intent_raw.strip().upper()
            intent_word = intent_word.split('\n')[0]
            intent_word = intent_word.split()[0] if intent_word.split() else ""
            intent_word = intent_word.rstrip('.,!?;:')
            
            logger.info(f"Mot extrait: '{intent_word}'")
            
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
                logger.warning(f"Intent invalide '{intent_word}', utilisation du fallback")
                return self._fallback_keyword_routing(message)
        
        except Exception as e:
            logger.error(f"Erreur détection LLM: {e}")
            logger.info("Utilisation du routing par mots-clés (fallback)")
            return self._fallback_keyword_routing(message)
    
    def _fallback_keyword_routing(self, message: str) -> str:
        logger.info("Fallback: routing par mots-clés")
        
        msg_lower = message.lower()
        
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
        
        rag_count = sum(1 for keyword in rag_keywords if keyword in msg_lower)
        form_count = sum(1 for keyword in form_keywords if keyword in msg_lower)
        
        logger.info(f"Scores - RAG: {rag_count}, FORM: {form_count}")
        
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
        logger.info(f"\n{'='*60}")
        logger.info(f"ROUTING - Session: {session_id[:8]}...")
        logger.info(f"{'='*60}")
        
        session = state_manager.get_or_create_session(session_id)
        
        last_assistant_message = None
        if session.history and len(session.history) >= 1:
            for msg in reversed(session.history):
                if msg['role'] == 'assistant':
                    last_assistant_message = msg['content']
                    logger.info(f"Dernier message assistant: {last_assistant_message}")
                    break
        
        form_questions = [
            'votre nom complet',
            'le programme qui vous intéresse',
            'quel champ souhaitez-vous modifier'
        ]

        if session.form_completed:
            logger.info("Formulaire terminé, réinitialisation de l'état")
            session.form_completed = False
         
        if last_assistant_message and any(q in last_assistant_message for q in form_questions) and session.form_completed == False:
            logger.info("RÈGLE 0: Question formulaire détectée dans message précédent → Agent Formulaire")
            return "formulaire"
        
        if session.awaiting_confirmation:
            logger.info("RÈGLE 1: Confirmation en attente → reste sur l'agent Formulaire")
            return "formulaire"
        
        if hasattr(session, 'editing_field') and session.editing_field:
            logger.info(f"RÈGLE 2: Édition du champ {session.editing_field} → reste sur l'agent Formulaire")
            return "formulaire"
        
        if any(session.form_data.values()):
            logger.info("RÈGLE 2.5: Formulaire partiel détecté → continue avec Form Agent")
            return "formulaire"
        
        if state_manager.is_form_active(session_id):
            logger.info("RÈGLE 3: Formulaire en cours → continue avec Form Agent")
            return "formulaire"
        
        intent = self.detect_intent_with_llm(message)
        
        if intent == "mixed":
            logger.info("RÈGLE 5: Intent MIXED → RAG d'abord, formulaire ensuite")
            return "rag"
        elif intent == "rag":
            logger.info("RÈGLE 5: Intent RAG → Agent RAG")
            return "rag"
        elif intent == "formulaire":
            logger.info("RÈGLE 5: Intent FORMULAIRE → Agent Formulaire")
            return "formulaire"
        else:
            logger.info("RÈGLE 5: Intent INTERACTION → Agent Interaction")
            return "interaction"
    
    def run(self, message: str, session_id: str) -> str:
        try:
            logger.info(f"\n{'#'*60}")
            logger.info(f"NOUVEAU MESSAGE")
            logger.info(f"   Session: {session_id[:8]}...")
            logger.info(f"   Message: '{message[:100]}{'...' if len(message) > 100 else ''}'")
            logger.info(f"{'#'*60}\n")
            
            session = state_manager.get_or_create_session(session_id)
            state_manager.add_to_history(session_id, "user", message)
            
            agent_type = self.route(message, session_id)
            intent = self.detect_intent_with_llm(message)
            is_mixed = (intent == "mixed")
            
            logger.info(f"\n{'='*60}")
            logger.info(f"EXÉCUTION AGENT: {agent_type.upper()}")
            logger.info(f"{'='*60}\n")
            
            if agent_type == "rag":
                if self.rag is None:
                    response = "Désolé, le service de recherche d'information est temporairement indisponible."
                else:
                    response = self.rag.run(message)
                
                if is_mixed and not state_manager.is_form_active(session_id):
                    logger.info("Intent MIXED détecté → activation du formulaire pour la prochaine interaction")
                    if not session.form_data:
                        session.form_data = {
                            'nom': None,
                            'email': None,
                            'telephone': None,
                            'programme': None,
                            'message': None
                        }
                    response += "\n\nJe vois que vous souhaitez également être contacté. Pouvons-nous prendre vos coordonnées ?"
            
            elif agent_type == "formulaire":
                if self.form is None:
                    response = "Désolé, le service de contact est temporairement indisponible."
                else:
                    response = self.form.run(message, session_id)
                    
                    if session.form_completed:
                        logger.info("Formulaire terminé, réinitialisation de l'état")
                        session.form_completed = False
                        session.awaiting_confirmation = False
            
            else:
                if self.interact is None:
                    response = "Bonjour ! Comment puis-je vous aider ?"
                else:
                    response = self.interact.run(message)
            
            state_manager.add_to_history(session_id, "assistant", response)
            
            logger.info(f"\n{'='*60}")
            logger.info(f"RÉPONSE GÉNÉRÉE")
            logger.info(f"   Longueur: {len(response)} caractères")
            logger.info(f"   Aperçu: '{response[:100]}{'...' if len(response) > 100 else ''}'")
            logger.info(f"{'='*60}\n")
            
            return response
        
        except Exception as e:
            logger.error(f"\n{'!'*60}")
            logger.error(f"ERREUR CRITIQUE dans run()")
            logger.error(f"   Exception: {type(e).__name__}")
            logger.error(f"   Message: {str(e)}")
            logger.error(f"   Session: {session_id[:8]}...")
            logger.error(f"   Message: '{message[:100]}{'...' if len(message) > 100 else ''}'")
            logger.error(f"{'!'*60}\n")
            return "Désolé, une erreur s'est produite. Pouvez-vous reformuler votre demande ?"
    
    def get_statistics(self, session_id: str) -> dict:
        return state_manager.get_session_summary(session_id)