#!/usr/bin/env python3
"""
Gestionnaire de données pour le Mode Conversationnel Actif

Ce module gère la sauvegarde de toutes les actions réelles
effectuées par l'agent IA Reddit en mode conversationnel.
"""

import json
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging


class ActiveDataManager:
    """Gestionnaire de données pour le mode conversationnel actif"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Configuration des dossiers de données
        self.data_dir = Path("data")
        self.active_dir = self.data_dir / "active_mode"
        self.scraped_dir = self.active_dir / "scraped_posts"
        self.responses_dir = self.active_dir / "posted_responses"
        self.posts_dir = self.active_dir / "created_posts"
        self.actions_dir = self.active_dir / "actions_log"
        self.reports_dir = self.active_dir / "reports"
        
        # Créer les dossiers
        for directory in [self.data_dir, self.active_dir, self.scraped_dir, 
                         self.responses_dir, self.posts_dir, self.actions_dir, self.reports_dir]:
            directory.mkdir(exist_ok=True)
        
        # Base de données SQLite pour le mode actif
        self.db_path = self.active_dir / "active_mode.db"
        self.init_database()
        
        # Statistiques de session
        self.session_stats = {
            'start_time': datetime.now(),
            'posts_scraped': 0,
            'responses_posted': 0,
            'posts_created': 0,
            'actions_performed': 0,
            'errors_encountered': 0,
            'last_action': None
        }
    
    def init_database(self):
        """Initialise la base de données SQLite pour le mode actif"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Table des posts scrapés (identique au mode passif mais avec actions)
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
                    response_confidence REAL,
                    action_taken TEXT, -- 'responded', 'ignored', 'error'
                    response_id TEXT   -- ID de la réponse si postée
                )
            ''')
            
            # Table des réponses postées (actions réelles)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS posted_responses (
                    id TEXT PRIMARY KEY,  -- ID Reddit de la réponse
                    post_id TEXT NOT NULL,
                    subreddit TEXT NOT NULL,
                    response_content TEXT NOT NULL,
                    confidence_score REAL,
                    trigger_reasons TEXT, -- JSON des raisons
                    posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reddit_score INTEGER DEFAULT 0,
                    reddit_replies INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'active', -- 'active', 'deleted', 'removed'
                    FOREIGN KEY (post_id) REFERENCES scraped_posts (id)
                )
            ''')
            
            # Table des posts créés (actions réelles)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS created_posts (
                    id TEXT PRIMARY KEY,  -- ID Reddit du post
                    subreddit TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT,
                    post_type TEXT NOT NULL, -- 'discussion', 'question', 'insight'
                    inspiration_post_id TEXT, -- Post qui a inspiré ce post
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reddit_score INTEGER DEFAULT 0,
                    reddit_comments INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'active', -- 'active', 'deleted', 'removed'
                    tags TEXT -- JSON des tags/catégories
                )
            ''')
            
            # Table des actions effectuées (log complet)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS actions_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action_type TEXT NOT NULL, -- 'scrape', 'respond', 'post', 'error'
                    subreddit TEXT NOT NULL,
                    target_id TEXT, -- ID du post/commentaire ciblé
                    result_id TEXT, -- ID du résultat (réponse/post créé)
                    action_data TEXT, -- JSON avec détails de l'action
                    success BOOLEAN,
                    error_message TEXT,
                    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    duration_seconds REAL
                )
            ''')
            
            # Table des métriques de session
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS session_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_start TIMESTAMP,
                    session_end TIMESTAMP,
                    posts_scraped INTEGER,
                    responses_posted INTEGER,
                    posts_created INTEGER,
                    actions_performed INTEGER,
                    errors_encountered INTEGER,
                    avg_response_confidence REAL,
                    avg_reddit_score REAL,
                    config_hash TEXT,
                    mode_type TEXT DEFAULT 'active'
                )
            ''')
            
            # Table de suivi des performances Reddit
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reddit_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_id TEXT NOT NULL, -- ID du post/commentaire
                    content_type TEXT NOT NULL, -- 'post' ou 'response'
                    subreddit TEXT NOT NULL,
                    initial_score INTEGER DEFAULT 0,
                    current_score INTEGER DEFAULT 0,
                    initial_comments INTEGER DEFAULT 0,
                    current_comments INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    performance_trend TEXT DEFAULT 'stable' -- 'rising', 'falling', 'stable'
                )
            ''')
            
            conn.commit()
            self.logger.info("Base de données active initialisée")
    
    def log_scraped_post(self, post_data: Dict[str, Any], subreddit_name: str, 
                        analysis_result: Dict[str, Any]) -> bool:
        """Enregistre un post scrapé"""
        try:
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
                    analysis_result.get('score', 0.0),
                    analysis_result.get('should_respond', False),
                    analysis_result.get('confidence', 0.0)
                ))
                conn.commit()
            
            # Sauvegarder aussi en JSON
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_file = self.scraped_dir / f"{subreddit_name}_{post_data['id']}_{timestamp}.json"
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'post_data': post_data,
                    'analysis_result': analysis_result,
                    'scraped_at': datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False, default=str)
            
            self.session_stats['posts_scraped'] += 1
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'enregistrement du post scrapé: {e}")
            return False
    
    def log_posted_response(self, post_id: str, response_id: str, subreddit_name: str,
                           response_content: str, confidence_score: float,
                           trigger_reasons: List[str]) -> bool:
        """Enregistre une réponse postée sur Reddit"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Enregistrer la réponse postée
                cursor.execute('''
                    INSERT INTO posted_responses 
                    (id, post_id, subreddit, response_content, confidence_score, trigger_reasons)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    response_id,
                    post_id,
                    subreddit_name,
                    response_content,
                    confidence_score,
                    json.dumps(trigger_reasons)
                ))
                
                # Mettre à jour le post original
                cursor.execute('''
                    UPDATE scraped_posts 
                    SET action_taken = 'responded', response_id = ?
                    WHERE id = ?
                ''', (response_id, post_id))
                
                conn.commit()
            
            # Sauvegarder en JSON
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_file = self.responses_dir / f"response_{subreddit_name}_{response_id}_{timestamp}.json"
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'response_id': response_id,
                    'post_id': post_id,
                    'subreddit': subreddit_name,
                    'content': response_content,
                    'confidence_score': confidence_score,
                    'trigger_reasons': trigger_reasons,
                    'posted_at': datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)
            
            self.session_stats['responses_posted'] += 1
            self.session_stats['actions_performed'] += 1
            self.session_stats['last_action'] = 'response_posted'
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'enregistrement de la réponse: {e}")
            self.session_stats['errors_encountered'] += 1
            return False
    
    def log_created_post(self, post_id: str, subreddit_name: str, title: str,
                        content: str, post_type: str, inspiration_post_id: str = None) -> bool:
        """Enregistre un post créé sur Reddit"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO created_posts 
                    (id, subreddit, title, content, post_type, inspiration_post_id, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    post_id,
                    subreddit_name,
                    title,
                    content,
                    post_type,
                    inspiration_post_id,
                    json.dumps([post_type])
                ))
                conn.commit()
            
            # Sauvegarder en JSON
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_file = self.posts_dir / f"post_{subreddit_name}_{post_id}_{timestamp}.json"
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'post_id': post_id,
                    'subreddit': subreddit_name,
                    'title': title,
                    'content': content,
                    'post_type': post_type,
                    'inspiration_post_id': inspiration_post_id,
                    'created_at': datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)
            
            self.session_stats['posts_created'] += 1
            self.session_stats['actions_performed'] += 1
            self.session_stats['last_action'] = 'post_created'
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'enregistrement du post créé: {e}")
            self.session_stats['errors_encountered'] += 1
            return False
    
    def log_action(self, action_type: str, subreddit: str, target_id: str = None,
                   result_id: str = None, action_data: Dict[str, Any] = None,
                   success: bool = True, error_message: str = None,
                   duration_seconds: float = 0.0) -> bool:
        """Enregistre une action dans le log général"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO actions_log 
                    (action_type, subreddit, target_id, result_id, action_data, 
                     success, error_message, duration_seconds)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    action_type,
                    subreddit,
                    target_id,
                    result_id,
                    json.dumps(action_data) if action_data else None,
                    success,
                    error_message,
                    duration_seconds
                ))
                conn.commit()
            
            # Sauvegarder aussi en JSON pour faciliter l'analyse
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_file = self.actions_dir / f"action_{action_type}_{timestamp}.json"
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'action_type': action_type,
                    'subreddit': subreddit,
                    'target_id': target_id,
                    'result_id': result_id,
                    'action_data': action_data,
                    'success': success,
                    'error_message': error_message,
                    'duration_seconds': duration_seconds,
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'enregistrement de l'action: {e}")
            return False
    
    def update_reddit_performance(self, content_id: str, content_type: str,
                                 subreddit: str, current_score: int,
                                 current_comments: int = 0) -> bool:
        """Met à jour les performances Reddit d'un contenu"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Vérifier si l'entrée existe
                cursor.execute('''
                    SELECT initial_score, current_score FROM reddit_performance 
                    WHERE content_id = ? AND content_type = ?
                ''', (content_id, content_type))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Mettre à jour
                    initial_score, previous_score = existing
                    
                    # Déterminer la tendance
                    if current_score > previous_score:
                        trend = 'rising'
                    elif current_score < previous_score:
                        trend = 'falling'
                    else:
                        trend = 'stable'
                    
                    cursor.execute('''
                        UPDATE reddit_performance 
                        SET current_score = ?, current_comments = ?, 
                            last_updated = CURRENT_TIMESTAMP, performance_trend = ?
                        WHERE content_id = ? AND content_type = ?
                    ''', (current_score, current_comments, trend, content_id, content_type))
                else:
                    # Créer nouvelle entrée
                    cursor.execute('''
                        INSERT INTO reddit_performance 
                        (content_id, content_type, subreddit, initial_score, current_score, 
                         initial_comments, current_comments)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (content_id, content_type, subreddit, current_score, current_score,
                          current_comments, current_comments))
                
                conn.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la mise à jour des performances: {e}")
            return False
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de la session actuelle"""
        duration = datetime.now() - self.session_stats['start_time']
        
        return {
            **self.session_stats,
            'session_duration_minutes': round(duration.total_seconds() / 60, 2),
            'actions_per_hour': round(self.session_stats['actions_performed'] / (duration.total_seconds() / 3600), 2) if duration.total_seconds() > 0 else 0
        }
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de la base de données"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Compter les entrées
                cursor.execute("SELECT COUNT(*) FROM scraped_posts")
                posts_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM posted_responses")
                responses_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM created_posts")
                created_posts_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM actions_log")
                actions_count = cursor.fetchone()[0]
                
                # Stats par subreddit
                cursor.execute('''
                    SELECT subreddit, COUNT(*) 
                    FROM scraped_posts 
                    GROUP BY subreddit
                ''')
                subreddit_counts = dict(cursor.fetchall())
                
                # Performance moyenne
                cursor.execute('''
                    SELECT AVG(current_score) 
                    FROM reddit_performance 
                    WHERE content_type = 'response'
                ''')
                avg_response_score = cursor.fetchone()[0] or 0
                
                cursor.execute('''
                    SELECT AVG(current_score) 
                    FROM reddit_performance 
                    WHERE content_type = 'post'
                ''')
                avg_post_score = cursor.fetchone()[0] or 0
                
                return {
                    'total_posts_scraped': posts_count,
                    'total_responses_posted': responses_count,
                    'total_posts_created': created_posts_count,
                    'total_actions_logged': actions_count,
                    'posts_by_subreddit': subreddit_counts,
                    'avg_response_score': round(avg_response_score, 2),
                    'avg_post_score': round(avg_post_score, 2),
                    'database_size_mb': os.path.getsize(self.db_path) / (1024 * 1024)
                }
                
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des stats DB: {e}")
            return {}
    
    def finalize_session(self):
        """Finalise la session active"""
        try:
            # Sauvegarder les métriques finales
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Calculer la confiance moyenne
                cursor.execute("SELECT AVG(confidence_score) FROM posted_responses")
                avg_confidence = cursor.fetchone()[0] or 0
                
                # Calculer le score Reddit moyen
                cursor.execute("SELECT AVG(current_score) FROM reddit_performance")
                avg_reddit_score = cursor.fetchone()[0] or 0
                
                cursor.execute('''
                    INSERT INTO session_metrics 
                    (session_start, session_end, posts_scraped, responses_posted, 
                     posts_created, actions_performed, errors_encountered, 
                     avg_response_confidence, avg_reddit_score, config_hash, mode_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    self.session_stats['start_time'],
                    datetime.now(),
                    self.session_stats['posts_scraped'],
                    self.session_stats['responses_posted'],
                    self.session_stats['posts_created'],
                    self.session_stats['actions_performed'],
                    self.session_stats['errors_encountered'],
                    avg_confidence,
                    avg_reddit_score,
                    "active_mode_v1",  # Hash de config simple
                    "active"
                ))
                conn.commit()
            
            # Sauvegarder les stats de session en JSON
            stats_file = self.active_dir / "final_session_stats.json"
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.get_session_stats(), f, indent=2, default=str)
            
            self.logger.info("Session active finalisée")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la finalisation: {e}")
    
    def export_session_report(self) -> str:
        """Exporte un rapport de session"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = self.reports_dir / f"session_report_{timestamp}.json"
            
            # Récupérer toutes les données de la session
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Posts scrapés
                cursor.execute('''
                    SELECT subreddit, COUNT(*) as count, AVG(analysis_score) as avg_score
                    FROM scraped_posts 
                    WHERE scraped_at >= ?
                    GROUP BY subreddit
                ''', (self.session_stats['start_time'],))
                scraped_stats = [
                    {'subreddit': row[0], 'count': row[1], 'avg_score': row[2]}
                    for row in cursor.fetchall()
                ]
                
                # Réponses postées
                cursor.execute('''
                    SELECT subreddit, COUNT(*) as count, AVG(confidence_score) as avg_confidence
                    FROM posted_responses 
                    WHERE posted_at >= ?
                    GROUP BY subreddit
                ''', (self.session_stats['start_time'],))
                response_stats = [
                    {'subreddit': row[0], 'count': row[1], 'avg_confidence': row[2]}
                    for row in cursor.fetchall()
                ]
                
                # Actions par type
                cursor.execute('''
                    SELECT action_type, COUNT(*) as count, 
                           SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count
                    FROM actions_log 
                    WHERE performed_at >= ?
                    GROUP BY action_type
                ''', (self.session_stats['start_time'],))
                action_stats = [
                    {'action_type': row[0], 'total': row[1], 'success': row[2]}
                    for row in cursor.fetchall()
                ]
            
            report = {
                'session_info': self.get_session_stats(),
                'scraped_stats': scraped_stats,
                'response_stats': response_stats,
                'action_stats': action_stats,
                'database_stats': self.get_database_stats(),
                'generated_at': datetime.now().isoformat()
            }
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Rapport de session exporté: {report_file}")
            return str(report_file)
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'export du rapport: {e}")
            return ""

