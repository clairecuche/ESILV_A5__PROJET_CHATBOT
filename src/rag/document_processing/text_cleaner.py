import re
import logging

logger = logging.getLogger(__name__)


class TextCleaner:
    """Nettoie et normalise le texte extrait des PDFs"""
    
    def clean(self, text: str) -> str:
        """Nettoie le texte"""
        
        if not text:
            return ""
        
        # Supprimer les sauts de ligne excessifs
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Supprimer les espaces multiples
        text = re.sub(r' {2,}', ' ', text)
        
        # Supprimer les tabulations
        text = text.replace('\t', ' ')
        
        # Normaliser les tirets
        text = text.replace('–', '-').replace('—', '-')
        
        # Supprimer les caractères de contrôle
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        # Strip les espaces en début et fin
        text = text.strip()
        
        return text