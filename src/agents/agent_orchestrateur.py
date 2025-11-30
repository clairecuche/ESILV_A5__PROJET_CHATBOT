# agent_superviseur.py
from agent_rag import AgentRAG
from agent_formulaire import AgentFormulaire
from agent_interaction import AgentInteraction
from state_manager import state_manager
import logging

logger = logging.getLogger(__name__)

class AgentSuperviseur:
    def __init__(self):
        self.rag = AgentRAG()
        self.form = AgentFormulaire()
        self.interact = AgentInteraction()
    
    def run(self, message: str, session_id: str):
        
        session = state_manager.get_or_create_session(session_id)
        state_manager.add_to_history(session_id, "user", message)
        agent_type = self.route(message, session_id)
        
        logger.info(f"Routing → {agent_type}")
        
        if agent_type == "rag":
            response = self.rag.run(message)
        elif agent_type == "formulaire":
            response = self.form.run(message, session_id)  
        else:
            response = self.interact.run(message)
        
        state_manager.add_to_history(session_id, "assistant", response)
        
        return response
    
    def route(self, message: str, session_id: str) -> str:
        """Route avec prise en compte de l'état"""
        
        if state_manager.is_form_active(session_id):
            logger.info("Formulaire actif → continue avec Form Agent")
            return "formulaire"
        if any(k in message.lower() for k in ["admission", "programme", "cours", "esilv"]):
            return "rag"
        if any(k in message.lower() for k in ["email", "nom", "inscription", "contact"]):
            return "formulaire"
        return "interaction"