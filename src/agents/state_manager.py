# state_manager.py

from typing import Dict, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ConversationState:
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        
        self.form_data = {
            'nom': None,
            'email': None,
            'telephone': None,
            'programme': None,
            'message': None
        }
        
        self.form_completed = False         
        self.awaiting_confirmation = False   
        self.current_agent = None  
        self.history = [] 
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return {
            'session_id': self.session_id,
            'form_data': self.form_data,
            'form_completed': self.form_completed,
            'awaiting_confirmation': self.awaiting_confirmation,
            'current_agent': self.current_agent,
            'history': self.history,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    def update_form_field(self, field: str, value: str):
        if field in self.form_data:
            self.form_data[field] = value
            self.updated_at = datetime.now().isoformat()
            logger.info(f"✓ Champ '{field}' mis à jour dans session {self.session_id[:8]}")
        else:
            logger.warning(f"Tentative mise à jour champ inconnu: {field}")
    
    def add_message(self, role: str, content: str, metadata: Dict = None):
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        self.history.append(message)
        self.updated_at = datetime.now().isoformat()
        logger.info(f"Message {role} ajouté (session {self.session_id[:8]})")
    
    def get_form_completion_percentage(self) -> int:
        required_fields = ['nom', 'email', 'telephone', 'programme']
        filled = sum(1 for field in required_fields if self.form_data.get(field))
        return int((filled / len(required_fields)) * 100)


class StateManager:
    
    def __init__(self):
        self.sessions: Dict[str, ConversationState] = {}
        logger.info("StateManager initialisé")
    
    def get_or_create_session(self, session_id: str) -> ConversationState:
        
        if session_id not in self.sessions:
            logger.info(f"Création nouvelle session: {session_id[:8]}...")
            self.sessions[session_id] = ConversationState(session_id)
        else:
            logger.debug(f"Récupération session existante: {session_id[:8]}...")
        
        return self.sessions[session_id]
    
    def update_form_data(self, session_id: str, field: str, value: str):
        session = self.get_or_create_session(session_id)
        session.update_form_field(field, value)
    
    def add_to_history(self, session_id: str, role: str, message: str, metadata: Dict = None):
        
        session = self.get_or_create_session(session_id)
        session.add_message(role, message, metadata)
    
    def get_form_data(self, session_id: str) -> Dict:
        
        session = self.get_or_create_session(session_id)
        return session.form_data
    
    def is_form_active(self, session_id: str) -> bool:
       
        session = self.get_or_create_session(session_id)
        has_data = any(session.form_data.values())
        return has_data and not session.form_completed
    
    def mark_form_complete(self, session_id: str):
        session = self.get_or_create_session(session_id)
        session.form_completed = True
        logger.info(f"Formulaire complété (session {session_id[:8]})")
    
    def reset_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Session {session_id[:8]} réinitialisée")
    
    def get_session_summary(self, session_id: str) -> Dict:
        session = self.get_or_create_session(session_id)
        return {
            'session_id': session_id[:8] + "...",
            'messages_count': len(session.history),
            'form_completion': session.get_form_completion_percentage(),
            'current_agent': session.current_agent,
            'form_data': session.form_data
        }



state_manager = StateManager()