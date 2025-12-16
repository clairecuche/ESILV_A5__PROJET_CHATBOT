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
        "Quels sont les programmes disponibles ?",
        "Comment s'inscrire ?",
        "Je souhaite être contacté",
        "Informations sur la Cybersécurité"
    ],
    'programmes': [
        "Data & IA",
        "Cybersécurité",
        "FinTech",
        "Systèmes Embarqués"
    ],
    'contact': [
        "Oui, contactez-moi",
        "Voir d'autres programmes"
    ],
    'default': [
        "Les programmes",
        "Les admissions",
        "Être contacté"
    ]
}

def get_suggestions(message: str, response: str) -> list:
    """Determine contextual suggestions based on message and response"""
    message_lower = message.lower()
    response_lower = response.lower()
    
    # Contact context
    if any(word in message_lower for word in ['contact', 'appel', 'rappel', 'contacté']):
        return SUGGESTIONS_MAP['contact']
    
    # Programme context
    if any(word in message_lower for word in ['programme', 'formation', 'cursus']):
        return SUGGESTIONS_MAP['programmes']
    
    # If response mentions contacting
    if 'contacté' in response_lower or 'contact' in response_lower:
        return SUGGESTIONS_MAP['contact']
    
    # If response mentions programmes
    if 'programme' in response_lower or 'formation' in response_lower:
        return SUGGESTIONS_MAP['programmes']
    
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
        
        logger.info(f"✅ Response sent to session {session_id[:8]}")
        
        return jsonify({
            'session_id': session_id,
            'message': response,
            'suggestions': suggestions,
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