# esilv_scraper.py
"""
Scraper complet du site ESILV
Extrait toutes les pages importantes et les convertit pour le RAG

Usage:
    python esilv_scraper.py
"""

import requests
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin, urlparse
import json
import time
import logging
from typing import List, Dict, Set

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)


class ESILVScraper:
    """Scraper complet du site ESILV"""
    
    def __init__(self, output_dir: str = "data/scraping"):
        """
        Initialise le scraper ESILV
        
        Args:
            output_dir: Répertoire de sortie
        """
        self.base_url = "https://www.esilv.fr"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        # Pages à scraper (sections importantes du site)
        self.target_pages = {
            # Formations et programmes
            'formations': '/formations/',
            'programmes_grande_ecole': '/programmes/cycle-ingenieur/',
            'specialisations': '/programmes/specialisations/',
            'bachelors': '/programmes/bachelor/',
            'masters': '/programmes/masters/',
            'apprentissage': '/programmes/apprentissage/',
            
            # Admissions
            'admissions': '/admissions/',
            'concours': '/admissions/concours/',
            'admissions_paralleles': '/admissions/admissions-paralleles/',
            'admissions_internationales': '/admissions/admissions-internationales/',
            
            # École
            'ecole': '/ecole/',
            'campus': '/ecole/campus/',
            'laboratoires': '/ecole/recherche/',
            'partenariats': '/ecole/partenariats/',
            'international': '/ecole/international/',
            
            # Vie étudiante
            'vie_etudiante': '/vie-etudiante/',
            'associations': '/vie-etudiante/associations/',
            'stages': '/vie-etudiante/stages-emploi/',
            'logement': '/vie-etudiante/logement/',
            
            # Contact et infos pratiques
            'contact': '/contact/',
            'journees_portes_ouvertes': '/evenements/journees-portes-ouvertes/',
        }
        
        self.visited_urls: Set[str] = set()
        self.scraped_data: List[Dict] = []
        
        logger.info("✓ ESILVScraper initialisé")
    
    def scrape_all(self, delay: float = 1.0, max_depth: int = 2) -> Dict:
        """
        Scrape toutes les pages importantes du site ESILV
        
        Args:
            delay: Délai entre requêtes (secondes)
            max_depth: Profondeur maximale de scraping
            
        Returns:
            Dict avec statistiques
        """
        logger.info(f"🚀 Début du scraping complet de {self.base_url}")
        logger.info(f"📋 {len(self.target_pages)} sections à scraper")
        
        start_time = time.time()
        
        # Scrape chaque section principale
        for section_name, section_path in self.target_pages.items():
            logger.info(f"\n📂 Section: {section_name}")
            url = urljoin(self.base_url, section_path)
            
            try:
                self._scrape_page(url, section_name, depth=0, max_depth=max_depth)
                time.sleep(delay)  # Respecte le serveur
            except Exception as e:
                logger.error(f"❌ Erreur sur {section_name}: {e}")
        
        # Sauvegarde les données
        self._save_data()
        
        # Convertit pour le RAG
        rag_file = self._convert_to_rag()
        
        elapsed = time.time() - start_time
        
        logger.info(f"\n✅ Scraping terminé en {elapsed:.1f}s")
        logger.info(f"📄 {len(self.scraped_data)} pages scrapées")
        logger.info(f"💾 Fichier RAG: {rag_file}")
        
        return {
            'success': True,
            'pages_scraped': len(self.scraped_data),
            'elapsed_time': elapsed,
            'rag_file': rag_file
        }
    
    def _scrape_page(self, url: str, section: str, depth: int = 0, max_depth: int = 2):
        """
        Scrape une page et ses liens internes
        
        Args:
            url: URL à scraper
            section: Nom de la section
            depth: Profondeur actuelle
            max_depth: Profondeur maximale
        """
        # Évite les doublons
        if url in self.visited_urls or depth > max_depth:
            return
        
        self.visited_urls.add(url)
        
        try:
            logger.info(f"  {'  ' * depth}🔍 {url}")
            
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extrait le contenu
            page_data = self._extract_content(soup, url, section)
            
            if page_data['content']:
                self.scraped_data.append(page_data)
                logger.info(f"  {'  ' * depth}✓ Contenu extrait ({len(page_data['content'])} caractères)")
            
            # Trouve les liens internes pour scraping récursif
            if depth < max_depth:
                internal_links = self._find_internal_links(soup, url, section)
                for link in internal_links[:5]:  # Limite à 5 sous-pages par page
                    time.sleep(0.5)
                    self._scrape_page(link, section, depth + 1, max_depth)
        
        except requests.RequestException as e:
            logger.warning(f"  {'  ' * depth}⚠️ Erreur requête: {e}")
        except Exception as e:
            logger.error(f"  {'  ' * depth}❌ Erreur: {e}")
    
    def _extract_content(self, soup: BeautifulSoup, url: str, section: str) -> Dict:
        """
        Extrait le contenu principal d'une page
        
        Args:
            soup: Objet BeautifulSoup
            url: URL de la page
            section: Nom de la section
            
        Returns:
            Dict avec le contenu structuré
        """
        # Titre
        title = ""
        if soup.title:
            title = soup.title.string.strip()
        elif soup.find('h1'):
            title = soup.find('h1').get_text(strip=True)
        
        # Supprime les éléments inutiles
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'iframe', 'noscript']):
            tag.decompose()
        
        # Contenu principal
        content_parts = []
        
        # 1. Titres principaux (h1, h2, h3)
        headings = soup.find_all(['h1', 'h2', 'h3'])
        for h in headings:
            text = h.get_text(strip=True)
            if text and len(text) > 3:
                content_parts.append(f"## {text}")
        
        # 2. Paragraphes
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            text = p.get_text(strip=True)
            if text and len(text) > 30:  # Ignore les paragraphes trop courts
                content_parts.append(text)
        
        # 3. Listes
        lists = soup.find_all(['ul', 'ol'])
        for lst in lists:
            items = lst.find_all('li')
            if items:
                list_text = []
                for item in items:
                    text = item.get_text(strip=True)
                    if text:
                        list_text.append(f"- {text}")
                if list_text:
                    content_parts.extend(list_text)
        
        # 4. Tableaux (pour les infos pratiques, tarifs, etc.)
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if cells:
                    row_text = ' | '.join([cell.get_text(strip=True) for cell in cells if cell.get_text(strip=True)])
                    if row_text:
                        content_parts.append(row_text)
        
        # Combine le contenu
        content = '\n\n'.join(content_parts)
        
        # Nettoie
        content = self._clean_text(content)
        
        return {
            'url': url,
            'title': title,
            'section': section,
            'content': content,
            'scraped_at': datetime.now().isoformat(),
            'word_count': len(content.split())
        }
    
    def _find_internal_links(self, soup: BeautifulSoup, current_url: str, section: str) -> List[str]:
        """
        Trouve les liens internes pertinents d'une page
        
        Args:
            soup: Objet BeautifulSoup
            current_url: URL actuelle
            section: Section actuelle
            
        Returns:
            Liste d'URLs internes
        """
        internal_links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Construit l'URL complète
            full_url = urljoin(current_url, href)
            
            # Vérifie si c'est un lien interne ESILV
            parsed = urlparse(full_url)
            if parsed.netloc and 'esilv.fr' not in parsed.netloc:
                continue
            
            # Ignore certains types de liens
            ignore_patterns = [
                '#', 'javascript:', 'mailto:', 'tel:',
                '.pdf', '.jpg', '.png', '.gif',
                '/wp-admin/', '/wp-content/', '/wp-json/'
            ]
            if any(pattern in full_url.lower() for pattern in ignore_patterns):
                continue
            
            # Ignore si déjà visité
            if full_url in self.visited_urls:
                continue
            
            internal_links.append(full_url)
        
        return internal_links
    
    def _clean_text(self, text: str) -> str:
        """
        Nettoie le texte extrait
        
        Args:
            text: Texte brut
            
        Returns:
            Texte nettoyé
        """
        import re
        
        # Supprime les espaces multiples
        text = re.sub(r'\s+', ' ', text)
        
        # Supprime les lignes vides multiples
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        
        # Trim
        text = text.strip()
        
        return text
    
    def _save_data(self):
        """Sauvegarde les données brutes en JSON"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            json_file = self.output_dir / f"esilv_scraped_{timestamp}.json"
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(self.scraped_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 JSON sauvegardé: {json_file}")
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde JSON: {e}")
    
    def _convert_to_rag(self) -> str:
        """
        Convertit les données scrapées en format texte pour le RAG
        
        Returns:
            Chemin du fichier créé
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            rag_file = self.output_dir / f"esilv_knowledge_{timestamp}.txt"
            
            with open(rag_file, 'w', encoding='utf-8') as f:
                for page in self.scraped_data:
                    if page['content']:
                        # Format structuré pour le RAG
                        f.write(f"=== {page['title']} ===\n")
                        f.write(f"Section: {page['section']}\n")
                        f.write(f"URL: {page['url']}\n\n")
                        f.write(page['content'])
                        f.write("\n\n" + "="*80 + "\n\n")
            
            logger.info(f"📄 Fichier RAG créé: {rag_file}")
            return str(rag_file)
        
        except Exception as e:
            logger.error(f"❌ Erreur conversion RAG: {e}")
            return ""
    
    def scrape_specific_sections(self, sections: List[str], delay: float = 1.0) -> Dict:
        """
        Scrape seulement certaines sections spécifiques
        
        Args:
            sections: Liste des noms de sections à scraper
            delay: Délai entre requêtes
            
        Returns:
            Dict avec résultats
        """
        logger.info(f"🎯 Scraping de sections spécifiques: {sections}")
        
        for section_name in sections:
            if section_name in self.target_pages:
                section_path = self.target_pages[section_name]
                url = urljoin(self.base_url, section_path)
                
                logger.info(f"\n📂 Section: {section_name}")
                self._scrape_page(url, section_name, depth=0, max_depth=1)
                time.sleep(delay)
            else:
                logger.warning(f"⚠️ Section inconnue: {section_name}")
        
        self._save_data()
        rag_file = self._convert_to_rag()
        
        return {
            'success': True,
            'pages_scraped': len(self.scraped_data),
            'rag_file': rag_file
        }


