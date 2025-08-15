#!/usr/bin/env python3
"""
Script de test pour le Mode Passive Conversational

Ce script teste toutes les fonctionnalités du mode passif
sans nécessiter une longue session de scraping.
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
from passive_mode import PassiveConversationalMode
from data_viewer import PassiveDataViewer
from report_generator import PassiveReportGenerator


def test_passive_mode_quick():
    """Test rapide du mode passif (5 minutes)"""
    print("=== Test Rapide du Mode Passive Conversational ===")
    print("Durée: 5 minutes pour validation")
    print()
    
    # Charger la configuration
    config_manager = ConfigManager('config/config.yaml')
    if not config_manager.load_config():
        print("❌ Erreur: Impossible de charger la configuration")
        return False
    
    # Configurer le logging
    setup_logging(config_manager)
    
    # Créer l'instance du mode passif
    passive_mode = PassiveConversationalMode(config_manager)
    
    print("✅ Mode passif initialisé")
    
    try:
        # Test d'authentification Reddit
        print("🔐 Test d'authentification Reddit...")
        if not passive_mode.reddit_interface.authenticate():
            print("❌ Échec de l'authentification Reddit")
            return False
        print("✅ Authentification Reddit réussie")
        
        # Test de connexion LM Studio
        print("🤖 Test de connexion LM Studio...")
        if not passive_mode.lm_studio_interface.initialize():
            print("❌ Échec de la connexion LM Studio")
            return False
        print("✅ Connexion LM Studio réussie")
        
        # Test de scraping (1 cycle seulement)
        print("📡 Test de scraping (1 cycle)...")
        passive_mode.process_passive_cycle()
        print("✅ Cycle de scraping terminé")
        
        # Vérifier les données
        stats = passive_mode.get_database_stats()
        print(f"📊 Résultats du test:")
        print(f"   - Posts scrapés: {stats.get('total_posts_scraped', 0)}")
        print(f"   - Réponses générées: {stats.get('total_responses_generated', 0)}")
        print(f"   - Posts générés: {stats.get('total_posts_generated', 0)}")
        
        if stats.get('total_posts_scraped', 0) > 0:
            print("✅ Test de scraping réussi")
        else:
            print("⚠️  Aucun post scrapé - vérifiez la configuration des subreddits")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur pendant le test: {e}")
        return False


def test_data_viewer():
    """Test du visualiseur de données"""
    print("\n=== Test du Visualiseur de Données ===")
    
    try:
        viewer = PassiveDataViewer()
        
        # Test des statistiques
        print("📊 Test des statistiques générales...")
        stats = viewer.get_overview_stats()
        print(f"✅ Statistiques récupérées: {stats['total_posts_scraped']} posts")
        
        # Test des stats par subreddit
        print("🎯 Test des statistiques par subreddit...")
        subreddit_stats = viewer.get_subreddit_stats()
        print(f"✅ Stats subreddits: {len(subreddit_stats)} subreddits")
        
        # Affichage rapide
        viewer.print_overview()
        
        return True
        
    except FileNotFoundError:
        print("⚠️  Base de données non trouvée - normal si c'est le premier test")
        return True
    except Exception as e:
        print(f"❌ Erreur dans le visualiseur: {e}")
        return False


def test_report_generator():
    """Test du générateur de rapports"""
    print("\n=== Test du Générateur de Rapports ===")
    
    try:
        generator = PassiveReportGenerator()
        
        # Test de génération JSON
        print("📄 Test de génération JSON...")
        json_file = generator.generate_json_summary()
        print(f"✅ Rapport JSON généré: {json_file}")
        
        # Test de génération HTML (sans graphiques pour éviter les erreurs)
        print("🌐 Test de génération HTML...")
        html_file = generator.generate_comprehensive_report()
        print(f"✅ Rapport HTML généré: {html_file}")
        
        return True
        
    except FileNotFoundError:
        print("⚠️  Base de données non trouvée - normal si c'est le premier test")
        return True
    except Exception as e:
        print(f"❌ Erreur dans le générateur: {e}")
        return False


def test_configuration():
    """Test de la configuration"""
    print("\n=== Test de Configuration ===")
    
    # Test de chargement de config
    print("⚙️  Test de chargement de configuration...")
    config_manager = ConfigManager('config/config.yaml')
    
    if not config_manager.load_config():
        print("❌ Échec du chargement de configuration")
        return False
    
    print("✅ Configuration chargée")
    
    # Vérifier les subreddits activés
    enabled_subreddits = config_manager.get_enabled_subreddits()
    print(f"🎯 Subreddits activés: {[s.name for s in enabled_subreddits]}")
    
    if not enabled_subreddits:
        print("⚠️  Aucun subreddit activé - activez au moins r/test")
        return False
    
    # Vérifier les triggers
    triggers = config_manager.get_triggers()
    print(f"🎯 Triggers configurés: {len(triggers.get('keywords', []))} mots-clés")
    
    return True


def run_full_test():
    """Lance tous les tests"""
    print("🧪 TESTS DU MODE PASSIVE CONVERSATIONAL")
    print("=" * 50)
    
    tests = [
        ("Configuration", test_configuration),
        ("Mode Passif", test_passive_mode_quick),
        ("Visualiseur", test_data_viewer),
        ("Générateur de Rapports", test_report_generator)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🔍 Test: {test_name}")
        print("-" * 30)
        
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
    print("📋 RÉSUMÉ DES TESTS")
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
        print("\nVous pouvez maintenant utiliser le mode passif:")
        print("  python run_passive_mode.py --duration 1")
        return True
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez la configuration.")
        return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Tests du Mode Passive Conversational')
    parser.add_argument('--quick', action='store_true',
                       help='Test rapide du mode passif seulement')
    parser.add_argument('--config', action='store_true',
                       help='Test de configuration seulement')
    parser.add_argument('--viewer', action='store_true',
                       help='Test du visualiseur seulement')
    parser.add_argument('--reports', action='store_true',
                       help='Test des rapports seulement')
    
    args = parser.parse_args()
    
    if args.quick:
        return 0 if test_passive_mode_quick() else 1
    elif args.config:
        return 0 if test_configuration() else 1
    elif args.viewer:
        return 0 if test_data_viewer() else 1
    elif args.reports:
        return 0 if test_report_generator() else 1
    else:
        return 0 if run_full_test() else 1


if __name__ == "__main__":
    sys.exit(main())

