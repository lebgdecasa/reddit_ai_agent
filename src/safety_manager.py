"""
Gestionnaire de sécurité et rate limiting pour l'Agent IA Reddit
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
from config_manager import SafetyConfig


class SafetyManager:
    """Gestionnaire de sécurité et rate limiting"""

    def __init__(self, safety_config: SafetyConfig, data_dir: str = "data"):
        self.safety_config = safety_config
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        self.actions_file = self.data_dir / "actions_log.json"
        self.stats_file = self.data_dir / "stats.json"

        self.logger = logging.getLogger(__name__)

        # Cache en mémoire pour les actions récentes
        self.recent_actions = []
        self.daily_stats = {}

        # Charger les données existantes
        self._load_data()

        # État d'urgence
        self.emergency_stop_active = False
        self.emergency_reason = ""

    def _load_data(self):
        """Charge les données d'actions depuis le fichier"""
        try:
            if self.actions_file.exists():
                with open(self.actions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.recent_actions = data.get('actions', [])

                # Nettoyer les actions anciennes (garder seulement les dernières 24h)
                cutoff_time = time.time() - 86400  # 24 heures
                self.recent_actions = [
                    action for action in self.recent_actions
                    if action.get('timestamp', 0) > cutoff_time
                ]

            if self.stats_file.exists():
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    self.daily_stats = json.load(f)

        except Exception as e:
            self.logger.error(f"Erreur lors du chargement des données: {e}")
            self.recent_actions = []
            self.daily_stats = {}

    def _save_data(self):
        """Sauvegarde les données d'actions"""
        try:
            # Sauvegarder les actions
            with open(self.actions_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'actions': self.recent_actions,
                    'last_updated': time.time()
                }, f, indent=2, ensure_ascii=False)

            # Sauvegarder les statistiques
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.daily_stats, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde: {e}")

    def can_perform_action(self, action_type: str, subreddit: str = None) -> Dict[str, Any]:
        """Vérifie si une action peut être effectuée"""
        result = {
            'allowed': False,
            'reason': '',
            'wait_time': 0,
            'limits_status': {}
        }

        try:
            # Vérifier l'arrêt d'urgence
            if self.emergency_stop_active:
                result['reason'] = f"Arrêt d'urgence actif: {self.emergency_reason}"
                return result

            current_time = time.time()

            # Vérifier les délais minimums
            delay_check = self._check_minimum_delays(action_type, current_time)
            if not delay_check['allowed']:
                result.update(delay_check)
                return result

            # Vérifier les limites horaires
            hourly_check = self._check_hourly_limits(action_type, current_time)
            if not hourly_check['allowed']:
                result.update(hourly_check)
                return result

            # Vérifier les limites quotidiennes
            daily_check = self._check_daily_limits(action_type, current_time)
            if not daily_check['allowed']:
                result.update(daily_check)
                return result

            # Vérifier les limites spécifiques au subreddit
            if subreddit:
                subreddit_check = self._check_subreddit_limits(action_type, subreddit, current_time)
                if not subreddit_check['allowed']:
                    result.update(subreddit_check)
                    return result

            # Toutes les vérifications passées
            result['allowed'] = True
            result['reason'] = "Action autorisée"
            result['limits_status'] = self._get_limits_status(current_time)

            return result

        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification d'action: {e}")
            result['reason'] = f"Erreur de vérification: {e}"
            return result

    def _check_minimum_delays(self, action_type: str, current_time: float) -> Dict[str, Any]:
        """Vérifie les délais minimums entre actions"""
        result = {'allowed': True, 'reason': '', 'wait_time': 0}

        # Délai minimum entre toutes actions
        last_action_time = self._get_last_action_time()
        if last_action_time:
            time_since_last = current_time - last_action_time
            min_delay = self.safety_config.min_delay_between_actions

            if time_since_last < min_delay:
                wait_time = min_delay - time_since_last
                result['allowed'] = False
                result['reason'] = f"Délai minimum non respecté: {time_since_last:.1f}s < {min_delay}s"
                result['wait_time'] = wait_time
                return result

        # Délais spécifiques par type d'action
        if action_type == 'post':
            last_post_time = self._get_last_action_time('post')
            if last_post_time:
                time_since_last_post = current_time - last_post_time
                min_delay = self.safety_config.min_delay_between_posts

                if time_since_last_post < min_delay:
                    wait_time = min_delay - time_since_last_post
                    result['allowed'] = False
                    result['reason'] = f"Délai minimum entre posts non respecté: {time_since_last_post:.1f}s < {min_delay}s"
                    result['wait_time'] = wait_time
                    return result

        elif action_type == 'comment':
            last_comment_time = self._get_last_action_time('comment')
            if last_comment_time:
                time_since_last_comment = current_time - last_comment_time
                min_delay = self.safety_config.min_delay_between_comments

                if time_since_last_comment < min_delay:
                    wait_time = min_delay - time_since_last_comment
                    result['allowed'] = False
                    result['reason'] = f"Délai minimum entre commentaires non respecté: {time_since_last_comment:.1f}s < {min_delay}s"
                    result['wait_time'] = wait_time
                    return result

        return result

    def _check_hourly_limits(self, action_type: str, current_time: float) -> Dict[str, Any]:
        """Vérifie les limites horaires"""
        result = {'allowed': True, 'reason': '', 'wait_time': 0}

        # Compter les actions de la dernière heure
        hour_ago = current_time - 3600
        hourly_actions = [
            action for action in self.recent_actions
            if action.get('timestamp', 0) > hour_ago
        ]

        if action_type == 'post':
            post_count = len([a for a in hourly_actions if a.get('type') == 'post'])
            if post_count >= self.safety_config.max_posts_per_hour:
                result['allowed'] = False
                result['reason'] = f"Limite horaire de posts atteinte: {post_count}/{self.safety_config.max_posts_per_hour}"
                # Calculer le temps d'attente jusqu'à ce que le plus ancien post sorte de la fenêtre d'1h
                oldest_post = min([a['timestamp'] for a in hourly_actions if a.get('type') == 'post'], default=current_time)
                result['wait_time'] = (oldest_post + 3600) - current_time
                return result

        elif action_type == 'comment':
            comment_count = len([a for a in hourly_actions if a.get('type') == 'comment'])
            if comment_count >= self.safety_config.max_comments_per_hour:
                result['allowed'] = False
                result['reason'] = f"Limite horaire de commentaires atteinte: {comment_count}/{self.safety_config.max_comments_per_hour}"
                oldest_comment = min([a['timestamp'] for a in hourly_actions if a.get('type') == 'comment'], default=current_time)
                result['wait_time'] = (oldest_comment + 3600) - current_time
                return result

        return result

    def _check_daily_limits(self, action_type: str, current_time: float) -> Dict[str, Any]:
        """Vérifie les limites quotidiennes"""
        result = {'allowed': True, 'reason': '', 'wait_time': 0}

        today = datetime.fromtimestamp(current_time).strftime('%Y-%m-%d')
        today_stats = self.daily_stats.get(today, {})

        total_actions = today_stats.get('total_actions', 0)
        if total_actions >= self.safety_config.max_actions_per_day:
            result['allowed'] = False
            result['reason'] = f"Limite quotidienne d'actions atteinte: {total_actions}/{self.safety_config.max_actions_per_day}"
            # Temps d'attente jusqu'à minuit
            tomorrow = datetime.fromtimestamp(current_time).replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            result['wait_time'] = tomorrow.timestamp() - current_time
            return result

        return result

    def _check_subreddit_limits(self, action_type: str, subreddit: str, current_time: float) -> Dict[str, Any]:
        """Vérifie les limites spécifiques au subreddit"""
        result = {'allowed': True, 'reason': '', 'wait_time': 0}

        # Compter les actions sur ce subreddit aujourd'hui
        today = datetime.fromtimestamp(current_time).strftime('%Y-%m-%d')
        today_stats = self.daily_stats.get(today, {})
        subreddit_stats = today_stats.get('subreddits', {}).get(subreddit, {})

        if action_type == 'post':
            post_count = subreddit_stats.get('posts', 0)
            # Limite par défaut de 2 posts par jour par subreddit
            max_posts = 2
            if post_count >= max_posts:
                result['allowed'] = False
                result['reason'] = f"Limite quotidienne de posts sur r/{subreddit} atteinte: {post_count}/{max_posts}"
                return result

        elif action_type == 'comment':
            comment_count = subreddit_stats.get('comments', 0)
            # Limite par défaut de 10 commentaires par jour par subreddit
            max_comments = 10
            if comment_count >= max_comments:
                result['allowed'] = False
                result['reason'] = f"Limite quotidienne de commentaires sur r/{subreddit} atteinte: {comment_count}/{max_comments}"
                return result

        return result

    def record_action(self, action_type: str, subreddit: str, target_id: str, content: str = "", success: bool = True):
        """Enregistre une action effectuée"""
        try:
            current_time = time.time()
            today = datetime.fromtimestamp(current_time).strftime('%Y-%m-%d')

            # Enregistrer l'action
            action_record = {
                'timestamp': current_time,
                'type': action_type,
                'subreddit': subreddit,
                'target_id': target_id,
                'content_length': len(content),
                'success': success,
                'date': today
            }

            self.recent_actions.append(action_record)

            # Mettre à jour les statistiques quotidiennes
            if today not in self.daily_stats:
                self.daily_stats[today] = {
                    'total_actions': 0,
                    'successful_actions': 0,
                    'failed_actions': 0,
                    'subreddits': {}
                }

            day_stats = self.daily_stats[today]
            day_stats['total_actions'] += 1

            if success:
                day_stats['successful_actions'] += 1
            else:
                day_stats['failed_actions'] += 1

            # Statistiques par subreddit
            if subreddit not in day_stats['subreddits']:
                day_stats['subreddits'][subreddit] = {
                    'posts': 0,
                    'comments': 0,
                    'total': 0
                }

            subreddit_stats = day_stats['subreddits'][subreddit]
            subreddit_stats['total'] += 1

            if action_type == 'post':
                subreddit_stats['posts'] += 1
            elif action_type == 'comment':
                subreddit_stats['comments'] += 1

            # Sauvegarder
            self._save_data()

            self.logger.info(f"Action enregistrée: {action_type} sur r/{subreddit} ({'succès' if success else 'échec'})")

        except Exception as e:
            self.logger.error(f"Erreur lors de l'enregistrement d'action: {e}")

    def _get_last_action_time(self, action_type: str = None) -> Optional[float]:
        """Récupère le timestamp de la dernière action"""
        if not self.recent_actions:
            return None

        if action_type:
            filtered_actions = [a for a in self.recent_actions if a.get('type') == action_type]
            if not filtered_actions:
                return None
            return max(a['timestamp'] for a in filtered_actions)
        else:
            return max(a['timestamp'] for a in self.recent_actions)

    def _get_limits_status(self, current_time: float) -> Dict[str, Any]:
        """Récupère le statut actuel des limites"""
        hour_ago = current_time - 3600
        hourly_actions = [
            action for action in self.recent_actions
            if action.get('timestamp', 0) > hour_ago
        ]

        today = datetime.fromtimestamp(current_time).strftime('%Y-%m-%d')
        today_stats = self.daily_stats.get(today, {})

        hourly_posts = len([a for a in hourly_actions if a.get('type') == 'post'])
        hourly_comments = len([a for a in hourly_actions if a.get('type') == 'comment'])

        return {
            'hourly': {
                'posts': f"{hourly_posts}/{self.safety_config.max_posts_per_hour}",
                'comments': f"{hourly_comments}/{self.safety_config.max_comments_per_hour}"
            },
            'daily': {
                'total_actions': f"{today_stats.get('total_actions', 0)}/{self.safety_config.max_actions_per_day}",
                'successful_actions': today_stats.get('successful_actions', 0),
                'failed_actions': today_stats.get('failed_actions', 0)
            }
        }

    def emergency_stop(self, reason: str):
        """Active l'arrêt d'urgence"""
        self.emergency_stop_active = True
        self.emergency_reason = reason
        self.logger.critical(f"ARRÊT D'URGENCE ACTIVÉ: {reason}")

    def clear_emergency_stop(self):
        """Désactive l'arrêt d'urgence"""
        self.emergency_stop_active = False
        self.emergency_reason = ""
        self.logger.info("Arrêt d'urgence désactivé")

    def get_statistics(self) -> Dict[str, Any]:
        """Récupère les statistiques complètes"""
        current_time = time.time()

        return {
            'emergency_stop': {
                'active': self.emergency_stop_active,
                'reason': self.emergency_reason
            },
            'limits_status': self._get_limits_status(current_time),
            'daily_stats': self.daily_stats,
            'recent_actions_count': len(self.recent_actions)
        }

    def cleanup_old_data(self, days_to_keep: int = 7):
        """Nettoie les anciennes données"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime('%Y-%m-%d')

            # Nettoyer les statistiques quotidiennes
            dates_to_remove = [date for date in self.daily_stats.keys() if date < cutoff_date]
            for date in dates_to_remove:
                del self.daily_stats[date]

            # Nettoyer les actions récentes (garder seulement les dernières 24h)
            cutoff_time = time.time() - 86400
            self.recent_actions = [
                action for action in self.recent_actions
                if action.get('timestamp', 0) > cutoff_time
            ]

            self._save_data()
            self.logger.info(f"Nettoyage effectué: supprimé {len(dates_to_remove)} jours de données")

        except Exception as e:
            self.logger.error(f"Erreur lors du nettoyage: {e}")


if __name__ == "__main__":
    # Test du gestionnaire de sécurité
    from config_manager import ConfigManager, setup_logging

    config_manager = ConfigManager()
    if config_manager.load_config():
        setup_logging(config_manager)

        safety_manager = SafetyManager(config_manager.safety_config)

        # Test de vérification d'action
        result = safety_manager.can_perform_action('comment', 'test')
        print(f"Peut commenter: {result['allowed']}")
        print(f"Raison: {result['reason']}")
        print(f"Statut des limites: {result['limits_status']}")

        # Test d'enregistrement d'action
        safety_manager.record_action('comment', 'test', 'test123', 'Test comment', True)

        # Afficher les statistiques
        stats = safety_manager.get_statistics()
        print(f"Statistiques: {json.dumps(stats, indent=2, ensure_ascii=False)}")
    else:
        print("Erreur de configuration")

