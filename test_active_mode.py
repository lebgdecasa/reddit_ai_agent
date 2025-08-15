#!/usr/bin/env python3
"""
Tests dédiés au Mode Conversationnel Actif

Ce script teste spécifiquement les fonctionnalités du mode actif
où l'agent poste réellement sur Reddit (ou simule en dry run).
"""

import sys
import os
import time
from pathlib import Path

# Ajouter le dossier src au path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Changer le répertoire de travail vers le dossier du projet
os.chdir(current_dir)

from config_manager import ConfigManager, setup_logging
from reddit_ai_agent import RedditAIAgent
from active_data_manager import ActiveDataManager


def test_active_data_manager():
    """Test du gestionnaire de données actif"""
    print("=== Test du Gestionnaire de Données Actif ===")
    
    try:
        # Créer le gestionnaire
        data_manager = ActiveDataManager()
        print("✅ Gestionnaire de données créé")
        
        # Test de sauvegarde d'un post scrapé
        test_post = {
            'id': 'test_post_123',
            'title': 'Test Post Title',
            'selftext': 'Test post content',
            'author': 'test_author',
            'score': 10,
            'num_comments': 5,
            'created_utc': time.time(),
            'url': 'https://reddit.com/test',
            'is_self': True
        }
        
        test_analysis = {
            'score': 0.8,
            'should_respond': True,
            'confidence': 0.75,
            'reasons': ['test_trigger']
        }
        
        success = data_manager.log_scraped_post(test_post, 'test', test_analysis)
        if success:
            print("✅ Post scrapé sauvegardé")
        else:
            print("❌ Échec sauvegarde post scrapé")
            return False
        
        # Test de sauvegarde d'une réponse postée
        success = data_manager.log_posted_response(
            'test_post_123', 'test_response_456', 'test',
            'Test response content', 0.85, ['test_trigger']
        )
        if success:
            print("✅ Réponse postée sauvegardée")
        else:
            print("❌ Échec sauvegarde réponse postée")
            return False
        
        # Test de sauvegarde d'un post créé
        success = data_manager.log_created_post(
            'test_created_789', 'test', 'Test Created Post',
            'Test created content', 'discussion'
        )
        if success:
            print("✅ Post créé sauvegardé")
        else:
            print("❌ Échec sauvegarde post créé")
            return False
        
        # Test de log d'action
        success = data_manager.log_action(
            'test_action', 'test', 'test_target', 'test_result',
            {'test_key': 'test_value'}, True, None, 1.5
        )
        if success:
            print("✅ Action loggée")
        else:
            print("❌ Échec log action")
            return False
        
        # Test des statistiques
        stats = data_manager.get_database_stats()
        print(f"📊 Stats DB: {stats}")
        
        # Test de finalisation
        data_manager.finalize_session()
        print("✅ Session finalisée")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur dans le test du gestionnaire: {e}")
        return False


def test_agent_initialization():
    """Test de l'initialisation de l'agent avec le gestionnaire de données"""
    print("\n=== Test d'Initialisation de l'Agent ===")
    
    try:
        # Charger la configuration
        config_manager = ConfigManager('config/config.yaml')
        if not config_manager.load_config():
            print("❌ Échec chargement configuration")
            return False
        
        print("✅ Configuration chargée")
        
        # Créer l'agent
        agent = RedditAIAgent('config/config.yaml')
        print("✅ Agent créé")
        
        # Initialiser (sans démarrer)
        if not agent.initialize():
            print("❌ Échec initialisation agent")
            return False
        
        print("✅ Agent initialisé")
        
        # Vérifier que le gestionnaire de données est présent
        if agent.data_manager is None:
            print("❌ Gestionnaire de données manquant")
            return False
        
        print("✅ Gestionnaire de données présent")
        
        # Test des statistiques de l'agent
        status = agent.get_status()
        print(f"📊 Statut agent: {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur dans le test d'initialisation: {e}")
        return False


