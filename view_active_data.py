#!/usr/bin/env python3
"""
Visualiseur de données pour le Mode Conversationnel Actif

Ce script permet de consulter et analyser les données collectées
par le mode actif de l'agent IA Reddit.
"""

import sys
import os
import sqlite3
import json
from datetime import datetime
from pathlib import Path

# Ajouter le dossier src au path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Changer le répertoire de travail vers le dossier du projet
os.chdir(current_dir)

from active_data_manager import ActiveDataManager


class ActiveDataViewer:
    """Visualiseur pour les données du mode actif"""
    
    def __init__(self, db_path: str = "data/active_mode/active_mode.db"):
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Base de données non trouvée: {db_path}")
    
    def get_connection(self):
        """Retourne une connexion à la base de données"""
        return sqlite3.connect(self.db_path)
    
    def get_overview_stats(self):
        """Retourne un aperçu général des statistiques"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Statistiques générales
            cursor.execute("SELECT COUNT(*) FROM scraped_posts")
            total_posts = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM posted_responses")
            total_responses = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM created_posts")
            total_created = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM actions_log")
            total_actions = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT subreddit) FROM scraped_posts")
            unique_subreddits = cursor.fetchone()[0]
            
            # Période couverte
            cursor.execute("SELECT MIN(scraped_at), MAX(scraped_at) FROM scraped_posts")
            date_range = cursor.fetchone()
            
            # Actions réussies vs échouées
            cursor.execute("SELECT COUNT(*) FROM actions_log WHERE success = 1")
            successful_actions = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM actions_log WHERE success = 0")
            failed_actions = cursor.fetchone()[0]
            
            # Performances moyennes
            cursor.execute("SELECT AVG(current_score) FROM reddit_performance WHERE content_type = 'response'")
            avg_response_score = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT AVG(current_score) FROM reddit_performance WHERE content_type = 'post'")
            avg_post_score = cursor.fetchone()[0] or 0
            
            return {
                'total_posts_scraped': total_posts,
                'total_responses_posted': total_responses,
                'total_posts_created': total_created,
                'total_actions_logged': total_actions,
                'unique_subreddits': unique_subreddits,
                'successful_actions': successful_actions,
                'failed_actions': failed_actions,
                'success_rate': round((successful_actions / total_actions * 100) if total_actions > 0 else 0, 2),
                'avg_response_score': round(avg_response_score, 2),
                'avg_post_score': round(avg_post_score, 2),
                'date_range': {
                    'start': date_range[0],
                    'end': date_range[1]
                },
                'database_size_mb': round(self.db_path.stat().st_size / (1024 * 1024), 2)
            }
    
    def get_recent_actions(self, limit: int = 20):
        """Retourne les actions récentes"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT action_type, subreddit, target_id, result_id, 
                       success, error_message, performed_at, duration_seconds
                FROM actions_log
                ORDER BY performed_at DESC
                LIMIT ?
            """, (limit,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'action_type': row[0],
                    'subreddit': row[1],
                    'target_id': row[2],
                    'result_id': row[3],
                    'success': bool(row[4]),
                    'error_message': row[5],
                    'performed_at': row[6],
                    'duration_seconds': row[7]
                })
            
            return results
    
    def get_posted_responses(self, limit: int = 10, subreddit: str = None):
        """Retourne les réponses postées"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT r.id, r.subreddit, r.response_content, r.confidence_score,
                       r.posted_at, r.reddit_score, r.reddit_replies, r.status,
                       s.title as post_title, s.score as post_score
                FROM posted_responses r
                JOIN scraped_posts s ON r.post_id = s.id
            """
            params = []
            
            if subreddit:
                query += " WHERE r.subreddit = ?"
                params.append(subreddit)
            
            query += " ORDER BY r.posted_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'subreddit': row[1],
                    'content': row[2],
                    'confidence_score': row[3],
                    'posted_at': row[4],
                    'reddit_score': row[5],
                    'reddit_replies': row[6],
                    'status': row[7],
                    'post_title': row[8],
                    'post_score': row[9]
                })
            
            return results
    
    def get_created_posts(self, limit: int = 10, subreddit: str = None):
        """Retourne les posts créés"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT id, subreddit, title, content, post_type,
                       created_at, reddit_score, reddit_comments, status
                FROM created_posts
            """
            params = []
            
            if subreddit:
                query += " WHERE subreddit = ?"
                params.append(subreddit)
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'subreddit': row[1],
                    'title': row[2],
                    'content': row[3][:200] + "..." if row[3] and len(row[3]) > 200 else row[3],
                    'post_type': row[4],
                    'created_at': row[5],
                    'reddit_score': row[6],
                    'reddit_comments': row[7],
                    'status': row[8]
                })
            
            return results
    
    def get_performance_stats(self):
        """Retourne les statistiques de performance"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Performance par subreddit
            cursor.execute("""
                SELECT p.subreddit, 
                       COUNT(CASE WHEN p.content_type = 'response' THEN 1 END) as responses,
                       COUNT(CASE WHEN p.content_type = 'post' THEN 1 END) as posts,
                       AVG(CASE WHEN p.content_type = 'response' THEN p.current_score END) as avg_response_score,
                       AVG(CASE WHEN p.content_type = 'post' THEN p.current_score END) as avg_post_score
                FROM reddit_performance p
                GROUP BY p.subreddit
                ORDER BY responses DESC, posts DESC
            """)
            
            subreddit_performance = []
            for row in cursor.fetchall():
                subreddit_performance.append({
                    'subreddit': row[0],
                    'responses': row[1],
                    'posts': row[2],
                    'avg_response_score': round(row[3] or 0, 2),
                    'avg_post_score': round(row[4] or 0, 2)
                })
            
            # Tendances de performance
            cursor.execute("""
                SELECT performance_trend, COUNT(*) as count
                FROM reddit_performance
                GROUP BY performance_trend
            """)
            
            trends = dict(cursor.fetchall())
            
            # Top performances
            cursor.execute("""
                SELECT content_id, content_type, subreddit, current_score, performance_trend
                FROM reddit_performance
                ORDER BY current_score DESC
                LIMIT 10
            """)
            
            top_performers = []
            for row in cursor.fetchall():
                top_performers.append({
                    'content_id': row[0],
                    'content_type': row[1],
                    'subreddit': row[2],
                    'score': row[3],
                    'trend': row[4]
                })
            
            return {
                'subreddit_performance': subreddit_performance,
                'trends': trends,
                'top_performers': top_performers
            }
    
    def get_error_analysis(self):
        """Analyse des erreurs"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Erreurs par type d'action
            cursor.execute("""
                SELECT action_type, COUNT(*) as error_count
                FROM actions_log
                WHERE success = 0
                GROUP BY action_type
                ORDER BY error_count DESC
            """)
            
            errors_by_action = dict(cursor.fetchall())
            
            # Erreurs par subreddit
            cursor.execute("""
                SELECT subreddit, COUNT(*) as error_count
                FROM actions_log
                WHERE success = 0
                GROUP BY subreddit
                ORDER BY error_count DESC
            """)
            
            errors_by_subreddit = dict(cursor.fetchall())
            
            # Messages d'erreur les plus fréquents
            cursor.execute("""
                SELECT error_message, COUNT(*) as count
                FROM actions_log
                WHERE success = 0 AND error_message IS NOT NULL
                GROUP BY error_message
                ORDER BY count DESC
                LIMIT 10
            """)
            
            common_errors = [
                {'message': row[0], 'count': row[1]}
                for row in cursor.fetchall()
            ]
            
            return {
                'errors_by_action': errors_by_action,
                'errors_by_subreddit': errors_by_subreddit,
                'common_errors': common_errors
            }
    
    def print_overview(self):
        """Affiche un aperçu général"""
        stats = self.get_overview_stats()
        
        print("=== APERÇU GÉNÉRAL MODE ACTIF ===")
        print(f"📊 Posts scrapés: {stats['total_posts_scraped']:,}")
        print(f"💬 Réponses postées: {stats['total_responses_posted']:,}")
        print(f"📝 Posts créés: {stats['total_posts_created']:,}")
        print(f"🎯 Actions totales: {stats['total_actions_logged']:,}")
        print(f"✅ Taux de succès: {stats['success_rate']}%")
        print(f"🌟 Score moyen réponses: {stats['avg_response_score']}")
        print(f"🌟 Score moyen posts: {stats['avg_post_score']}")
        print(f"🎯 Subreddits uniques: {stats['unique_subreddits']}")
        print(f"💾 Taille DB: {stats['database_size_mb']} MB")
        
        if stats['date_range']['start']:
            print(f"📅 Période: {stats['date_range']['start']} → {stats['date_range']['end']}")
        print()
    
    def print_recent_activity(self, limit: int = 10):
        """Affiche l'activité récente"""
        actions = self.get_recent_actions(limit)
        
        print(f"=== ACTIVITÉ RÉCENTE ({limit} dernières actions) ===")
        if not actions:
            print("Aucune action trouvée")
            return
        
        for action in actions:
            status = "✅" if action['success'] else "❌"
            duration = f"({action['duration_seconds']:.1f}s)" if action['duration_seconds'] else ""
            
            print(f"{status} {action['performed_at']} | {action['action_type']} | r/{action['subreddit']} {duration}")
            
            if action['target_id']:
                print(f"   Target: {action['target_id']}")
            if action['result_id']:
                print(f"   Result: {action['result_id']}")
            if not action['success'] and action['error_message']:
                print(f"   Erreur: {action['error_message']}")
            print()
    
    def print_posted_responses(self, limit: int = 5):
        """Affiche les réponses postées"""
        responses = self.get_posted_responses(limit)
        
        print(f"=== RÉPONSES POSTÉES ({limit} plus récentes) ===")
        if not responses:
            print("Aucune réponse trouvée")
            return
        
        for i, response in enumerate(responses, 1):
            score_info = f"Score: {response['reddit_score']}" if response['reddit_score'] else "Score: N/A"
            replies_info = f"Réponses: {response['reddit_replies']}" if response['reddit_replies'] else "Réponses: 0"
            
            print(f"{i}. r/{response['subreddit']} | {score_info} | {replies_info}")
            print(f"   Post: {response['post_title'][:60]}...")
            print(f"   Réponse: {response['content'][:100]}...")
            print(f"   Confiance: {response['confidence_score']:.3f} | Statut: {response['status']}")
            print(f"   Posté: {response['posted_at']}")
            print()
    
    def print_performance_summary(self):
        """Affiche un résumé des performances"""
        perf = self.get_performance_stats()
        
        print("=== RÉSUMÉ DES PERFORMANCES ===")
        
        print("Par subreddit:")
        for sub_perf in perf['subreddit_performance'][:5]:  # Top 5
            print(f"  r/{sub_perf['subreddit']}: {sub_perf['responses']} réponses "
                  f"(score: {sub_perf['avg_response_score']}), "
                  f"{sub_perf['posts']} posts (score: {sub_perf['avg_post_score']})")
        
        print(f"\nTendances de performance:")
        for trend, count in perf['trends'].items():
            print(f"  {trend}: {count}")
        
        print(f"\nTop performers:")
        for performer in perf['top_performers'][:3]:
            print(f"  {performer['content_type']} sur r/{performer['subreddit']}: "
                  f"score {performer['score']} ({performer['trend']})")
        print()
    
    def print_error_summary(self):
        """Affiche un résumé des erreurs"""
        errors = self.get_error_analysis()
        
        print("=== ANALYSE DES ERREURS ===")
        
        if errors['errors_by_action']:
            print("Erreurs par type d'action:")
            for action, count in errors['errors_by_action'].items():
                print(f"  {action}: {count}")
        
        if errors['errors_by_subreddit']:
            print(f"\nErreurs par subreddit:")
            for subreddit, count in list(errors['errors_by_subreddit'].items())[:5]:
                print(f"  r/{subreddit}: {count}")
        
        if errors['common_errors']:
            print(f"\nErreurs les plus fréquentes:")
            for error in errors['common_errors'][:3]:
                print(f"  {error['message'][:60]}... ({error['count']}x)")
        print()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Visualiseur de données - Mode Actif')
    parser.add_argument('--db', default='data/active_mode/active_mode.db',
                       help='Chemin vers la base de données')
    parser.add_argument('--overview', action='store_true',
                       help='Afficher l\'aperçu général')
    parser.add_argument('--recent', type=int, default=10,
                       help='Nombre d\'actions récentes à afficher')
    parser.add_argument('--responses', type=int, default=5,
                       help='Nombre de réponses postées à afficher')
    parser.add_argument('--performance', action='store_true',
                       help='Afficher les performances')
    parser.add_argument('--errors', action='store_true',
                       help='Afficher l\'analyse des erreurs')
    parser.add_argument('--subreddit', type=str,
                       help='Filtrer par subreddit')
    
    args = parser.parse_args()
    
    try:
        viewer = ActiveDataViewer(args.db)
        
        # Affichage par défaut ou selon les options
        if args.overview or not any([args.performance, args.errors]):
            viewer.print_overview()
        
        viewer.print_recent_activity(args.recent)
        viewer.print_posted_responses(args.responses)
        
        if args.performance:
            viewer.print_performance_summary()
        
        if args.errors:
            viewer.print_error_summary()
        
    except FileNotFoundError as e:
        print(f"❌ Erreur: {e}")
        print("Lancez d'abord le mode actif avec: python run_active_mode.py")
        return 1
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

