#!/usr/bin/env python3
"""
Visualiseur de données pour le Mode Passive Conversational

Ce module permet de consulter et analyser les données collectées
par le mode passif de l'agent IA Reddit.
"""

import sqlite3
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import argparse


class PassiveDataViewer:
    """Visualiseur pour les données du mode passif"""

    def __init__(self, db_path: str = "data/passive_mode.db"):
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Base de données non trouvée: {db_path}")

    def get_connection(self):
        """Retourne une connexion à la base de données"""
        return sqlite3.connect(self.db_path)

    def get_overview_stats(self) -> Dict[str, Any]:
        """Retourne un aperçu général des statistiques"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Statistiques générales
            cursor.execute("SELECT COUNT(*) FROM scraped_posts")
            total_posts = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM simulated_responses")
            total_responses = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM simulated_posts")
            total_generated_posts = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT subreddit) FROM scraped_posts")
            unique_subreddits = cursor.fetchone()[0]

            # Période couverte
            cursor.execute("SELECT MIN(scraped_at), MAX(scraped_at) FROM scraped_posts")
            date_range = cursor.fetchone()

            # Posts avec réponses générées
            cursor.execute("""
                SELECT COUNT(*) FROM scraped_posts
                WHERE should_respond = 1
            """)
            posts_worth_responding = cursor.fetchone()[0]

            # Taux de réponse
            response_rate = (total_responses / posts_worth_responding * 100) if posts_worth_responding > 0 else 0

            return {
                'total_posts_scraped': total_posts,
                'total_responses_generated': total_responses,
                'total_posts_generated': total_generated_posts,
                'unique_subreddits': unique_subreddits,
                'posts_worth_responding': posts_worth_responding,
                'response_rate_percent': round(response_rate, 2),
                'date_range': {
                    'start': date_range[0],
                    'end': date_range[1]
                },
                'database_size_mb': round(self.db_path.stat().st_size / (1024 * 1024), 2)
            }

    def get_subreddit_stats(self) -> List[Dict[str, Any]]:
        """Retourne les statistiques par subreddit"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    s.subreddit,
                    COUNT(s.id) as posts_scraped,
                    AVG(s.score) as avg_post_score,
                    AVG(s.analysis_score) as avg_analysis_score,
                    COUNT(CASE WHEN s.should_respond = 1 THEN 1 END) as posts_worth_responding,
                    COUNT(r.id) as responses_generated,
                    COUNT(p.id) as posts_generated,
                    AVG(r.confidence_score) as avg_response_confidence
                FROM scraped_posts s
                LEFT JOIN simulated_responses r ON s.id = r.post_id
                LEFT JOIN simulated_posts p ON s.subreddit = p.subreddit
                GROUP BY s.subreddit
                ORDER BY posts_scraped DESC
            """)

            results = []
            for row in cursor.fetchall():
                results.append({
                    'subreddit': row[0],
                    'posts_scraped': row[1],
                    'avg_post_score': round(row[2] or 0, 2),
                    'avg_analysis_score': round(row[3] or 0, 3),
                    'posts_worth_responding': row[4],
                    'responses_generated': row[5],
                    'posts_generated': row[6],
                    'avg_response_confidence': round(row[7] or 0, 3),
                    'response_rate': round((row[5] / row[4] * 100) if row[4] > 0 else 0, 2)
                })

            return results

    def get_top_posts(self, limit: int = 10, subreddit: str = None) -> List[Dict[str, Any]]:
        """Retourne les posts les mieux notés"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT id, subreddit, title, score, num_comments,
                       analysis_score, should_respond, scraped_at
                FROM scraped_posts
            """
            params = []

            if subreddit:
                query += " WHERE subreddit = ?"
                params.append(subreddit)

            query += " ORDER BY score DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)

            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'subreddit': row[1],
                    'title': row[2],
                    'score': row[3],
                    'num_comments': row[4],
                    'analysis_score': row[5],
                    'should_respond': bool(row[6]),
                    'scraped_at': row[7]
                })

            return results

    def get_best_responses(self, limit: int = 10, subreddit: str = None) -> List[Dict[str, Any]]:
        """Retourne les meilleures réponses générées"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT r.id, r.subreddit, r.generated_content, r.confidence_score,
                       r.generated_at, s.title, s.score as post_score
                FROM simulated_responses r
                JOIN scraped_posts s ON r.post_id = s.id
            """
            params = []

            if subreddit:
                query += " WHERE r.subreddit = ?"
                params.append(subreddit)

            query += " ORDER BY r.confidence_score DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)

            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'subreddit': row[1],
                    'content': row[2],
                    'confidence_score': row[3],
                    'generated_at': row[4],
                    'post_title': row[5],
                    'post_score': row[6]
                })

            return results

    def get_generated_posts(self, limit: int = 10, subreddit: str = None) -> List[Dict[str, Any]]:
        """Retourne les posts générés"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT id, subreddit, title, content, post_type,
                       estimated_engagement, generated_at
                FROM simulated_posts
            """
            params = []

            if subreddit:
                query += " WHERE subreddit = ?"
                params.append(subreddit)

            query += " ORDER BY estimated_engagement DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)

            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'subreddit': row[1],
                    'title': row[2],
                    'content': row[3],
                    'post_type': row[4],
                    'estimated_engagement': row[5],
                    'generated_at': row[6]
                })

            return results

    def search_posts(self, keyword: str, subreddit: str = None) -> List[Dict[str, Any]]:
        """Recherche dans les posts scrapés"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT id, subreddit, title, selftext, score, analysis_score, should_respond
                FROM scraped_posts
                WHERE (title LIKE ? OR selftext LIKE ?)
            """
            params = [f"%{keyword}%", f"%{keyword}%"]

            if subreddit:
                query += " AND subreddit = ?"
                params.append(subreddit)

            query += " ORDER BY score DESC"

            cursor.execute(query, params)

            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'subreddit': row[1],
                    'title': row[2],
                    'content': row[3][:200] + "..." if row[3] and len(row[3]) > 200 else row[3],
                    'score': row[4],
                    'analysis_score': row[5],
                    'should_respond': bool(row[6])
                })

            return results

    def get_engagement_analysis(self) -> Dict[str, Any]:
        """Analyse l'engagement prévu vs réel"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Distribution des scores d'analyse
            cursor.execute("""
                SELECT
                    CASE
                        WHEN analysis_score < 0.3 THEN 'Faible (0-0.3)'
                        WHEN analysis_score < 0.6 THEN 'Moyen (0.3-0.6)'
                        WHEN analysis_score < 0.8 THEN 'Bon (0.6-0.8)'
                        ELSE 'Excellent (0.8+)'
                    END as score_range,
                    COUNT(*) as count
                FROM scraped_posts
                GROUP BY score_range
            """)

            analysis_distribution = dict(cursor.fetchall())

            # Corrélation score d'analyse vs score Reddit
            cursor.execute("""
                SELECT analysis_score, score, should_respond
                FROM scraped_posts
                WHERE score > 0
                ORDER BY analysis_score DESC
                LIMIT 100
            """)

            correlation_data = cursor.fetchall()

            # Confiance moyenne des réponses par subreddit
            cursor.execute("""
                SELECT subreddit, AVG(confidence_score) as avg_confidence, COUNT(*) as count
                FROM simulated_responses
                GROUP BY subreddit
                ORDER BY avg_confidence DESC
            """)

            confidence_by_subreddit = [
                {'subreddit': row[0], 'avg_confidence': round(row[1], 3), 'count': row[2]}
                for row in cursor.fetchall()
            ]

            return {
                'analysis_score_distribution': analysis_distribution,
                'confidence_by_subreddit': confidence_by_subreddit,
                'correlation_sample_size': len(correlation_data)
            }

    def export_to_csv(self, table: str, output_file: str, subreddit: str = None):
        """Exporte une table vers CSV"""
        with self.get_connection() as conn:
            if table == 'posts':
                query = "SELECT * FROM scraped_posts"
                params = []
                if subreddit:
                    query += " WHERE subreddit = ?"
                    params.append(subreddit)
            elif table == 'responses':
                query = "SELECT * FROM simulated_responses"
                params = []
                if subreddit:
                    query += " WHERE subreddit = ?"
                    params.append(subreddit)
            elif table == 'generated_posts':
                query = "SELECT * FROM simulated_posts"
                params = []
                if subreddit:
                    query += " WHERE subreddit = ?"
                    params.append(subreddit)
            else:
                raise ValueError(f"Table inconnue: {table}")

            df = pd.read_sql_query(query, conn, params=params)
            df.to_csv(output_file, index=False, encoding='utf-8')
            print(f"Données exportées vers {output_file}")

    def print_overview(self):
        """Affiche un aperçu général"""
        stats = self.get_overview_stats()

        print("=== APERÇU GÉNÉRAL ===")
        print(f"📊 Posts scrapés: {stats['total_posts_scraped']:,}")
        print(f"💬 Réponses générées: {stats['total_responses_generated']:,}")
        print(f"📝 Posts générés: {stats['total_posts_generated']:,}")
        print(f"🎯 Subreddits uniques: {stats['unique_subreddits']}")
        print(f"📈 Taux de réponse: {stats['response_rate_percent']}%")
        print(f"💾 Taille DB: {stats['database_size_mb']} MB")

        if stats['date_range']['start']:
            print(f"📅 Période: {stats['date_range']['start']} → {stats['date_range']['end']}")
        print()

    def print_subreddit_stats(self):
        """Affiche les statistiques par subreddit"""
        stats = self.get_subreddit_stats()

        print("=== STATISTIQUES PAR SUBREDDIT ===")
        print(f"{'Subreddit':<20} {'Posts':<8} {'Réponses':<10} {'Taux':<8} {'Score Moy':<10} {'Confiance':<10}")
        print("-" * 80)

        for stat in stats:
            print(f"r/{stat['subreddit']:<19} {stat['posts_scraped']:<8} "
                  f"{stat['responses_generated']:<10} {stat['response_rate']:<7}% "
                  f"{stat['avg_post_score']:<10} {stat['avg_response_confidence']:<10}")
        print()

    def print_top_content(self, limit: int = 5):
        """Affiche le meilleur contenu"""
        print("=== TOP POSTS SCRAPÉS ===")
        top_posts = self.get_top_posts(limit)
        for i, post in enumerate(top_posts, 1):
            print(f"{i}. r/{post['subreddit']} | Score: {post['score']} | "
                  f"Analyse: {post['analysis_score']:.3f}")
            print(f"   {post['title'][:80]}...")
            print()

        print("=== MEILLEURES RÉPONSES GÉNÉRÉES ===")
        best_responses = self.get_best_responses(limit)
        for i, response in enumerate(best_responses, 1):
            print(f"{i}. r/{response['subreddit']} | Confiance: {response['confidence_score']:.3f}")
            print(f"   Post: {response['post_title'][:60]}...")
            print(f"   Réponse: {response['content'][:100]}...")
            print()


