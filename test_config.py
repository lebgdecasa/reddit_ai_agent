#!/usr/bin/env python3
"""
Script de test pour vérifier la configuration de l'Agent IA Reddit
"""

import sys
import os
from pathlib import Path

# Ajouter le dossier src au path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Changer le répertoire de travail vers le dossier du projet
os.chdir(current_dir)

from config_manager import ConfigManager, setup_logging
from reddit_interface import RedditInterface
from lm_studio_interface import LMStudioInterface


def test_configuration():
    """Teste la configuration complète"""
    print("=== Test de Configuration de l'Agent IA Reddit ===\n")
    
    # Test 1: Chargement de la configuration
    print("1. Test du chargement de la configuration...")
    config_manager = ConfigManager()
    
    if not config_manager.load_config():
        print("❌ ÉCHEC: Impossible de charger la configuration")
        print("   Vérifiez que le fichier config/config.yaml existe et est correctement configuré")
        return False
    
    print("✅ Configuration chargée avec succès")
    
    # Configurer le logging
    setup_logging(config_manager)
    
    # Test 2: Configuration Reddit
    print("\n2. Test de la configuration Reddit...")
    try:
        reddit_config = config_manager.reddit_config
        print(f"   Client ID: {reddit_config.client_id[:10]}...")
        print(f"   Username: {reddit_config.username}")
        print(f"   User Agent: {reddit_config.user_agent}")
        print("✅ Configuration Reddit OK")
    except Exception as e:
        print(f"❌ ÉCHEC: Configuration Reddit invalide - {e}")
        return False
    
    # Test 3: Configuration LM Studio
    print("\n3. Test de la configuration LM Studio...")
    try:
        lm_config = config_manager.lm_studio_config
        print(f"   URL: {lm_config.base_url}")
        print(f"   Modèle: {lm_config.model}")
        print(f"   Température: {lm_config.temperature}")
        print("✅ Configuration LM Studio OK")
    except Exception as e:
        print(f"❌ ÉCHEC: Configuration LM Studio invalide - {e}")
        return False
    
    # Test 4: Subreddits configurés
    print("\n4. Test des subreddits configurés...")
    enabled_subreddits = config_manager.get_enabled_subreddits()
    if enabled_subreddits:
        print(f"   Subreddits activés: {[s.name for s in enabled_subreddits]}")
        for sub in enabled_subreddits:
            print(f"   - r/{sub.name}: posts={sub.post_enabled}, comments={sub.comment_enabled}")
        print("✅ Subreddits configurés")
    else:
        print("⚠️  ATTENTION: Aucun subreddit activé")
    
    # Test 5: Modes de fonctionnement
    print("\n5. Test des modes de fonctionnement...")
    print(f"   Dry Run: {config_manager.is_dry_run()}")
    print(f"   Debug: {config_manager.is_debug()}")
    print(f"   Monitor Only: {config_manager.is_monitor_only()}")
    print("✅ Modes configurés")
    
    return True


def test_reddit_connection():
    """Teste la connexion Reddit"""
    print("\n=== Test de Connexion Reddit ===")
    
    config_manager = ConfigManager()
    if not config_manager.load_config():
        print("❌ Configuration non chargée")
        return False
    
    setup_logging(config_manager)
    
    print("Tentative de connexion à Reddit...")
    reddit_interface = RedditInterface(config_manager.reddit_config)
    
    if reddit_interface.authenticate():
        print("✅ Connexion Reddit réussie")
        
        # Test de récupération de posts
        print("Test de récupération de posts...")
        try:
            posts = reddit_interface.get_subreddit_posts('test', limit=3)
            print(f"✅ Récupéré {len(posts)} posts de r/test")
            
            if posts:
                print("   Exemple de post:")
                post = posts[0]
                print(f"   - Titre: {post['title'][:50]}...")
                print(f"   - Score: {post['score']}")
                print(f"   - Auteur: {post['author']}")
        except Exception as e:
            print(f"⚠️  Erreur lors de la récupération: {e}")
        
        return True
    else:
        print("❌ ÉCHEC: Impossible de se connecter à Reddit")
        print("   Vérifiez vos credentials dans config/config.yaml")
        return False


def test_lm_studio_connection():
    """Teste la connexion LM Studio"""
    print("\n=== Test de Connexion LM Studio ===")
    
    config_manager = ConfigManager()
    if not config_manager.load_config():
        print("❌ Configuration non chargée")
        return False
    
    setup_logging(config_manager)
    
    print("Tentative de connexion à LM Studio...")
    lm_interface = LMStudioInterface(config_manager.lm_studio_config)
    
    if lm_interface.initialize():
        print("✅ Connexion LM Studio réussie")
        
        # Test de génération
        print("Test de génération de réponse...")
        try:
            response = lm_interface.generate_response(
                "Dis bonjour en français",
                system_instruction="Tu es un assistant IA utile."
            )
            
            if response:
                print(f"✅ Réponse générée: {response[:100]}...")
            else:
                print("⚠️  Aucune réponse générée")
        except Exception as e:
            print(f"⚠️  Erreur lors de la génération: {e}")
        
        return True
    else:
        print("❌ ÉCHEC: Impossible de se connecter à LM Studio")
        print("   Vérifiez que LM Studio est démarré et accessible")
        print(f"   URL configurée: {config_manager.lm_studio_config.base_url}")
        return False


def main():
    """Fonction principale de test"""
    success = True
    
    # Test de configuration
    if not test_configuration():
        success = False
    
    # Test de connexion Reddit
    if not test_reddit_connection():
        success = False
    
    # Test de connexion LM Studio
    if not test_lm_studio_connection():
        success = False
    
    print("\n" + "="*50)
    if success:
        print("✅ TOUS LES TESTS SONT PASSÉS")
        print("L'agent est prêt à être lancé avec: python run_agent.py")
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("Corrigez les erreurs avant de lancer l'agent")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

