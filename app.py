import streamlit as st
from src.agents.agent_orchestrateur import AgentSuperviseur
import logging
from datetime import datetime
import uuid
import json
from pathlib import Path

st.set_page_config(
    page_title="Chatbot ESILV",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

SUGGESTED_QUESTIONS = {
    "accueil": [
        "📚 Quels sont les programmes disponibles ?",
        "💰 Quels sont les frais de scolarité ?",
        "📍 Où se trouve le campus ?",
        "📞 Je souhaite être contacté",
    ],
    "programmes": [
        "🤖 Parlez-moi du programme Intelligence Artificielle",
        "📊 Qu'est-ce que le programme Data Science ?",
        "🔒 Informations sur la Cybersécurité",
        "💻 Quelles sont les spécialisations disponibles ?",
    ],
    "admission": [
        "✅ Quelles sont les conditions d'admission ?",
        "📝 Comment s'inscrire ?",
        "📅 Quelles sont les dates importantes ?",
        "🎓 Quel est le niveau requis ?",
    ],
    "vie_etudiante": [
        "🏠 Où se loger près du campus ?",
        "🎯 Quelles sont les associations étudiantes ?",
        "💼 Y a-t-il des stages obligatoires ?",
        "🌍 Peut-on partir à l'étranger ?",
    ]
}

PROGRAMMES = [
    "Data Science",
    "Intelligence Artificielle",
    "Cybersécurité",
    "Systèmes Embarqués",
    "FinTech",
    "Génie Civil",
    "Autre"
]

st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    
    .user-message {
        background-color: #007bff;
        color: white;
        padding: 12px 16px;
        border-radius: 18px;
        margin: 8px 0;
        margin-left: 20%;
        text-align: right;
    }
    
    .bot-message {
        background-color: #ffffff;
        color: #333;
        padding: 12px 16px;
        border-radius: 18px;
        margin: 8px 0;
        margin-right: 20%;
        border: 1px solid #e0e0e0;
    }
    
    .header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
    }
    
    .stat-box {
        background-color: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 45px;
        font-weight: 500;
    }
    
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        border-radius: 8px;
    }
    
    div[data-testid="stButton"] > button[kind="secondary"] {
        border-radius: 20px;
        border: 1px solid #e0e0e0;
        background-color: #f8f9fa;
        color: #333;
        font-size: 14px;
        padding: 8px 16px;
        transition: all 0.2s;
        margin: 4px 0;
    }
    
    div[data-testid="stButton"] > button[kind="secondary"]:hover {
        background-color: #e3f2fd;
        border-color: #2196F3;
        transform: translateY(-2px);
        box-shadow: 0 2px 8px rgba(33, 150, 243, 0.2);
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .suggestion-container {
        animation: slideIn 0.3s ease-out;
        margin: 20px 0;
        padding: 15px;
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    .suggestion-title {
        color: #667eea;
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 12px;
    }
    
    .form-container {
        background-color: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin: 20px 0;
        animation: slideIn 0.4s ease-out;
    }
    
    .form-title {
        color: #667eea;
        font-size: 20px;
        font-weight: 700;
        margin-bottom: 20px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
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
    
    if 'last_input' not in st.session_state:
        st.session_state.last_input = ""
    
    if 'show_form' not in st.session_state:
        st.session_state.show_form = False


def get_suggestions_for_context(messages):
    if not messages or len(messages) <= 1:
        return SUGGESTED_QUESTIONS["accueil"]
    
    last_messages = " ".join([m["content"].lower() for m in messages[-3:]])
    
    if any(word in last_messages for word in ["programme", "formation", "cursus", "spécialisation"]):
        return SUGGESTED_QUESTIONS["programmes"]
    elif any(word in last_messages for word in ["admission", "inscription", "candidature", "concours"]):
        return SUGGESTED_QUESTIONS["admission"]
    elif any(word in last_messages for word in ["campus", "vie", "étudiant", "stage", "association"]):
        return SUGGESTED_QUESTIONS["vie_etudiante"]
    else:
        return SUGGESTED_QUESTIONS["accueil"]


def display_header():
    st.markdown("""
    <div class="header">
        <h1>🎓 Chatbot ESILV</h1>
        <p>Votre assistant intelligent pour découvrir nos formations</p>
    </div>
    """, unsafe_allow_html=True)


def display_sidebar():
    with st.sidebar:
        st.markdown("### 📊 Informations")
        
        st.markdown(f"""
        <div class="stat-box">
            <b>🆔 Session</b><br>
            <code>{st.session_state.session_id[:8]}...</code>
        </div>
        """, unsafe_allow_html=True)
        
        stats = st.session_state.supervisor.get_statistics(st.session_state.session_id)
        
        st.markdown(f"""
        <div class="stat-box">
            <b>💬 Messages échangés</b><br>
            <h2 style="margin:0; color:#667eea;">{stats.get('messages_count', 0)}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        st.markdown("### ⚙️ Actions")
        
        if st.button("🔄 Nouvelle conversation", use_container_width=True):
            reset_conversation()
            st.rerun()
        
        if st.button("📥 Exporter l'historique", use_container_width=True):
            export_conversation()
        
        st.markdown("---")
        
        st.markdown("### ℹ️ Système")
        st.markdown("""
        <div class="stat-box">
            <b>🤖 Agents actifs</b><br>
            • Agent RAG<br>
            • Agent Formulaire<br>
            • Agent Interaction
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("📖 Guide d'utilisation"):
            st.markdown("""
            **Comment utiliser ce chatbot ?**
            
            1. **Poser des questions** sur les programmes, admissions, etc.
            2. **Demander à être contacté** pour obtenir plus d'informations
            3. **Remplir le formulaire** en une seule fois
            
            **Exemples de questions :**
            - Quels sont les programmes disponibles ?
            - Comment s'inscrire ?
            - Je souhaite être contacté
            """)


def display_suggestions():
    suggestions = get_suggestions_for_context(st.session_state.messages)
    
    st.markdown('<div class="suggestion-container">', unsafe_allow_html=True)
    st.markdown('<div class="suggestion-title">💡 Questions suggérées</div>', unsafe_allow_html=True)
    
    cols = st.columns(2)
    for idx, question in enumerate(suggestions):
        col = cols[idx % 2]
        with col:
            clean_question = question.split(" ", 1)[1] if " " in question else question
            if st.button(
                question,
                key=f"suggestion_{idx}_{len(st.session_state.messages)}",
                use_container_width=True,
                type="secondary"
            ):
                if "contacté" in clean_question.lower():
                    st.session_state.show_form = True
                    st.rerun()
                else:
                    send_message(clean_question)
                    st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)


def display_contact_form():
    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    st.markdown('<div class="form-title">📋 Formulaire de contact</div>', unsafe_allow_html=True)
    
    with st.form("contact_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            prenom = st.text_input("Prénom *", placeholder="Jean")
            email = st.text_input("Email *", placeholder="jean.dupont@email.com")
        
        with col2:
            nom = st.text_input("Nom *", placeholder="Dupont")
            telephone = st.text_input("Téléphone *", placeholder="06 12 34 56 78")
        
        programme = st.selectbox("Programme d'intérêt *", PROGRAMMES)
        
        message = st.text_area(
            "Message (optionnel)",
            placeholder="Décrivez votre projet ou posez vos questions...",
            height=100
        )
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col2:
            submitted = st.form_submit_button("✅ Envoyer", use_container_width=True)
        
        if submitted:
            if not prenom or not nom or not email or not telephone:
                st.error("❌ Veuillez remplir tous les champs obligatoires (*)")
            elif not validate_email(email):
                st.error("❌ Format d'email invalide")
            elif not validate_phone(telephone):
                st.error("❌ Format de téléphone invalide (ex: 06 12 34 56 78)")
            else:
                form_data = {
                    'nom': f"{prenom} {nom}",
                    'email': email,
                    'telephone': telephone,
                    'programme': programme,
                    'message': message
                }
                
                if save_contact(form_data):
                    st.success("✅ Votre demande a bien été enregistrée ! Notre équipe vous contactera rapidement.")
                    
                    bot_response = f"""Parfait {prenom} ! 🎉

Vos informations ont été enregistrées :
• 👤 Nom : {prenom} {nom}
• 📧 Email : {email}
• 📱 Téléphone : {telephone}
• 🎓 Programme : {programme}

Un conseiller vous contactera dans les plus brefs délais pour répondre à vos questions et vous accompagner dans votre projet.

Y a-t-il autre chose que je puisse faire pour vous ?"""
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": bot_response,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    st.session_state.show_form = False
                    st.rerun()
                else:
                    st.error("❌ Erreur lors de l'enregistrement. Veuillez réessayer.")
    
    if st.button("❌ Annuler", use_container_width=True):
        st.session_state.show_form = False
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)


def validate_email(email: str) -> bool:
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone: str) -> bool:
    import re
    phone_clean = re.sub(r'[\s\-\.]', '', phone)
    return re.match(r'^(0[1-9]\d{8}|\+33[1-9]\d{8})$', phone_clean) is not None


def save_contact(form_data: dict) -> bool:
    try:
        contacts_file = Path("data/contacts/contacts.json")
        contacts_file.parent.mkdir(parents=True, exist_ok=True)
        
        if contacts_file.exists():
            contacts = json.loads(contacts_file.read_text(encoding='utf-8'))
        else:
            contacts = []
        
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
            'session_id': st.session_state.session_id[:8]
        }
        
        contacts.append(contact)
        
        contacts_file.write_text(
            json.dumps(contacts, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
        
        logger.info(f"✅ Contact sauvegardé: {contact['email']}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur sauvegarde contact: {e}")
        return False


def display_chat_history():
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
    if not user_input.strip():
        return
    
    if any(word in user_input.lower() for word in ["contacté", "contact", "rappel", "appeler", "inscription"]):
        st.session_state.show_form = True
        st.session_state.messages.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        })
        return
    
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "timestamp": datetime.now().isoformat()
    })
    
    with st.spinner("🤔 Réflexion en cours..."):
        try:
            response = st.session_state.supervisor.run(
                message=user_input,
                session_id=st.session_state.session_id
            )
            
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
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.session_state.conversation_started = False
    st.session_state.last_input = ""
    st.session_state.show_form = False
    logger.info(f"Conversation réinitialisée - Nouvelle session: {st.session_state.session_id[:8]}")


