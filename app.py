# app.py
"""
Application Streamlit - Chatbot Multi-Agents ESILV
Interface utilisateur pour le système de chatbot conversationnel
"""

import streamlit as st
from src.agents.agent_orchestrateur import AgentSuperviseur
import logging
from datetime import datetime
import uuid

# Configuration de la page
st.set_page_config(
    page_title="Chatbot ESILV",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# CSS personnalisé
st.markdown("""
<style>
    /* Style général */
    .main {
        background-color: #f8f9fa;
    }
    
    /* Messages utilisateur */
    .user-message {
        background-color: #007bff;
        color: white;
        padding: 12px 16px;
        border-radius: 18px;
        margin: 8px 0;
        margin-left: 20%;
        text-align: right;
    }
    
    /* Messages bot */
    .bot-message {
        background-color: #ffffff;
        color: #333;
        padding: 12px 16px;
        border-radius: 18px;
        margin: 8px 0;
        margin-right: 20%;
        border: 1px solid #e0e0e0;
    }
    
    /* En-tête */
    .header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
    }
    
    /* Statistiques */
    .stat-box {
        background-color: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    
    /* Boutons */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 45px;
        font-weight: 500;
    }
    
    /* Input */
    .stTextInput>div>div>input {
        border-radius: 20px;
    }
</style>
""", unsafe_allow_html=True)


# Initialisation de la session Streamlit
def init_session_state():
    """Initialise les variables de session Streamlit"""
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
        logger.info(f"Nouvelle session créée: {st.session_state.session_id[:8]}")
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'supervisor' not in st.session_state:
        with st.spinner("🔧 Initialisation du système..."):
            st.session_state.supervisor = AgentSuperviseur()
            logger.info("Superviseur initialisé")
    
    if 'conversation_started' not in st.session_state:
        st.session_state.conversation_started = False


def display_header():
    """Affiche l'en-tête de l'application"""
    st.markdown("""
    <div class="header">
        <h1>🎓 Chatbot ESILV</h1>
        <p>Votre assistant intelligent pour découvrir nos formations</p>
    </div>
    """, unsafe_allow_html=True)


def display_sidebar():
    """Affiche la barre latérale avec les statistiques"""
    with st.sidebar:
        st.markdown("### 📊 Informations")
        
        # Session ID
        st.markdown(f"""
        <div class="stat-box">
            <b>🆔 Session</b><br>
            <code>{st.session_state.session_id[:8]}...</code>
        </div>
        """, unsafe_allow_html=True)
        
        # Statistiques de conversation
        stats = st.session_state.supervisor.get_statistics(st.session_state.session_id)
        
        st.markdown(f"""
        <div class="stat-box">
            <b>💬 Messages échangés</b><br>
            <h2 style="margin:0; color:#667eea;">{stats.get('messages_count', 0)}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Progression du formulaire
        form_completion = stats.get('form_completion', 0)
        st.markdown(f"""
        <div class="stat-box">
            <b>📝 Formulaire</b><br>
            <div style="margin-top:10px;">
                <div style="background:#e0e0e0; border-radius:10px; height:20px;">
                    <div style="background:linear-gradient(90deg, #667eea, #764ba2); 
                                width:{form_completion}%; 
                                height:100%; 
                                border-radius:10px;
                                transition: width 0.3s ease;">
                    </div>
                </div>
                <p style="text-align:center; margin-top:5px;">{form_completion}%</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Boutons d'action
        st.markdown("### ⚙️ Actions")
        
        if st.button("🔄 Nouvelle conversation", use_container_width=True):
            reset_conversation()
            st.rerun()
        
        if st.button("📥 Exporter l'historique", use_container_width=True):
            export_conversation()
        
        st.markdown("---")
        
        # Informations système
        st.markdown("### ℹ️ Système")
        st.markdown("""
        <div class="stat-box">
            <b>🤖 Agents actifs</b><br>
            • Agent RAG<br>
            • Agent Formulaire<br>
            • Agent Interaction
        </div>
        """, unsafe_allow_html=True)
        
        # Guide d'utilisation
        with st.expander("📖 Guide d'utilisation"):
            st.markdown("""
            **Comment utiliser ce chatbot ?**
            
            1. **Poser des questions** sur les programmes, admissions, etc.
            2. **Demander à être contacté** pour obtenir plus d'informations
            3. **Modifier vos informations** si nécessaire
            
            **Exemples de questions :**
            - Quels sont les programmes disponibles ?
            - Comment s'inscrire ?
            - Je souhaite être contacté
            - Quels sont les frais de scolarité ?
            """)


def display_chat_history():
    """Affiche l'historique de la conversation"""
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f"""
            <div class="user-message">
                {message["content"]}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="bot-message">
                {message["content"]}
            </div>
            """, unsafe_allow_html=True)


def send_message(user_input: str):
    """Envoie un message et obtient la réponse du superviseur"""
    if not user_input.strip():
        return
    
    # Ajoute le message utilisateur
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "timestamp": datetime.now().isoformat()
    })
    
    # Obtient la réponse du superviseur
    with st.spinner("🤔 Réflexion en cours..."):
        try:
            response = st.session_state.supervisor.run(
                message=user_input,
                session_id=st.session_state.session_id
            )
            
            # Ajoute la réponse du bot
            st.session_state.messages.append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now().isoformat()
            })
            
            logger.info(f"Message traité avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement: {e}")
            st.error(f"Une erreur s'est produite : {str(e)}")


