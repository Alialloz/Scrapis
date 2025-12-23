# 🚀 GUIDE DE DÉPLOIEMENT - Scraper Centris sur DigitalOcean

## 📋 Prérequis

Vous devez avoir :
- ✅ Un Droplet DigitalOcean créé (Ubuntu 22.04/24.04)
- ✅ L'adresse IP de votre Droplet
- ✅ Accès SSH (clé SSH ou mot de passe root)
- ✅ Votre code en local

---

## 🎯 DÉPLOIEMENT EN 5 ÉTAPES

### **ÉTAPE 1 : Connexion au serveur**

```bash
# Remplacez VOTRE_IP par l'IP de votre Droplet
ssh root@VOTRE_IP
```

**Si première connexion :**
```
Are you sure you want to continue connecting (yes/no)? 
# Tapez: yes
```

---

### **ÉTAPE 2 : Télécharger le script d'installation**

```bash
# Sur le serveur
cd /root
wget https://raw.githubusercontent.com/VOTRE-REPO/Scrapis/main/install_server.sh
chmod +x install_server.sh
```

**OU** si vous n'avez pas Git/GitHub, copiez le contenu du fichier `install_server.sh` :

```bash
# Sur le serveur
nano install_server.sh
# Collez le contenu du fichier install_server.sh
# Ctrl+O pour sauvegarder, Ctrl+X pour quitter
chmod +x install_server.sh
```

---

### **ÉTAPE 3 : Exécuter l'installation (10-15 minutes)**

```bash
sudo ./install_server.sh
```

**Ce script installe automatiquement :**
- ✅ Python 3.12
- ✅ Google Chrome
- ✅ ChromeDriver
- ✅ Toutes les dépendances système
- ✅ Service systemd
- ✅ Configuration des logs

☕ **Prenez un café, ça prend ~10 minutes...**

---

### **ÉTAPE 4 : Déployer votre code**

#### **Option A : Avec Git (recommandé)**

```bash
cd /opt/scraper-centris
git clone https://github.com/VOTRE-REPO/Scrapis.git .
```

#### **Option B : Upload manuel depuis votre PC**

```bash
# Sur VOTRE PC (pas le serveur)
cd /chemin/vers/Scrapis
scp -r *.py *.txt root@VOTRE_IP:/opt/scraper-centris/
```

**Vérifiez que les fichiers sont là :**
```bash
# Sur le serveur
ls -la /opt/scraper-centris/
# Vous devriez voir: scraper_production.py, config_api.py, etc.
```

---

### **ÉTAPE 5 : Installer les dépendances Python**

```bash
cd /opt/scraper-centris
pip3.12 install -r requirements.txt
```

**Si requirements.txt n'existe pas :**
```bash
pip3.12 install selenium beautifulsoup4 requests webdriver-manager pandas
```

---

## ⚙️ CONFIGURATION

### **Vérifier config_api.py**

```bash
nano /opt/scraper-centris/config_api.py
```

**Vérifiez que l'URL API est correcte :**
```python
API_ENDPOINT = "https://api.rayharvey.ca/robot/api/scraping"  # ✓ Bon
```

`Ctrl+X` pour quitter (pas besoin de modifier si déjà correct)

---

## 🚀 LANCEMENT DU SERVICE

### **Démarrer le scraper**

```bash
systemctl start scraper-centris
```

### **Activer le démarrage automatique**

```bash
systemctl enable scraper-centris
```

### **Vérifier que ça tourne**

```bash
systemctl status scraper-centris
```

**Résultat attendu :**
```
● scraper-centris.service - Scraper Centris - Monitoring automatique
   Active: active (running) since...
```

---

## 📊 SURVEILLANCE

### **Voir les logs en temps réel**

```bash
tail -f /var/log/scraper-centris.log
```

`Ctrl+C` pour quitter

### **Voir les erreurs**

```bash
tail -f /var/log/scraper-centris-error.log
```

### **Dernières 50 lignes**

```bash
tail -50 /var/log/scraper-centris.log
```

---

## 🔧 COMMANDES UTILES

### **Redémarrer le service**
```bash
systemctl restart scraper-centris
```

### **Arrêter le service**
```bash
systemctl stop scraper-centris
```

### **Voir le statut**
```bash
systemctl status scraper-centris
```

### **Désactiver le démarrage automatique**
```bash
systemctl disable scraper-centris
```