def export_conversation():
    if not st.session_state.messages:
        st.warning("Aucun message à exporter")
        return
    
    export_text = f"Historique de conversation - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    export_text += f"Session ID: {st.session_state.session_id}\n"
    export_text += "=" * 60 + "\n\n"
    
    for msg in st.session_state.messages:
        role = "Vous" if msg["role"] == "user" else "Bot"
        export_text += f"{role}: {msg['content']}\n\n"
    
    st.download_button(
        label="📥 Télécharger",
        data=export_text,
        file_name=f"conversation_{st.session_state.session_id[:8]}.txt",
        mime="text/plain"
    )


def main():
    init_session_state()
    
    display_header()
    display_sidebar()
    
    st.markdown("### 💬 Conversation")
    
    chat_container = st.container()
    
    with chat_container:
        if not st.session_state.conversation_started:
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
        
        display_chat_history()
    
    if st.session_state.show_form:
        display_contact_form()
    else:
        if len(st.session_state.messages) == 1 or (len(st.session_state.messages) > 1 and st.session_state.messages[-1]["role"] == "assistant"):
            display_suggestions()
        
        st.markdown("---")
        
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
        
        is_new_message = user_input and user_input != st.session_state.last_input
        
        if is_new_message:
            st.session_state.last_input = user_input
            send_message(user_input)
            st.rerun()
        elif send_button and user_input:
            st.session_state.last_input = user_input
            send_message(user_input)
            st.rerun()


if __name__ == "__main__":
    main()