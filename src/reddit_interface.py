"""
Interface Reddit utilisant PRAW pour l'Agent IA Reddit
"""

import praw
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from config_manager import RedditConfig


class RedditInterface:
    """Interface pour interagir avec Reddit via PRAW"""

    def __init__(self, config: RedditConfig):
        self.config = config
        self.reddit = None
        self.logger = logging.getLogger(__name__)
        self.last_request_time = 0
        self.min_request_interval = 2  # 2 secondes entre les requêtes

    def authenticate(self) -> bool:
        """Authentifie l'agent avec Reddit"""
        try:
            self.reddit = praw.Reddit(
                client_id=self.config.client_id,
                client_secret=self.config.client_secret,
                username=self.config.username,
                password=self.config.password,
                user_agent=self.config.user_agent
            )

            # Test de l'authentification
            user = self.reddit.user.me()
            if user:
                self.logger.info(f"Authentifié avec succès en tant que: {user.name}")
                return True
            else:
                self.logger.error("Échec de l'authentification Reddit")
                return False

        except Exception as e:
            self.logger.error(f"Erreur lors de l'authentification Reddit: {e}")
            return False

    def _rate_limit(self):
        """Applique le rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            self.logger.debug(f"Rate limiting: attente de {sleep_time:.2f} secondes")
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def get_subreddit_posts(self, subreddit_name: str, limit: int = 200, sort: str = 'new') -> List[Dict[str, Any]]:
        """Récupère les posts d'un subreddit"""
        try:
            self._rate_limit()

            subreddit = self.reddit.subreddit(subreddit_name)
            posts = []

            # Choisir la méthode de tri
            if sort == 'hot':
                submissions = subreddit.hot(limit=limit)
            elif sort == 'new':
                submissions = subreddit.new(limit=limit)
            elif sort == 'top':
                submissions = subreddit.top(limit=limit, time_filter='day')
            else:
                submissions = subreddit.new(limit=limit)

            for submission in submissions:
                post_data = {
                    'id': submission.id,
                    'title': submission.title,
                    'selftext': submission.selftext,
                    'author': str(submission.author) if submission.author else '[deleted]',
                    'score': submission.score,
                    'upvote_ratio': submission.upvote_ratio,
                    'num_comments': submission.num_comments,
                    'created_utc': submission.created_utc,
                    'url': submission.url,
                    'permalink': submission.permalink,
                    'subreddit': subreddit_name,
                    'is_self': submission.is_self,
                    'over_18': submission.over_18
                }
                posts.append(post_data)

            self.logger.info(f"Récupéré {len(posts)} posts de r/{subreddit_name}")
            return posts

        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des posts de r/{subreddit_name}: {e}")
            return []

    def get_post_comments(self, post_id: str, limit: int = 200) -> List[Dict[str, Any]]:
        """Récupère les commentaires d'un post"""
        try:
            self._rate_limit()

            submission = self.reddit.submission(id=post_id)
            submission.comments.replace_more(limit=0)  # Éviter les "MoreComments"

            comments = []
            for comment in submission.comments.list()[:limit]:
                if hasattr(comment, 'body'):  # Vérifier que c'est un vrai commentaire
                    comment_data = {
                        'id': comment.id,
                        'body': comment.body,
                        'author': str(comment.author) if comment.author else '[deleted]',
                        'score': comment.score,
                        'created_utc': comment.created_utc,
                        'parent_id': comment.parent_id,
                        'post_id': post_id,
                        'permalink': comment.permalink
                    }
                    comments.append(comment_data)

            self.logger.debug(f"Récupéré {len(comments)} commentaires pour le post {post_id}")
            return comments

        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des commentaires du post {post_id}: {e}")
            return []

    def post_comment(self, post_id: str, content: str, dry_run: bool = True) -> bool:
        """Poste un commentaire sur un post"""
        try:
            if dry_run:
                self.logger.info(f"[DRY RUN] Commentaire sur post {post_id}: {content[:100]}...")
                return True

            self._rate_limit()

            submission = self.reddit.submission(id=post_id)
            comment = submission.reply(content)

            if comment:
                self.logger.info(f"Commentaire posté avec succès sur {post_id}: {comment.id}")
                return True
            else:
                self.logger.error(f"Échec du posting du commentaire sur {post_id}")
                return False

        except Exception as e:
            self.logger.error(f"Erreur lors du posting du commentaire sur {post_id}: {e}")
            return False

    def reply_to_comment(self, comment_id: str, content: str, dry_run: bool = True) -> bool:
        """Répond à un commentaire"""
        try:
            if dry_run:
                self.logger.info(f"[DRY RUN] Réponse au commentaire {comment_id}: {content[:100]}...")
                return True

            self._rate_limit()

            comment = self.reddit.comment(id=comment_id)
            reply = comment.reply(content)

            if reply:
                self.logger.info(f"Réponse postée avec succès au commentaire {comment_id}: {reply.id}")
                return True
            else:
                self.logger.error(f"Échec de la réponse au commentaire {comment_id}")
                return False

        except Exception as e:
            self.logger.error(f"Erreur lors de la réponse au commentaire {comment_id}: {e}")
            return False

    def create_post(self, subreddit_name: str, title: str, content: str, dry_run: bool = True) -> bool:
        """Crée un nouveau post"""
        try:
            if dry_run:
                self.logger.info(f"[DRY RUN] Nouveau post sur r/{subreddit_name}: {title}")
                return True

            self._rate_limit()

            subreddit = self.reddit.subreddit(subreddit_name)
            submission = subreddit.submit(title=title, selftext=content)

            if submission:
                self.logger.info(f"Post créé avec succès sur r/{subreddit_name}: {submission.id}")
                return True
            else:
                self.logger.error(f"Échec de la création du post sur r/{subreddit_name}")
                return False

        except Exception as e:
            self.logger.error(f"Erreur lors de la création du post sur r/{subreddit_name}: {e}")
            return False

    def check_post_age(self, post_data: Dict[str, Any], max_age_hours: int = 24) -> bool:
        """Vérifie si un post n'est pas trop ancien"""
        post_time = datetime.fromtimestamp(post_data['created_utc'])
        current_time = datetime.now()
        age = current_time - post_time

        return age.total_seconds() / 3600 <= max_age_hours

    def check_post_score(self, post_data: Dict[str, Any], min_score: int = -5) -> bool:
        """Vérifie si le score du post est acceptable"""
        return post_data['score'] >= min_score

    def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """Récupère les informations d'un utilisateur"""
        try:
            self._rate_limit()

            redditor = self.reddit.redditor(username)

            user_info = {
                'name': redditor.name,
                'comment_karma': redditor.comment_karma,
                'link_karma': redditor.link_karma,
                'created_utc': redditor.created_utc,
                'is_suspended': redditor.is_suspended if hasattr(redditor, 'is_suspended') else False
            }

            return user_info

        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des infos utilisateur {username}: {e}")
            return None

    def check_subreddit_rules(self, subreddit_name: str) -> Dict[str, Any]:
        """Récupère les règles d'un subreddit"""
        try:
            self._rate_limit()

            subreddit = self.reddit.subreddit(subreddit_name)

            rules_info = {
                'name': subreddit.display_name,
                'title': subreddit.title,
                'description': subreddit.description,
                'subscribers': subreddit.subscribers,
                'over18': subreddit.over18,
                'rules': []
            }

            # Récupérer les règles si disponibles
            try:
                for rule in subreddit.rules:
                    rules_info['rules'].append({
                        'short_name': rule.short_name,
                        'description': rule.description,
                        'kind': rule.kind
                    })
            except:
                self.logger.debug(f"Impossible de récupérer les règles de r/{subreddit_name}")

            return rules_info

        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification des règles de r/{subreddit_name}: {e}")
            return {}


if __name__ == "__main__":
    # Test de l'interface Reddit
    from config_manager import ConfigManager, setup_logging

    config_manager = ConfigManager()
    if config_manager.load_config():
        setup_logging(config_manager)

        reddit_interface = RedditInterface(config_manager.reddit_config)
        if reddit_interface.authenticate():
            print("Test de récupération des posts...")
            posts = reddit_interface.get_subreddit_posts('test', limit=200)
            for post in posts:
                print(f"- {post['title']} (score: {post['score']})")
        else:
            print("Échec de l'authentification")
    else:
        print("Erreur de configuration")
