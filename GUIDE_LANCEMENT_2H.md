# Guide de Lancement - Mode Conversationnel 2 Heures

Ce guide détaille comment lancer l'agent IA Reddit en mode conversationnel actif pour une durée de 2 heures, avec sauvegarde complète de toutes les actions.

## 🎯 Objectif

Lancer l'agent en mode actif qui va :
- Surveiller les subreddits business/entrepreneuriat configurés
- Analyser et scraper tous les posts
- Générer et poster des réponses réelles sur Reddit
- Sauvegarder toutes les données dans `data/active_mode/`
- Fonctionner de manière autonome pendant 2 heures

## ⚠️ Prérequis Critiques

### 1. Configuration Validée

Assurez-vous que votre configuration est correcte :

```bash
python test_config.py
```

Vérifiez spécifiquement :
- ✅ Credentials Reddit valides
- ✅ LM Studio connecté et modèle chargé
- ✅ Subreddits business activés
- ✅ Triggers configurés

### 2. Tests Préalables

**OBLIGATOIRE** : Testez d'abord le mode actif :

```bash
python test_active_mode.py
```

Tous les tests doivent passer avant de continuer.

### 3. Mode Dry Run (Recommandé)

Pour votre première utilisation, activez le mode dry run dans `config/config.yaml` :

```yaml
mode:
  dry_run: true  # Aucune action réelle sur Reddit
```

## 🚀 Lancement du Mode Conversationnel 2 Heures

### Étape 1 : Préparation

```bash
# Aller dans le dossier du projet
cd reddit_ai_agent

# Vérifier que tous les scripts sont exécutables
chmod +x run_active_mode.py test_active_mode.py view_active_data.py

# Nettoyer les données précédentes (optionnel)
rm -rf data/active_mode/*
```

### Étape 2 : Configuration des Subreddits

Assurez-vous que les subreddits business sont activés dans votre configuration :

```yaml
subreddits:
  - name: "startups"
    enabled: true
    post_enabled: true
    comment_enabled: true
    max_posts_per_day: 3
    max_comments_per_day: 15

  - name: "entrepreneur"
    enabled: true
    post_enabled: true
    comment_enabled: true
    max_posts_per_day: 3
    max_comments_per_day: 15

  - name: "investing"
    enabled: true
    post_enabled: false  # Commentaires seulement
    comment_enabled: true
    max_posts_per_day: 0
    max_comments_per_day: 10

  # ... autres subreddits business
```

### Étape 3 : Lancement

```bash
# Lancement pour exactement 2 heures
python run_active_mode.py --duration 2
```

Le script va :
1. Vérifier la configuration
2. Demander confirmation si le mode dry run est désactivé
3. Afficher les subreddits surveillés
4. Démarrer la surveillance avec cycles de 5 minutes
5. Sauvegarder toutes les actions en temps réel

### Étape 4 : Monitoring en Temps Réel

Pendant l'exécution, ouvrez un autre terminal pour surveiller :

```bash
# Voir l'activité en temps réel
tail -f logs/reddit_agent.log

# Statistiques actuelles
python view_active_data.py --overview

# Actions récentes
python view_active_data.py --recent 10
```

## 📊 Ce qui se Passe Pendant les 2 Heures

### Cycle de Surveillance (toutes les 5 minutes)

1. **Scraping** : L'agent récupère les nouveaux posts de chaque subreddit
2. **Analyse** : Chaque post est analysé selon les triggers configurés
3. **Sauvegarde** : Tous les posts sont sauvegardés dans la base de données
4. **Génération** : L'agent génère des réponses pour les posts pertinents
5. **Posting** : Les réponses sont postées sur Reddit (si dry_run = false)
6. **Logging** : Toutes les actions sont enregistrées

### Données Sauvegardées

Pendant l'exécution, toutes les données sont sauvegardées dans `data/active_mode/` :

- **Base de données SQLite** : `active_mode.db`
- **Posts scrapés** : `scraped_posts/startups_abc123_20250815_143022.json`
- **Réponses postées** : `posted_responses/response_startups_def456_20250815_143045.json`
- **Log des actions** : `actions_log/action_respond_20250815_143045.json`

## 📈 Résultats Attendus

Après 2 heures, vous devriez avoir :

### Statistiques Typiques
- **Posts scrapés** : 200-500 selon l'activité des subreddits
- **Réponses générées** : 20-50 selon les triggers
- **Réponses postées** : 10-30 (si dry_run = false)
- **Actions loggées** : 300-600 au total

