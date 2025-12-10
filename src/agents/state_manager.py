from typing import Dict, Optional, List
from datetime import datetime
from dataclasses import dataclass, field, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConversationState:
    session_id: str
    form_data: Dict[str, Optional[str]] = field(default_factory=lambda: {
        'nom': None,
        'email': None,
        'telephone': None,
        'programme': None,
        'message': None
    })
    form_completed: bool = False
    awaiting_confirmation: bool = False
    editing_field: Optional[str] = None
    current_agent: Optional[str] = None
    history: List[Dict] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def update_form_field(self, field: str, value: str):
        if field in self.form_data:
            self.form_data[field] = value
            self.updated_at = datetime.now().isoformat()
            logger.info(f"✓ Champ '{field}' mis à jour dans session {self.session_id[:8]}")
        else:
            logger.warning(f"✗ Tentative mise à jour champ inconnu: {field}")
    
    def add_message(self, role: str, content: str, metadata: Dict = None):
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        self.history.append(message)
        self.updated_at = datetime.now().isoformat()
        logger.debug(f"Message {role} ajouté (session {self.session_id[:8]})")
    
    def get_form_completion_percentage(self) -> int:
        required_fields = ['nom', 'email', 'telephone', 'programme']
        filled = sum(1 for field in required_fields if self.form_data.get(field))
        return int((filled / len(required_fields)) * 100)
    
    def reset_form(self):
        self.form_data = {
            'nom': None,
            'email': None,
            'telephone': None,
            'programme': None,
            'message': None
        }
        self.form_completed = False
        self.awaiting_confirmation = False
        self.editing_field = None
        self.updated_at = datetime.now().isoformat()
        logger.info(f"✓ Formulaire réinitialisé (session {self.session_id[:8]})")


class StateManager:
    def __init__(self):
        self.sessions: Dict[str, ConversationState] = {}
        logger.info("✓ StateManager initialisé")
    
    def get_or_create_session(self, session_id: str) -> ConversationState:
        if session_id not in self.sessions:
            logger.info(f"✓ Création nouvelle session: {session_id[:8]}...")
            self.sessions[session_id] = ConversationState(session_id=session_id)
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
    
    def remove_form_field(self, field: str, session_id: str):
        session = self.get_or_create_session(session_id)
        if field in session.form_data:
            session.form_data[field] = None
            logger.info(f"✓ Champ '{field}' supprimé (session {session_id[:8]})")
    
    def is_form_active(self, session_id: str) -> bool:
        session = self.get_or_create_session(session_id)
        has_data = any(session.form_data.values())
        not_completed = not session.form_completed
        return has_data and not_completed
    
    def mark_form_complete(self, session_id: str):
        session = self.get_or_create_session(session_id)
        session.form_completed = True
        logger.info(f"✓ Formulaire complété (session {session_id[:8]})")
    
    def reset_form(self, session_id: str):
        session = self.get_or_create_session(session_id)
        session.reset_form()
    
    def reset_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"✓ Session {session_id[:8]} réinitialisée")
    
    
    def get_session_summary(self, session_id: str) -> Dict:
        session = self.get_or_create_session(session_id)
        return {
            'session_id': session_id[:8] + "...",
            'messages_count': len(session.history),
            'form_completion': session.get_form_completion_percentage(),
            'current_agent': session.current_agent,
            'form_data': session.form_data,
            'awaiting_confirmation': session.awaiting_confirmation,
            'editing_field': session.editing_field,
        }
    
    def get_conversation_history(self, session_id: str, last_n: Optional[int] = None) -> List[Dict]:
        session = self.get_or_create_session(session_id)
        if last_n:
            return session.history[-last_n:]
        return session.history
    

state_manager = StateManager()