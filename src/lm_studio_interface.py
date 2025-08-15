"""
Interface LM Studio pour l'Agent IA Reddit
"""

import logging
import requests
import json
from typing import Dict, Any, Optional
from openai import OpenAI
from config_manager import LMStudioConfig


class LMStudioInterface:
    """Interface pour communiquer avec LM Studio via l'API OpenAI compatible"""

    def __init__(self, config: LMStudioConfig):
        self.config = config
        self.client = None
        self.logger = logging.getLogger(__name__)

    def initialize(self) -> bool:
        """Initialise la connexion avec LM Studio"""
        try:
            self.client = OpenAI(
                base_url=f"{self.config.base_url}/v1",
                api_key=self.config.api_key
            )

            # Test de connexion
            if self.check_connection():
                self.logger.info(f"Connexion LM Studio établie: {self.config.base_url}")
                return True
            else:
                self.logger.error("Impossible de se connecter à LM Studio")
                return False

        except Exception as e:
            self.logger.error(f"Erreur lors de l'initialisation LM Studio: {e}")
            return False

    def check_connection(self) -> bool:
        """Vérifie la connexion avec LM Studio"""
        try:
            # Vérifier si le serveur répond
            response = requests.get(f"{self.config.base_url}/v1/models", timeout=5)
            if response.status_code == 200:
                models = response.json()
                self.logger.debug(f"Modèles disponibles: {models}")
                return True
            else:
                self.logger.error(f"Serveur LM Studio inaccessible: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erreur de connexion LM Studio: {e}")
            return False

    def get_available_models(self) -> list:
        """Récupère la liste des modèles disponibles"""
        try:
            response = requests.get(f"{self.config.base_url}/v1/models", timeout=5)
            if response.status_code == 200:
                models_data = response.json()
                return [model['id'] for model in models_data.get('data', [])]
            else:
                return []
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des modèles: {e}")
            return []

    def generate_response(self, prompt: str, context: Dict[str, Any] = None, system_instruction: str = None) -> Optional[str]:
        """Génère une réponse via LM Studio"""
        try:
            if not self.client:
                self.logger.error("Client LM Studio non initialisé")
                return None

            # Construire les messages
            messages = []

            # Instruction système
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})

            # Contexte si fourni
            if context:
                context_str = self._format_context(context)
                if context_str:
                    messages.append({"role": "system", "content": f"Contexte: {context_str}"})

            # Prompt utilisateur
            messages.append({"role": "user", "content": prompt})

            # Appel à l'API
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                timeout=self.config.timeout
            )

            if response.choices and len(response.choices) > 0:
                generated_text = response.choices[0].message.content
                self.logger.debug(f"Réponse générée: {generated_text[:100]}...")
                return generated_text.strip()
            else:
                self.logger.error("Aucune réponse générée par LM Studio")
                return None

        except Exception as e:
            self.logger.error(f"Erreur lors de la génération de réponse: {e}")
            return None

    def generate_comment_response(self, post_data: Dict[str, Any], instruction: str) -> Optional[str]:
        """Génère une réponse pour commenter un post"""
        try:
            # Construire le prompt pour un commentaire
            prompt = f"""
Post Title: {post_data.get('title', '')}
Post Content: {post_data.get('selftext', '')[:500]}
Subreddit: r/{post_data.get('subreddit', '')}
Score: {post_data.get('score', 0)}

Génère un commentaire utile et pertinent pour ce post Reddit.
Le commentaire doit être:
- Utile et constructif
- Respectueux du contexte
- Adapté au subreddit
- Pas trop long (max 300 mots)
- En français si le post est en français, sinon en anglais
"""

            return self.generate_response(prompt, post_data, instruction)

        except Exception as e:
            self.logger.error(f"Erreur lors de la génération de commentaire: {e}")
            return None

    def generate_reply_response(self, comment_data: Dict[str, Any], post_data: Dict[str, Any], instruction: str) -> Optional[str]:
        """Génère une réponse à un commentaire"""
        try:
            # Construire le prompt pour une réponse
            prompt = f"""
Post Original: {post_data.get('title', '')}
Commentaire à répondre: {comment_data.get('body', '')[:300]}
Auteur du commentaire: {comment_data.get('author', '')}
Subreddit: r/{post_data.get('subreddit', '')}

Génère une réponse appropriée à ce commentaire Reddit.
La réponse doit être:
- Directement liée au commentaire
- Utile et constructive
- Respectueuse
- Concise (max 200 mots)
- En français si le commentaire est en français, sinon en anglais
"""

            context = {
                'post': post_data,
                'comment': comment_data
            }

            return self.generate_response(prompt, context, instruction)

        except Exception as e:
            self.logger.error(f"Erreur lors de la génération de réponse: {e}")
            return None

    def generate_post_content(self, subreddit: str, topic: str, instruction: str) -> Optional[Dict[str, str]]:
        """Génère le contenu pour un nouveau post"""
        try:
            prompt = f"""
Subreddit: r/{subreddit}
Sujet: {topic}

Génère un post Reddit complet avec:
1. Un titre accrocheur et pertinent
2. Un contenu informatif et engageant
3. Adapté au style du subreddit

Le post doit être:
- Original et intéressant
- Respectueux des règles du subreddit
- Bien structuré
- Pas trop long (max 500 mots pour le contenu)

Réponds au format:
TITRE: [titre du post]
CONTENU: [contenu du post]
"""

            response = self.generate_response(prompt, {'subreddit': subreddit, 'topic': topic}, instruction)

            if response:
                return self._parse_post_response(response)
            else:
                return None

        except Exception as e:
            self.logger.error(f"Erreur lors de la génération de post: {e}")
            return None

    def _format_context(self, context: Dict[str, Any]) -> str:
        """Formate le contexte pour l'IA"""
        try:
            context_parts = []

            if 'post' in context:
                post = context['post']
                context_parts.append(f"Post: {post.get('title', '')} (score: {post.get('score', 0)})")

            if 'comment' in context:
                comment = context['comment']
                context_parts.append(f"Commentaire: {comment.get('body', '')[:100]}...")

            if 'subreddit' in context:
                context_parts.append(f"Subreddit: r/{context['subreddit']}")

            return " | ".join(context_parts)

        except Exception as e:
            self.logger.error(f"Erreur lors du formatage du contexte: {e}")
            return ""

    def _parse_post_response(self, response: str) -> Dict[str, str]:
        """Parse la réponse pour extraire titre et contenu"""
        try:
            lines = response.strip().split('\n')
            title = ""
            content = ""

            for line in lines:
                if line.startswith('TITRE:'):
                    title = line.replace('TITRE:', '').strip()
                elif line.startswith('CONTENU:'):
                    content = line.replace('CONTENU:', '').strip()
                elif content and not line.startswith('TITRE:'):
                    content += '\n' + line

            # Si le parsing échoue, utiliser la réponse complète comme contenu
            if not title and not content:
                content = response
                title = "Post généré automatiquement"

            return {
                'title': title[:300],  # Limiter la longueur du titre
                'content': content[:10000]  # Limiter la longueur du contenu
            }

        except Exception as e:
            self.logger.error(f"Erreur lors du parsing de la réponse: {e}")
            return {
                'title': "Post généré automatiquement",
                'content': response[:10000]
            }

    def validate_response(self, response: str, max_length: int = 1000) -> bool:
        """Valide une réponse générée"""
        if not response or len(response.strip()) == 0:
            return False

        if len(response) > max_length:
            self.logger.warning(f"Réponse trop longue: {len(response)} caractères")
            return False

        # Vérifier qu'il n'y a pas de contenu inapproprié évident
        inappropriate_keywords = ['spam', 'buy now', 'click here', 'advertisement']
        response_lower = response.lower()

        for keyword in inappropriate_keywords:
            if keyword in response_lower:
                self.logger.warning(f"Contenu potentiellement inapproprié détecté: {keyword}")
                return False

        return True


if __name__ == "__main__":
    # Test de l'interface LM Studio
    from config_manager import ConfigManager, setup_logging

    config_manager = ConfigManager()
    if config_manager.load_config():
        setup_logging(config_manager)

        lm_interface = LMStudioInterface(config_manager.lm_studio_config)
        if lm_interface.initialize():
            print("Test de génération de réponse...")

            # Test simple
            response = lm_interface.generate_response(
                "Dis bonjour en français",
                system_instruction="Tu es un assistant IA utile."
            )

            if response:
                print(f"Réponse générée: {response}")
            else:
                print("Aucune réponse générée")
        else:
            print("Échec de l'initialisation LM Studio")
    else:
        print("Erreur de configuration")

