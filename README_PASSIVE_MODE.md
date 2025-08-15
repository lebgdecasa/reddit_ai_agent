# Mode Passive Conversational - Agent IA Reddit

## 🎯 Vue d'ensemble

Le **Mode Passive Conversational** est une fonctionnalité avancée qui permet de **prévisualiser et analyser** les interactions de votre agent IA Reddit **sans poster réellement** sur la plateforme. C'est l'outil parfait pour :

- **Tester** vos configurations avant le déploiement
- **Analyser** la qualité des réponses générées
- **Optimiser** vos instructions et triggers
- **Créer une base de données** d'interactions simulées

## 🚀 Fonctionnalités

### **Scraping Intelligent**
- ✅ Récupère automatiquement les posts des subreddits configurés
- ✅ Sauvegarde tout en base de données SQLite
- ✅ Analyse chaque post selon vos critères
- ✅ Exporte en JSON pour analyse externe

### **Simulation d'Interactions**
- ✅ Génère des réponses/commentaires (sans les poster)
- ✅ Crée des posts originaux (sans les publier)
- ✅ Calcule des scores de confiance
- ✅ Estime l'engagement potentiel

### **Analytics Avancés**
- ✅ Rapports HTML détaillés avec graphiques
- ✅ Statistiques par subreddit
- ✅ Analyse de la qualité du contenu
- ✅ Corrélations et tendances

### **Visualisation des Données**
- ✅ Interface en ligne de commande intuitive
- ✅ Export CSV pour Excel/Google Sheets
- ✅ Recherche dans les posts scrapés
- ✅ Filtrage par subreddit

## 📁 Structure des Données

```
data/
├── passive_mode.db          # Base de données SQLite principale
├── scraped_posts/           # Posts scrapés par subreddit (JSON)
├── simulated_interactions/  # Réponses et posts simulés (JSON)
├── reports/                 # Rapports HTML et graphiques
└── session_stats.json      # Statistiques de session
```

## 🛠️ Installation

### **Dépendances supplémentaires**
```bash
pip install pandas matplotlib seaborn numpy
```

Ou utilisez le fichier requirements.txt mis à jour :
```bash
pip install -r requirements.txt
```

## 🚀 Utilisation

### **1. Lancement du Mode Passif**

#### **Test rapide (1 heure)**
```bash
python run_passive_mode.py --duration 1
```

#### **Session complète (24 heures)**
```bash
python run_passive_mode.py --duration 24
```

#### **Configuration personnalisée**
```bash
python run_passive_mode.py --config config/config_conversationnel.yaml --duration 6
```

### **2. Visualisation des Données**

#### **Aperçu général**
```bash
python view_data.py --overview
```

#### **Statistiques par subreddit**
```bash
python view_data.py --subreddits
```

#### **Recherche dans les posts**
```bash
python view_data.py --search "startup funding"
```

#### **Filtrage par subreddit**
```bash
python view_data.py --subreddit startups --top 10
```

#### **Export CSV**
```bash
python view_data.py --export posts --output posts_startups.csv --subreddit startups
```

### **3. Génération de Rapports**

#### **Rapport HTML complet**
```bash
python generate_report.py --html
```

#### **Résumé JSON**
```bash
python generate_report.py --json
```

### **4. Tests et Validation**

#### **Test complet**
```bash
python test_passive_mode.py
```

#### **Test rapide**
```bash
python test_passive_mode.py --quick
```

#### **Test de configuration**
```bash
python test_passive_mode.py --config
```

## 📊 Base de Données

### **Tables principales**

#### **scraped_posts**
- Posts récupérés avec métadonnées Reddit
- Scores d'analyse et de pertinence
- Décisions de réponse automatique

#### **simulated_responses**
- Réponses générées par l'IA
- Scores de confiance
- Raisons de déclenchement

#### **simulated_posts**
- Posts originaux créés par l'IA
- Types de contenu (discussion, question, insight)
- Estimation d'engagement

#### **session_metrics**
- Métriques de chaque session
- Performance et statistiques

### **Requêtes utiles**

#### **Posts les mieux notés**
```sql
SELECT title, score, analysis_score 
FROM scraped_posts 
ORDER BY score DESC 
LIMIT 10;
```

#### **Meilleures réponses par confiance**
```sql
SELECT subreddit, generated_content, confidence_score 
FROM simulated_responses 
ORDER BY confidence_score DESC 
LIMIT 10;
```

#### **Statistiques par subreddit**
```sql
SELECT subreddit, COUNT(*) as posts, AVG(analysis_score) as avg_score
FROM scraped_posts 
GROUP BY subreddit;
```

## 📈 Rapports et Analytics

### **Rapport HTML**
Le rapport HTML complet inclut :

- **📊 Statistiques générales** : Posts, réponses, taux d'engagement
- **🎯 Analyse par subreddit** : Performance détaillée
- **📈 Graphiques** : Visualisations des tendances
- **⭐ Meilleures réponses** : Exemples de qualité
- **📝 Analyse du contenu** : Mots-clés et patterns

### **Métriques clés**

#### **Taux de réponse**
```
Taux = (Réponses générées / Posts méritant une réponse) × 100
```

#### **Score d'analyse moyen**
Mesure la pertinence des posts selon vos critères (0.0 à 1.0)

#### **Confiance moyenne**
Qualité estimée des réponses générées (0.0 à 1.0)

