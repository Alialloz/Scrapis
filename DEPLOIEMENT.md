# 🚀 GUIDE DE DÉPLOIEMENT - SCRAPER CENTRIS

## 📋 Pré-requis

- ✅ Python 3.8 ou supérieur installé
- ✅ Toutes les dépendances installées (`pip install -r requirements.txt`)
- ✅ ChromeDriver compatible avec votre version de Chrome
- ✅ URL de votre API prête

---

## 🔧 ÉTAPE 1 : Configuration de l'API

### 1.1 Éditer `config_api.py`

Ouvrez le fichier `config_api.py` et configurez :

```python
# URL de votre API
API_ENDPOINT = "https://votre-api.com/api/properties"  # ← MODIFIER ICI

# Headers (si authentification requise)
API_HEADERS = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer VOTRE_TOKEN_ICI',  # ← Décommenter et configurer
}
```

### 1.2 Tester la connexion à l'API

```bash
python test_api.py
```

Ce script va :
- Vérifier que l'API est accessible
- Envoyer un JSON de test
- Afficher la réponse

---

## 🧪 ÉTAPE 2 : Test avec une annonce

Avant de lancer le monitoring continu, testez avec une seule annonce :

```bash
python scraper_with_list_info.py
```

Vérifiez que :
- ✅ Le scraping fonctionne
- ✅ Les 9 photos sont extraites
- ✅ La source est correcte (pas "s.")
- ✅ Le JSON est complet

---

## ▶️ ÉTAPE 3 : Lancement du Monitoring Continu

### Windows

Double-cliquez sur `start_monitoring.bat` ou :

```cmd
python scraper_production.py
```

### Linux/Mac

```bash
chmod +x start_monitoring.sh
./start_monitoring.sh
```

ou :

```bash
python3 scraper_production.py
```

---

## 🔄 Fonctionnement du Monitoring

### Cycle Automatique

Le système va :
1. **Toutes les heures** : Scanner la page Matrix
2. **Détecter** les nouvelles annonces (via numéro Centris)
3. **Scraper** chaque nouvelle annonce (60 sec/annonce)
4. **Sauvegarder** localement dans `property_XXXXXXXX.json`
5. **Envoyer** le JSON complet à votre API
6. **Enregistrer** l'ID dans `scraped_properties.json`
7. **Attendre** 1 heure avant le prochain cycle

### Logs

Le système affiche en temps réel :
- Nombre d'annonces trouvées
- Nouvelles annonces détectées
- Progression du scraping
- Statut de l'envoi à l'API
- Résumé du cycle

---

## 📊 Fichiers Générés

| Fichier | Description |
|---------|-------------|
| `scraped_properties.json` | Liste des IDs déjà scrapés avec dates |
| `property_XXXXXXXX.json` | Données complètes de chaque propriété |
| `monitoring_stats.json` | Statistiques des 100 derniers cycles |

---

## ⚙️ Configuration Avancée

### Modifier l'intervalle de monitoring

Dans `config_api.py` :

```python
MONITORING_INTERVAL = 30  # Minutes (30 = toutes les 30 minutes)
```

### Désactiver la sauvegarde locale

```python
SAVE_JSON_LOCALLY = False  # Ne pas sauvegarder les JSON localement
```

### Limiter le nombre d'annonces par cycle

```python
MAX_LISTINGS_PER_CYCLE = 5  # Scraper max 5 annonces par cycle
```

---

## 🖥️ DÉPLOIEMENT EN PRODUCTION

### Option 1 : Service Windows

1. Créer une tâche planifiée Windows :
   - Ouvrir "Planificateur de tâches"
   - Créer une tâche de base
   - Action : `python.exe C:\chemin\vers\scraper_production.py`
   - Déclencheur : Au démarrage du système
   - Options : Redémarrer en cas d'échec

### Option 2 : Service Linux (systemd)

Créer `/etc/systemd/system/centris-scraper.service` :

```ini
[Unit]
Description=Centris Scraper Monitoring Service
After=network.target

[Service]
Type=simple
User=votre-utilisateur
WorkingDirectory=/chemin/vers/Scrapis
ExecStart=/usr/bin/python3 scraper_production.py
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
```