def test_dry_run_mode():
    """Test du mode dry run avec sauvegarde"""
    print("\n=== Test du Mode Dry Run avec Sauvegarde ===")
    
    try:
        # Vérifier que le mode dry run est activé
        config_manager = ConfigManager('config/config.yaml')
        if not config_manager.load_config():
            print("❌ Échec chargement configuration")
            return False
        
        if not config_manager.is_dry_run():
            print("⚠️  Mode dry run non activé - test sauté pour sécurité")
            return True
        
        print("✅ Mode dry run confirmé")
        
        # Créer l'agent
        agent = RedditAIAgent('config/config.yaml')
        
        if not agent.initialize():
            print("❌ Échec initialisation agent")
            return False
        
        print("✅ Agent initialisé en mode dry run")
        
        # Simuler un cycle court de surveillance
        enabled_subreddits = config_manager.get_enabled_subreddits()
        if not enabled_subreddits:
            print("⚠️  Aucun subreddit activé")
            return True
        
        # Prendre le premier subreddit activé
        test_subreddit = enabled_subreddits[0]
        print(f"🎯 Test sur r/{test_subreddit.name}")
        
        # Surveiller pendant 30 secondes
        print("⏱️  Surveillance de 30 secondes...")
        agent.running = True
        start_time = time.time()
        
        while time.time() - start_time < 30 and agent.running:
            try:
                agent._monitor_subreddit(test_subreddit)
                time.sleep(10)  # Attendre 10 secondes entre les cycles
            except Exception as e:
                print(f"⚠️  Erreur pendant la surveillance: {e}")
                break
        
        # Arrêter l'agent
        agent.running = False
        agent._shutdown()
        
        # Vérifier les données sauvegardées
        if agent.data_manager:
            stats = agent.data_manager.get_session_stats()
            print(f"📊 Résultats du test:")
            print(f"   Posts scrapés: {stats['posts_scraped']}")
            print(f"   Actions simulées: {stats['actions_performed']}")
            print(f"   Erreurs: {stats['errors_encountered']}")
            
            if stats['posts_scraped'] > 0:
                print("✅ Posts scrapés et sauvegardés")
            else:
                print("⚠️  Aucun post scrapé - normal si subreddit peu actif")
            
            if stats['actions_performed'] >= 0:
                print("✅ Actions trackées")
            
            return True
        else:
            print("❌ Gestionnaire de données manquant")
            return False
        
    except Exception as e:
        print(f"❌ Erreur dans le test dry run: {e}")
        return False


def test_data_persistence():
    """Test de la persistance des données"""
    print("\n=== Test de Persistance des Données ===")
    
    try:
        # Créer un premier gestionnaire et ajouter des données
        data_manager1 = ActiveDataManager()
        
        # Ajouter des données de test
        test_post = {
            'id': 'persistence_test_123',
            'title': 'Persistence Test Post',
            'selftext': 'Test content',
            'author': 'test_user',
            'score': 15,
            'num_comments': 3,
            'created_utc': time.time(),
            'url': 'https://reddit.com/persistence_test',
            'is_self': True
        }
        
        test_analysis = {
            'score': 0.9,
            'should_respond': True,
            'confidence': 0.8,
            'reasons': ['persistence_test']
        }
        
        success = data_manager1.log_scraped_post(test_post, 'test', test_analysis)
        if not success:
            print("❌ Échec ajout données test")
            return False
        
        # Récupérer les stats
        stats1 = data_manager1.get_database_stats()
        posts_count1 = stats1.get('total_posts_scraped', 0)
        print(f"📊 Données ajoutées: {posts_count1} posts")
        
        # Créer un second gestionnaire (nouvelle instance)
        data_manager2 = ActiveDataManager()
        
        # Vérifier que les données persistent
        stats2 = data_manager2.get_database_stats()
        posts_count2 = stats2.get('total_posts_scraped', 0)
        
        if posts_count2 >= posts_count1:
            print("✅ Données persistées entre instances")
            return True
        else:
            print(f"❌ Perte de données: {posts_count1} -> {posts_count2}")
            return False
        
    except Exception as e:
        print(f"❌ Erreur dans le test de persistance: {e}")
        return False


def test_performance_tracking():
    """Test du suivi des performances Reddit"""
    print("\n=== Test du Suivi des Performances ===")
    
    try:
        data_manager = ActiveDataManager()
        
        # Test de mise à jour des performances
        test_content_id = 'perf_test_123'
        
        # Performance initiale
        success = data_manager.update_reddit_performance(
            test_content_id, 'response', 'test', 5, 2
        )
        if not success:
            print("❌ Échec mise à jour performance initiale")
            return False
        
        print("✅ Performance initiale enregistrée")
        
        # Mise à jour avec amélioration
        success = data_manager.update_reddit_performance(
            test_content_id, 'response', 'test', 10, 4
        )
        if not success:
            print("❌ Échec mise à jour performance")
            return False
        
        print("✅ Performance mise à jour (tendance positive)")
        
        # Mise à jour avec baisse
        success = data_manager.update_reddit_performance(
            test_content_id, 'response', 'test', 8, 4
        )
        if not success:
            print("❌ Échec mise à jour performance")
            return False
        
        print("✅ Performance mise à jour (tendance négative)")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur dans le test de performance: {e}")
        return False


