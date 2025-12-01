import uuid
from state_manager import state_manager
from agent_orchestrateur import AgentSuperviseur
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



# TEST ORCHESTRATEUR
print("\n" + "="*60)
print("🧪 TESTS DE L'AGENT SUPERVISEUR")
print("="*60 + "\n")

# Test 1: Initialisation
print("📝 Test 1: Initialisation")
try:
    superviseur = AgentSuperviseur()
    print("   ✅ Superviseur initialisé\n")
except Exception as e:
    print(f"   ❌ Erreur: {e}\n")
    exit(1)

# Test 2: Détection d'intention
print("📝 Test 2: Détection d'intention avec LLM")
test_messages = [
    "Quels sont les programmes ?",
    "Je veux être contacté",
    "Info sur l'IA et appelez-moi",
    "Bonjour"
]

for msg in test_messages:
    try:
        intent = superviseur.detect_intent_with_llm(msg)
        print(f"   '{msg[:40]}' → {intent}")
    except Exception as e:
        print(f"   ❌ Erreur pour '{msg}': {e}")

print()

# Test 3: Routing complet
print("📝 Test 3: Routing complet")
test_session = "test_session_123"

for msg in test_messages[:2]:  # Teste juste 2 messages
    try:
        agent = superviseur.route(msg, test_session)
        print(f"   '{msg[:40]}' → Agent: {agent}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

print()

# Test 4: Execution complète (simulation)
print("📝 Test 4: Exécution complète (simulation)")
try:
    # Note: Ceci ne fonctionnera que si tu as les autres agents implémentés
    # response = superviseur.run("Quels programmes proposez-vous ?", test_session)
    # print(f"   Réponse: {response[:100]}...")
    print("   ⏭️ Test skippé (nécessite les autres agents)")
except Exception as e:
    print(f"   ⏭️ Test skippé: {e}")

print()
print("="*60)
print("✅ Tests terminés")
print("="*60 + "\n")




# ========================================================================
# TESTS FORMULAIRE
# ========================================================================

from agent_formulaire import AgentFormulaire


    
print("\n" + "="*60)
print("🧪 TESTS DE L'AGENT FORMULAIRE")
print("="*60 + "\n")

# Init
agent = AgentFormulaire()
test_session = str(uuid.uuid4())

# Test 1: Extraction d'email
print("📝 Test 1: Extraction d'email")
extracted = agent._extract_info("Mon email est test@esilv.fr", test_session)
print(f"   Résultat: {extracted}")
print(f"   ✓ Email extrait\n" if 'email' in extracted else "   ✗ Échec\n")

# Test 2: Extraction téléphone
print("📝 Test 2: Extraction téléphone")
extracted = agent._extract_info("Mon numéro est 06 12 34 56 78", test_session)
print(f"   Résultat: {extracted}")
print(f"   ✓ Téléphone extrait\n" if 'telephone' in extracted else "   ✗ Échec\n")

# Test 3: Validation email
print("📝 Test 3: Validation email")
test_emails = ["test@esilv.fr", "invalid.email", "test@", "@test.com"]
for email in test_emails:
    valid = agent._is_valid_email(email)
    status = "✓" if valid else "✗"
    print(f"   {status} {email}: {valid}")
print()

# Test 4: Normalisation téléphone
print("📝 Test 4: Normalisation téléphone")
test_phones = ["0612345678", "06 12 34 56 78", "+33 6 12 34 56 78", "123"]
for phone in test_phones:
    normalized = agent._normalize_phone(phone)
    print(f"   {phone:20} → {normalized or 'INVALIDE'}")
print()

# Test 5: Workflow complet simulé
print("📝 Test 5: Workflow complet")
conversation = [
    "Jean Dupont",
    "jean.dupont@test.com",
    "0612345678",
    "Data Science",
    "oui"
]

for i, msg in enumerate(conversation, 1):
    print(f"\n   Tour {i}: '{msg}'")
    response = agent.run(msg, test_session)
    print(f"   Bot: {response[:100]}...")

print("\n" + "="*60)
print(f"✅ Tests terminés - {agent.get_contact_count()} contact(s) enregistré(s)")
print("="*60 + "\n")

def run_interactive_mode():
    """Run interactive console mode for testing"""
    print("\n" + "="*60)
    print("🤖 Mode Interactif")
    print("Tapez 'exit' pour quitter")
    print("="*60 + "\n")
    
    supervisor = AgentSuperviseur()
    form_agent = AgentFormulaire()
    session_id = str(uuid.uuid4())
    
    while True:
        try:
            user_input = input("\n👤 Vous: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("👋 Au revoir !")
                break
                
            if not user_input:
                continue
                
            # Vérifie si c'est une entrée de formulaire
            if state_manager.is_form_active(session_id):
                print("📝 Traitement du formulaire...")
                response = form_agent.run(user_input, session_id)
            else:
                # Route vers l'agent approprié
                response = supervisor.run(user_input, session_id)
                
            print(f"\n🤖 Bot: {response}")
            
        except KeyboardInterrupt:
            print("\n👋 Au revoir !")
            break
        except Exception as e:
            print(f"\n❌ Erreur: {str(e)}")
            
    # Afficher le résumé de la session
    print("\n📊 Résumé de la session:" + "="*50)
    stats = supervisor.get_statistics(session_id) if hasattr(supervisor, 'get_statistics') else {}
    for key, value in stats.items():
        print(f"  {key}: {value}")

def main():
    print("🎭 Menu Principal" + "\n" + "="*60)
    print("1. Exécuter les tests automatisés")
    print("2. Mode interactif")
    print("3. Les deux")
    print("4. Quitter")
    print("="*60)
    
    while True:
        choice = input("\nVotre choix (1-4): ").strip()
        
        if choice == '1':
            print("\n" + "="*60)
            print("🚀 Exécution des tests automatisés...")
            print("="*60)
            # Le reste du code de test existant s'exécutera ici
            break
        elif choice == '2':
            run_interactive_mode()
            break
        elif choice == '3':
            print("\n" + "="*60)
            print("🚀 Exécution des tests automatisés...")
            print("="*60)
            # Le reste du code de test existant s'exécutera ici
            print("\n" + "="*60)
            print("✅ Tests automatisés terminés. Passage en mode interactif...")
            print("="*60)
            run_interactive_mode()
            break
        elif choice == '4':
            print("\n👋 Au revoir !")
            return
        else:
            print("❌ Choix invalide. Veuillez entrer un nombre entre 1 et 4.")

if __name__ == "__main__":
    main()