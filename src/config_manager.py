"""
Gestionnaire de configuration pour l'Agent IA Reddit
"""

import yaml
import os
import logging
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class RedditConfig:
    """Configuration Reddit OAuth2"""
    client_id: str
    client_secret: str
    username: str
    password: str
    user_agent: str


@dataclass
class LMStudioConfig:
    """Configuration LM Studio"""
    base_url: str
    model: str
    api_key: str
    temperature: float
    max_tokens: int
    timeout: int


@dataclass
class SubredditConfig:
    """Configuration d'un subreddit"""
    name: str
    enabled: bool
    post_enabled: bool
    comment_enabled: bool
    max_posts_per_day: int
    max_comments_per_day: int


@dataclass
class SafetyConfig:
    """Configuration de sécurité"""
    max_posts_per_hour: int
    max_comments_per_hour: int
    max_actions_per_day: int
    min_delay_between_actions: int
    min_delay_between_posts: int
    min_delay_between_comments: int
    banned_keywords: List[str]
    min_post_length: int
    max_response_length: int
    min_score_threshold: int


class ConfigManager:
    """Gestionnaire de configuration principal"""

    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = config_path
        self.config = None
        self.reddit_config = None
        self.lm_studio_config = None
        self.subreddit_configs = []
        self.safety_config = None
        self.logger = logging.getLogger(__name__)

    def load_config(self) -> bool:
        """Charge la configuration depuis le fichier YAML"""
        try:
            if not os.path.exists(self.config_path):
                self.logger.error(f"Fichier de configuration non trouvé: {self.config_path}")
                return False

            with open(self.config_path, 'r', encoding='utf-8') as file:
                self.config = yaml.safe_load(file)

            # Valider et parser la configuration
            if not self._validate_config():
                return False

            self._parse_config()
            self.logger.info("Configuration chargée avec succès")
            return True

        except Exception as e:
            self.logger.error(f"Erreur lors du chargement de la configuration: {e}")
            return False

    def _validate_config(self) -> bool:
        """Valide la structure de la configuration"""
        required_sections = ['reddit', 'lm_studio', 'subreddits', 'safety']

        for section in required_sections:
            if section not in self.config:
                self.logger.error(f"Section manquante dans la configuration: {section}")
                return False

        # Vérifier les credentials Reddit
        reddit_config = self.config['reddit']
        required_reddit_fields = ['client_id', 'client_secret', 'username', 'password', 'user_agent']

        for field in required_reddit_fields:
            if field not in reddit_config or not reddit_config[field] or reddit_config[field].startswith('VOTRE_'):
                self.logger.error(f"Configuration Reddit incomplète: {field}")
                return False

        # Vérifier la configuration LM Studio
        lm_config = self.config['lm_studio']
        if lm_config['model'].startswith('VOTRE_'):
            self.logger.error("Modèle LM Studio non configuré")
            return False

        return True

    def _parse_config(self):
        """Parse la configuration en objets typés"""
        # Configuration Reddit
        reddit_data = self.config['reddit']
        self.reddit_config = RedditConfig(
            client_id=reddit_data['client_id'],
            client_secret=reddit_data['client_secret'],
            username=reddit_data['username'],
            password=reddit_data['password'],
            user_agent=reddit_data['user_agent']
        )

        # Configuration LM Studio
        lm_data = self.config['lm_studio']
        self.lm_studio_config = LMStudioConfig(
            base_url=lm_data['base_url'],
            model=lm_data['model'],
            api_key=lm_data['api_key'],
            temperature=lm_data['temperature'],
            max_tokens=lm_data['max_tokens'],
            timeout=lm_data['timeout']
        )

        # Configuration des subreddits
        self.subreddit_configs = []
        for sub_data in self.config['subreddits']:
            sub_config = SubredditConfig(
                name=sub_data['name'],
                enabled=sub_data['enabled'],
                post_enabled=sub_data['post_enabled'],
                comment_enabled=sub_data['comment_enabled'],
                max_posts_per_day=sub_data['max_posts_per_day'],
                max_comments_per_day=sub_data['max_comments_per_day']
            )
            self.subreddit_configs.append(sub_config)

        # Configuration de sécurité
        safety_data = self.config['safety']
        self.safety_config = SafetyConfig(
            max_posts_per_hour=safety_data['max_posts_per_hour'],
            max_comments_per_hour=safety_data['max_comments_per_hour'],
            max_actions_per_day=safety_data['max_actions_per_day'],
            min_delay_between_actions=safety_data['min_delay_between_actions'],
            min_delay_between_posts=safety_data['min_delay_between_posts'],
            min_delay_between_comments=safety_data['min_delay_between_comments'],
            banned_keywords=safety_data['banned_keywords'],
            min_post_length=safety_data['min_post_length'],
            max_response_length=safety_data['max_response_length'],
            min_score_threshold=safety_data['min_score_threshold']
        )

    def get_subreddit_config(self, subreddit_name: str) -> SubredditConfig:
        """Récupère la configuration d'un subreddit spécifique"""
        for config in self.subreddit_configs:
            if config.name == subreddit_name:
                return config
        return None

    def get_enabled_subreddits(self) -> List[SubredditConfig]:
        """Récupère la liste des subreddits activés"""
        return [config for config in self.subreddit_configs if config.enabled]

    def get_instruction(self, subreddit_name: str = None) -> str:
        """Récupère l'instruction pour un subreddit ou l'instruction globale"""
        instructions = self.config.get('instructions', {})

        if subreddit_name and 'subreddit_specific' in instructions:
            specific = instructions['subreddit_specific'].get(subreddit_name)
            if specific:
                return specific

        return instructions.get('global', "Tu es un assistant IA utile.")

    def get_triggers(self) -> Dict[str, Any]:
        """Récupère les triggers de configuration"""
        return self.config.get('triggers', {})

    def is_dry_run(self) -> bool:
        """Vérifie si le mode dry run est activé"""
        return self.config.get('mode', {}).get('dry_run', True)

    def is_debug(self) -> bool:
        """Vérifie si le mode debug est activé"""
        return self.config.get('mode', {}).get('debug', False)

    def is_monitor_only(self) -> bool:
        """Vérifie si le mode monitor only est activé"""
        return self.config.get('mode', {}).get('monitor_only', False)

    def get_logging_config(self) -> Dict[str, Any]:
        """Récupère la configuration de logging"""
        return self.config.get('logging', {})


def setup_logging(config_manager: ConfigManager):
    """Configure le système de logging"""
    log_config = config_manager.get_logging_config()

    # Créer le dossier de logs s'il n'existe pas
    log_file = log_config.get('file', 'logs/reddit_agent.log')
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # Configuration du logging
    logging.basicConfig(
        level=getattr(logging, log_config.get('level', 'INFO')),
        format=log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()  # Aussi afficher dans la console
        ]
    )


if __name__ == "__main__":
    # Test de la configuration
    config_manager = ConfigManager()
    if config_manager.load_config():
        print("Configuration chargée avec succès!")
        print(f"Subreddits activés: {[s.name for s in config_manager.get_enabled_subreddits()]}")
        print(f"Mode dry run: {config_manager.is_dry_run()}")
    else:
        print("Erreur lors du chargement de la configuration")

