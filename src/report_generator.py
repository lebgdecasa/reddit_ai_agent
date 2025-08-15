#!/usr/bin/env python3
"""
Générateur de rapports avancés pour le Mode Passive Conversational

Ce module génère des rapports détaillés et des visualisations
des données collectées par le mode passif.
"""

import sqlite3
import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import numpy as np
from collections import Counter
import re


class PassiveReportGenerator:
    """Générateur de rapports pour les données du mode passif"""

    def __init__(self, db_path: str = "data/passive_mode.db"):
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Base de données non trouvée: {db_path}")

        self.reports_dir = Path("data/reports")
        self.reports_dir.mkdir(exist_ok=True)

        # Configuration des graphiques
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")

    def get_connection(self):
        """Retourne une connexion à la base de données"""
        return sqlite3.connect(self.db_path)

    def generate_comprehensive_report(self) -> str:
        """Génère un rapport complet"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.reports_dir / f"comprehensive_report_{timestamp}.html"

        # Collecter toutes les données
        overview = self._get_overview_data()
        subreddit_analysis = self._get_subreddit_analysis()
        content_analysis = self._get_content_analysis()
        engagement_analysis = self._get_engagement_analysis()
        temporal_analysis = self._get_temporal_analysis()
        quality_analysis = self._get_quality_analysis()

        # Générer les graphiques
        charts = self._generate_charts()

        # Créer le HTML
        html_content = self._create_html_report(
            overview, subreddit_analysis, content_analysis,
            engagement_analysis, temporal_analysis, quality_analysis, charts
        )

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"Rapport complet généré: {report_file}")
        return str(report_file)

    def _get_overview_data(self) -> Dict[str, Any]:
        """Collecte les données d'aperçu général"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Statistiques de base
            cursor.execute("SELECT COUNT(*) FROM scraped_posts")
            total_posts = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM simulated_responses")
            total_responses = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM simulated_posts")
            total_generated = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT subreddit) FROM scraped_posts")
            unique_subreddits = cursor.fetchone()[0]

            # Période d'activité
            cursor.execute("SELECT MIN(scraped_at), MAX(scraped_at) FROM scraped_posts")
            date_range = cursor.fetchone()

            # Scores moyens
            cursor.execute("SELECT AVG(score), AVG(analysis_score) FROM scraped_posts")
            avg_scores = cursor.fetchone()

            # Taux de réponse
            cursor.execute("SELECT COUNT(*) FROM scraped_posts WHERE should_respond = 1")
            posts_worth_responding = cursor.fetchone()[0]

            return {
                'total_posts': total_posts,
                'total_responses': total_responses,
                'total_generated': total_generated,
                'unique_subreddits': unique_subreddits,
                'date_range': date_range,
                'avg_reddit_score': round(avg_scores[0] or 0, 2),
                'avg_analysis_score': round(avg_scores[1] or 0, 3),
                'posts_worth_responding': posts_worth_responding,
                'response_rate': round((total_responses / posts_worth_responding * 100) if posts_worth_responding > 0 else 0, 2)
            }

    def _get_subreddit_analysis(self) -> List[Dict[str, Any]]:
        """Analyse détaillée par subreddit"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    s.subreddit,
                    COUNT(s.id) as posts_count,
                    AVG(s.score) as avg_score,
                    AVG(s.analysis_score) as avg_analysis,
                    COUNT(CASE WHEN s.should_respond = 1 THEN 1 END) as worth_responding,
                    COUNT(r.id) as responses_generated,
                    AVG(r.confidence_score) as avg_confidence,
                    COUNT(p.id) as posts_generated,
                    MAX(s.score) as max_score,
                    MIN(s.score) as min_score
                FROM scraped_posts s
                LEFT JOIN simulated_responses r ON s.id = r.post_id
                LEFT JOIN simulated_posts p ON s.subreddit = p.subreddit
                GROUP BY s.subreddit
                ORDER BY posts_count DESC
            """)

            results = []
            for row in cursor.fetchall():
                results.append({
                    'subreddit': row[0],
                    'posts_count': row[1],
                    'avg_score': round(row[2] or 0, 2),
                    'avg_analysis': round(row[3] or 0, 3),
                    'worth_responding': row[4],
                    'responses_generated': row[5],
                    'avg_confidence': round(row[6] or 0, 3),
                    'posts_generated': row[7],
                    'max_score': row[8] or 0,
                    'min_score': row[9] or 0,
                    'response_rate': round((row[5] / row[4] * 100) if row[4] > 0 else 0, 2)
                })

            return results

    def _get_content_analysis(self) -> Dict[str, Any]:
        """Analyse du contenu des posts et réponses"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Analyse des titres les plus fréquents
            cursor.execute("SELECT title FROM scraped_posts WHERE title IS NOT NULL")
            titles = [row[0] for row in cursor.fetchall()]

            # Extraire les mots-clés des titres
            title_words = []
            for title in titles:
                words = re.findall(r'\b[a-zA-Z]{4,}\b', title.lower())
                title_words.extend(words)

            common_words = Counter(title_words).most_common(20)

            # Analyse de la longueur des réponses
            cursor.execute("SELECT LENGTH(generated_content) FROM simulated_responses")
            response_lengths = [row[0] for row in cursor.fetchall()]

            # Types de posts générés
            cursor.execute("SELECT post_type, COUNT(*) FROM simulated_posts GROUP BY post_type")
            post_types = dict(cursor.fetchall())

            return {
                'common_title_words': common_words,
                'response_length_stats': {
                    'avg': round(np.mean(response_lengths) if response_lengths else 0, 2),
                    'median': round(np.median(response_lengths) if response_lengths else 0, 2),
                    'min': min(response_lengths) if response_lengths else 0,
                    'max': max(response_lengths) if response_lengths else 0
                },
                'generated_post_types': post_types
            }

    def _get_engagement_analysis(self) -> Dict[str, Any]:
        """Analyse de l'engagement prévu"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Distribution des scores d'analyse
            cursor.execute("""
                SELECT
                    CASE
                        WHEN analysis_score < 0.2 THEN 'Très faible'
                        WHEN analysis_score < 0.4 THEN 'Faible'
                        WHEN analysis_score < 0.6 THEN 'Moyen'
                        WHEN analysis_score < 0.8 THEN 'Bon'
                        ELSE 'Excellent'
                    END as category,
                    COUNT(*) as count
                FROM scraped_posts
                GROUP BY category
            """)

            analysis_distribution = dict(cursor.fetchall())

            # Corrélation score Reddit vs score d'analyse
            cursor.execute("""
                SELECT score, analysis_score
                FROM scraped_posts
                WHERE score > 0 AND analysis_score > 0
            """)

            correlation_data = cursor.fetchall()

            # Confiance des réponses par subreddit
            cursor.execute("""
                SELECT subreddit, AVG(confidence_score), COUNT(*)
                FROM simulated_responses
                GROUP BY subreddit
                ORDER BY AVG(confidence_score) DESC
            """)

            confidence_by_subreddit = [
                {'subreddit': row[0], 'avg_confidence': round(row[1], 3), 'count': row[2]}
                for row in cursor.fetchall()
            ]

            return {
                'analysis_distribution': analysis_distribution,
                'correlation_data': correlation_data,
                'confidence_by_subreddit': confidence_by_subreddit
            }

    def _get_temporal_analysis(self) -> Dict[str, Any]:
        """Analyse temporelle de l'activité"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Activité par heure
            cursor.execute("""
                SELECT
                    strftime('%H', scraped_at) as hour,
                    COUNT(*) as count
                FROM scraped_posts
                GROUP BY hour
                ORDER BY hour
            """)

            hourly_activity = dict(cursor.fetchall())

            # Activité par jour
            cursor.execute("""
                SELECT
                    DATE(scraped_at) as date,
                    COUNT(*) as posts_count,
                    COUNT(CASE WHEN should_respond = 1 THEN 1 END) as worth_responding
                FROM scraped_posts
                GROUP BY date
                ORDER BY date
            """)

            daily_activity = [
                {'date': row[0], 'posts': row[1], 'worth_responding': row[2]}
                for row in cursor.fetchall()
            ]

            return {
                'hourly_activity': hourly_activity,
                'daily_activity': daily_activity
            }

    def _get_quality_analysis(self) -> Dict[str, Any]:
        """Analyse de la qualité des réponses générées"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Distribution de la confiance
            cursor.execute("""
                SELECT
                    CASE
                        WHEN confidence_score < 0.3 THEN 'Faible'
                        WHEN confidence_score < 0.6 THEN 'Moyenne'
                        WHEN confidence_score < 0.8 THEN 'Bonne'
                        ELSE 'Excellente'
                    END as quality,
                    COUNT(*) as count
                FROM simulated_responses
                GROUP BY quality
            """)

            confidence_distribution = dict(cursor.fetchall())

            # Meilleures réponses
            cursor.execute("""
                SELECT r.subreddit, r.generated_content, r.confidence_score, s.title
                FROM simulated_responses r
                JOIN scraped_posts s ON r.post_id = s.id
                ORDER BY r.confidence_score DESC
                LIMIT 10
            """)

            best_responses = [
                {
                    'subreddit': row[0],
                    'content': row[1][:200] + '...' if len(row[1]) > 200 else row[1],
                    'confidence': row[2],
                    'post_title': row[3][:100] + '...' if len(row[3]) > 100 else row[3]
                }
                for row in cursor.fetchall()
            ]

            return {
                'confidence_distribution': confidence_distribution,
                'best_responses': best_responses
            }

    def _generate_charts(self) -> Dict[str, str]:
        """Génère les graphiques et retourne les chemins des fichiers"""
        charts = {}

        # 1. Graphique des posts par subreddit
        subreddit_data = self._get_subreddit_analysis()
        if subreddit_data:
            plt.figure(figsize=(12, 6))
            subreddits = [s['subreddit'] for s in subreddit_data]
            counts = [s['posts_count'] for s in subreddit_data]

            plt.bar(subreddits, counts)
            plt.title('Posts Scrapés par Subreddit')
            plt.xlabel('Subreddit')
            plt.ylabel('Nombre de Posts')
            plt.xticks(rotation=45)
            plt.tight_layout()

            chart_file = self.reports_dir / 'chart_posts_by_subreddit.png'
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            charts['posts_by_subreddit'] = str(chart_file)

        # 2. Distribution des scores d'analyse
        engagement_data = self._get_engagement_analysis()
        if engagement_data['analysis_distribution']:
            plt.figure(figsize=(10, 6))
            categories = list(engagement_data['analysis_distribution'].keys())
            values = list(engagement_data['analysis_distribution'].values())

            plt.pie(values, labels=categories, autopct='%1.1f%%')
            plt.title('Distribution des Scores d\'Analyse')

            chart_file = self.reports_dir / 'chart_analysis_distribution.png'
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            charts['analysis_distribution'] = str(chart_file)

        # 3. Corrélation score Reddit vs score d'analyse
        if engagement_data['correlation_data']:
            plt.figure(figsize=(10, 6))
            reddit_scores = [d[0] for d in engagement_data['correlation_data']]
            analysis_scores = [d[1] for d in engagement_data['correlation_data']]

            plt.scatter(reddit_scores, analysis_scores, alpha=0.6)
            plt.xlabel('Score Reddit')
            plt.ylabel('Score d\'Analyse')
            plt.title('Corrélation Score Reddit vs Score d\'Analyse')

            # Ligne de tendance
            z = np.polyfit(reddit_scores, analysis_scores, 1)
            p = np.poly1d(z)
            plt.plot(reddit_scores, p(reddit_scores), "r--", alpha=0.8)

            chart_file = self.reports_dir / 'chart_correlation.png'
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            charts['correlation'] = str(chart_file)

        # 4. Activité temporelle
        temporal_data = self._get_temporal_analysis()
        if temporal_data['daily_activity']:
            plt.figure(figsize=(12, 6))
            dates = [d['date'] for d in temporal_data['daily_activity']]
            posts = [d['posts'] for d in temporal_data['daily_activity']]

            plt.plot(dates, posts, marker='o')
            plt.title('Activité de Scraping par Jour')
            plt.xlabel('Date')
            plt.ylabel('Nombre de Posts')
            plt.xticks(rotation=45)
            plt.tight_layout()

            chart_file = self.reports_dir / 'chart_daily_activity.png'
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            charts['daily_activity'] = str(chart_file)

        return charts

    def _create_html_report(self, overview, subreddit_analysis, content_analysis,
                           engagement_analysis, temporal_analysis, quality_analysis, charts) -> str:
        """Crée le rapport HTML complet"""

        html = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rapport Mode Passive Conversational</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }}
        h1, h2, h3 {{
            color: #2c3e50;
        }}
        h1 {{
            text-align: center;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }}
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            display: block;
        }}
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        .chart {{
            text-align: center;
            margin: 30px 0;
        }}
        .chart img {{
            max-width: 100%;
            height: auto;
            border-radius: 5px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        .response-sample {{
            background: #ecf0f1;
            padding: 15px;
            border-left: 4px solid #3498db;
            margin: 10px 0;
            border-radius: 5px;
        }}
        .confidence-high {{ color: #27ae60; font-weight: bold; }}
        .confidence-medium {{ color: #f39c12; font-weight: bold; }}
        .confidence-low {{ color: #e74c3c; font-weight: bold; }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #7f8c8d;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Rapport Mode Passive Conversational</h1>
        <p style="text-align: center; color: #7f8c8d;">
            Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}
        </p>

        <h2>📊 Aperçu Général</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <span class="stat-number">{overview['total_posts']:,}</span>
                <span class="stat-label">Posts Scrapés</span>
            </div>
            <div class="stat-card">
                <span class="stat-number">{overview['total_responses']:,}</span>
                <span class="stat-label">Réponses Générées</span>
            </div>
            <div class="stat-card">
                <span class="stat-number">{overview['total_generated']:,}</span>
                <span class="stat-label">Posts Générés</span>
            </div>
            <div class="stat-card">
                <span class="stat-number">{overview['unique_subreddits']}</span>
                <span class="stat-label">Subreddits</span>
            </div>
            <div class="stat-card">
                <span class="stat-number">{overview['response_rate']}%</span>
                <span class="stat-label">Taux de Réponse</span>
            </div>
            <div class="stat-card">
                <span class="stat-number">{overview['avg_analysis_score']}</span>
                <span class="stat-label">Score Analyse Moyen</span>
            </div>
        </div>

        <p><strong>Période d'activité:</strong> {overview['date_range'][0]} → {overview['date_range'][1]}</p>
        <p><strong>Score Reddit moyen:</strong> {overview['avg_reddit_score']}</p>

        <h2>🎯 Analyse par Subreddit</h2>
        <table>
            <thead>
                <tr>
                    <th>Subreddit</th>
                    <th>Posts</th>
                    <th>Réponses</th>
                    <th>Taux</th>
                    <th>Score Moyen</th>
                    <th>Confiance</th>
                    <th>Posts Générés</th>
                </tr>
            </thead>
            <tbody>
        """

        for sub in subreddit_analysis:
            html += f"""
                <tr>
                    <td>r/{sub['subreddit']}</td>
                    <td>{sub['posts_count']}</td>
                    <td>{sub['responses_generated']}</td>
                    <td>{sub['response_rate']}%</td>
                    <td>{sub['avg_score']}</td>
                    <td>{sub['avg_confidence']}</td>
                    <td>{sub['posts_generated']}</td>
                </tr>
            """

        html += """
            </tbody>
        </table>
        """

        # Ajouter les graphiques
        if charts:
            html += "<h2>📈 Visualisations</h2>"

            for chart_name, chart_path in charts.items():
                chart_filename = Path(chart_path).name
                html += f"""
                <div class="chart">
                    <h3>{chart_name.replace('_', ' ').title()}</h3>
                    <img src="{chart_filename}" alt="{chart_name}">
                </div>
                """

        # Analyse du contenu
        html += f"""
        <h2>📝 Analyse du Contenu</h2>
        <h3>Mots-clés les plus fréquents dans les titres</h3>
        <p>
        """

        for word, count in content_analysis['common_title_words'][:10]:
            html += f"<span style='background: #3498db; color: white; padding: 5px 10px; margin: 5px; border-radius: 15px; display: inline-block;'>{word} ({count})</span> "

        html += f"""
        </p>

        <h3>Statistiques des réponses générées</h3>
        <ul>
            <li><strong>Longueur moyenne:</strong> {content_analysis['response_length_stats']['avg']} caractères</li>
            <li><strong>Longueur médiane:</strong> {content_analysis['response_length_stats']['median']} caractères</li>
            <li><strong>Plus courte:</strong> {content_analysis['response_length_stats']['min']} caractères</li>
            <li><strong>Plus longue:</strong> {content_analysis['response_length_stats']['max']} caractères</li>
        </ul>

        <h2>⭐ Meilleures Réponses Générées</h2>
        """

        for i, response in enumerate(quality_analysis['best_responses'][:5], 1):
            confidence_class = 'confidence-high' if response['confidence'] > 0.7 else 'confidence-medium' if response['confidence'] > 0.4 else 'confidence-low'
            html += f"""
            <div class="response-sample">
                <h4>{i}. r/{response['subreddit']} - <span class="{confidence_class}">Confiance: {response['confidence']:.3f}</span></h4>
                <p><strong>Post:</strong> {response['post_title']}</p>
                <p><strong>Réponse:</strong> {response['content']}</p>
            </div>
            """

        html += f"""
        <div class="footer">
            <p>Rapport généré par l'Agent IA Reddit - Mode Passive Conversational</p>
            <p>Base de données: {self.db_path}</p>
        </div>
    </div>
</body>
</html>
        """

        return html

    def generate_json_summary(self) -> str:
        """Génère un résumé JSON pour l'API"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_file = self.reports_dir / f"summary_{timestamp}.json"

        summary = {
            'generated_at': datetime.now().isoformat(),
            'overview': self._get_overview_data(),
            'subreddit_analysis': self._get_subreddit_analysis(),
            'content_analysis': self._get_content_analysis(),
            'engagement_analysis': self._get_engagement_analysis(),
            'quality_analysis': self._get_quality_analysis()
        }

        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False, default=str)

        print(f"Résumé JSON généré: {json_file}")
        return str(json_file)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Générateur de rapports - Mode Passive')
    parser.add_argument('--db', default='data/passive_mode.db',
                       help='Chemin vers la base de données')
    parser.add_argument('--html', action='store_true',
                       help='Générer un rapport HTML complet')
    parser.add_argument('--json', action='store_true',
                       help='Générer un résumé JSON')

    args = parser.parse_args()

    try:
        generator = PassiveReportGenerator(args.db)

        if args.html or not args.json:
            report_file = generator.generate_comprehensive_report()
            print(f"✅ Rapport HTML généré: {report_file}")

        if args.json:
            json_file = generator.generate_json_summary()
            print(f"✅ Résumé JSON généré: {json_file}")

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
