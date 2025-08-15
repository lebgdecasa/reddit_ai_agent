"""
Analyseur de contenu pour l'Agent IA Reddit
"""

import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from config_manager import SafetyConfig


class ContentAnalyzer:
    """Analyse le contenu Reddit pour déterminer les actions appropriées"""

    def __init__(self, safety_config: SafetyConfig, triggers: Dict[str, Any]):
        self.safety_config = safety_config
        self.triggers = triggers
        self.logger = logging.getLogger(__name__)

        # Compiler les patterns regex pour l'efficacité
        self.compiled_patterns = []
        for pattern in triggers.get('patterns', []):
            try:
                self.compiled_patterns.append(re.compile(pattern, re.IGNORECASE))
            except re.error as e:
                self.logger.warning(f"Pattern regex invalide '{pattern}': {e}")

    def should_respond_to_post(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Détermine si l'agent doit répondre à un post"""
        analysis = {
            'should_respond': False,
            'confidence': 0.0,
            'reasons': [],
            'warnings': []
        }

        try:
            # Vérifications de sécurité de base
            if not self._basic_safety_checks(post_data, analysis):
                return analysis

            # Vérifier l'âge du post
            if not self._check_post_age(post_data, analysis):
                return analysis

            # Vérifier le score du post
            if not self._check_post_score(post_data, analysis):
                return analysis

            # Vérifier la longueur du contenu
            if not self._check_content_length(post_data, analysis):
                return analysis

            # Analyser les triggers
            trigger_score = self._analyze_triggers(post_data, analysis)

            # Analyser le contenu pour la pertinence
            relevance_score = self._analyze_relevance(post_data, analysis)

            # Calculer le score final
            final_score = (trigger_score + relevance_score) / 2
            analysis['confidence'] = final_score

            # Décision finale
            if final_score >= 0.6:  # Seuil de confiance
                analysis['should_respond'] = True
                analysis['reasons'].append(f"Score de confiance élevé: {final_score:.2f}")
            else:
                analysis['reasons'].append(f"Score de confiance insuffisant: {final_score:.2f}")

            return analysis

        except Exception as e:
            self.logger.error(f"Erreur lors de l'analyse du post {post_data.get('id', 'unknown')}: {e}")
            analysis['warnings'].append(f"Erreur d'analyse: {e}")
            return analysis

    def should_respond_to_comment(self, comment_data: Dict[str, Any], post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Détermine si l'agent doit répondre à un commentaire"""
        analysis = {
            'should_respond': False,
            'confidence': 0.0,
            'reasons': [],
            'warnings': []
        }

        try:
            # Vérifications de sécurité de base
            if not self._basic_safety_checks(comment_data, analysis, is_comment=True):
                return analysis

            # Vérifier que ce n'est pas notre propre commentaire
            # (cette vérification devrait être faite ailleurs avec le nom d'utilisateur)

            # Vérifier la longueur du commentaire
            comment_length = len(comment_data.get('body', ''))
            min_length = self.triggers.get('conditions', {}).get('min_comment_length', 5)

            if comment_length < min_length:
                analysis['reasons'].append(f"Commentaire trop court: {comment_length} caractères")
                return analysis

            # Analyser les triggers dans le commentaire
            trigger_score = self._analyze_triggers(comment_data, analysis, content_field='body')

            # Analyser la pertinence
            relevance_score = self._analyze_comment_relevance(comment_data, post_data, analysis)

            # Calculer le score final
            final_score = (trigger_score + relevance_score) / 2
            analysis['confidence'] = final_score

            # Décision finale
            if final_score >= 0.5:  # Seuil plus bas pour les commentaires
                analysis['should_respond'] = True
                analysis['reasons'].append(f"Score de confiance suffisant: {final_score:.2f}")
            else:
                analysis['reasons'].append(f"Score de confiance insuffisant: {final_score:.2f}")

            return analysis

        except Exception as e:
            self.logger.error(f"Erreur lors de l'analyse du commentaire {comment_data.get('id', 'unknown')}: {e}")
            analysis['warnings'].append(f"Erreur d'analyse: {e}")
            return analysis

    def _basic_safety_checks(self, content_data: Dict[str, Any], analysis: Dict[str, Any], is_comment: bool = False) -> bool:
        """Effectue les vérifications de sécurité de base"""

        # Vérifier les mots-clés interdits
        content_field = 'body' if is_comment else 'selftext'
        content = content_data.get(content_field, '') + ' ' + content_data.get('title', '')
        content_lower = content.lower()

        for banned_word in self.safety_config.banned_keywords:
            if banned_word.lower() in content_lower:
                analysis['reasons'].append(f"Mot-clé interdit détecté: {banned_word}")
                analysis['warnings'].append("Contenu potentiellement inapproprié")
                return False

        # Vérifier le score minimum
        score = content_data.get('score', 0)
        if score < self.safety_config.min_score_threshold:
            analysis['reasons'].append(f"Score trop bas: {score}")
            return False

        # Vérifier si l'auteur existe
        author = content_data.get('author', '')
        if author in ['[deleted]', '', None]:
            analysis['reasons'].append("Auteur supprimé ou inexistant")
            return False

        return True

    def _check_post_age(self, post_data: Dict[str, Any], analysis: Dict[str, Any]) -> bool:
        """Vérifie l'âge du post"""
        try:
            conditions = self.triggers.get('conditions', {})
            max_age_hours = conditions.get('max_post_age_hours', 24)
            min_age_minutes = conditions.get('min_post_age_minutes', 5)

            post_time = datetime.fromtimestamp(post_data['created_utc'])
            current_time = datetime.now()
            age = current_time - post_time

            age_hours = age.total_seconds() / 3600
            age_minutes = age.total_seconds() / 60

            if age_hours > max_age_hours:
                analysis['reasons'].append(f"Post trop ancien: {age_hours:.1f}h")
                return False

            if age_minutes < min_age_minutes:
                analysis['reasons'].append(f"Post trop récent: {age_minutes:.1f}min")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification de l'âge: {e}")
            return True  # En cas d'erreur, on continue

    def _check_post_score(self, post_data: Dict[str, Any], analysis: Dict[str, Any]) -> bool:
        """Vérifie le score du post"""
        score = post_data.get('score', 0)
        if score < self.safety_config.min_score_threshold:
            analysis['reasons'].append(f"Score insuffisant: {score}")
            return False
        return True

    def _check_content_length(self, post_data: Dict[str, Any], analysis: Dict[str, Any]) -> bool:
        """Vérifie la longueur du contenu"""
        content = post_data.get('selftext', '') + post_data.get('title', '')
        content_length = len(content.strip())

        if content_length < self.safety_config.min_post_length:
            analysis['reasons'].append(f"Contenu trop court: {content_length} caractères")
            return False

        return True

    def _analyze_triggers(self, content_data: Dict[str, Any], analysis: Dict[str, Any], content_field: str = 'selftext') -> float:
        """Analyse les triggers dans le contenu"""
        score = 0.0

        # Récupérer le contenu à analyser
        content = content_data.get(content_field, '') + ' ' + content_data.get('title', '')
        content_lower = content.lower()

        # Vérifier les mots-clés
        keywords = self.triggers.get('keywords', [])
        keyword_matches = 0

        for keyword in keywords:
            if keyword.lower() in content_lower:
                keyword_matches += 1
                analysis['reasons'].append(f"Mot-clé trouvé: {keyword}")

        if keywords:
            keyword_score = min(keyword_matches / len(keywords), 1.0)
            score += keyword_score * 0.5

        # Vérifier les patterns regex
        pattern_matches = 0
        for pattern in self.compiled_patterns:
            if pattern.search(content):
                pattern_matches += 1
                analysis['reasons'].append(f"Pattern trouvé: {pattern.pattern}")

        if self.compiled_patterns:
            pattern_score = min(pattern_matches / len(self.compiled_patterns), 1.0)
            score += pattern_score * 0.5

        return score

    def _analyze_relevance(self, post_data: Dict[str, Any], analysis: Dict[str, Any]) -> float:
        """Analyse la pertinence du post"""
        score = 0.0

        # Vérifier si c'est un post texte (plus susceptible d'être une question)
        if post_data.get('is_self', False):
            score += 0.3
            analysis['reasons'].append("Post texte (self-post)")

        # Vérifier la présence de points d'interrogation
        content = post_data.get('selftext', '') + ' ' + post_data.get('title', '')
        question_marks = content.count('?')
        if question_marks > 0:
            score += min(question_marks * 0.2, 0.4)
            analysis['reasons'].append(f"Questions détectées: {question_marks}")

        # Vérifier le ratio upvote (engagement positif)
        upvote_ratio = post_data.get('upvote_ratio', 0.5)
        if upvote_ratio > 0.7:
            score += 0.2
            analysis['reasons'].append(f"Bon ratio upvote: {upvote_ratio:.2f}")

        # Vérifier le nombre de commentaires (engagement)
        num_comments = post_data.get('num_comments', 0)
        conditions = self.triggers.get('conditions', {})
        max_comments = conditions.get('max_existing_comments', 50)

        if 0 < num_comments < max_comments:
            comment_score = min(num_comments / 10, 0.3)
            score += comment_score
            analysis['reasons'].append(f"Engagement modéré: {num_comments} commentaires")
        elif num_comments >= max_comments:
            analysis['warnings'].append(f"Trop de commentaires: {num_comments}")
            score -= 0.2

        return min(score, 1.0)

    def _analyze_comment_relevance(self, comment_data: Dict[str, Any], post_data: Dict[str, Any], analysis: Dict[str, Any]) -> float:
        """Analyse la pertinence d'un commentaire"""
        score = 0.0

        # Vérifier si le commentaire semble être une question ou demande d'aide
        comment_body = comment_data.get('body', '').lower()

        help_indicators = ['help', 'how', 'what', 'why', 'where', 'when', 'can someone', 'please']
        help_count = sum(1 for indicator in help_indicators if indicator in comment_body)

        if help_count > 0:
            score += min(help_count * 0.2, 0.6)
            analysis['reasons'].append(f"Indicateurs d'aide détectés: {help_count}")

        # Vérifier la longueur du commentaire (plus long = plus substantiel)
        comment_length = len(comment_data.get('body', ''))
        if comment_length > 50:
            length_score = min(comment_length / 200, 0.3)
            score += length_score
            analysis['reasons'].append(f"Commentaire substantiel: {comment_length} caractères")

        # Vérifier le score du commentaire
        comment_score = comment_data.get('score', 0)
        if comment_score > 0:
            score += min(comment_score / 10, 0.2)
            analysis['reasons'].append(f"Commentaire bien noté: {comment_score}")

        return min(score, 1.0)

    def extract_context(self, content_data: Dict[str, Any], is_comment: bool = False) -> Dict[str, Any]:
        """Extrait le contexte pertinent du contenu"""
        context = {
            'type': 'comment' if is_comment else 'post',
            'subreddit': content_data.get('subreddit', ''),
            'author': content_data.get('author', ''),
            'score': content_data.get('score', 0),
            'age_hours': 0
        }

        # Calculer l'âge
        try:
            created_time = datetime.fromtimestamp(content_data['created_utc'])
            age = datetime.now() - created_time
            context['age_hours'] = age.total_seconds() / 3600
        except:
            pass

        # Extraire le contenu principal
        if is_comment:
            context['content'] = content_data.get('body', '')[:500]
        else:
            context['title'] = content_data.get('title', '')
            context['content'] = content_data.get('selftext', '')[:500]
            context['num_comments'] = content_data.get('num_comments', 0)

        return context

    def is_safe_content(self, content: str) -> bool:
        """Vérifie si le contenu généré est sûr"""
        if not content or len(content.strip()) == 0:
            return False

        content_lower = content.lower()

        # Vérifier les mots-clés interdits
        for banned_word in self.safety_config.banned_keywords:
            if banned_word.lower() in content_lower:
                self.logger.warning(f"Contenu généré contient un mot interdit: {banned_word}")
                return False

        # Vérifier la longueur
        if len(content) > self.safety_config.max_response_length:
            self.logger.warning(f"Contenu généré trop long: {len(content)} caractères")
            return False

        return True


if __name__ == "__main__":
    # Test de l'analyseur de contenu
    from config_manager import ConfigManager, setup_logging

    config_manager = ConfigManager()
    if config_manager.load_config():
        setup_logging(config_manager)

        analyzer = ContentAnalyzer(config_manager.safety_config, config_manager.get_triggers())

        # Test avec un post exemple
        test_post = {
            'id': 'test123',
            'title': 'I need help with Python',
            'selftext': 'Can someone help me understand how to use loops in Python?',
            'author': 'testuser',
            'score': 5,
            'created_utc': datetime.now().timestamp() - 3600,  # 1 heure ago
            'is_self': True,
            'num_comments': 3,
            'upvote_ratio': 0.8,
            'subreddit': 'learnpython'
        }

        analysis = analyzer.should_respond_to_post(test_post)
        print(f"Analyse du post test:")
        print(f"Doit répondre: {analysis['should_respond']}")
        print(f"Confiance: {analysis['confidence']:.2f}")
        print(f"Raisons: {analysis['reasons']}")
        if analysis['warnings']:
            print(f"Avertissements: {analysis['warnings']}")
    else:
        print("Erreur de configuration")


    def calculate_response_confidence(self, response_content: str, post_data: Dict[str, Any]) -> float:
        """Calcule un score de confiance pour une réponse générée"""
        try:
            confidence = 0.0

            # Vérifier la longueur de la réponse (ni trop courte, ni trop longue)
            response_length = len(response_content.strip())
            if 50 <= response_length <= 500:
                confidence += 0.3
            elif 20 <= response_length < 50:
                confidence += 0.1
            elif response_length > 500:
                confidence += 0.1  # Pénalité pour les réponses trop longues

            # Vérifier la présence de mots-clés pertinents dans la réponse
            response_lower = response_content.lower()
            keywords = self.triggers.get('keywords', [])
            keyword_matches = sum(1 for keyword in keywords if keyword.lower() in response_lower)
            if keyword_matches > 0:
                confidence += min(keyword_matches * 0.1, 0.3)

            # Vérifier la structure de la réponse
            sentences = response_content.split('.')
            if len(sentences) >= 2:  # Au moins 2 phrases
                confidence += 0.2

            # Vérifier la présence de questions (engagement)
            if '?' in response_content:
                confidence += 0.1

            # Vérifier la pertinence au subreddit
            subreddit = post_data.get('subreddit', '').lower()
            subreddit_keywords = {
                'startups': ['startup', 'entrepreneur', 'business', 'funding'],
                'entrepreneur': ['business', 'entrepreneur', 'startup', 'growth'],
                'investing': ['investment', 'portfolio', 'returns', 'market'],
                'business': ['business', 'strategy', 'revenue', 'growth']
            }

            if subreddit in subreddit_keywords:
                relevant_words = subreddit_keywords[subreddit]
                relevance_matches = sum(1 for word in relevant_words if word in response_lower)
                if relevance_matches > 0:
                    confidence += min(relevance_matches * 0.05, 0.2)

            # Vérifier l'absence de contenu problématique
            problematic_phrases = ['i am an ai', 'as an ai', 'i cannot', 'i don\'t know']
            if any(phrase in response_lower for phrase in problematic_phrases):
                confidence -= 0.3

            # Normaliser le score entre 0 et 1
            confidence = max(0.0, min(1.0, confidence))

            return confidence

        except Exception as e:
            self.logger.error(f"Erreur lors du calcul de confiance: {e}")
            return 0.5  # Score neutre en cas d'erreur

