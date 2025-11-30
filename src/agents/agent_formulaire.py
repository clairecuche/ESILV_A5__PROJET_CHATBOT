# agent_formulaire.py
from state_manager import state_manager
from ollama import Client
import logging

logger = logging.getLogger(__name__)
client = Client()


class AgentFormulaire:
    def __init__(self):
        self.model = "mistral"
        

    def run(self, message: str, session_id: str) -> str:
        session = state_manager.get_or_create_session(session_id)
        form_data = session.form_data
        
        logger.info(f"Agent Formulaire - État actuel: {form_data}")
        
        if session.awaiting_confirmation:
            return self._handle_confirmation(message, session_id)
        
        extracted = self._extract_info(message)
        
        for field, value in extracted.items():
            state_manager.update_form_data(session_id, field, value)
        
        missing = self._get_missing_fields(session_id)
        
        if not missing:
            session.awaiting_confirmation = True
            return self._generate_confirmation(session_id)
        else:
            return self._ask_next_field(missing[0])
    
    def _get_missing_fields(self, session_id: str) -> list:
        form_data = state_manager.get_form_data(session_id)
        required = ['nom', 'email', 'telephone', 'programme']
        return [f for f in required if not form_data.get(f)]
    
    def _extract_info(self, message: str) -> dict:
        import re
        extracted = {}
        
        # Email
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', message)
        if email_match:
            extracted['email'] = email_match.group()
        
        # Téléphone
        phone_match = re.search(r'(?:\+33|0)[1-9](?:[\s\-\.]?\d{2}){4}', message)
        if phone_match:
            extracted['telephone'] = phone_match.group()
        
        if not extracted:
            extracted['nom'] = message.strip()
        
        return extracted
    
    def _ask_next_field(self, field: str) -> str:
        questions = {
            'nom': "Pour commencer, quel est votre nom complet ?",
            'email': "Parfait ! Quelle est votre adresse email ?",
            'telephone': "Merci ! Quel est votre numéro de téléphone ?",
            'programme': "Quel programme vous intéresse ?"
        }
        return questions.get(field, "Informations supplémentaires ?")
    
    def _generate_confirmation(self, session_id: str) -> str:
        form_data = state_manager.get_form_data(session_id)
        return f"""Récapitulatif de vos informations :

Nom : {form_data['nom']}
Email : {form_data['email']}
Téléphone : {form_data['telephone']}
Programme : {form_data['programme']}

Confirmez-vous ces informations ? (oui/non)"""
    
    def _handle_confirmation(self, message: str, session_id: str) -> str:
        if message.lower() in ['oui', 'yes', 'ok', 'confirme']:
            state_manager.mark_form_complete(session_id)
            # TODO: Sauvegarder dans storage
            return "Parfait ! Vos informations ont été enregistrées. Notre équipe vous contactera bientôt."
        else:
            session = state_manager.get_or_create_session(session_id)
            session.awaiting_confirmation = False
            return "D'accord, recommençons. Quel est votre nom ?"