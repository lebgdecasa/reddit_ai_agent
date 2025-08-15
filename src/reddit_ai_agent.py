"""
Agent IA Reddit Principal
Orchestre tous les composants pour surveiller et répondre automatiquement sur Reddit
"""

import time
import logging
import signal
import sys
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

from config_manager import ConfigManager, setup_logging
from reddit_interface import RedditInterface
from lm_studio_interface import LMStudioInterface
from content_analyzer import ContentAnalyzer
from safety_manager import SafetyManager
from active_data_manager import ActiveDataManager


class RedditAIAgent:
    """Agent IA principal pour Reddit"""

    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_manager = ConfigManager(config_path)
        self.reddit_interface = None
        self.lm_studio_interface = None
        self.content_analyzer = None
        self.safety_manager = None
        self.data_manager = None  # Gestionnaire de données actif

        self.logger = None
        self.running = False
        self.processed_posts = set()
        self.processed_comments = set()

        # Gestionnaire de signaux pour arrêt propre
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def initialize(self) -> bool:
        """Initialise tous les composants de l'agent"""
        try:
            # Charger la configuration
            if not self.config_manager.load_config():
                print("Erreur: Impossible de charger la configuration")
                return False

            # Configurer le logging
            setup_logging(self.config_manager)
            self.logger = logging.getLogger(__name__)

            self.logger.info("=== Initialisation de l'Agent IA Reddit ===")

            # Initialiser les composants
            self.reddit_interface = RedditInterface(self.config_manager.reddit_config)
            self.lm_studio_interface = LMStudioInterface(self.config_manager.lm_studio_config)

            # Récupérer les triggers depuis la configuration
            triggers = self.config_manager.get_triggers()
            self.content_analyzer = ContentAnalyzer(
                self.config_manager.safety_config,
                triggers
            )
            self.safety_manager = SafetyManager(self.config_manager.safety_config)

            # Initialiser le gestionnaire de données actif
            self.data_manager = ActiveDataManager()

            # Authentifier Reddit
            if not self.reddit_interface.authenticate():
                self.logger.error("Échec de l'authentification Reddit")
                return False

            # Initialiser LM Studio
            if not self.lm_studio_interface.initialize():
                self.logger.error("Échec de l'initialisation LM Studio")
                return False

            # Vérifier le mode de fonctionnement
            if self.config_manager.is_dry_run():
                self.logger.warning("MODE DRY RUN ACTIVÉ - Aucune action réelle ne sera effectuée")

            if self.config_manager.is_monitor_only():
                self.logger.info("MODE MONITOR ONLY - Surveillance sans réponse")

            self.logger.info("Initialisation terminée avec succès")
            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"Erreur lors de l'initialisation: {e}")
            else:
                print(f"Erreur lors de l'initialisation: {e}")
            return False

    def start(self):
        """Démarre l'agent"""
        if not self.initialize():
            return False

        self.logger.info("=== Démarrage de l'Agent IA Reddit ===")
        self.running = True

        try:
            # Afficher les subreddits surveillés
            enabled_subreddits = self.config_manager.get_enabled_subreddits()
            subreddit_names = [sub.name for sub in enabled_subreddits]
            self.logger.info(f"Surveillance des subreddits: {subreddit_names}")

            # Boucle principale
            cycle_count = 0
            while self.running:
                cycle_count += 1
                self.logger.info(f"=== Cycle {cycle_count} ===")

                try:
                    # Surveiller chaque subreddit activé
                    for subreddit_config in enabled_subreddits:
                        if not self.running:
                            break

                        self._monitor_subreddit(subreddit_config)

                    # Nettoyer les anciennes données périodiquement
                    if cycle_count % 10 == 0:  # Tous les 10 cycles
                        self.safety_manager.cleanup_old_data()

                    # Attendre avant le prochain cycle
                    if self.running:
                        sleep_time = 300  # 5 minutes entre les cycles
                        self.logger.info(f"Attente de {sleep_time} secondes avant le prochain cycle...")
                        time.sleep(sleep_time)

                except Exception as e:
                    self.logger.error(f"Erreur dans le cycle {cycle_count}: {e}")
                    time.sleep(60)  # Attendre 1 minute avant de reprendre

        except KeyboardInterrupt:
            self.logger.info("Arrêt demandé par l'utilisateur")
        except Exception as e:
            self.logger.error(f"Erreur fatale: {e}")
        finally:
            self._shutdown()

    def _monitor_subreddit(self, subreddit_config):
        """Surveille un subreddit spécifique"""
        subreddit_name = subreddit_config.name
        self.logger.info(f"Surveillance de r/{subreddit_name}")

        try:
            # Récupérer les nouveaux posts
            posts = self.reddit_interface.get_subreddit_posts(
                subreddit_name,
                limit=20,
                sort='new'
            )

            new_posts = [post for post in posts if post['id'] not in self.processed_posts]

            if new_posts:
                self.logger.info(f"Trouvé {len(new_posts)} nouveaux posts sur r/{subreddit_name}")

                for post in new_posts:
                    if not self.running:
                        break

                    self._process_post(post, subreddit_config)
                    self.processed_posts.add(post['id'])

            # Surveiller les commentaires sur les posts récents
            if subreddit_config.comment_enabled:
                recent_posts = posts[:5]  # Surveiller les 5 posts les plus récents
                for post in recent_posts:
                    if not self.running:
                        break

                    self._monitor_post_comments(post, subreddit_config)

        except Exception as e:
            self.logger.error(f"Erreur lors de la surveillance de r/{subreddit_name}: {e}")

    def _process_post(self, post_data: Dict[str, Any], subreddit_config):
        """Traite un post individuel"""
        post_id = post_data['id']
        subreddit_name = subreddit_config.name

        try:
            self.logger.debug(f"Analyse du post {post_id}: {post_data['title'][:50]}...")

            # Analyser si on doit répondre
            analysis = self.content_analyzer.should_respond_to_post(post_data)

            # Sauvegarder le post scrapé avec l'analyse
            self.data_manager.log_scraped_post(post_data, subreddit_name, analysis)

            if analysis['should_respond'] and subreddit_config.comment_enabled:
                self.logger.info(f"Post intéressant détecté: {post_id} (confiance: {analysis['confidence']:.2f})")
                self.logger.debug(f"Raisons: {analysis['reasons']}")

                if not self.config_manager.is_monitor_only():
                    self._respond_to_post(post_data, subreddit_config)
            else:
                self.logger.debug(f"Post ignoré: {post_id} - {analysis['reasons']}")

        except Exception as e:
            self.logger.error(f"Erreur lors du traitement du post {post_id}: {e}")
            # Enregistrer l'erreur
            self.data_manager.log_action('error', subreddit_name, post_id,
                                       success=False, error_message=str(e))

    def _monitor_post_comments(self, post_data: Dict[str, Any], subreddit_config):
        """Surveille les commentaires d'un post"""
        post_id = post_data['id']

        try:
            comments = self.reddit_interface.get_post_comments(post_id, limit=10)
            new_comments = [comment for comment in comments if comment['id'] not in self.processed_comments]

            for comment in new_comments:
                if not self.running:
                    break

                self._process_comment(comment, post_data, subreddit_config)
                self.processed_comments.add(comment['id'])

        except Exception as e:
            self.logger.error(f"Erreur lors de la surveillance des commentaires du post {post_id}: {e}")

    def _process_comment(self, comment_data: Dict[str, Any], post_data: Dict[str, Any], subreddit_config):
        """Traite un commentaire individuel"""
        comment_id = comment_data['id']

        try:
            # Vérifier que ce n'est pas notre propre commentaire
            if comment_data['author'] == self.config_manager.reddit_config.username:
                return

            self.logger.debug(f"Analyse du commentaire {comment_id}")

            # Analyser si on doit répondre
            analysis = self.content_analyzer.should_respond_to_comment(comment_data, post_data)

            if analysis['should_respond'] and subreddit_config.comment_enabled:
                self.logger.info(f"Commentaire intéressant détecté: {comment_id} (confiance: {analysis['confidence']:.2f})")

                if not self.config_manager.is_monitor_only():
                    self._respond_to_comment(comment_data, post_data, subreddit_config)
            else:
                self.logger.debug(f"Commentaire ignoré: {comment_id} - {analysis['reasons']}")

        except Exception as e:
            self.logger.error(f"Erreur lors du traitement du commentaire {comment_id}: {e}")

    def _respond_to_post(self, post_data: Dict[str, Any], subreddit_config):
        """Génère et poste une réponse à un post"""
        post_id = post_data['id']
        subreddit_name = subreddit_config.name
        start_time = time.time()

        try:
            # Vérifier les limites de sécurité
            safety_check = self.safety_manager.can_perform_action('comment', subreddit_name)
            if not safety_check['allowed']:
                self.logger.warning(f"Action bloquée par la sécurité: {safety_check['reason']}")
                self.data_manager.log_action('respond', subreddit_name, post_id,
                                           success=False, error_message=safety_check['reason'])
                return

            # Récupérer l'instruction pour ce subreddit
            instruction = self.config_manager.get_instruction(subreddit_name)

            # Générer la réponse
            self.logger.info(f"Génération d'une réponse pour le post {post_id}...")
            response = self.lm_studio_interface.generate_comment_response(post_data, instruction)

            if not response:
                self.logger.error("Aucune réponse générée")
                self.data_manager.log_action('respond', subreddit_name, post_id,
                                           success=False, error_message="Aucune réponse générée")
                return

            # Valider la réponse
            if not self.content_analyzer.is_safe_content(response):
                self.logger.warning("Réponse générée non sécurisée, ignorée")
                self.data_manager.log_action('respond', subreddit_name, post_id,
                                           success=False, error_message="Contenu non sécurisé")
                return

            # Poster la réponse
            dry_run = self.config_manager.is_dry_run()
            result = self.reddit_interface.post_comment(post_id, response, dry_run)

            # Calculer la durée
            duration = time.time() - start_time

            if result and not dry_run:
                # Réponse postée avec succès
                response_id = result.get('id', f"dry_run_{int(time.time())}")
                confidence = self.content_analyzer.calculate_response_confidence(response, post_data)

                # Sauvegarder la réponse postée
                self.data_manager.log_posted_response(
                    post_id, response_id, subreddit_name, response,
                    confidence, ['post_analysis']
                )

                # Enregistrer l'action
                self.data_manager.log_action('respond', subreddit_name, post_id,
                                           result_id=response_id,
                                           action_data={'response': response, 'confidence': confidence},
                                           success=True, duration_seconds=duration)

                self.logger.info(f"Réponse postée avec succès sur {post_id} (ID: {response_id})")

                # Enregistrer pour suivi des performances
                self.data_manager.update_reddit_performance(response_id, 'response', subreddit_name, 0, 0)

            elif dry_run:
                # Mode dry run
                response_id = f"dry_run_{int(time.time())}"
                confidence = self.content_analyzer.calculate_response_confidence(response, post_data)

                self.data_manager.log_action('respond', subreddit_name, post_id,
                                           result_id=response_id,
                                           action_data={'response': response, 'confidence': confidence, 'dry_run': True},
                                           success=True, duration_seconds=duration)

                self.logger.info(f"[DRY RUN] Réponse générée pour {post_id}: {response[:100]}...")
            else:
                # Échec du posting
                self.data_manager.log_action('respond', subreddit_name, post_id,
                                           success=False, error_message="Échec du posting",
                                           duration_seconds=duration)
                self.logger.error(f"Échec du posting de la réponse sur {post_id}")

            # Enregistrer l'action dans le safety manager
            self.safety_manager.record_action('comment', subreddit_name, post_id, response, bool(result))

        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Erreur lors de la réponse au post {post_id}: {e}")
            self.data_manager.log_action('respond', subreddit_name, post_id,
                                       success=False, error_message=str(e),
                                       duration_seconds=duration)

    def _respond_to_comment(self, comment_data: Dict[str, Any], post_data: Dict[str, Any], subreddit_config):
        """Génère et poste une réponse à un commentaire"""
        comment_id = comment_data['id']
        subreddit_name = subreddit_config.name

        try:
            # Vérifier les limites de sécurité
            safety_check = self.safety_manager.can_perform_action('comment', subreddit_name)
            if not safety_check['allowed']:
                self.logger.warning(f"Action bloquée par la sécurité: {safety_check['reason']}")
                return

            # Récupérer l'instruction pour ce subreddit
            instruction = self.config_manager.get_instruction(subreddit_name)

            # Générer la réponse
            self.logger.info(f"Génération d'une réponse pour le commentaire {comment_id}...")
            response = self.lm_studio_interface.generate_reply_response(comment_data, post_data, instruction)

            if not response:
                self.logger.error("Aucune réponse générée")
                return

            # Valider la réponse
            if not self.content_analyzer.is_safe_content(response):
                self.logger.warning("Réponse générée non sécurisée, ignorée")
                return

            # Poster la réponse
            dry_run = self.config_manager.is_dry_run()
            success = self.reddit_interface.reply_to_comment(comment_id, response, dry_run)

            # Enregistrer l'action
            self.safety_manager.record_action('comment', subreddit_name, comment_id, response, success)

            if success:
                self.logger.info(f"Réponse postée avec succès au commentaire {comment_id}")
            else:
                self.logger.error(f"Échec de la réponse au commentaire {comment_id}")

        except Exception as e:
            self.logger.error(f"Erreur lors de la réponse au commentaire {comment_id}: {e}")

    def _signal_handler(self, signum, frame):
        """Gestionnaire de signaux pour arrêt propre"""
        self.logger.info(f"Signal {signum} reçu, arrêt en cours...")
        self.running = False

    def _shutdown(self):
        """Arrêt propre de l'agent"""
        self.logger.info("=== Arrêt de l'Agent IA Reddit ===")
        self.running = False

        # Finaliser les données
        if self.data_manager:
            self.data_manager.finalize_session()

            # Exporter un rapport final
            report_file = self.data_manager.export_session_report()
            if report_file:
                self.logger.info(f"Rapport de session exporté: {report_file}")

            # Afficher les statistiques de données
            data_stats = self.data_manager.get_database_stats()
            self.logger.info(f"Statistiques de données: {data_stats}")

        # Afficher les statistiques finales
        if self.safety_manager:
            stats = self.safety_manager.get_statistics()
            self.logger.info(f"Statistiques finales: {stats}")

        self.logger.info("Agent arrêté")

    def get_status(self) -> Dict[str, Any]:
        """Récupère le statut actuel de l'agent"""
        status = {
            'running': self.running,
            'processed_posts': len(self.processed_posts),
            'processed_comments': len(self.processed_comments),
            'config': {
                'dry_run': self.config_manager.is_dry_run(),
                'monitor_only': self.config_manager.is_monitor_only(),
                'enabled_subreddits': [s.name for s in self.config_manager.get_enabled_subreddits()]
            }
        }

        if self.safety_manager:
            status['safety'] = self.safety_manager.get_statistics()

        return status


def main():
    """Point d'entrée principal"""
    print("=== Agent IA Reddit ===")
    print("Initialisation...")

    agent = RedditAIAgent()

    try:
        agent.start()
    except Exception as e:
        print(f"Erreur fatale: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

