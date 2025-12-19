#!/bin/bash
# setup.sh - Script de configuration et lancement du projet

echo "🚀 Configuration du projet Chatbot ESILV"
echo "========================================"

# Crée les dossiers nécessaires
echo "📁 Création des dossiers..."
mkdir -p data/contacts
mkdir -p data/rag
mkdir -p logs

# Crée le fichier contacts.json s'il n'existe pas
if [ ! -f "data/contacts/contacts.json" ]; then
    echo "[]" > data/contacts/contacts.json
    echo "✓ Fichier contacts.json créé"
fi

# Crée un fichier .gitkeep pour les logs
touch logs/.gitkeep

# Vérifie si Ollama est installé et lancé
echo ""
echo "🔍 Vérification d'Ollama..."
if command -v ollama &> /dev/null; then
    echo "✓ Ollama est installé"
    
    # Vérifie si Ollama tourne
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✓ Ollama est en cours d'exécution"
    else
        echo "⚠️  Ollama n'est pas lancé. Démarrez-le avec 'ollama serve'"
    fi
    
    # Vérifie si le modèle mistral est disponible
    if ollama list | grep -q "mistral"; then
        echo "✓ Modèle Mistral disponible"
    else
        echo "⚠️  Modèle Mistral non trouvé"
        echo "   Téléchargez-le avec: ollama pull mistral"
    fi
else
    echo "❌ Ollama n'est pas installé"
    echo "   Installez-le depuis: https://ollama.ai"
    exit 1
fi

# Vérifie les dépendances Python
echo ""
echo "📦 Vérification des dépendances Python..."
python3 -c "import streamlit" 2>/dev/null && echo "✓ Streamlit installé" || echo "❌ Streamlit manquant (pip install streamlit)"
python3 -c "import ollama" 2>/dev/null && echo "✓ Ollama Python installé" || echo "❌ Ollama manquant (pip install ollama)"

echo ""
echo "========================================"
echo "✅ Configuration terminée !"
echo ""
echo "Pour lancer l'application :"
echo "  streamlit run app.py"
echo ""