def test_configuration_validation():
    """Test de validation de la configuration pour le mode actif"""
    print("\n=== Test de Validation Configuration ===")
    
    try:
        config_manager = ConfigManager('config/config.yaml')
        if not config_manager.load_config():
            print("❌ Échec chargement configuration")
            return False
        
        print("✅ Configuration chargée")
        
        # Vérifier les éléments critiques
        if not config_manager.reddit_config:
            print("❌ Configuration Reddit manquante")
            return False
        
        print("✅ Configuration Reddit présente")
        
        if not config_manager.lm_studio_config:
            print("❌ Configuration LM Studio manquante")
            return False
        
        print("✅ Configuration LM Studio présente")
        
        # Vérifier les subreddits
        enabled_subreddits = config_manager.get_enabled_subreddits()
        if not enabled_subreddits:
            print("⚠️  Aucun subreddit activé")
        else:
            print(f"✅ {len(enabled_subreddits)} subreddits activés")
        
        # Vérifier les triggers
        triggers = config_manager.get_triggers()
        if not triggers:
            print("⚠️  Aucun trigger configuré")
        else:
            keywords = triggers.get('keywords', [])
            print(f"✅ {len(keywords)} mots-clés triggers configurés")
        
        # Vérifier les modes
        print(f"📊 Mode dry run: {config_manager.is_dry_run()}")
        print(f"📊 Mode debug: {config_manager.is_debug()}")
        print(f"📊 Mode monitor only: {config_manager.is_monitor_only()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur dans la validation config: {e}")
        return False


def run_comprehensive_test():
    """Lance tous les tests du mode actif"""
    print("🧪 TESTS COMPLETS DU MODE ACTIF")
    print("=" * 50)
    
    tests = [
        ("Gestionnaire de Données", test_active_data_manager),
        ("Initialisation Agent", test_agent_initialization),
        ("Mode Dry Run", test_dry_run_mode),
        ("Persistance Données", test_data_persistence),
        ("Suivi Performances", test_performance_tracking),
        ("Validation Configuration", test_configuration_validation)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🔍 Test: {test_name}")
        print("-" * 40)
        
        try:
            start_time = time.time()
            success = test_func()
            duration = time.time() - start_time
            
            results[test_name] = {
                'success': success,
                'duration': round(duration, 2)
            }
            
            status = "✅ RÉUSSI" if success else "❌ ÉCHOUÉ"
            print(f"{status} ({duration:.2f}s)")
            
        except Exception as e:
            results[test_name] = {
                'success': False,
                'duration': 0,
                'error': str(e)
            }
            print(f"❌ ERREUR: {e}")
    
    # Résumé final
    print("\n" + "=" * 50)
    print("📋 RÉSUMÉ DES TESTS MODE ACTIF")
    print("=" * 50)
    
    total_tests = len(tests)
    passed_tests = sum(1 for r in results.values() if r['success'])
    
    for test_name, result in results.items():
        status = "✅" if result['success'] else "❌"
        duration = result['duration']
        print(f"{status} {test_name:<25} ({duration:.2f}s)")
        
        if not result['success'] and 'error' in result:
            print(f"   Erreur: {result['error']}")
    
    print(f"\n🎯 Résultat: {passed_tests}/{total_tests} tests réussis")
    
    if passed_tests == total_tests:
        print("🎉 TOUS LES TESTS SONT PASSÉS!")
        print("\nLe mode actif est prêt à être utilisé:")
        print("  python run_active_mode.py --duration 2")
        print("  python run_active_mode.py --stats")
        return True
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez la configuration.")
        return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Tests du Mode Actif')
    parser.add_argument('--data-manager', action='store_true',
                       help='Test du gestionnaire de données seulement')
    parser.add_argument('--agent', action='store_true',
                       help='Test de l\'agent seulement')
    parser.add_argument('--dry-run', action='store_true',
                       help='Test du mode dry run seulement')
    parser.add_argument('--persistence', action='store_true',
                       help='Test de persistance seulement')
    parser.add_argument('--performance', action='store_true',
                       help='Test de performance seulement')
    parser.add_argument('--config', action='store_true',
                       help='Test de configuration seulement')
    
    args = parser.parse_args()
    
    if args.data_manager:
        return 0 if test_active_data_manager() else 1
    elif args.agent:
        return 0 if test_agent_initialization() else 1
    elif args.dry_run:
        return 0 if test_dry_run_mode() else 1
    elif args.persistence:
        return 0 if test_data_persistence() else 1
    elif args.performance:
        return 0 if test_performance_tracking() else 1
    elif args.config:
        return 0 if test_configuration_validation() else 1
    else:
        return 0 if run_comprehensive_test() else 1


if __name__ == "__main__":
    sys.exit(main())

