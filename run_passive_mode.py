#!/usr/bin/env python3
"""
Script de lancement pour le Mode Passive Conversational
"""

import sys
import os
import argparse
from pathlib import Path

# Ajouter le dossier src au path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Changer le répertoire de travail vers le dossier du projet
os.chdir(current_dir)

from config_manager import ConfigManager, setup_logging
from passive_mode import PassiveConversationalMode


def main():
    parser = argparse.ArgumentParser(description='Mode Passive Conversational - Agent IA Reddit')
    parser.add_argument('--config', default='config/config.yaml', 
                       help='Fichier de configuration (défaut: config/config.yaml)')
    parser.add_argument('--duration', type=int, default=24,
                       help='Durée en heures (défaut: 24)')
    parser.add_argument('--stats', action='store_true',
                       help='Afficher les statistiques de la base de données')
    
    args = parser.parse_args()
    
    # Charger la configuration
    config_manager = ConfigManager(args.config)
    if not config_manager.load_config():
        print("❌ Erreur: Impossible de charger la configuration")
        return 1
    
    # Configurer le logging
    setup_logging(config_manager)
    
    # Créer l'instance du mode passif
    passive_mode = PassiveConversationalMode(config_manager)
    
    if args.stats:
        # Afficher les statistiques
        print("=== Statistiques de la Base de Données ===")
        stats = passive_mode.get_database_stats()
        
        print(f"Posts scrapés: {stats.get('total_posts_scraped', 0)}")
        print(f"Réponses générées: {stats.get('total_responses_generated', 0)}")
        print(f"Posts générés: {stats.get('total_posts_generated', 0)}")
        print(f"Taille DB: {stats.get('database_size_mb', 0):.2f} MB")
        
        print("\nPosts par subreddit:")
        for subreddit, count in stats.get('posts_by_subreddit', {}).items():
            print(f"  r/{subreddit}: {count} posts")
        
        return 0
    
    print("=== Mode Passive Conversational ===")
    print(f"Configuration: {args.config}")
    print(f"Durée: {args.duration} heures")
    print()
    print("Ce mode va:")
    print("✅ Scraper les subreddits configurés")
    print("✅ Analyser tous les posts")
    print("✅ Générer des réponses simulées")
    print("✅ Créer des posts originaux simulés")
    print("✅ Sauvegarder tout en base de données")
    print("❌ AUCUNE action réelle sur Reddit")
    print()
    
    try:
        # Démarrer le mode passif
        success = passive_mode.start_passive_mode(args.duration)
        
        if success:
            print("\n✅ Mode passif terminé avec succès!")
            print("Consultez le dossier 'data/' pour les résultats:")
            print("  - data/scraped_posts/ : Posts scrapés par subreddit")
            print("  - data/simulated_interactions/ : Réponses et posts simulés")
            print("  - data/reports/ : Rapports de session")
            print("  - data/passive_mode.db : Base de données SQLite")
            return 0
        else:
            print("\n❌ Le mode passif a échoué")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Arrêt demandé par l'utilisateur")
        return 0
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

