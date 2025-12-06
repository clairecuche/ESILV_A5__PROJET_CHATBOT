from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

from src.agents.state_manager import state_manager
from src.agents.prompts import prompts, get_field_question, format_confirmation_message
import logging
import re
import json
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class AgentFormulaire:
    def __init__(self):
        self.llm = ChatOllama(
            model="gemma2:2b", 
            temperature=0.3,
            num_predict=256,      # Limite tokens générés
            num_ctx=2048          # Réduit contexte
        )
        self.required_fields = ['nom', 'email', 'telephone', 'programme']
        
        self.contacts_file = Path("data/contacts/contacts.json")
        self._ensure_contacts_file()
        
        self.extraction_prompt = ChatPromptTemplate.from_messages([
            ("system", """Tu es un assistant spécialisé dans l'extraction d'informations de contact.
Extrait UNIQUEMENT les informations suivantes du message :
- email (format valide)
- telephone (format français)
- nom (si c'est clairement un nom)
- programme (nom de formation)

Réponds UNIQUEMENT au format JSON sans aucun texte supplémentaire :
{{"email": "...", "telephone": "...", "nom": "...", "programme": "..."}}

Si une information n'est pas présente, utilise null."""),
            ("human", "{message}")
        ])
        
        self.extraction_chain = self.extraction_prompt | self.llm | StrOutputParser()
        
        logger.info("Agent Formulaire initialisé")
    
    def _ensure_contacts_file(self):
        self.contacts_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.contacts_file.exists():
            self.contacts_file.write_text("[]", encoding='utf-8')
            logger.info(f"✓ Fichier contacts créé: {self.contacts_file}")
    
    def run(self, message: str, session_id: str) -> str:
        logger.info(f"\n{'='*50}")
        logger.info(f"AGENT FORMULAIRE - Session: {session_id[:8]}")
        logger.info(f"{'='*50}")
        
        session = state_manager.get_or_create_session(session_id)
        form_data = session.form_data
        
        logger.info(f"État actuel du formulaire:")
        for field in self.required_fields:
            value = form_data.get(field)
            status = "✓" if value else "○"
            logger.info(f"  {status} {field}: {value if value else 'manquant'}")

        # --- Début du mode édition (pour la correction d'un champ spécifique) ---
        if hasattr(session, 'editing_field') and session.editing_field:
            field = session.editing_field
            new_value = message.strip()

            logger.info(f"Modification du champ '{field}' avec la valeur: {new_value}")

            # Revalider la nouvelle valeur avant de la sauvegarder
            validated_data = self._validate_extracted_data({field: new_value})
            
            if validated_data['valid'] and field in validated_data['data']:
                state_manager.update_form_data(session_id, field, validated_data['data'][field])
                session.editing_field = None
                session.awaiting_confirmation = True
                return self._generate_confirmation(session_id)
            else:
                # Gérer l'erreur de validation
                error_msg = self._get_validation_error_message(validated_data['errors'])
                # L'agent reste en mode editing pour le champ actuel
                return f"{error_msg} Veuillez saisir à nouveau {self._get_field_label(field)} :"
        # --- Fin du mode édition ---
        
        # --- Gestion de la confirmation (oui/non/modifier) ---
        if session.awaiting_confirmation:
            logger.info("En attente de confirmation utilisateur")
            return self._handle_confirmation(message, session_id)
        # --- Fin de la gestion de la confirmation ---
        
        logger.info(f"Extraction d'informations du message: '{message}'")
        
        # 1. Extraction des informations (nouvelle et existante)
        extracted = self._extract_info(message, session_id)
        
        if extracted:
            logger.info(f"Informations extraites: {extracted}")
            
            # 2. Validation des informations extraites
            validated = self._validate_extracted_data(extracted)
            
            if validated['valid']:
                # 3. Mise à jour de toutes les données valides
                for field, value in validated['data'].items():
                    state_manager.update_form_data(session_id, field, value)
                    logger.info(f"Champ '{field}' mis à jour: {value}")
            else:
                logger.warning(f"Validation échouée: {validated['errors']}")
                # Retourne l'erreur si au moins une information est invalide
                return self._get_validation_error_message(validated['errors'])
        else:
            logger.info("○ Aucune information structurée extraite")
        
        # 4. Vérification des champs manquants après extraction et mise à jour
        missing = self._get_missing_fields(session_id)
        
        if not missing:
            # Tous les champs sont remplis (potentiellement en un seul message ou via le formulaire)
            logger.info("✓ Formulaire complet, demande de confirmation")
            session.awaiting_confirmation = True
            return self._generate_confirmation(session_id)
        else:
            # Il manque des champs, demande du premier champ manquant
            logger.info(f"Champs manquants: {missing}")
            next_field = missing[0]
            field_labels = {
                'nom': 'votre nom complet',
                'email': 'votre adresse email',
                'telephone': 'votre numéro de téléphone',
                'programme': 'le programme qui vous intéresse'
            }
            # Message générique pour le champ manquant
            return f"Pour continuer, j'aurais besoin de {field_labels[next_field]} :"
    
    # Nouvelle méthode d'aide
    def _get_field_label(self, field: str) -> str:
        field_labels = {
            'nom': 'votre nom complet',
            'email': 'votre adresse email',
            'telephone': 'votre numéro de téléphone',
            'programme': 'le programme qui vous intéresse'
        }
        return field_labels.get(field, field)
    
    def _extract_info(self, message: str, session_id: str) -> dict:
        extracted = {}
        message_clean = message.strip()
        
        # --- Extraction Email ---
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, message_clean)
        if email_match:
            extracted['email'] = email_match.group()
            logger.info(f"✓ Email détecté: {extracted['email']}")
        
        # --- Extraction Téléphone ---
        # Pattern pour numéros français (commençant par +33 ou 0)
        phone_pattern = r'(?:\+33|0)[1-9](?:[\s\-\.]?\d{2}){4}' 
        phone_match = re.search(phone_pattern, message_clean)
        if phone_match:
            extracted['telephone'] = phone_match.group()
            logger.info(f"✓ Téléphone détecté: {extracted['telephone']}")
        
        # --- Extraction Programme ---
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
                logger.info(f"✓ Programme détecté: {programme_name}")
                break
        
        # --- Extraction Nom ---
        if not extracted:
            form_data = state_manager.get_form_data(session_id)
            if not form_data.get('nom'):
                # Mots-clés qui indiquent que le message n'est PAS un nom
                non_name_keywords = [
                    'je veux', 'je souhaite', 'je voudrais', 'je vais',
                    'contact', 'contacte', 'contacté', 'appel', 'rappel', 
                    'information', 'brochure', 'renseignement', 'inscription',
                    'bonjour', 'salut', 'coucou', 'bonsoir', 'bon matin',
                    's\'il vous plaît', 'stp', 'svp', 'merci', 'cordialement'
                ]
                
                is_likely_name = not any(keyword in message_lower for keyword in non_name_keywords)
                
                is_valid = (
                    message_clean.strip() and
                    not any(char.isdigit() for char in message_clean) and
                    len(message_clean) >= 2 and
                    len(message_clean) <= 100
                )
                
                if is_likely_name and is_valid:
                    # Tente d'interpréter le message comme un nom (capitalisation simple)
                    formatted_name = ' '.join(word.capitalize() for word in message_clean.split())
                    extracted['nom'] = formatted_name
                    logger.info(f"✓ Message interprété comme nom: {extracted['nom']}")
                else:
                    logger.info("✗ Message non interprété comme nom")
        
        # --- Extraction Programme (si l'utilisateur a déjà donné son nom et donne le programme dans le message suivant) ---
        if not extracted:
            form_data = state_manager.get_form_data(session_id)
            if not form_data.get('programme') and form_data.get('nom'):
                extracted['programme'] = message_clean
                logger.info(f"✓ Message interprété comme programme: {extracted['programme']}")
        
        return extracted
    
    def _validate_extracted_data(self, extracted: dict) -> dict:
        validated_data = {}
        errors = {}
        
        if 'email' in extracted:
            email = extracted['email']
            if self._is_valid_email(email):
                validated_data['email'] = email.lower()
            else:
                errors['email'] = "Format d'email invalide"
        
        if 'telephone' in extracted:
            phone = extracted['telephone']
            normalized_phone = self._normalize_phone(phone)
            if normalized_phone:
                validated_data['telephone'] = normalized_phone
            else:
                errors['telephone'] = "Format de téléphone invalide"
        
        if 'nom' in extracted:
            nom = extracted['nom'].strip()
            if len(nom) >= 2:
                validated_data['nom'] = nom
            else:
                errors['nom'] = "Nom trop court"
        
        if 'programme' in extracted:
            validated_data['programme'] = extracted['programme'].strip()
        
        return {
            'valid': len(errors) == 0,
            'data': validated_data,
            'errors': errors
        }
    
    def _is_valid_email(self, email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _normalize_phone(self, phone: str) -> str:
        phone_clean = re.sub(r'[\s\-\.]', '', phone)
        
        if re.match(r'^0[1-9]\d{8}$', phone_clean):
            return '+33' + phone_clean[1:]
        elif re.match(r'^\+33[1-9]\d{8}$', phone_clean):
            return phone_clean
        else:
            return None
    
    def _get_validation_error_message(self, errors: dict) -> str:
        if 'email' in errors:
            return prompts.VALIDATION_ERRORS['email']
        elif 'telephone' in errors:
            return prompts.VALIDATION_ERRORS['telephone']
        elif 'nom' in errors:
            return prompts.VALIDATION_ERRORS['nom']
        else:
            return "Les informations fournies semblent incorrectes. Pouvez-vous réessayer ?"
    
    def _get_missing_fields(self, session_id: str) -> list:
        form_data = state_manager.get_form_data(session_id)
        return [f for f in self.required_fields if not form_data.get(f)]
    
    def _ask_next_field(self, field: str) -> str:
        return get_field_question(field)
    
    def _generate_confirmation(self, session_id: str) -> str:
        form_data = state_manager.get_form_data(session_id)
        return format_confirmation_message(form_data)
    
    def _handle_confirmation(self, message: str, session_id: str) -> str:
        logger.info(f"Traitement de la confirmation: '{message}'")
        
        session = state_manager.get_or_create_session(session_id)
        
        normalized = message.strip().lower()
        
        if normalized in ['oui', 'yes', 'ok', 'confirmé', 'confirmer', 'valider']:
            self._save_contact(session_id)
            
            session.form_completed = True
            session.awaiting_confirmation = False
            
            # Réinitialisation du formulaire après sauvegarde
            session.form_data = {
                'nom': None,
                'email': None,
                'telephone': None,
                'programme': None,
                'message': None
            }
            
            if hasattr(session, 'editing_field'):
                session.editing_field = None
            
            logger.info("✅ Formulaire complètement réinitialisé après sauvegarde")
            
            return "Parfait ! Votre demande a bien été enregistrée. Un conseiller vous contactera bientôt."
            
        elif normalized in ['non', 'non merci', 'annuler', 'modifier']:
            session.awaiting_confirmation = True
            return "D'accord, quel champ souhaitez-vous modifier ? (nom, email, téléphone, programme)"
        
        # Logique de détection du champ à modifier
        field_map = {
            'téléphone': 'telephone', 'telephone': 'telephone', 'tel': 'telephone', 'tél': 'telephone', 'phone': 'telephone',
            'nom': 'nom', 'name': 'nom', 'prénom': 'nom', 'prenom': 'nom',
            'email': 'email', 'mail': 'email', 'e-mail': 'email',
            'programme': 'programme', 'program': 'programme', 'formation': 'programme', 'cours': 'programme'
        }
        
        if normalized in field_map:
            field = field_map[normalized]
            
            session.editing_field = field
            session.awaiting_confirmation = False
            
            current_value = session.form_data.get(field, 'non renseigné')
            logger.info(f"✓ Mode édition activé pour le champ: {field}")
            return f"Quelle est {self._get_field_label(field)} ? (Actuel : {current_value})"
        else:
            return (
                "Je n'ai pas bien compris votre réponse. " +
                "Veuillez :\n" +
                "- Donner le nom du champ à modifier (nom, email, téléphone, programme)\n" +
                "- Ou répondre 'oui' pour confirmer\n" +
                "- Ou 'non' pour annuler"
            )
    
    def _save_contact(self, session_id: str) -> bool:
        try:
            form_data = state_manager.get_form_data(session_id)
            
            contacts = json.loads(self.contacts_file.read_text(encoding='utf-8'))
            
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
            
            contacts.append(contact)
            
            self.contacts_file.write_text(
                json.dumps(contacts, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
            
            logger.info(f"✓ Contact sauvegardé: {contact['email']}")
            return True
        
        except Exception as e:
            logger.error(f"✗ Erreur sauvegarde contact: {e}")
            return False
    
    def get_contact_count(self) -> int:
        try:
            contacts = json.loads(self.contacts_file.read_text(encoding='utf-8'))
            return len(contacts)
        except:
            return 0