# ==========================================
# FONCTIONS RAPIDES
# ==========================================

def scrape_esilv_full(delay: float = 1.0, max_depth: int = 2) -> str:
    """
    Scrape complet du site ESILV
    
    Args:
        delay: Délai entre requêtes (secondes)
        max_depth: Profondeur de scraping (0-2)
        
    Returns:
        Chemin du fichier RAG créé
    """
    scraper = ESILVScraper()
    result = scraper.scrape_all(delay=delay, max_depth=max_depth)
    return result['rag_file']


def scrape_esilv_sections(sections: List[str], delay: float = 1.0) -> str:
    """
    Scrape des sections spécifiques
    
    Args:
        sections: Liste des sections (ex: ['formations', 'admissions'])
        delay: Délai entre requêtes
        
    Returns:
        Chemin du fichier RAG créé
    """
    scraper = ESILVScraper()
    result = scraper.scrape_specific_sections(sections, delay=delay)
    return result['rag_file']


# ==========================================
# SCRIPT PRINCIPAL
# ==========================================

if __name__ == "__main__":
    import sys
    
    print("""
╔════════════════════════════════════════════════════════════╗
║           ESILV Website Scraper                            ║
╚════════════════════════════════════════════════════════════╝
""")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("""
Usage:
    python esilv_scraper.py                    # Scrape complet (rapide)
    python esilv_scraper.py --full             # Scrape complet (profond)
    python esilv_scraper.py --sections <list>  # Sections spécifiques

Exemples:
    python esilv_scraper.py
    python esilv_scraper.py --full
    python esilv_scraper.py --sections formations admissions

Sections disponibles:
    formations, programmes_grande_ecole, specialisations, bachelors, 
    masters, apprentissage, admissions, concours, admissions_paralleles,
    admissions_internationales, ecole, campus, laboratoires, partenariats,
    international, vie_etudiante, associations, stages, logement, contact
        """)
        sys.exit(0)
    
    scraper = ESILVScraper()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--full":
        # Scraping profond
        print("🔥 Mode COMPLET - Scraping en profondeur (peut prendre 5-10 min)\n")
        result = scraper.scrape_all(delay=1.0, max_depth=2)
    
    elif len(sys.argv) > 1 and sys.argv[1] == "--sections":
        # Sections spécifiques
        sections = sys.argv[2:]
        if not sections:
            print("❌ Spécifiez au moins une section")
            sys.exit(1)
        
        print(f"🎯 Scraping de {len(sections)} section(s)\n")
        result = scraper.scrape_specific_sections(sections, delay=1.0)
    
    else:
        # Scraping rapide par défaut
        print("⚡ Mode RAPIDE - Scraping des pages principales (1-2 min)\n")
        result = scraper.scrape_all(delay=1.0, max_depth=1)
    
    print(f"""
╔════════════════════════════════════════════════════════════╗
║                   SCRAPING TERMINÉ                         ║
╠════════════════════════════════════════════════════════════╣
║  📄 Pages scrapées: {result['pages_scraped']:<37} ║
║  ⏱️  Temps écoulé: {result['elapsed_time']:.1f}s{' ' * (37 - len(f"{result['elapsed_time']:.1f}s"))}║
║  💾 Fichier RAG: {Path(result['rag_file']).name:<40}║
╚════════════════════════════════════════════════════════════╝

✅ Le fichier est prêt pour le RAG dans data/rag/
🤖 Redémarrez l'agent RAG pour charger les nouvelles données
    """)