Activer et démarrer :
```bash
sudo systemctl enable centris-scraper
sudo systemctl start centris-scraper
sudo systemctl status centris-scraper
```

### Option 3 : Cron (Linux/Mac)

Pour un monitoring toutes les heures :

```bash
crontab -e
```

Ajouter :
```cron
0 * * * * cd /chemin/vers/Scrapis && python3 scraper_production.py --single-cycle
```

### Option 4 : Docker

Créer `Dockerfile` :

```dockerfile
FROM python:3.9-slim

# Installer Chrome
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    chromium \
    chromium-driver

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "scraper_production.py"]
```

Build et run :
```bash
docker build -t centris-scraper .
docker run -d --restart always centris-scraper
```

---

## 🔍 Monitoring et Maintenance

### Vérifier que le service tourne

```bash
# Linux
ps aux | grep scraper_production

# Windows
tasklist | findstr python
```

### Consulter les logs en temps réel

Le script affiche tout dans la console. Pour rediriger vers un fichier :

```bash
python scraper_production.py > logs/scraper.log 2>&1
```

### Consulter les statistiques

```bash
cat monitoring_stats.json
```

### Réinitialiser le système

Pour tout rescraper depuis le début :

```bash
rm scraped_properties.json
```

---

## 🐛 Dépannage

### Problème : Le monitoring ne démarre pas

**Vérifications :**
- Python installé ? `python --version`
- Dépendances installées ? `pip install -r requirements.txt`
- ChromeDriver installé ? Le script l'installe automatiquement

### Problème : L'API ne reçoit pas les données

**Vérifications :**
1. L'API_ENDPOINT est-il correct dans `config_api.py` ?
2. L'API est-elle accessible ? `curl https://votre-api.com/api/properties`
3. Les logs montrent-ils des erreurs ?
4. Testez avec `test_api.py`

### Problème : Erreur "No such element"

**Solution :**
- La page Matrix a peut-être changé de structure
- Augmentez les délais d'attente dans le code
- Vérifiez que la page se charge correctement

### Problème : ChromeDriver incompatible

**Solution :**
```bash
pip install --upgrade selenium webdriver-manager
```

### Problème : Mémoire insuffisante

**Solution :**
- Limiter le nombre d'annonces par cycle dans `config_api.py`
- Fermer Chrome entre chaque scraping (déjà fait)

---

## 📞 Support

### Logs importants à fournir :

1. Sortie console complète
2. Contenu de `scraped_properties.json`
3. Un fichier `property_XXXXXXXX.json` exemple
4. Version de Python : `python --version`
5. Version de Chrome

---

## 🎯 Checklist de Déploiement

Avant de mettre en production :

- [ ] API configurée dans `config_api.py`
- [ ] Test réussi avec `scraper_with_list_info.py`
- [ ] Test API réussi avec `test_api.py`
- [ ] Intervalle de monitoring configuré (60 minutes)
- [ ] Service/tâche planifiée configuré
- [ ] Logs redirigés vers un fichier
- [ ] Mécanisme de redémarrage automatique en place
- [ ] Monitoring des erreurs en place
- [ ] Espace disque suffisant pour les JSON

---

## 📈 Estimation des Ressources

### Espace Disque

- ~10 KB par annonce (JSON)
- Si 100 nouvelles annonces/mois = 1 MB/mois
- Photos non téléchargées (seulement URLs)

### Mémoire

- ~200-300 MB pendant le scraping
- ~50 MB au repos

### CPU

- Pics à 50% pendant le scraping
- ~0% au repos

### Bande Passante

- ~1 MB par annonce scrapée
- ~60 MB pour scraper 60 annonces

---

## ✅ Le Système Est Prêt !

Une fois configuré, le système tournera **automatiquement 24/7** et :
- ✅ Détectera les nouvelles annonces toutes les heures
- ✅ Scrapera automatiquement toutes les données
- ✅ Enverra le JSON complet à votre API
- ✅ Ne re-scrapera jamais une annonce déjà traitée

**Le déploiement est simple et robuste ! 🚀**

