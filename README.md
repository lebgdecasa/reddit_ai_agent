# Agent IA Reddit

Un agent IA autonome pour Reddit qui surveille des subreddits spécifiques, analyse le contenu selon des instructions configurables, et génère des réponses automatiquement en utilisant LM Studio local.

## 🚀 Fonctionnalités

### Mode Conversationnel Actif
- **Surveillance automatique** de subreddits configurables
- **Génération et posting** de réponses réelles sur Reddit
- **Création de posts** originaux basés sur les tendances
- **Sauvegarde complète** de toutes les actions dans `data/active_mode/`
- **Suivi des performances** Reddit en temps réel

### Mode Passif (Simulation)
- **Scraping et analyse** sans poster sur Reddit
- **Génération de réponses simulées** pour prévisualisation
- **Base de données** complète des interactions simulées
- **Rapports détaillés** et analytics avancés

### Fonctionnalités Communes
- **Analyse intelligente** du contenu avec filtrage avancé
- **Système de sécurité** avec rate limiting et protection anti-spam
- **Mode dry run** pour tester sans poster
- **Logging détaillé** et statistiques d'utilisation
- **Configuration flexible** via fichiers YAML
- **Interface LM Studio** locale pour l'IA

## ⚠️ Avertissements Importants

**LISEZ ATTENTIVEMENT AVANT UTILISATION**

1. **Respect des règles Reddit** : Cet agent doit être utilisé en conformité avec les conditions d'utilisation de Reddit et les règles de chaque subreddit.

2. **Usage personnel uniquement** : L'utilisation commerciale sans autorisation de Reddit est interdite.

3. **Risque de bannissement** : Un usage inapproprié peut entraîner la suspension de votre compte Reddit.

4. **Mode test recommandé** : Utilisez toujours le mode dry run pour tester avant l'activation réelle.

5. **Surveillance requise** : L'agent nécessite une surveillance humaine régulière.

## 📋 Prérequis

### Logiciels requis

- Python 3.8 ou supérieur
- LM Studio installé et configuré
- Compte Reddit avec application OAuth2 configurée

### Dépendances Python

```bash
pip install -r requirements.txt
```

Les dépendances incluent :
- `praw` : Interface Python pour l'API Reddit
- `openai` : Client pour l'API OpenAI compatible (LM Studio)
- `pyyaml` : Parsing des fichiers de configuration
- `requests` : Requêtes HTTP

## 🛠️ Installation

### 1. Cloner ou télécharger le projet

```bash
git clone <repository-url>
cd reddit_ai_agent
```

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 3. Configurer Reddit OAuth2

1. Allez sur https://www.reddit.com/prefs/apps
2. Cliquez sur "Create App" ou "Create Another App"
3. Choisissez "script" comme type d'application
4. Notez le `client_id` et `client_secret`

### 4. Configurer LM Studio

