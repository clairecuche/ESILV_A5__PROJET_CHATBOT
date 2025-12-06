import streamlit as st
from src.agents.agent_orchestrateur import AgentSuperviseur
import logging
from datetime import datetime
import uuid

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
    
    .stTextInput>div>div>input {
        border-radius: 20px;
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
            3. **Modifier vos informations** si nécessaire
            
            **Exemples de questions :**
            - Quels sont les programmes disponibles ?
            - Comment s'inscrire ?
            - Je souhaite être contacté
            - Quels sont les frais de scolarité ?
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
                send_message(clean_question)
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)


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


    def send_message(user_input: str, is_form_submission: bool = False): # ⬅️ MODIFIÉ
        if not user_input.strip():
            return
        
        # 🚨 MODIFICATION ICI pour stocker le rôle et l'info du formulaire
        st.session_state.messages.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat()
            # On pourrait ajouter 'is_form_submission': is_form_submission ici si on voulait masquer le message
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
    logger.info(f"Conversation réinitialisée - Nouvelle session: {st.session_state.session_id[:8]}")

def display_contact_form():
    """
    Affiche un formulaire de contact structuré avec 4 champs obligatoires.
    Les données sont injectées dans l'état de la session (st.session_state.supervisor)
    pour être traitées par l'AgentFormulaire.
    """
    st.markdown("### 📝 Formulaire de Contact Express")
    
    # Utilisation de st.form pour regrouper les champs et gérer la soumission
    with st.form(key='contact_form', clear_on_submit=True):
        
        # Récupérer les données actuelles pour pré-remplir ou afficher l'état
        form_data = st.session_state.supervisor.get_form_data(st.session_state.session_id)
        
        # CHAMPS DE SAISIE
        col1, col2 = st.columns(2)
        with col1:
            nom_input = st.text_input(
                "Nom & Prénom",
                value=form_data.get('nom', ''),
                placeholder="Ex: Jean Dupont",
                key="form_nom"
            )
        with col2:
            email_input = st.text_input(
                "Email",
                value=form_data.get('email', ''),
                placeholder="Ex: jean.dupont@exemple.com",
                key="form_email"
            )

        col3, col4 = st.columns(2)
        with col3:
            phone_input = st.text_input(
                "Téléphone",
                value=form_data.get('telephone', ''),
                placeholder="Ex: 06 12 34 56 78",
                key="form_telephone"
            )
        with col4:
            # Champ de sélection pour Programme (ou texte libre si préféré)
            programmes = ["Non spécifié", "Data Science", "Intelligence Artificielle", "Cybersécurité", "Systèmes Embarqués", "FinTech"]
            programme_selection = st.selectbox(
                "Programme intéressé",
                options=programmes,
                index=programmes.index(form_data.get('programme', 'Non spécifié')) if form_data.get('programme') in programmes else 0,
                key="form_programme"
            )
            
        st.markdown("---")
        
        # BOUTON DE SOUMISSION
        submitted = st.form_submit_button("✅ Envoyer ma demande de contact")
        
        if submitted:
            # 1. Préparer le message pour l'AgentFormulaire
            programme_value = programme_selection if programme_selection != "Non spécifié" else ""
            
            # On combine les données en un seul message formaté pour l'AgentFormulaire
            full_message = f"Demande de contact : Nom: {nom_input}, Email: {email_input}, Tél: {phone_input}, Programme: {programme_value}. Oui, je confirme la demande."
            
            # 2. Utiliser la fonction send_message existante pour traiter les données
            # L'AgentFormulaire va extraire, valider et sauvegarder les infos.
            send_message(full_message, is_form_submission=True)
            
            # 3. Afficher un message de confirmation (sera remplacé par la réponse du bot)
            st.success("Demande soumise ! Veuillez voir la réponse de l'assistant dans la conversation ci-dessous.")
            st.rerun()

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
    
    # 🚨 AJOUTEZ L'AFFICHAGE DU FORMULAIRE ICI
    display_contact_form()
    
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