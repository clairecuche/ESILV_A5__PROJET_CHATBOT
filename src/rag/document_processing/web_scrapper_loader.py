import json
from pathlib import Path
from typing import List
from langchain_core.documents import Document as LCDocument

class WebScraperLoader:
    """
    Charge les données scrapées (JSON ou TXT) pour les intégrer au vector store
    """
    
    def __init__(self, data_folder: str = "data/autres"):
        self.data_folder = Path(data_folder)
    
    def load_json_scraped_data(self, json_file: str) -> List[LCDocument]:
        """
        Charge un fichier JSON scraped
        
        Format JSON attendu:
        [
            {
                "url": "https://...",
                "title": "...",
                "section": "...",
                "content": "...",
                "scraped_at": "...",
                "word_count": 123
            }
        ]
        """
        json_path = self.data_folder / json_file
        
        if not json_path.exists():
            print(f"❌ Fichier non trouvé: {json_path}")
            return []
        
        with open(json_path, 'r', encoding='utf-8') as f:
            scraped_data = json.load(f)
        
        documents = []
        
        for item in scraped_data:
            doc = LCDocument(
                page_content=item.get('content', ''),
                metadata={
                    'source': item.get('url', 'unknown'),
                    'title': item.get('title', ''),
                    'section': item.get('section', ''),
                    'scraped_at': item.get('scraped_at', ''),
                    'word_count': item.get('word_count', 0),
                    'type': 'web_scraped'
                }
            )
            documents.append(doc)
        
        print(f" Chargé {len(documents)} pages web depuis {json_file}")
        return documents
    
    def load_txt_scraped_data(self, txt_file: str) -> List[LCDocument]:
        """
        Charge un fichier TXT scraped
        
        Format TXT attendu:
        === Titre ===
        Section: nom_section
        URL: https://...
        
        Contenu...
        ================================================================================
        """
        txt_path = self.data_folder / txt_file
        
        if not txt_path.exists():
            print(f" Fichier non trouvé: {txt_path}")
            return []
        
        with open(txt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        documents = []
        pages = content.split('=' * 80)
        
        for page in pages:
            if not page.strip():
                continue
            
            lines = page.strip().split('\n')
            title = ''
            section = ''
            url = ''
            content_lines = []
            in_content = False
            
            for line in lines:
                if line.startswith('===') and line.endswith('==='):
                    title = line.strip('= ')
                elif line.startswith('Section:'):
                    section = line.replace('Section:', '').strip()
                elif line.startswith('URL:'):
                    url = line.replace('URL:', '').strip()
                elif line.strip() == '':
                    if title:
                        in_content = True
                elif in_content:
                    content_lines.append(line)
            
            page_content = '\n'.join(content_lines).strip()
            
            if page_content:
                doc = LCDocument(
                    page_content=page_content,
                    metadata={
                        'source': url or 'unknown',
                        'title': title,
                        'section': section,
                        'type': 'web_scraped'
                    }
                )
                documents.append(doc)
        
        print(f" Chargé {len(documents)} pages web depuis {txt_file}")
        return documents
    
    def load_all_scraped_data(self) -> List[LCDocument]:
        """
        Charge TOUS les fichiers JSON et TXT du dossier data/scraping
        """
        all_documents = []
        
        # Charger tous les JSON
        json_files = list(self.data_folder.glob('*.json'))
        for json_file in json_files:
            docs = self.load_json_scraped_data(json_file.name)
            all_documents.extend(docs)
        
        # Charger tous les TXT
        txt_files = list(self.data_folder.glob('*.txt'))
        for txt_file in txt_files:
            docs = self.load_txt_scraped_data(txt_file.name)
            all_documents.extend(docs)
        
        print(f"\n Total: {len(all_documents)} documents web chargés")
        print(f"   - {len(json_files)} fichiers JSON")
        print(f"   - {len(txt_files)} fichiers TXT")
        
        return all_documents