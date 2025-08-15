#!/usr/bin/env python3
"""
Mode Passive Conversational pour l'Agent IA Reddit

Ce module implémente un mode où l'agent scrape les subreddits,
génère des réponses simulées et sauvegarde tout sans poster sur Reddit.
"""

import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import sqlite3
import logging
from pathlib import Path

from reddit_interface import RedditInterface
from lm_studio_interface import LMStudioInterface
from content_analyzer import ContentAnalyzer
from safety_manager import SafetyManager


class PassiveConversationalMode:
    """Mode passif qui simule les interactions sans poster sur Reddit"""

    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)

        # Initialiser les composants
        self.reddit_interface = RedditInterface(config_manager.reddit_config)
        self.lm_studio_interface = LMStudioInterface(config_manager.lm_studio_config)
        # Récupérer les triggers depuis la configuration
        triggers = config_manager.get_triggers()
        self.content_analyzer = ContentAnalyzer(
            config_manager.safety_config,
            triggers
        )
        self.safety_manager = SafetyManager(config_manager.safety_config)

        # Configuration des dossiers de données
        self.data_dir = Path("data")
        self.posts_dir = self.data_dir / "scraped_posts"
        self.simulations_dir = self.data_dir / "simulated_interactions"
        self.reports_dir = self.data_dir / "reports"

        # Créer les dossiers
        for directory in [self.data_dir, self.posts_dir, self.simulations_dir, self.reports_dir]:
            directory.mkdir(exist_ok=True)

        # Base de données SQLite
        self.db_path = self.data_dir / "passive_mode.db"
        self.init_database()

        # Statistiques
        self.stats = {
            'posts_scraped': 0,
            'responses_generated': 0,
            'posts_generated': 0,
            'subreddits_processed': 0,
            'start_time': None,
            'last_update': None
        }

    def init_database(self):
        """Initialise la base de données SQLite"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Table des posts scrapés
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scraped_posts (
                    id TEXT PRIMARY KEY,
                    subreddit TEXT NOT NULL,
                    title TEXT NOT NULL,
                    selftext TEXT,
                    author TEXT,
                    score INTEGER,
                    num_comments INTEGER,
                    created_utc REAL,
                    url TEXT,
                    is_self BOOLEAN,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    analysis_score REAL,
                    should_respond BOOLEAN,
                    response_confidence REAL
                )
            ''')

            # Table des réponses simulées
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS simulated_responses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id TEXT NOT NULL,
                    subreddit TEXT NOT NULL,
                    response_type TEXT NOT NULL, -- 'comment' ou 'post'
                    generated_content TEXT NOT NULL,
                    confidence_score REAL,
                    trigger_reasons TEXT, -- JSON des raisons
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    estimated_engagement REAL,
                    FOREIGN KEY (post_id) REFERENCES scraped_posts (id)
                )
            ''')

            # Table des posts originaux simulés
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS simulated_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subreddit TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT,
                    post_type TEXT NOT NULL, -- 'discussion', 'question', 'insight'
                    inspiration_post_id TEXT, -- Post qui a inspiré ce post
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    estimated_engagement REAL,
                    tags TEXT -- JSON des tags/catégories
                )
            ''')

            # Table des métriques de session
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS session_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_start TIMESTAMP,
                    session_end TIMESTAMP,
                    posts_scraped INTEGER,
                    responses_generated INTEGER,
                    posts_generated INTEGER,
                    subreddits_processed INTEGER,
                    avg_response_confidence REAL,
                    config_hash TEXT
                )
            ''')

            conn.commit()
            self.logger.info("Base de données initialisée")

    def start_passive_mode(self, duration_hours: int = 24):
        """Démarre le mode passif pour une durée donnée"""
        self.logger.info(f"=== Démarrage du Mode Passive Conversational ===")
        self.logger.info(f"Durée: {duration_hours} heures")

        self.stats['start_time'] = datetime.now()

        # Authentification Reddit
        if not self.reddit_interface.authenticate():
            self.logger.error("Échec de l'authentification Reddit")
            return False

        # Test LM Studio
        if not self.lm_studio_interface.initialize():
            self.logger.error("Échec de la connexion LM Studio")
            return False

        self.logger.info("Mode passif démarré avec succès")

        # Boucle principale
        end_time = datetime.now() + timedelta(hours=duration_hours)
        cycle = 1

        while datetime.now() < end_time:
            self.logger.info(f"=== Cycle Passif {cycle} ===")

            try:
                self.process_passive_cycle()
                cycle += 1

                # Attendre avant le prochain cycle
                wait_time = self.config_manager.safety_config.get('passive_cycle_delay', 300)  # 5 minutes par défaut
                self.logger.info(f"Attente de {wait_time} secondes avant le prochain cycle...")
                time.sleep(wait_time)

            except KeyboardInterrupt:
                self.logger.info("Arrêt demandé par l'utilisateur")
                break
            except Exception as e:
                self.logger.error(f"Erreur dans le cycle passif: {e}")
                time.sleep(60)  # Attendre 1 minute avant de reprendre

        self.finalize_session()
        return True

    def process_passive_cycle(self):
        """Traite un cycle complet du mode passif"""
        enabled_subreddits = self.config_manager.get_enabled_subreddits()

        for subreddit_config in enabled_subreddits:
            subreddit_name = subreddit_config.name
            self.logger.info(f"Traitement passif de r/{subreddit_name}")

            try:
                # 1. Scraper les posts
                posts = self.scrape_subreddit_posts(subreddit_name)

                # 2. Analyser et sauvegarder
                for post in posts:
                    self.analyze_and_save_post(post, subreddit_name)

                # 3. Générer des réponses simulées
                self.generate_simulated_responses(subreddit_name)

                # 4. Générer des posts originaux simulés
                self.generate_simulated_posts(subreddit_name)

                self.stats['subreddits_processed'] += 1

            except Exception as e:
                self.logger.error(f"Erreur lors du traitement de r/{subreddit_name}: {e}")

        self.stats['last_update'] = datetime.now()
        self.save_session_stats()

    def scrape_subreddit_posts(self, subreddit_name: str, limit: int = 25) -> List[Dict[str, Any]]:
        """Scrape les posts d'un subreddit"""
        try:
            posts = self.reddit_interface.get_subreddit_posts(subreddit_name, limit)
            self.logger.info(f"Scrapé {len(posts)} posts de r/{subreddit_name}")
            self.stats['posts_scraped'] += len(posts)

            # Sauvegarder en JSON aussi
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_file = self.posts_dir / f"{subreddit_name}_{timestamp}.json"

            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(posts, f, indent=2, ensure_ascii=False, default=str)

            return posts

        except Exception as e:
            self.logger.error(f"Erreur lors du scraping de r/{subreddit_name}: {e}")
            return []

    def analyze_and_save_post(self, post_data: Dict[str, Any], subreddit_name: str):
        """Analyse un post et le sauvegarde en base"""
        try:
            # Analyser le post
            analysis = self.content_analyzer.should_respond_to_post(post_data)

            # Sauvegarder en base de données
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO scraped_posts
                    (id, subreddit, title, selftext, author, score, num_comments,
                     created_utc, url, is_self, analysis_score, should_respond, response_confidence)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    post_data['id'],
                    subreddit_name,
                    post_data.get('title', ''),
                    post_data.get('selftext', ''),
                    post_data.get('author', ''),
                    post_data.get('score', 0),
                    post_data.get('num_comments', 0),
                    post_data.get('created_utc', 0),
                    post_data.get('url', ''),
                    post_data.get('is_self', False),
                    analysis.get('score', 0.0),
                    analysis.get('should_respond', False),
                    analysis.get('confidence', 0.0)
                ))
                conn.commit()

            self.logger.debug(f"Post {post_data['id']} analysé et sauvegardé")

        except Exception as e:
            self.logger.error(f"Erreur lors de l'analyse du post {post_data.get('id', 'unknown')}: {e}")

    def generate_simulated_responses(self, subreddit_name: str):
        """Génère des réponses simulées pour les posts pertinents"""
        try:
            # Récupérer les posts qui méritent une réponse
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, title, selftext, author, score
                    FROM scraped_posts
                    WHERE subreddit = ? AND should_respond = 1
                    AND id NOT IN (SELECT post_id FROM simulated_responses)
                    ORDER BY analysis_score DESC
                    LIMIT 10
                ''', (subreddit_name,))

                posts_to_respond = cursor.fetchall()

            for post_row in posts_to_respond:
                post_id, title, selftext, author, score = post_row

                # Générer la réponse
                response = self.generate_response_for_post({
                    'id': post_id,
                    'title': title,
                    'selftext': selftext,
                    'author': author,
                    'score': score
                }, subreddit_name)

                if response:
                    # Sauvegarder la réponse simulée
                    self.save_simulated_response(post_id, subreddit_name, response)
                    self.stats['responses_generated'] += 1

            self.logger.info(f"Généré {len(posts_to_respond)} réponses simulées pour r/{subreddit_name}")

        except Exception as e:
            self.logger.error(f"Erreur lors de la génération de réponses pour r/{subreddit_name}: {e}")

    def generate_response_for_post(self, post_data: Dict[str, Any], subreddit_name: str) -> Optional[Dict[str, Any]]:
        """Génère une réponse pour un post spécifique"""
        try:
            # Construire le prompt
            instructions = self.config_manager.get_instruction(subreddit_name)

            prompt = f"""
Subreddit: r/{subreddit_name}
Post Title: {post_data['title']}
Post Content: {post_data.get('selftext', 'N/A')}
Author: {post_data.get('author', 'unknown')}
Score: {post_data.get('score', 0)}

Instructions: {instructions}

Génère une réponse engageante et pertinente pour ce post.
La réponse doit être naturelle, apporter de la valeur, et respecter le ton du subreddit.
"""

            # Générer la réponse
            generated_content = self.lm_studio_interface.generate_response(
                prompt,
                system_instruction=instructions
            )

            if generated_content:
                # Calculer un score de confiance basique
                confidence = min(len(generated_content) / 100, 1.0)  # Simple heuristique

                return {
                    'content': generated_content,
                    'confidence': confidence,
                    'type': 'comment',
                    'trigger_reasons': ['passive_mode_generation']
                }

        except Exception as e:
            self.logger.error(f"Erreur lors de la génération de réponse pour {post_data['id']}: {e}")

        return None

    def save_simulated_response(self, post_id: str, subreddit_name: str, response_data: Dict[str, Any]):
        """Sauvegarde une réponse simulée en base"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO simulated_responses
                    (post_id, subreddit, response_type, generated_content,
                     confidence_score, trigger_reasons, estimated_engagement)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    post_id,
                    subreddit_name,
                    response_data['type'],
                    response_data['content'],
                    response_data['confidence'],
                    json.dumps(response_data['trigger_reasons']),
                    response_data.get('estimated_engagement', 0.5)
                ))
                conn.commit()

            # Sauvegarder aussi en JSON pour faciliter la lecture
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_file = self.simulations_dir / f"response_{subreddit_name}_{post_id}_{timestamp}.json"

            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'post_id': post_id,
                    'subreddit': subreddit_name,
                    'response': response_data,
                    'generated_at': datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde de la réponse simulée: {e}")

    def generate_simulated_posts(self, subreddit_name: str):
        """Génère des posts originaux simulés pour un subreddit"""
        try:
            # Analyser les posts récents pour inspiration
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT title, selftext, score
                    FROM scraped_posts
                    WHERE subreddit = ? AND score > 5
                    ORDER BY created_utc DESC
                    LIMIT 5
                ''', (subreddit_name,))

                recent_posts = cursor.fetchall()

            if not recent_posts:
                return

            # Générer 1-2 posts originaux basés sur les tendances
            for i in range(min(2, len(recent_posts))):
                post = self.generate_original_post(subreddit_name, recent_posts)
                if post:
                    self.save_simulated_post(subreddit_name, post)
                    self.stats['posts_generated'] += 1

            self.logger.info(f"Généré des posts originaux simulés pour r/{subreddit_name}")

        except Exception as e:
            self.logger.error(f"Erreur lors de la génération de posts pour r/{subreddit_name}: {e}")

    def generate_original_post(self, subreddit_name: str, inspiration_posts: List) -> Optional[Dict[str, Any]]:
        """Génère un post original basé sur les tendances du subreddit"""
        try:
            instructions = self.config_manager.get_instruction(subreddit_name)

            # Analyser les tendances
            topics = []
            for title, content, score in inspiration_posts:
                topics.append(f"- {title} (score: {score})")

            prompt = f"""
Subreddit: r/{subreddit_name}
Instructions: {instructions}

Posts récents populaires:
{chr(10).join(topics)}

Génère un post original et engageant pour ce subreddit qui :
1. S'inspire des tendances actuelles
2. Apporte une perspective unique
3. Encourage la discussion
4. Respecte le style du subreddit

Format:
TITRE: [titre accrocheur]
CONTENU: [contenu du post]
TYPE: [discussion/question/insight]
"""

            generated_content = self.lm_studio_interface.generate_response(
                prompt,
                system_instruction=instructions
            )

            if generated_content:
                # Parser la réponse
                lines = generated_content.strip().split('\n')
                title = ""
                content = ""
                post_type = "discussion"

                current_section = None
                for line in lines:
                    if line.startswith('TITRE:'):
                        title = line.replace('TITRE:', '').strip()
                        current_section = 'title'
                    elif line.startswith('CONTENU:'):
                        content = line.replace('CONTENU:', '').strip()
                        current_section = 'content'
                    elif line.startswith('TYPE:'):
                        post_type = line.replace('TYPE:', '').strip().lower()
                        current_section = 'type'
                    elif current_section == 'content' and line.strip():
                        content += '\n' + line

                if title and content:
                    return {
                        'title': title,
                        'content': content,
                        'type': post_type,
                        'estimated_engagement': 0.6  # Estimation basique
                    }

        except Exception as e:
            self.logger.error(f"Erreur lors de la génération de post original: {e}")

        return None

    def save_simulated_post(self, subreddit_name: str, post_data: Dict[str, Any]):
        """Sauvegarde un post simulé en base"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO simulated_posts
                    (subreddit, title, content, post_type, estimated_engagement, tags)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    subreddit_name,
                    post_data['title'],
                    post_data['content'],
                    post_data['type'],
                    post_data.get('estimated_engagement', 0.5),
                    json.dumps([post_data['type']])  # Tags basiques
                ))
                conn.commit()

            # Sauvegarder aussi en JSON
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_file = self.simulations_dir / f"post_{subreddit_name}_{timestamp}.json"

            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'subreddit': subreddit_name,
                    'post': post_data,
                    'generated_at': datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde du post simulé: {e}")

    def save_session_stats(self):
        """Sauvegarde les statistiques de la session"""
        try:
            stats_file = self.data_dir / "session_stats.json"
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde des stats: {e}")

    def finalize_session(self):
        """Finalise la session passive"""
        self.logger.info("=== Finalisation du Mode Passive ===")

        # Sauvegarder les métriques finales
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO session_metrics
                (session_start, session_end, posts_scraped, responses_generated,
                 posts_generated, subreddits_processed, config_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.stats['start_time'],
                datetime.now(),
                self.stats['posts_scraped'],
                self.stats['responses_generated'],
                self.stats['posts_generated'],
                self.stats['subreddits_processed'],
                "passive_mode_v1"  # Hash de config simple
            ))
            conn.commit()

        self.save_session_stats()

        # Générer un rapport final
        self.generate_session_report()

        self.logger.info(f"Session terminée:")
        self.logger.info(f"- Posts scrapés: {self.stats['posts_scraped']}")
        self.logger.info(f"- Réponses générées: {self.stats['responses_generated']}")
        self.logger.info(f"- Posts générés: {self.stats['posts_generated']}")
        self.logger.info(f"- Subreddits traités: {self.stats['subreddits_processed']}")

    def generate_session_report(self):
        """Génère un rapport de session"""
        try:
            report_file = self.reports_dir / f"session_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            # Récupérer des statistiques détaillées
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Stats par subreddit
                cursor.execute('''
                    SELECT subreddit, COUNT(*) as posts_count, AVG(analysis_score) as avg_score
                    FROM scraped_posts
                    WHERE scraped_at >= ?
                    GROUP BY subreddit
                ''', (self.stats['start_time'],))
                subreddit_stats = cursor.fetchall()

                # Top réponses par confiance
                cursor.execute('''
                    SELECT subreddit, generated_content, confidence_score
                    FROM simulated_responses
                    WHERE generated_at >= ?
                    ORDER BY confidence_score DESC
                    LIMIT 10
                ''', (self.stats['start_time'],))
                top_responses = cursor.fetchall()

            report = {
                'session_info': self.stats,
                'subreddit_stats': [
                    {'subreddit': s[0], 'posts_count': s[1], 'avg_score': s[2]}
                    for s in subreddit_stats
                ],
                'top_responses': [
                    {'subreddit': r[0], 'content': r[1][:200] + '...', 'confidence': r[2]}
                    for r in top_responses
                ],
                'generated_at': datetime.now().isoformat()
            }

            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)

            self.logger.info(f"Rapport de session généré: {report_file}")

        except Exception as e:
            self.logger.error(f"Erreur lors de la génération du rapport: {e}")

    def get_database_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de la base de données"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Compter les entrées
                cursor.execute("SELECT COUNT(*) FROM scraped_posts")
                posts_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM simulated_responses")
                responses_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM simulated_posts")
                generated_posts_count = cursor.fetchone()[0]

                # Stats par subreddit
                cursor.execute('''
                    SELECT subreddit, COUNT(*)
                    FROM scraped_posts
                    GROUP BY subreddit
                ''')
                subreddit_counts = dict(cursor.fetchall())

                return {
                    'total_posts_scraped': posts_count,
                    'total_responses_generated': responses_count,
                    'total_posts_generated': generated_posts_count,
                    'posts_by_subreddit': subreddit_counts,
                    'database_size_mb': os.path.getsize(self.db_path) / (1024 * 1024)
                }

        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des stats DB: {e}")
            return {}