### **Voir les logs avec filtres**
```bash
# Seulement les erreurs
grep -i error /var/log/scraper-centris.log

# Seulement les succès API
grep -i "API.*succes" /var/log/scraper-centris.log

# Statistiques des cycles
grep -i "RESUME DU CYCLE" /var/log/scraper-centris.log -A 6
```

---

## 🔄 MISE À JOUR DU CODE

### **Méthode 1 : Avec Git**

```bash
cd /opt/scraper-centris
git pull
systemctl restart scraper-centris
```

### **Méthode 2 : Avec le script deploy.sh**

**Sur VOTRE PC (pas le serveur) :**

1. Éditez `deploy.sh` :
```bash
nano deploy.sh
# Changez SERVER_IP="VOTRE_IP_SERVEUR" avec la vraie IP
```

2. Exécutez :
```bash
chmod +x deploy.sh
./deploy.sh
```

Le script :
- ✅ Crée une archive du code
- ✅ L'envoie sur le serveur
- ✅ La décompresse
- ✅ Redémarre le service

---

## 🐛 DÉPANNAGE

### **Le service ne démarre pas**

```bash
# Voir les logs détaillés
journalctl -u scraper-centris -n 50

# Tester manuellement
cd /opt/scraper-centris
python3.12 scraper_production.py
```

### **Erreur "Chrome not found"**

```bash
# Vérifier Chrome
google-chrome --version

# Réinstaller si besoin
sudo ./install_server.sh
```

### **Erreur "Permission denied"**

```bash
# Donner les permissions
chmod +x /opt/scraper-centris/*.py
chmod +x /opt/scraper-centris/*.sh
```

### **Le scraper ne trouve pas les annonces**

```bash
# Vérifier la connexion
curl https://api.rayharvey.ca/robot/api/scraping

# Tester manuellement
cd /opt/scraper-centris
python3.12 test_api.py
```

### **Espace disque plein**

```bash
# Voir l'espace disque
df -h

# Nettoyer les fichiers JSON anciens
cd /opt/scraper-centris
rm property_*.json  # Garde scraped_properties.json !

# Nettoyer les logs (attention !)
> /var/log/scraper-centris.log
```

---

## 📈 MONITORING & MAINTENANCE

### **Vérification quotidienne**

```bash
# Statut rapide
systemctl status scraper-centris

# Dernière activité
tail -20 /var/log/scraper-centris.log
```

### **Vérification hebdomadaire**

```bash
# Espace disque
df -h

# RAM utilisée
free -h

# Nombre d'annonces scrapées
wc -l /opt/scraper-centris/scraped_properties.json
```

### **Backup automatique**

Le système fait déjà des backups automatiques de `scraped_properties.json`.

**Pour faire un backup manuel :**
```bash
cd /opt/scraper-centris
cp scraped_properties.json scraped_properties_backup_$(date +%Y%m%d).json
```

---

## 🔒 SÉCURITÉ

### **Créer un utilisateur non-root (recommandé)**

```bash
# Créer un utilisateur
adduser scraper
usermod -aG sudo scraper

# Changer le propriétaire des fichiers
chown -R scraper:scraper /opt/scraper-centris

# Modifier le service
nano /etc/systemd/system/scraper-centris.service
# Changez: User=root -> User=scraper
systemctl daemon-reload
systemctl restart scraper-centris
```

### **Configurer le firewall**

```bash
# Installer UFW
apt install ufw

# Autoriser SSH
ufw allow ssh

# Activer
ufw enable

# Vérifier
ufw status
```

---

## ✅ CHECKLIST POST-DÉPLOIEMENT

- [ ] Le service démarre sans erreur
- [ ] Les logs montrent l'activité du scraper
- [ ] Le test API fonctionne
- [ ] scraped_properties.json se remplit
- [ ] Les fichiers property_*.json sont créés
- [ ] Le monitoring DigitalOcean montre de l'activité
- [ ] Vous recevez les données dans votre API

---

## 📞 SUPPORT

**En cas de problème :**

1. Vérifiez les logs : `tail -f /var/log/scraper-centris.log`
2. Testez manuellement : `python3.12 scraper_production.py`
3. Vérifiez la config : `cat config_api.py`

**Commandes de diagnostic :**
```bash
# Info système
uname -a
python3.12 --version
google-chrome --version
chromedriver --version

# Processus en cours
ps aux | grep python

# Connexions réseau
netstat -tlnp | grep python
```

---

## 🎉 FÉLICITATIONS !

Votre scraper Centris est maintenant **en production** ! 🚀

Il va tourner 24/7 et scraper automatiquement les nouvelles annonces !