#### **Engagement estimé**
Prédiction de l'engagement potentiel sur Reddit

## ⚙️ Configuration

### **Mode passif dans config.yaml**
```yaml
mode:
  dry_run: true              # Toujours true en mode passif
  passive_mode: true         # Active le mode passif
  passive_cycle_delay: 300   # Délai entre cycles (secondes)

safety:
  passive_cycle_delay: 300   # 5 minutes entre cycles
  max_posts_per_cycle: 25    # Posts à scraper par cycle
```

### **Subreddits optimisés pour le mode passif**
```yaml
subreddits:
  - name: "startups"
    enabled: true
    post_enabled: true       # Génère des posts simulés
    comment_enabled: true    # Génère des réponses simulées
    max_posts_per_day: 5     # Limite pour simulation
    max_comments_per_day: 20
```

## 🔍 Cas d'Usage

### **1. Test de Configuration**
Avant d'activer votre agent en mode réel :
```bash
# 1. Configurer vos subreddits et instructions
# 2. Lancer le mode passif
python run_passive_mode.py --duration 2

# 3. Analyser les résultats
python view_data.py --overview
python generate_report.py --html

# 4. Ajuster la configuration si nécessaire
```

### **2. Optimisation des Triggers**
Pour améliorer la pertinence :
```bash
# 1. Analyser les posts qui déclenchent des réponses
python view_data.py --search "should_respond = 1"

# 2. Examiner les mots-clés les plus fréquents
python generate_report.py --html

# 3. Ajuster les triggers dans config.yaml
```

### **3. Analyse de Marché**
Pour comprendre les tendances :
```bash
# 1. Scraper pendant plusieurs jours
python run_passive_mode.py --duration 72

# 2. Analyser les sujets populaires
python view_data.py --search "funding" --subreddit startups

# 3. Identifier les opportunités de contenu
```

### **4. Formation et Amélioration**
Pour améliorer la qualité :
```bash
# 1. Examiner les réponses de faible confiance
python view_data.py --export responses --output low_confidence.csv

# 2. Analyser dans Excel/Google Sheets
# 3. Ajuster les instructions LM Studio
```

## 🎯 Optimisation

### **Performance**
- **Délai entre cycles** : Ajustez selon votre usage (300s par défaut)
- **Limite de posts** : 25 posts par cycle recommandé
- **Durée de session** : 1-24 heures selon vos besoins

### **Qualité**
- **Instructions spécifiques** : Personnalisez par subreddit
- **Triggers affinés** : Basés sur l'analyse des données
- **Température LM Studio** : 0.7-0.8 pour l'équilibre créativité/cohérence

### **Stockage**
- **Nettoyage régulier** : Supprimez les anciennes sessions
- **Export CSV** : Pour analyse externe
- **Sauvegarde DB** : Copiez passive_mode.db régulièrement

## 🚨 Limitations

### **Techniques**
- **Dépendant de LM Studio** : Doit être actif pendant la session
- **Pas de posting réel** : Mode simulation uniquement
- **Stockage local** : Base de données SQLite

### **Reddit API**
- **Rate limits** : Respecte les limites (60 req/min)
- **Authentification** : Nécessite des credentials valides
- **Subreddits privés** : Non accessibles

## 🔧 Dépannage

### **Erreurs courantes**

#### **"Base de données non trouvée"**
```bash
# Solution : Lancez d'abord le mode passif
python run_passive_mode.py --duration 1
```

#### **"Connexion LM Studio échouée"**
```bash
# Solution : Vérifiez que LM Studio est démarré
# et que l'URL est correcte dans config.yaml
```

#### **"Aucun post scrapé"**
```bash
# Solution : Vérifiez que des subreddits sont activés
python test_passive_mode.py --config
```

#### **"Erreur de graphiques"**
```bash
# Solution : Installez les dépendances manquantes
pip install matplotlib seaborn
```

### **Logs de débogage**
```bash
# Vérifiez les logs pour plus de détails
tail -f logs/reddit_agent.log
```

## 📚 Exemples d'Analyse

### **Analyse de Performance par Subreddit**
```bash
python view_data.py --subreddits
```
Résultat :
```
Subreddit         Posts    Réponses  Taux    Score Moy  Confiance
r/startups        45       12        26.7%   8.2        0.742
r/entrepreneur    38       15        39.5%   6.8        0.689
r/investing       52       8         15.4%   12.4       0.801
```

### **Recherche de Tendances**
```bash
python view_data.py --search "AI" --subreddit startups
```

### **Export pour Analyse Externe**
```bash
python view_data.py --export posts --output analysis.csv
# Ouvrir analysis.csv dans Excel pour analyse pivot
```

## 🎉 Avantages du Mode Passif

### **🔒 Sécurité**
- **Aucun risque** de bannissement Reddit
- **Test sans conséquences** de nouvelles configurations
- **Validation** avant déploiement réel

### **📊 Insights**
- **Compréhension** des communautés ciblées
- **Optimisation** des stratégies de contenu
- **Identification** des opportunités

### **⚡ Efficacité**
- **Itération rapide** sur les configurations
- **Données structurées** pour analyse
- **Rapports automatisés** pour suivi

---

**Le Mode Passive Conversational transforme votre agent IA Reddit en un outil d'analyse et de prévisualisation puissant !** 🚀

Commencez par un test rapide :
```bash
python test_passive_mode.py
python run_passive_mode.py --duration 1
python generate_report.py --html
```

