#!/usr/bin/env python3
"""
Script de lancement pour le Mode Conversationnel Actif

Ce script lance l'agent IA Reddit en mode actif avec sauvegarde
complète de toutes les actions dans le dossier data/.
"""

import sys
import os
import time
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# Ajouter le dossier src au path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Changer le répertoire de travail vers le dossier du projet
os.chdir(current_dir)

from config_manager import ConfigManager, setup_logging
from reddit_ai_agent import RedditAIAgent
from active_data_manager import ActiveDataManager


def run_active_mode(duration_hours: int, config_path: str = "config/config_conversationnel.yaml"):
    """Lance l'agent en mode actif pour une durée donnée"""
    print(f"=== Mode Conversationnel Actif ===")
    print(f"Durée: {duration_hours} heures")
    print(f"Configuration: {config_path}")
    print()
    
    # Vérifier la configuration
    config_manager = ConfigManager(config_path)
    if not config_manager.load_config():
        print("❌ Erreur: Impossible de charger la configuration")
        return False
    
    # Avertissement sur le mode dry run
    if config_manager.is_dry_run():
        print("⚠️  MODE DRY RUN ACTIVÉ - Aucune action réelle ne sera effectuée")
        print("   Les réponses seront générées mais pas postées sur Reddit")
    else:
        print("🚨 MODE ACTIF - Les actions seront réellement effectuées sur Reddit")
        response = input("Êtes-vous sûr de vouloir continuer ? (oui/non): ")
        if response.lower() not in ['oui', 'o', 'yes', 'y']:
            print("Annulation demandée par l'utilisateur")
            return False
    
    print()
    print("Subreddits surveillés:")
    enabled_subreddits = config_manager.get_enabled_subreddits()
    for sub in enabled_subreddits:
        status = []
        if sub.comment_enabled:
            status.append("commentaires")
        if sub.post_enabled:
            status.append("posts")
        print(f"  - r/{sub.name} ({', '.join(status)})")
    
    print()
    print("Démarrage de l'agent...")
    
    # Créer l'agent
    agent = RedditAIAgent(config_path)
    
    # Calculer l'heure de fin
    start_time = datetime.now()
    end_time = start_time + timedelta(hours=duration_hours)
    
    print(f"Début: {start_time.strftime('%H:%M:%S')}")
    print(f"Fin prévue: {end_time.strftime('%H:%M:%S')}")
    print()
    
    try:
        # Initialiser l'agent
        if not agent.initialize():
            print("❌ Échec de l'initialisation de l'agent")
            return False
        
        print("✅ Agent initialisé avec succès")
        print("📊 Toutes les actions seront sauvegardées dans data/active_mode/")
        print()
        
        # Démarrer la surveillance
        agent.running = True
        cycle = 1
        
        while datetime.now() < end_time and agent.running:
            print(f"=== Cycle {cycle} ===")
            current_time = datetime.now()
            remaining = end_time - current_time
            print(f"Temps restant: {str(remaining).split('.')[0]}")
            
            # Traiter chaque subreddit
            for subreddit_config in enabled_subreddits:
                if not agent.running:
                    break
                
                print(f"Surveillance de r/{subreddit_config.name}...")
                agent._monitor_subreddit(subreddit_config)
            
            # Afficher les statistiques
            if agent.data_manager:
                stats = agent.data_manager.get_session_stats()
                print(f"📊 Stats: {stats['posts_scraped']} posts, "
                      f"{stats['responses_posted']} réponses, "
                      f"{stats['actions_performed']} actions")
            
            cycle += 1
            
            # Attendre avant le prochain cycle (5 minutes par défaut)
            if datetime.now() < end_time and agent.running:
                wait_time = 300  # 5 minutes
                print(f"Attente de {wait_time} secondes avant le prochain cycle...")
                
                # Attendre avec possibilité d'interruption
                for i in range(wait_time):
                    if not agent.running or datetime.now() >= end_time:
                        break
                    time.sleep(1)
                    
                    # Afficher un point toutes les 30 secondes
                    if (i + 1) % 30 == 0:
                        print(".", end="", flush=True)
                
                print()  # Nouvelle ligne après les points
        
        print("\n=== Fin de la session ===")
        
        # Arrêt propre
        agent._shutdown()
        
        # Afficher les statistiques finales
        if agent.data_manager:
            final_stats = agent.data_manager.get_session_stats()
            print(f"\n📊 Statistiques finales:")
            print(f"   Posts scrapés: {final_stats['posts_scraped']}")
            print(f"   Réponses postées: {final_stats['responses_posted']}")
            print(f"   Posts créés: {final_stats['posts_created']}")
            print(f"   Actions totales: {final_stats['actions_performed']}")
            print(f"   Erreurs: {final_stats['errors_encountered']}")
            print(f"   Durée: {final_stats['session_duration_minutes']:.1f} minutes")
            print(f"   Actions/heure: {final_stats['actions_per_hour']:.1f}")
            
            # Exporter un rapport final
            print(f"\n📄 Données sauvegardées dans:")
            print(f"   - data/active_mode/active_mode.db (base de données)")
            print(f"   - data/active_mode/scraped_posts/ (posts scrapés)")
            print(f"   - data/active_mode/posted_responses/ (réponses postées)")
            print(f"   - data/active_mode/actions_log/ (log des actions)")
            print(f"   - data/active_mode/reports/ (rapports)")
        
        print("\n✅ Session terminée avec succès!")
        return True
        
    except KeyboardInterrupt:
        print("\n⚠️ Arrêt demandé par l'utilisateur")
        if agent:
            agent.running = False
            agent._shutdown()
        return True
    except Exception as e:
        print(f"\n❌ Erreur pendant l'exécution: {e}")
        if agent:
            agent.running = False
            agent._shutdown()
        return False