def main():
    parser = argparse.ArgumentParser(description='Visualiseur de données - Mode Passive')
    parser.add_argument('--db', default='data/passive_mode.db',
                       help='Chemin vers la base de données')
    parser.add_argument('--overview', action='store_true',
                       help='Afficher l\'aperçu général')
    parser.add_argument('--subreddits', action='store_true',
                       help='Afficher les stats par subreddit')
    parser.add_argument('--top', type=int, default=5,
                       help='Nombre d\'éléments top à afficher')
    parser.add_argument('--search', type=str,
                       help='Rechercher un mot-clé dans les posts')
    parser.add_argument('--subreddit', type=str,
                       help='Filtrer par subreddit')
    parser.add_argument('--export', choices=['posts', 'responses', 'generated_posts'],
                       help='Exporter une table vers CSV')
    parser.add_argument('--output', type=str,
                       help='Fichier de sortie pour l\'export')

    args = parser.parse_args()

    try:
        viewer = PassiveDataViewer(args.db)

        if args.export:
            if not args.output:
                args.output = f"{args.export}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            viewer.export_to_csv(args.export, args.output, args.subreddit)
            return

        if args.search:
            results = viewer.search_posts(args.search, args.subreddit)
            print(f"=== RÉSULTATS POUR '{args.search}' ===")
            for result in results[:10]:
                print(f"r/{result['subreddit']} | Score: {result['score']} | "
                      f"Analyse: {result['analysis_score']:.3f}")
                print(f"  {result['title']}")
                if result['content']:
                    print(f"  {result['content']}")
                print()
            return

        # Affichage par défaut ou selon les options
        if args.overview or not any([args.subreddits]):
            viewer.print_overview()

        if args.subreddits or not any([args.overview]):
            viewer.print_subreddit_stats()

        viewer.print_top_content(args.top)

    except FileNotFoundError as e:
        print(f"❌ Erreur: {e}")
        print("Lancez d'abord le mode passif avec: python run_passive_mode.py")
        return 1
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())

