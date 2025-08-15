# Guide d'Installation Détaillé - Agent IA Reddit

Ce guide vous accompagne étape par étape dans l'installation et la configuration de l'Agent IA Reddit.

## Table des matières

1. [Prérequis système](#prérequis-système)
2. [Installation de Python et dépendances](#installation-de-python-et-dépendances)
3. [Configuration du compte Reddit](#configuration-du-compte-reddit)
4. [Installation et configuration de LM Studio](#installation-et-configuration-de-lm-studio)
5. [Installation de l'agent](#installation-de-lagent)
6. [Configuration initiale](#configuration-initiale)
7. [Tests et validation](#tests-et-validation)
8. [Premier lancement](#premier-lancement)
9. [Dépannage](#dépannage)

## Prérequis système

### Système d'exploitation
- Windows 10/11, macOS 10.15+, ou Linux (Ubuntu 18.04+)
- 8 GB de RAM minimum (16 GB recommandé pour LM Studio)
- 10 GB d'espace disque libre

### Logiciels requis
- Python 3.8 ou supérieur
- Git (optionnel, pour cloner le repository)
- Éditeur de texte (VS Code, Sublime Text, etc.)

## Installation de Python et dépendances

### Windows

1. **Télécharger Python**
   - Allez sur https://python.org/downloads/
   - Téléchargez Python 3.8 ou supérieur
   - **Important** : Cochez "Add Python to PATH" lors de l'installation

2. **Vérifier l'installation**
   ```cmd
   python --version
   pip --version
   ```

3. **Installer pip si nécessaire**
   ```cmd
   python -m ensurepip --upgrade
   ```

### macOS

1. **Installer Homebrew** (si pas déjà installé)
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Installer Python**
   ```bash
   brew install python
   ```

3. **Vérifier l'installation**
   ```bash
   python3 --version
   pip3 --version
   ```

### Linux (Ubuntu/Debian)

1. **Mettre à jour le système**
   ```bash
   sudo apt update
   sudo apt upgrade
   ```

2. **Installer Python et pip**
   ```bash
   sudo apt install python3 python3-pip python3-venv
   ```

3. **Vérifier l'installation**
   ```bash
   python3 --version
   pip3 --version
   ```

## Configuration du compte Reddit

### Étape 1 : Créer une application Reddit

1. **Connectez-vous à Reddit**
   - Allez sur https://www.reddit.com
   - Connectez-vous avec votre compte

2. **Accéder aux préférences d'applications**
   - Allez sur https://www.reddit.com/prefs/apps
   - Ou : Profil → Paramètres utilisateur → Sécurité et confidentialité → Applications autorisées

3. **Créer une nouvelle application**
   - Cliquez sur "Create App" ou "Create Another App"
   - Remplissez le formulaire :
     ```
     Nom : Reddit AI Agent
     Type d'application : script
     Description : Agent IA personnel pour Reddit
     URL de redirection : http://localhost:8080
     ```

4. **Récupérer les identifiants**
   - **Client ID** : Chaîne sous le nom de l'app (ex: `dQw4w9WgXcQ`)
   - **Client Secret** : Chaîne "secret" (ex: `dQw4w9WgXcQ-dQw4w9WgXcQ`)

### Étape 2 : Préparer les informations de connexion

Notez les informations suivantes :
- Client ID
- Client Secret  
- Nom d'utilisateur Reddit
- Mot de passe Reddit

**⚠️ Sécurité** : Ne partagez jamais ces informations. Elles donnent accès à votre compte Reddit.

## Installation et configuration de LM Studio

### Étape 1 : Télécharger LM Studio

1. **Télécharger**
   - Allez sur https://lmstudio.ai
   - Téléchargez la version pour votre système d'exploitation
   - Installez en suivant les instructions

### Étape 2 : Premier lancement

1. **Lancer LM Studio**
   - Ouvrez l'application
   - Acceptez les conditions d'utilisation

2. **Télécharger un modèle**
   - Cliquez sur l'onglet "Discover"
   - Recherchez un modèle (recommandations) :
     - **Pour débuter** : `microsoft/DialoGPT-medium`
     - **Qualité/Performance** : `mistralai/Mistral-7B-Instruct-v0.1`
     - **Français** : `croissantllm/CroissantLLMChat-v0.1`
   - Cliquez sur "Download"

### Étape 3 : Configuration du serveur

1. **Charger le modèle**
   - Allez dans l'onglet "Chat"
   - Sélectionnez votre modèle téléchargé
   - Cliquez sur "Load model"

2. **Démarrer le serveur local**
   - Allez dans l'onglet "Local Server"
   - Cliquez sur "Start Server"
   - Notez l'URL (généralement `http://localhost:1234`)

3. **Tester le serveur**
   - Ouvrez un navigateur
   - Allez sur `http://localhost:1234/v1/models`
   - Vous devriez voir une réponse JSON avec votre modèle

### Étape 4 : Identifier le modèle

1. **Récupérer l'ID du modèle**
   - Dans la réponse JSON, notez le champ `"id"`
   - Exemple : `"microsoft/DialoGPT-medium"`

## Installation de l'agent

### Méthode 1 : Téléchargement direct

1. **Télécharger les fichiers**
   - Téléchargez tous les fichiers du projet
   - Extraire dans un dossier (ex: `C:\reddit_ai_agent` ou `~/reddit_ai_agent`)

### Méthode 2 : Git (recommandé)

1. **Cloner le repository**
   ```bash
   git clone <repository-url>
   cd reddit_ai_agent
   ```

### Installation des dépendances

1. **Créer un environnement virtuel** (recommandé)
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration initiale

### Étape 1 : Copier le fichier de configuration

```bash
# Créer une sauvegarde
cp config/config.yaml config/config.yaml.example

# Le fichier config.yaml sera votre configuration personnelle
```

### Étape 2 : Éditer la configuration

Ouvrez `config/config.yaml` dans un éditeur de texte et modifiez :

#### Configuration Reddit
```yaml
reddit:
  client_id: "VOTRE_CLIENT_ID_ICI"
  client_secret: "VOTRE_CLIENT_SECRET_ICI"
  username: "VOTRE_USERNAME_ICI"
  password: "VOTRE_PASSWORD_ICI"
  user_agent: "RedditAIAgent/1.0 by u/VOTRE_USERNAME_ICI"
```

#### Configuration LM Studio
```yaml
lm_studio:
  base_url: "http://localhost:1234"
  model: "VOTRE_MODEL_ID_ICI"
  api_key: "lm-studio"
  temperature: 0.7
  max_tokens: 500
```

#### Configuration des subreddits (pour débuter)
```yaml
subreddits:
  - name: "test"
    enabled: true
    post_enabled: false  # Désactivé pour la sécurité
    comment_enabled: true
    max_posts_per_day: 1
    max_comments_per_day: 5
```

### Étape 3 : Configuration des instructions

Personnalisez les instructions pour votre agent :

```yaml
instructions:
  global: |
    Tu es un assistant IA utile qui aide les utilisateurs Reddit.
    Réponds de manière concise, utile et respectueuse.
    Évite le spam et respecte les règles de chaque communauté.
  
  subreddit_specific:
    test: |
      Tu es dans un subreddit de test. Réponds brièvement et poliment.
      Indique que tu es un bot en test.
```

## Tests et validation

### Étape 1 : Test de configuration

```bash
python test_config.py
```

**Résultats attendus :**
- ✅ Configuration chargée avec succès
- ✅ Configuration Reddit OK
- ✅ Configuration LM Studio OK
- ✅ Connexion Reddit réussie
- ✅ Connexion LM Studio réussie

### Étape 2 : Résolution des problèmes

#### Erreur de configuration Reddit
```
❌ ÉCHEC: Configuration Reddit invalide
```
**Solution :** Vérifiez vos credentials dans `config/config.yaml`

#### Erreur de connexion LM Studio
```
❌ ÉCHEC: Impossible de se connecter à LM Studio
```
**Solutions :**
1. Vérifiez que LM Studio est ouvert
2. Vérifiez qu'un modèle est chargé
3. Vérifiez que le serveur local est démarré
4. Vérifiez l'URL dans la configuration

#### Erreur d'authentification Reddit
```
❌ ÉCHEC: Impossible de se connecter à Reddit
```
**Solutions :**
1. Vérifiez votre nom d'utilisateur et mot de passe
2. Vérifiez que l'application Reddit est de type "script"
3. Vérifiez le client ID et secret

## Premier lancement

### Étape 1 : Lancement en mode dry run

Le mode dry run est activé par défaut. L'agent analysera le contenu mais ne postera rien.

```bash
python run_agent.py
```

**Logs attendus :**
```
=== Agent IA Reddit ===
Initialisation...
=== Initialisation de l'Agent IA Reddit ===
MODE DRY RUN ACTIVÉ - Aucune action réelle ne sera effectuée
Authentifié avec succès en tant que: votre_username
Connexion LM Studio établie: http://localhost:1234
Initialisation terminée avec succès
=== Démarrage de l'Agent IA Reddit ===
Surveillance des subreddits: ['test']
```

### Étape 2 : Surveillance des logs

Ouvrez un autre terminal pour suivre les logs :

```bash
# Windows
type logs\reddit_agent.log

# macOS/Linux
tail -f logs/reddit_agent.log
```

### Étape 3 : Arrêt de l'agent

Utilisez `Ctrl+C` pour arrêter l'agent proprement.

### Étape 4 : Activation du mode production (optionnel)

**⚠️ Attention** : Ne faites ceci qu'après avoir testé en mode dry run !

1. **Modifier la configuration**
   ```yaml
   mode:
     dry_run: false
   ```

2. **Relancer l'agent**
   ```bash
   python run_agent.py
   ```

## Dépannage

### Problèmes Python

#### "python n'est pas reconnu"
**Windows :** Ajoutez Python au PATH ou utilisez `py` au lieu de `python`

#### "Module not found"
```bash
pip install -r requirements.txt
```

### Problèmes Reddit

#### "Invalid credentials"
- Vérifiez username/password
- Vérifiez que l'app Reddit est de type "script"

#### "Forbidden"
- Votre compte Reddit est peut-être trop récent
- Vérifiez les permissions de l'application

### Problèmes LM Studio

#### "Connection refused"
- LM Studio n'est pas démarré
- Vérifiez l'URL et le port

#### "Model not found"
- Vérifiez que le modèle est chargé dans LM Studio
- Vérifiez l'ID du modèle dans la configuration

### Problèmes de performance

#### L'agent est lent
- Réduisez `max_tokens` dans la configuration LM Studio
- Utilisez un modèle plus petit
- Augmentez les délais entre actions

#### Trop de logs
- Changez le niveau de log à "WARNING" dans la configuration

### Support

Si vous rencontrez des problèmes non couverts ici :

1. Vérifiez les logs dans `logs/reddit_agent.log`
2. Activez le mode debug dans la configuration
3. Testez chaque composant individuellement avec `test_config.py`

---

**Félicitations !** Votre Agent IA Reddit est maintenant installé et configuré. Commencez toujours par le mode dry run pour vous familiariser avec le système.

