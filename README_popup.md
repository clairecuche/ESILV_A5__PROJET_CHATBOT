# 🎓 ESILV Chatbot Widget - Installation

Ce projet permet d'intégrer un chatbot intelligent sur le site web de l'ESILV sous forme de pop-up.

## 📁 Structure du projet

```
votre_projet/
├── api_chatbot.py          # Serveur Flask (API backend)
├── index.html              # Page de démonstration ESILV avec widget
├── src/
│   └── agents/
│       └── agent_orchestrateur.py  # Votre logique existante
├── requirements.txt        # Dépendances Python
└── logs/                   # Logs des conversations
```

## 🚀 Installation

### 1. Installer les dépendances

```bash
pip install flask flask-cors
```

Ou ajoutez à votre `requirements.txt` :
```
flask==3.0.0
flask-cors==4.0.0
```

### 2. Créer le dossier logs

```bash
mkdir -p logs
```

### 3. Lancer l'API Flask

```bash
python api_chatbot.py
```

L'API sera accessible sur `http://localhost:5000`

**Endpoints disponibles :**
- `POST /api/chat` - Envoyer un message
- `GET /api/session/<session_id>` - Récupérer l'historique
- `GET /api/health` - Vérifier l'état du serveur
- `GET /api/stats` - Statistiques globales

### 4. Ouvrir la page de démonstration

Ouvrez simplement `index.html` dans votre navigateur, ou utilisez un serveur local :

```bash
# Option 1 : Python
python -m http.server 8000

# Option 2 : Node.js
npx serve

# Option 3 : Ouvrir directement le fichier
open index.html  # Mac
start index.html # Windows
```

Puis visitez : `http://localhost:8000`

## 🎨 Fonctionnalités du Widget

### Interface
- ✅ Bouton flottant en bas à droite
- ✅ Pop-up moderne et responsive
- ✅ Animations fluides
- ✅ Design cohérent avec la charte ESILV
- ✅ Compatible mobile et desktop

### Chatbot
- ✅ Connexion à votre logique RAG existante
- ✅ Suggestions contextuelles intelligentes
- ✅ Indicateur de frappe
- ✅ Historique de conversation
- ✅ Gestion des sessions

## 🔧 Configuration

### Modifier l'URL de l'API

Dans `index.html`, ligne ~370 :
```javascript
const API_URL = 'http://localhost:5000/api/chat';
```

Pour la production, changez en :
```javascript
const API_URL = 'https://votre-domaine.com/api/chat';
```

### Personnaliser les couleurs

Dans `index.html`, section `<style>` :
```css
/* Couleur principale */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Modifier les couleurs selon votre charte */
```

### Modifier le message de bienvenue

Dans `api_chatbot.py`, ajoutez dans les suggestions :
```python
SUGGESTIONS_MAP = {
    'welcome': [
        "Vos questions personnalisées ici",
        # ...
    ]
}
```

## 📱 Intégration sur le vrai site ESILV

### Option 1 : Injection via script (recommandé)

Créez un fichier `chatbot-widget.js` :

```javascript
(function() {
    // Injecter le CSS
    const style = document.createElement('link');
    style.rel = 'stylesheet';
    style.href = 'https://votre-cdn.com/chatbot-widget.css';
    document.head.appendChild(style);

    // Injecter le HTML du widget
    const widget = document.createElement('div');
    widget.innerHTML = `<!-- Code du widget ici -->`;
    document.body.appendChild(widget);

    // Injecter le JS
    const script = document.createElement('script');
    script.src = 'https://votre-cdn.com/chatbot-widget.js';
    document.body.appendChild(script);
})();
```

Puis sur le site ESILV, ajoutez avant `</body>` :
```html
<script src="https://votre-cdn.com/chatbot-loader.js"></script>
```

### Option 2 : iframe (plus simple mais moins flexible)

```html
<iframe 
    src="https://votre-domaine.com/chatbot-widget.html"
    style="position:fixed; bottom:20px; right:20px; width:400px; height:600px; border:none; z-index:9999;"
></iframe>
```

### Option 3 : Extension navigateur

Pour tester sans accès au site :
1. Créer une extension Chrome/Firefox
2. Injecter le widget via content script
3. Démonstration complète sans modifier le vrai site

## 🔒 Sécurité en Production

### 1. Activer HTTPS
```python
# api_chatbot.py
if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        ssl_context=('cert.pem', 'key.pem')  # Certificats SSL
    )
```

### 2. Limiter CORS
```python
# Autoriser uniquement votre domaine
CORS(app, resources={r"/api/*": {"origins": "https://www.esilv.fr"}})
```

### 3. Rate limiting
```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=lambda: request.remote_addr)

@app.route('/api/chat', methods=['POST'])
@limiter.limit("20 per minute")  # Max 20 messages/min
def chat():
    # ...
```

### 4. Authentification (optionnel)
```python
@app.before_request
def check_auth():
    token = request.headers.get('Authorization')
    if not verify_token(token):
        return jsonify({'error': 'Unauthorized'}), 401
```

## 📊 Monitoring

### Logs
Les conversations sont loggées dans `logs/chatbot_api.log`

### Statistiques
Consultez : `http://localhost:5000/api/stats`

Exemple de réponse :
```json
{
  "total_sessions": 42,
  "total_messages": 156,
  "supervisor_stats": {...}
}
```

## 🐛 Dépannage

### Le widget ne s'affiche pas
- Vérifiez que l'API Flask tourne (`curl http://localhost:5000/api/health`)
- Ouvrez la console navigateur (F12) pour voir les erreurs
- Vérifiez les CORS si domaine différent

### Messages ne s'envoient pas
- Vérifiez l'URL de l'API dans `index.html`
- Testez l'API avec curl :
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Bonjour", "session_id": "test123"}'
```

### Erreur CORS
Ajoutez dans `api_chatbot.py` :
```python
CORS(app, resources={r"/api/*": {"origins": "*"}})  # Pour dev uniquement
```

## 🚀 Déploiement

### Option 1 : Heroku
```bash
heroku create votre-chatbot-api
git push heroku main
```

### Option 2 : AWS / GCP / Azure
Utilisez Docker :
```dockerfile
FROM python:3.10
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "api_chatbot.py"]
```

### Option 3 : VPS (DigitalOcean, OVH...)
```bash
# Installer sur serveur
sudo apt install python3-pip nginx
pip3 install -r requirements.txt

# Lancer avec gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 api_chatbot:app

# Configurer nginx reverse proxy
# ...
```

## 📞 Support

Pour toute question :
- Email : support@esilv.fr
- Issues GitHub : [votre-repo]/issues

## 📝 Licence

© 2024 ESILV - Tous droits réservés