1. Installez et lancez LM Studio
2. Chargez un modèle de votre choix
3. Démarrez le serveur local (généralement sur http://localhost:1234)
4. Notez l'URL et l'identifiant du modèle

### 5. Configuration

Copiez et modifiez le fichier de configuration :

```bash
cp config/config.yaml config/config.yaml.backup
# Éditez config/config.yaml avec vos paramètres
```

## ⚙️ Configuration

### Configuration Reddit

```yaml
reddit:
  client_id: "votre_client_id"
  client_secret: "votre_client_secret"
  username: "votre_username"
  password: "votre_password"
  user_agent: "RedditAIAgent/1.0 by u/votre_username"
```

### Configuration LM Studio

```yaml
lm_studio:
  base_url: "http://localhost:1234"
  model: "votre_model_identifier"
  temperature: 0.7
  max_tokens: 500
```

### Configuration des Subreddits

```yaml
subreddits:
  - name: "test"
    enabled: true
    post_enabled: false
    comment_enabled: true
    max_posts_per_day: 2
    max_comments_per_day: 10
```

## 🚦 Utilisation

### Test de configuration

Avant de lancer l'agent, testez votre configuration :

```bash
python test_config.py
```

### Mode Passif (Recommandé pour débuter)

Le mode passif permet de tester l'agent sans poster sur Reddit :

```bash
# Test rapide (5 minutes)
python run_passive_mode.py --duration 0.1

# Session d'analyse (1 heure)
python run_passive_mode.py --duration 1

# Visualiser les résultats
python view_data.py --overview
python generate_report.py --html
```

### Mode Conversationnel Actif

⚠️ **ATTENTION** : Ce mode poste réellement sur Reddit !

```bash
# Tests préalables
python test_active_mode.py

# Lancement pour 2 heures (comme demandé)
python run_active_mode.py --duration 2

# Visualiser les données actives
python view_active_data.py --overview
python view_active_data.py --recent 20 --responses 10
```

### Mode Dry Run (Sécurisé)

Pour tester le mode actif sans poster :

```bash
# S'assurer que dry_run est activé dans config/config.yaml
python run_active_mode.py --duration 0.5
```

### Arrêt de l'agent

Utilisez `Ctrl+C` pour arrêter l'agent proprement. Toutes les données seront sauvegardées automatiquement.

## 📊 Monitoring et Données

### Logs

Les logs sont sauvegardés dans `logs/reddit_agent.log` avec rotation automatique.

### Données du Mode Passif

Toutes les données de simulation sont dans `data/passive_mode/` :
- `passive_mode.db` : Base de données SQLite
- `scraped_posts/` : Posts analysés par subreddit
- `simulated_interactions/` : Réponses et posts simulés
- `reports/` : Rapports HTML et analyses

```bash
# Visualiser les données passives
python view_data.py --overview
python view_data.py --search "startup" --limit 10
python generate_report.py --html --output rapport.html
```

### Données du Mode Actif

Toutes les actions réelles sont sauvegardées dans `data/active_mode/` :
- `active_mode.db` : Base de données SQLite complète
- `scraped_posts/` : Posts scrapés avec analyses
- `posted_responses/` : Réponses réellement postées sur Reddit
- `created_posts/` : Posts créés par l'agent
- `actions_log/` : Log détaillé de toutes les actions
- `reports/` : Rapports de session

```bash
# Visualiser les données actives
python view_active_data.py --overview
python view_active_data.py --recent 50
python view_active_data.py --performance
python view_active_data.py --errors
```

### Statistiques en Temps Réel

```bash
# Stats mode passif
python run_passive_mode.py --stats

# Stats mode actif
python run_active_mode.py --stats

# Comparaison des performances
python view_active_data.py --performance
```

## 🔒 Sécurité

### Rate Limiting

L'agent respecte automatiquement :
- Maximum 2 posts par heure
- Maximum 10 commentaires par heure
- Délai minimum de 2 minutes entre actions
- Limites spécifiques par subreddit

### Filtres de sécurité

- Détection de mots-clés interdits
- Validation de la longueur du contenu
- Vérification du score des posts
- Analyse de l'âge du contenu

### Mode d'urgence

L'agent peut s'arrêter automatiquement en cas de :
- Erreurs répétées
- Dépassement des limites
- Détection de contenu inapproprié

## 🎯 Personnalisation

### Instructions par subreddit

```yaml
instructions:
  subreddit_specific:
    learnpython: |
      Tu aides les débutants en Python. Sois pédagogique et patient.
      Fournis des exemples de code quand c'est approprié.
```

### Triggers personnalisés

```yaml
triggers:
  keywords:
    - "help"
    - "question"
    - "how to"
  patterns:
    - "I need help.*"
    - "How do I.*"
```

## 🐛 Dépannage

### Problèmes courants

1. **Erreur d'authentification Reddit**
   - Vérifiez vos credentials
   - Assurez-vous que l'application Reddit est configurée comme "script"

2. **Connexion LM Studio échouée**
   - Vérifiez que LM Studio est démarré
   - Confirmez l'URL et le port
   - Vérifiez qu'un modèle est chargé

3. **Aucune réponse générée**
   - Vérifiez les triggers dans la configuration
   - Consultez les logs pour les détails
   - Testez LM Studio manuellement

### Logs de débogage

Activez le mode debug dans la configuration :

```yaml
mode:
  debug: true
```

## 📁 Structure du projet

```
reddit_ai_agent/
├── config/
│   ├── config.yaml              # Configuration principale
│   ├── config_conversationnel.yaml # Config mode conversationnel
│   └── config_test.yaml         # Config pour tests
├── src/
│   ├── config_manager.py        # Gestionnaire de configuration
│   ├── reddit_interface.py      # Interface Reddit/PRAW
│   ├── lm_studio_interface.py   # Interface LM Studio
│   ├── content_analyzer.py      # Analyseur de contenu
│   ├── safety_manager.py        # Gestionnaire de sécurité
│   ├── reddit_ai_agent.py       # Agent principal (mode actif)
│   ├── passive_mode.py          # Mode passif/simulation
│   ├── active_data_manager.py   # Gestionnaire données actives
│   ├── data_viewer.py           # Visualiseur données passives
│   └── report_generator.py      # Générateur de rapports
├── data/
│   ├── passive_mode/            # Données mode passif
│   │   ├── passive_mode.db      # Base de données SQLite
│   │   ├── scraped_posts/       # Posts analysés
│   │   ├── simulated_interactions/ # Interactions simulées
│   │   └── reports/             # Rapports générés
│   └── active_mode/             # Données mode actif
│       ├── active_mode.db       # Base de données SQLite
│       ├── scraped_posts/       # Posts scrapés
│       ├── posted_responses/    # Réponses postées
│       ├── created_posts/       # Posts créés
│       ├── actions_log/         # Log des actions
│       └── reports/             # Rapports de session
├── logs/                        # Fichiers de logs
├── tests/                       # Tests unitaires
├── run_agent.py                 # Script de lancement classique
├── run_active_mode.py          # Script mode actif avec durée
├── run_passive_mode.py         # Script mode passif
├── test_config.py              # Test de configuration
├── test_active_mode.py         # Tests mode actif
├── test_passive_mode.py        # Tests mode passif
├── view_data.py                # Visualiseur données passives
├── view_active_data.py         # Visualiseur données actives
├── generate_report.py          # Générateur de rapports
├── requirements.txt            # Dépendances Python
└── README.md                   # Cette documentation
```

## 🤝 Contribution

Ce projet est fourni comme exemple éducatif. Les améliorations et corrections sont les bienvenues.

## 📄 Licence

Ce projet est fourni à des fins éducatives. Respectez les conditions d'utilisation de Reddit et les lois applicables.

## ⚖️ Responsabilité

L'utilisateur est entièrement responsable de l'usage de cet agent. Les auteurs ne peuvent être tenus responsables des conséquences de son utilisation.

---

**Développé par Manus AI** - Agent IA Reddit v1.0

