# Utiliser une image Python légère
FROM python:3.10-slim

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les bibliothèques Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du code source
COPY . .

# Créer les répertoires nécessaires pour les logs et les contacts
RUN mkdir -p logs data/contacts

# Exposer le port utilisé par Flask
EXPOSE 5000

# Commande pour lancer l'API
CMD ["python", "chatbot.py"]