def reset_conversation():
    """Réinitialise la conversation"""
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.session_state.conversation_started = False
    logger.info(f"Conversation réinitialisée - Nouvelle session: {st.session_state.session_id[:8]}")


def export_conversation():
    """Exporte l'historique de conversation"""
    if not st.session_state.messages:
        st.warning("Aucun message à exporter")
        return
    
    # Crée un fichier texte avec l'historique
    export_text = f"Historique de conversation - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    export_text += f"Session ID: {st.session_state.session_id}\n"
    export_text += "=" * 60 + "\n\n"
    
    for msg in st.session_state.messages:
        role = "Vous" if msg["role"] == "user" else "Bot"
        export_text += f"{role}: {msg['content']}\n\n"
    
    # Bouton de téléchargement
    st.download_button(
        label="📥 Télécharger",
        data=export_text,
        file_name=f"conversation_{st.session_state.session_id[:8]}.txt",
        mime="text/plain"
    )


def main():
    """Fonction principale de l'application"""
    
    # Initialisation
    init_session_state()
    
    # Affichage de l'interface
    display_header()
    display_sidebar()
    
    # Zone de conversation
    st.markdown("### 💬 Conversation")
    
    # Conteneur pour les messages
    chat_container = st.container()
    
    with chat_container:
        if not st.session_state.conversation_started:
            # Message de bienvenue
            welcome_message = """
            👋 Bonjour ! Je suis l'assistant virtuel de l'ESILV.
            
            Je suis là pour vous aider à :

            • 📚 Découvrir nos programmes et formations

            • 📝 Vous renseigner sur les admissions

            • 📞 Être mis en contact avec un conseiller
            
            • ❓ Répondre à toutes vos questions
            
            Comment puis-je vous aider aujourd'hui ?
            """
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": welcome_message,
                "timestamp": datetime.now().isoformat()
            })
            st.session_state.conversation_started = True
        
        # Affiche l'historique
        display_chat_history()
    
    # Zone de saisie (toujours en bas)
    st.markdown("---")
    
    # Utilise des colonnes pour un meilleur layout
    col1, col2 = st.columns([6, 1])
    
    with col1:
        user_input = st.text_input(
            "Votre message",
            key="user_input",
            placeholder="Tapez votre message ici...",
            label_visibility="collapsed"
        )
    
    with col2:
        send_button = st.button("📤 Envoyer", use_container_width=True)
    
    # Traitement du message
    # Gestion de la touche Entrée - vérifie d'abord si c'est un nouveau message
    if user_input and user_input != st.session_state.get('last_input', ''):
        st.session_state.last_input = user_input
        send_message(user_input)
        st.rerun()

    # Gestion du bouton Envoyer (seulement si pas déjà traité par Entrée)
    elif send_button and user_input:
        send_message(user_input)
        st.rerun()
# Point d'entrée de l'application
if __name__ == "__main__":
    main()