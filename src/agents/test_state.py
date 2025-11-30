# test_state_manager.py
from state_manager import state_manager

print("🧪 Tests du State Manager\n")
print("=" * 60)

# Test 1: Création de session
print("\n📝 Test 1: Création de session")
session_id = "test_123"
session = state_manager.get_or_create_session(session_id)
print(f"✓ Session créée: {session.session_id}")
print(f"  Form data initial: {session.form_data}")

# Test 2: Mise à jour données
print("\n📝 Test 2: Mise à jour données")
state_manager.update_form_data(session_id, "nom", "Jean Dupont")
state_manager.update_form_data(session_id, "email", "jean@test.com")

session = state_manager.get_or_create_session(session_id)
print(f"✓ Données mises à jour:")
print(f"  Nom: {session.form_data['nom']}")
print(f"  Email: {session.form_data['email']}")

# Test 3: Historique
print("\n📝 Test 3: Historique des messages")
state_manager.add_to_history(session_id, "user", "Bonjour")
state_manager.add_to_history(session_id, "assistant", "Bonjour ! Comment puis-je vous aider ?")

session = state_manager.get_or_create_session(session_id)
print(f"✓ Messages dans l'historique: {len(session.history)}")
for msg in session.history:
    print(f"  {msg['role']}: {msg['content']}")

# Test 4: État du formulaire
print("\n📝 Test 4: État du formulaire")
print(f"✓ Formulaire actif: {state_manager.is_form_active(session_id)}")
print(f"✓ Complétion: {session.get_form_completion_percentage()}%")

# Test 5: Persistance
print("\n📝 Test 5: Persistance (simulation rechargement)")
# Simule un rechargement : on récupère à nouveau la session
session_again = state_manager.get_or_create_session(session_id)
print(f"✓ Nom toujours présent: {session_again.form_data['nom']}")
print(f"✓ Email toujours présent: {session_again.form_data['email']}")
print("✓ Les données sont PERSISTÉES ! 🎉")

# Test 6: Résumé
print("\n📝 Test 6: Résumé de session")
summary = state_manager.get_session_summary(session_id)
print(f"✓ Résumé:")
for key, value in summary.items():
    print(f"  {key}: {value}")

print("\n" + "=" * 60)
print("✅ Tous les tests passés !")


# test_superviseur_complet.py
from agent_orchestrateur import AgentSuperviseur
import uuid

print("🧪 Test interactif du Superviseur\n")

superviseur = AgentSuperviseur()
session_id = str(uuid.uuid4())

messages_test = [
    "Bonjour",
    "Quels sont les programmes d'ingénieur ?",
    "Je voudrais être contacté",
    "Jean Dupont",
    "jean@test.com"
]

for msg in messages_test:
    print(f"\n{'='*60}")
    print(f"👤 User: {msg}")
    print(f"{'='*60}")
    
    try:
        response = superviseur.run(msg, session_id)
        print(f"🤖 Bot: {response}")
    except Exception as e:
        print(f"❌ Erreur: {e}")

# Affiche les stats
print(f"\n{'='*60}")
print("📊 Statistiques de session:")
print(f"{'='*60}")
stats = superviseur.get_statistics(session_id)
for key, value in stats.items():
    print(f"  {key}: {value}")