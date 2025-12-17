from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from src.agents.agent_orchestrateur import AgentSuperviseur
import uuid
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for the widget

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('logs/chatbot_api.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize supervisor
supervisor = AgentSuperviseur()

# Store sessions (in production, use Redis or database)
sessions = {}

# Suggested questions by context

SUGGESTIONS_MAP = {
    'welcome': [
        "Où se trouve le campus principal ?",
        "Je souhaite être contacté",
        "Qui est le directeur de l'esilv ?",
        "Quelle est la durée du cursus ingénieur ?"
    ],
    'programmes': [
        "Data & IA", 
        "FinTech",    
        "Mécanique", 
        "Energie et villes durables",
    ],
    'cursus_general': [
        "Quelle est la durée du cursus ingénieur ?",
        "Existe t'il un double diplôme ingénieur-manager ?",
        "Y a-t-il un programme en Data Science ?",
        "Quels sont les programmes disponibles ?"
    ],
    'admission': [
        "Y a-t-il des bourses disponibles ?",
        "Acceptez-vous les étudiants internationaux ?"
    ],
    'vie_etudiante': [
        "Quelles sont les associations étudiantes ?",
        "Quelles activités sportives sont proposées ?"
    ],
    'contact': [
        "Où se trouve le campus principal ?",
        "Quelle est la durée du cursus ingénieur ?"
    ],
    'default': [
        "Où se trouve le campus principal ?",
        "Je souhaite être contacté",
        "Quelles sont les associations étudiantes ?",
        "Quelle est la durée du cursus ingénieur ?"
    ]
}

def get_suggestions(message: str, response: str) -> list:
    """Determine contextual suggestions based on message and response"""
    message_lower = message.lower()
    response_lower = response.lower()
    
    # 1. Contexte CONTACT
    if any(word in message_lower for word in ['contact', 'appel', 'rappel', 'contacté']):
        return SUGGESTIONS_MAP['contact']
    
    # 2. Contexte ADMISSION / INTERNATIONAL / BOURSES
    if any(word in message_lower for word in ['admission', 'bourse', 'international', 'étranger', 'prix', 'coût']):
        return SUGGESTIONS_MAP['admission']
        
    # 3. Contexte VIE ÉTUDIANTE / SPORT / ASSOS
    if any(word in message_lower for word in ['association', 'asso', 'sport', 'vie', 'activité']):
        return SUGGESTIONS_MAP['vie_etudiante']
    
    # 4. Contexte MAJEURES (Spécificités)
    majeure_keywords = ['data', 'ia', 'intelligence', 'cyber', 'sécurité', 'fintech', 'mécanique', 'énergie', 'villes']
    if any(word in message_lower for word in majeure_keywords) or any(word in response_lower for word in majeure_keywords):
        return SUGGESTIONS_MAP['programmes']

    # 5. Contexte CURSUS GÉNÉRAL
    gen_keywords = ['programme', 'formation', 'cursus', 'diplôme', 'ingénieur', 'manager', 'spécialité']
    if any(word in message_lower for word in gen_keywords) or any(word in response_lower for word in gen_keywords):
        return SUGGESTIONS_MAP['cursus_general']
    
    # 6. Fallback si la réponse mentionne un contact
    if 'contact' in response_lower:
        return SUGGESTIONS_MAP['contact']
    
    return SUGGESTIONS_MAP['default']

@app.route('/api/chat', methods=['POST'])
def chat():
    """Main chat endpoint"""
    try:
        data = request.json
        message = data.get('message', '').strip()
        session_id = data.get('session_id')
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Initialize session if new
        if session_id not in sessions:
            sessions[session_id] = {
                'created_at': datetime.now().isoformat(),
                'messages': []
            }
        
        logger.info(f"📩 Message from session {session_id[:8]}: {message[:100]}")
        
        # Process message through supervisor
        response = supervisor.run(
            message=message,
            session_id=session_id
        )

        # Store in session history
        sessions[session_id]['messages'].append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.now().isoformat()
        })
        sessions[session_id]['messages'].append({
            'role': 'assistant',
            'content': response,
            'timestamp': datetime.now().isoformat()
        })
        
        # Get contextual suggestions
        suggestions = get_suggestions(message, response)

        is_form_detected = "nom complet" in response.lower() or "FORMULAIRE" in response.upper()
        
        logger.info(f"✅ Response sent to session {session_id[:8]}")
        
        return jsonify({
            'session_id': session_id,
            'message': response,
            'suggestions': suggestions,
            'is_form': is_form_detected,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Error in chat endpoint: {e}", exc_info=True)
        return jsonify({
            'error': 'Une erreur s\'est produite. Veuillez réessayer.',
            'details': str(e)
        }), 500


@app.route('/api/session/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get session history"""
    try:
        if session_id not in sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        return jsonify({
            'session_id': session_id,
            'session': sessions[session_id]
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting session: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'active_sessions': len(sessions)
    })


@app.route('/api/stats', methods=['GET'])
def stats():
    """Get chatbot statistics"""
    try:
        total_messages = sum(len(s['messages']) for s in sessions.values())
        
        return jsonify({
            'total_sessions': len(sessions),
            'total_messages': total_messages,
            'supervisor_stats': supervisor.get_statistics('global')
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    logger.info("🚀 Starting Chatbot API Server...")
    logger.info("📝 Endpoints:")
    logger.info("   POST /api/chat - Send message")
    logger.info("   GET  /api/session/<id> - Get session history")
    logger.info("   GET  /api/health - Health check")
    logger.info("   GET  /api/stats - Statistics")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False
    )