### Données Collectées
- Analyse complète de l'activité des subreddits business
- Base de données des interactions de l'agent
- Métriques de performance des réponses
- Historique détaillé de toutes les actions

## 🔍 Analyse Post-Exécution

Une fois les 2 heures terminées :

### 1. Statistiques Finales

```bash
# Aperçu général
python view_active_data.py --overview

# Activité détaillée
python view_active_data.py --recent 50 --responses 20

# Analyse des performances
python view_active_data.py --performance

# Analyse des erreurs
python view_active_data.py --errors
```

### 2. Rapports Détaillés

```bash
# Générer un rapport complet
python view_active_data.py > rapport_session_2h.txt

# Voir les statistiques de la base de données
python run_active_mode.py --stats
```

### 3. Données Brutes

Consultez directement les fichiers dans `data/active_mode/` :
- Ouvrez `active_mode.db` avec un client SQLite
- Parcourez les JSON dans les sous-dossiers
- Analysez les logs dans `actions_log/`

## ⚠️ Gestion des Problèmes

### Arrêt d'Urgence

Si vous devez arrêter l'agent :

```bash
# Ctrl+C dans le terminal de l'agent
# L'agent se fermera proprement et sauvegarde les données
```

### Erreurs Communes

1. **Erreur d'authentification Reddit**
   - Vérifiez vos credentials dans `config/config.yaml`
   - Testez avec `python test_config.py`

2. **LM Studio déconnecté**
   - Vérifiez que LM Studio est démarré
   - Confirmez l'URL dans la configuration

3. **Rate limiting Reddit**
   - L'agent respecte automatiquement les limites
   - Les actions sont mises en attente, pas perdues

### Récupération de Session

Si l'agent s'arrête prématurément :

```bash
# Les données sont automatiquement sauvegardées
# Consultez ce qui a été collecté
python view_active_data.py --overview

# Relancez pour le temps restant
python run_active_mode.py --duration 1.5  # Si 30 min se sont écoulées
```

## 🎯 Optimisation pour les Subreddits Business

### Configuration Recommandée

Pour maximiser l'engagement sur les subreddits business :

```yaml
triggers:
  keywords:
    # Business général
    - "startup"
    - "entrepreneur" 
    - "business"
    - "funding"
    - "investment"
    - "valuation"
    - "growth"
    - "revenue"
    - "pitch"
    - "investor"
    
    # Questions et discussions
    - "advice"
    - "experience"
    - "opinion"
    - "thoughts"
    - "feedback"
    - "help"
    - "question"
    
    # Patterns conversationnels
    - "what do you think"
    - "any advice"
    - "has anyone"
    - "looking for"
    - "need help"

  patterns:
    - ".*startup.*"
    - ".*entrepreneur.*"
    - ".*funding.*"
    - ".*investment.*"
    - "What.*think.*"
    - "How.*experience.*"
    - "Any.*advice.*"
```

### Instructions Spécialisées

```yaml
instructions:
  global: |
    Tu es un entrepreneur expérimenté et investisseur qui partage des insights pratiques.
    
    Ton style :
    - Conversationnel et authentique
    - Basé sur l'expérience réelle
    - Constructif et encourageant
    - Pose des questions pertinentes
    
    Évite :
    - Les réponses génériques
    - Les conseils trop théoriques  
    - Les promotions ou spam
    - Les réponses trop longues (max 3 paragraphes)
```

## 📋 Checklist de Lancement

Avant de lancer les 2 heures :

- [ ] Configuration testée avec `python test_config.py`
- [ ] Tests du mode actif passés avec `python test_active_mode.py`
- [ ] Subreddits business activés dans la config
- [ ] Mode dry_run configuré selon vos besoins
- [ ] LM Studio démarré avec un modèle chargé
- [ ] Espace disque suffisant pour les données
- [ ] Terminal de monitoring préparé
- [ ] Temps disponible pour surveiller la session

## 🎉 Commande Finale

Une fois tout vérifié :

```bash
python run_active_mode.py --duration 2
```

**L'agent va maintenant fonctionner de manière autonome pendant 2 heures, en sauvegardant toutes ses actions dans `data/active_mode/` !**

---

**Développé par Manus AI** - Guide de Lancement Mode Conversationnel 2H

