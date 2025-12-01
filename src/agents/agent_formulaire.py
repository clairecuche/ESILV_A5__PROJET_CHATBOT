# agent_formulaire.py
"""
Agent Formulaire - Collecte conversationnelle des informations de contact

Rôle :
- Collecter nom, email, téléphone, programme
- Valider les données
- Demander confirmation
- Sauvegarder les contacts
"""

from state_manager import state_manager
from prompts import prompts, get_field_question, format_confirmation_message
from ollama import Client
import logging
import re
import json
from pathlib import Path
from datetime import datetime

# Configuration logging
logger = logging.getLogger(__name__)
client = Client()


class AgentFormulaire:
    """Agent responsable de la collecte des informations de contact"""
    
    def __init__(self):
        """Initialise l'agent formulaire"""
        self.model = "mistral"
        
        # Champs requis
        self.required_fields = ['nom', 'email', 'telephone', 'programme']
        
        # Fichier de sauvegarde des contacts
        self.contacts_file = Path("data/contacts/contacts.json")
        self._ensure_contacts_file()
        
        logger.info("Agent Formulaire initialisé")
    
    def _ensure_contacts_file(self):
        """Crée le fichier contacts.json s'il n'existe pas"""
        self.contacts_file.parent.mkdir(parents=True, exist_ok=True)
        
        if not self.contacts_file.exists():
            self.contacts_file.write_text("[]", encoding='utf-8')
            logger.info(f"✓ Fichier contacts créé: {self.contacts_file}")
    
    def run(self, message: str, session_id: str) -> str:
        """
        Point d'entrée principal de l'agent formulaire
        
        Workflow :
        1. Récupère l'état de la session
        2. Si attente confirmation → gère confirmation
        3. Sinon → extrait infos du message
        4. Met à jour les données
        5. Vérifie si formulaire complet
        6. Retourne question suivante ou confirmation
        
        Args:
            message: Message de l'utilisateur
            session_id: ID de la session
            
        Returns:
            str: Réponse de l'agent
        """
        logger.info(f"\n{'='*50}")
        logger.info(f"AGENT FORMULAIRE - Session: {session_id[:8]}")
        logger.info(f"{'='*50}")
        
        # Récupère la session
        session = state_manager.get_or_create_session(session_id)
        form_data = session.form_data
        
        logger.info(f"État actuel du formulaire:")
        for field in self.required_fields:
            value = form_data.get(field)
            status = "✓" if value else "○"
            logger.info(f"  {status} {field}: {value if value else 'manquant'}")
        
        # Cas 1 : Attente de confirmation
        if session.awaiting_confirmation:
            logger.info("En attente de confirmation utilisateur")
            return self._handle_confirmation(message, session_id)
        
        # Cas 2 : Collecte des informations
        logger.info(f"Extraction d'informations du message: '{message}'")
        
        # Extrait les informations
        extracted = self._extract_info(message, session_id)
        
        if extracted:
            logger.info(f"Informations extraites: {extracted}")
            
            # Valide les données extraites
            validated = self._validate_extracted_data(extracted)
            
            if validated['valid']:
                # Met à jour les données validées
                for field, value in validated['data'].items():
                    state_manager.update_form_data(session_id, field, value)
                    logger.info(f"Champ '{field}' mis à jour: {value}")
            else:
                # Données invalides, retourne un message d'erreur
                logger.warning(f"Validation échouée: {validated['errors']}")
                return self._get_validation_error_message(validated['errors'])
        else:
            logger.info("○ Aucune information structurée extraite")
        
        # Vérifie les champs manquants
        missing = self._get_missing_fields(session_id)
        
        if not missing:
            # Formulaire complet → demande confirmation
            logger.info("Formulaire complet, demande de confirmation")
            session.awaiting_confirmation = True
            return self._generate_confirmation(session_id)
        else:
            # Formulaire incomplet → demande le prochain champ
            logger.info(f"Champs manquants: {missing}")
            return self._ask_next_field(missing[0])
    
    def _extract_info(self, message: str, session_id: str) -> dict:
        """
        Extrait les informations du message utilisateur
        
        Stratégies d'extraction :
        1. Regex pour email et téléphone
        2. Détection de mots-clés pour programme
        3. Si rien trouvé et nom manquant → considère comme nom
        
        Args:
            message: Message utilisateur
            session_id: ID de session
            
        Returns:
            dict: Données extraites
        """
        extracted = {}
        message_clean = message.strip()
        
        # 1. Extraction EMAIL (regex)
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, message_clean)
        if email_match:
            extracted['email'] = email_match.group()
            logger.info(f"Email détecté: {extracted['email']}")
        
        # 2. Extraction TÉLÉPHONE (regex)
        phone_pattern = r'(?:\+33|0)[1-9](?:[\s\-\.]?\d{2}){4}'
        phone_match = re.search(phone_pattern, message_clean)
        if phone_match:
            extracted['telephone'] = phone_match.group()
            logger.info(f"Téléphone détecté: {extracted['telephone']}")
        
        # 3. Extraction PROGRAMME (mots-clés)
        programmes_keywords = {
            'data science': 'Data Science',
            'ia': 'Intelligence Artificielle',
            'intelligence artificielle': 'Intelligence Artificielle',
            'cybersécurité': 'Cybersécurité',
            'cyber': 'Cybersécurité',
            'systèmes embarqués': 'Systèmes Embarqués',
            'embarqué': 'Systèmes Embarqués',
            'fintech': 'FinTech',
            'finance': 'Finance'
        }
        
        message_lower = message_clean.lower()
        for keyword, programme_name in programmes_keywords.items():
            if keyword in message_lower:
                extracted['programme'] = programme_name
                logger.info(f"Programme détecté: {programme_name}")
                break
        
        # 4. Si aucune structure détectée et nom manquant → c'est probablement un nom
        if not extracted:
            form_data = state_manager.get_form_data(session_id)
            if not form_data.get('nom'):
                # Considère le message comme un nom
                # Mais seulement si ça ressemble à un nom (pas trop long, pas de chiffres partout)
                if len(message_clean.split()) <= 4 and not message_clean.isdigit():
                    extracted['nom'] = message_clean
                    logger.info(f" Message interprété comme nom: {extracted['nom']}")
        
        # 5. Si toujours rien et programme manquant, considère comme programme
        if not extracted:
            form_data = state_manager.get_form_data(session_id)
            if not form_data.get('programme') and form_data.get('nom'):
                extracted['programme'] = message_clean
                logger.info(f" Message interprété comme programme: {extracted['programme']}")
        
        return extracted
    
    def _validate_extracted_data(self, extracted: dict) -> dict:
        """
        Valide les données extraites
        
        Args:
            extracted: Dictionnaire avec les données extraites
            
        Returns:
            dict: {'valid': bool, 'data': dict, 'errors': dict}
        """
        validated_data = {}
        errors = {}
        
        # Validation EMAIL
        if 'email' in extracted:
            email = extracted['email']
            if self._is_valid_email(email):
                validated_data['email'] = email.lower()
            else:
                errors['email'] = "Format d'email invalide"
        
        # Validation TÉLÉPHONE
        if 'telephone' in extracted:
            phone = extracted['telephone']
            normalized_phone = self._normalize_phone(phone)
            if normalized_phone:
                validated_data['telephone'] = normalized_phone
            else:
                errors['telephone'] = "Format de téléphone invalide"
        
        # Validation NOM (pas de validation stricte, juste nettoyage)
        if 'nom' in extracted:
            nom = extracted['nom'].strip()
            if len(nom) >= 2:
                validated_data['nom'] = nom
            else:
                errors['nom'] = "Nom trop court"
        
        # Validation PROGRAMME (pas de validation stricte)
        if 'programme' in extracted:
            validated_data['programme'] = extracted['programme'].strip()
        
        return {
            'valid': len(errors) == 0,
            'data': validated_data,
            'errors': errors
        }
    
    def _is_valid_email(self, email: str) -> bool:
        """Valide un email avec regex"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _normalize_phone(self, phone: str) -> str:
        """
        Normalise un numéro de téléphone français
        
        Args:
            phone: Numéro brut
            
        Returns:
            str: Numéro normalisé ou None si invalide
        """
        # Enlève espaces, tirets, points
        phone_clean = re.sub(r'[\s\-\.]', '', phone)
        
        # Format français : 0612345678 ou +33612345678
        if re.match(r'^0[1-9]\d{8}$', phone_clean):
            # 0612345678 → +33612345678
            return '+33' + phone_clean[1:]
        elif re.match(r'^\+33[1-9]\d{8}$', phone_clean):
            return phone_clean
        else:
            return None
    
    def _get_validation_error_message(self, errors: dict) -> str:
        """
        Génère un message d'erreur convivial
        
        Args:
            errors: Dictionnaire des erreurs
            
        Returns:
            str: Message d'erreur
        """
        if 'email' in errors:
            return prompts.VALIDATION_ERRORS['email']
        elif 'telephone' in errors:
            return prompts.VALIDATION_ERRORS['telephone']
        elif 'nom' in errors:
            return prompts.VALIDATION_ERRORS['nom']
        else:
            return "Les informations fournies semblent incorrectes. Pouvez-vous réessayer ?"
    
    def _get_missing_fields(self, session_id: str) -> list:
        """
        Retourne la liste des champs manquants
        
        Args:
            session_id: ID de session
            
        Returns:
            list: Liste des champs manquants
        """
        form_data = state_manager.get_form_data(session_id)
        return [f for f in self.required_fields if not form_data.get(f)]
    
    def _ask_next_field(self, field: str) -> str:
        """
        Retourne la question pour le prochain champ
        
        Args:
            field: Nom du champ à demander
            
        Returns:
            str: Question à poser
        """
        return get_field_question(field)
    
    def _generate_confirmation(self, session_id: str) -> str:
        """
        Génère le message de confirmation avec récapitulatif
        
        Args:
            session_id: ID de session
            
        Returns:
            str: Message de confirmation
        """
        form_data = state_manager.get_form_data(session_id)
        return format_confirmation_message(form_data)
    
    def _handle_confirmation(self, message: str, session_id: str) -> str:
        """
        Gère la réponse de l'utilisateur à la confirmation
        
        Args:
            message: Réponse de l'utilisateur
            session_id: ID de session
            
        Returns:
            str: Message de réponse
        """
        message_lower = message.lower().strip()
        
        # Mots de confirmation
        confirmation_words = ['oui', 'yes', 'ok', 'confirme', 'valide', 'correct', 'd\'accord']
        
        # Mots de refus
        refusal_words = ['non', 'no', 'pas', 'incorrect', 'faux']
        
        if any(word in message_lower for word in confirmation_words):
            logger.info("Confirmation acceptée par l'utilisateur")
            
            # Sauvegarde les données
            success = self._save_contact(session_id)
            
            if success:
                # Marque le formulaire comme complet
                state_manager.mark_form_complete(session_id)
                
                # Réinitialise l'état
                session = state_manager.get_or_create_session(session_id)
                session.awaiting_confirmation = False
                
                logger.info("Contact sauvegardé avec succès")
                return prompts.SUCCESS_MESSAGE
            else:
                logger.error("Échec de la sauvegarde")
                return "Une erreur s'est produite lors de l'enregistrement. Nos équipes ont été notifiées."
        
        elif any(word in message_lower for word in refusal_words):
            logger.info("Confirmation refusée, recommence le formulaire")
            
            # Réinitialise le formulaire
            session = state_manager.get_or_create_session(session_id)
            session.form_data = {
                'nom': None,
                'email': None,
                'telephone': None,
                'programme': None,
                'message': None
            }
            session.awaiting_confirmation = False
            
            return prompts.RESTART_FORM_MESSAGE
        
        else:
            # Réponse ambiguë, redemande
            logger.warning(f"Réponse ambiguë: '{message}'")
            return "Je n'ai pas bien compris. Confirmez-vous ces informations ? Répondez par 'oui' ou 'non'."
    
    def _save_contact(self, session_id: str) -> bool:
        """
        Sauvegarde le contact dans le fichier JSON
        
        Args:
            session_id: ID de session
            
        Returns:
            bool: True si succès, False sinon
        """
        try:
            # Récupère les données
            form_data = state_manager.get_form_data(session_id)
            
            # Charge les contacts existants
            contacts = json.loads(self.contacts_file.read_text(encoding='utf-8'))
            
            # Crée le nouveau contact
            contact = {
                'id': len(contacts) + 1,
                'nom': form_data['nom'],
                'email': form_data['email'],
                'telephone': form_data['telephone'],
                'programme': form_data['programme'],
                'message': form_data.get('message', ''),
                'created_at': datetime.now().isoformat(),
                'status': 'nouveau',
                'source': 'chatbot',
                'session_id': session_id[:8]
            }
            
            # Ajoute à la liste
            contacts.append(contact)
            
            # Sauvegarde
            self.contacts_file.write_text(
                json.dumps(contacts, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
            
            logger.info(f"Contact sauvegardé: {contact['email']}")
            return True
        
        except Exception as e:
            logger.error(f"Erreur sauvegarde contact: {e}")
            return False
    
    def get_contact_count(self) -> int:
        """Retourne le nombre de contacts enregistrés"""
        try:
            contacts = json.loads(self.contacts_file.read_text(encoding='utf-8'))
            return len(contacts)
        except:
            return 0