def main():
    parser = argparse.ArgumentParser(description='Mode Conversationnel Actif - Agent IA Reddit')
    parser.add_argument('--config', default='config/config_conversationnel.yaml', 
                       help='Fichier de configuration (défaut: config/config_conversationnel.yaml)')
    parser.add_argument('--duration', type=float, default=2.0,
                       help='Durée en heures (défaut: 2.0)')
    parser.add_argument('--stats', action='store_true',
                       help='Afficher les statistiques de la base de données active')
    
    args = parser.parse_args()
    
    if args.stats:
        # Afficher les statistiques de la base de données active
        try:
            data_manager = ActiveDataManager()
            stats = data_manager.get_database_stats()
            
            print("=== Statistiques de la Base de Données Active ===")
            print(f"Posts scrapés: {stats.get('total_posts_scraped', 0)}")
            print(f"Réponses postées: {stats.get('total_responses_posted', 0)}")
            print(f"Posts créés: {stats.get('total_posts_created', 0)}")
            print(f"Actions loggées: {stats.get('total_actions_logged', 0)}")
            print(f"Score moyen réponses: {stats.get('avg_response_score', 0)}")
            print(f"Score moyen posts: {stats.get('avg_post_score', 0)}")
            print(f"Taille DB: {stats.get('database_size_mb', 0):.2f} MB")
            
            print("\nPosts par subreddit:")
            for subreddit, count in stats.get('posts_by_subreddit', {}).items():
                print(f"  r/{subreddit}: {count} posts")
            
            return 0
            
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des stats: {e}")
            return 1
    
    # Validation de la durée
    if args.duration <= 0:
        print("❌ Erreur: La durée doit être positive")
        return 1
    
    if args.duration > 24:
        print("⚠️  Attention: Durée supérieure à 24 heures")
        response = input("Continuer ? (oui/non): ")
        if response.lower() not in ['oui', 'o', 'yes', 'y']:
            return 0
    
    # Lancer le mode actif
    success = run_active_mode(args.duration, args.config)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

