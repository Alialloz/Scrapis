# Scraper Centris – Essentiel serveur

Guide minimal pour faire tourner et administrer le scraper sur le droplet.

---

## 1. Rôle du système

- **Scraper** : surveille une page Matrix Centris et récupère les nouvelles annonces.
- **Envoi** : envoie les données à une API (`config_api.py`).
- **Exécution** : tourne en continu via un service systemd, avec redémarrage auto en cas de crash.

---

## 2. Emplacements sur le serveur

| Élément | Chemin |
|--------|--------|
| Code | `/opt/scraper-centris/` |
| Script principal | `/opt/scraper-centris/scraper_production.py` |
| Config (API, URL Matrix, etc.) | `/opt/scraper-centris/config_api.py` |
| Logs applicatifs (rotation) | `/opt/scraper-centris/logs/production.log` |
| Logs systemd (stdout) | `/var/log/scraper-centris.log` |
| Logs erreurs systemd | `/var/log/scraper-centris-error.log` |
| IDs déjà scrapés | `/opt/scraper-centris/scraped_properties.json` |
| Service systemd | `/etc/systemd/system/scraper-centris.service` |

---

## 3. Commandes du service

```bash
# Statut
systemctl status scraper-centris

# Démarrer
systemctl start scraper-centris

# Arrêter
systemctl stop scraper-centris

# Redémarrer (après mise à jour du code)
systemctl restart scraper-centris

# Démarrer au boot
systemctl enable scraper-centris

# Ne plus démarrer au boot
systemctl disable scraper-centris
```

---

## 4. Logs

```bash
# Logs applicatifs (recommandé, avec niveaux et rotation)
tail -f /opt/scraper-centris/logs/production.log

# Logs systemd
tail -f /var/log/scraper-centris.log

# Erreurs systemd
tail -f /var/log/scraper-centris-error.log

# Analyse des logs (résumé, stats, alertes)
cd /opt/scraper-centris && python3.12 analyze_logs.py
```

---

## 5. Mise à jour du code

```bash
cd /opt/scraper-centris
git pull origin main
pip3.12 install -r requirements.txt   # si de nouvelles dépendances
systemctl restart scraper-centris
```

---

## 6. Configuration

Fichier à éditer : **`/opt/scraper-centris/config_api.py`**

- **`API_ENDPOINT`** : URL de l’API qui reçoit les annonces.
- **`MATRIX_URL`** : URL de la page Centris à surveiller.
- **`MONITORING_INTERVAL`** : intervalle entre deux cycles (en minutes).
- **`scraped_properties.json`** : ne pas supprimer (liste des annonces déjà traitées).

Après modification :

```bash
systemctl restart scraper-centris
```

---

## 7. Dépannage

| Problème | Commande |
|----------|----------|
| Le service ne démarre pas | `journalctl -u scraper-centris -n 80 --no-pager` |
| Tester à la main | `cd /opt/scraper-centris && python3.12 scraper_production.py` |
| Vérifier Chrome | `google-chrome --version` |
| Vérifier Python | `python3.12 --version` |

---

## 8. Cycle de fonctionnement

1. Toutes les **`MONITORING_INTERVAL`** minutes, le script :
   - charge la page Matrix ;
   - détecte les nouvelles annonces (non présentes dans `scraped_properties.json`) ;
   - scrape chaque nouvelle annonce (détails, photos, etc.) ;
   - envoie les données à l’API ;
   - enregistre l’ID dans `scraped_properties.json`.

2. Nettoyage automatique (si activé dans `config_api.py`) : suppression des anciens `property_*.json` selon la config (jour, heure, conservation de la semaine en cours).

---

## 9. Fichiers à ne pas toucher / supprimer

- `scraped_properties.json` – perte = re-scraping de toutes les annonces.
- `config_api.py` – contient l’URL de l’API et la page Centris.
- `logs/` – générés par l’application ; ne pas supprimer en cours d’exécution si vous suivez les logs en direct.

---

## 10. Connexion rapide

```bash
ssh root@VOTRE_IP
cd /opt/scraper-centris
```

Pour un suivi rapide après connexion :

```bash
systemctl status scraper-centris
tail -20 /opt/scraper-centris/logs/production.log
```
