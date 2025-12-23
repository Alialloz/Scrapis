# ⚡ DÉMARRAGE RAPIDE - 3 ÉTAPES

## 📝 ÉTAPE 1 : Configurer l'API (2 minutes)

Ouvrez `config_api.py` et modifiez la ligne 10 :

```python
API_ENDPOINT = "https://VOTRE-API.com/api/properties"  # ← VOTRE URL ICI
```

Si votre API nécessite une authentification, décommentez et configurez aussi :

```python
API_HEADERS = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer VOTRE_TOKEN',  # ← DÉCOMMENTER ET CONFIGURER
}
```

---

## 🧪 ÉTAPE 2 : Tester l'API (1 minute)

```bash
python test_api.py
```

✅ Si vous voyez `[SUCCESS]` → Passez à l'étape 3  
❌ Si erreur → Vérifiez l'URL et que votre API est accessible

---

## 🚀 ÉTAPE 3 : Lancer le Monitoring Continu

### Windows
Double-cliquez sur : `start_monitoring.bat`

### Linux/Mac
```bash
chmod +x start_monitoring.sh
./start_monitoring.sh
```

---

## ✅ C'EST PARTI !

Le système va maintenant :
- ✅ Vérifier **toutes les heures** s'il y a de nouvelles annonces
- ✅ Scraper automatiquement chaque nouvelle annonce (60 sec/annonce)
- ✅ Envoyer le JSON complet à votre API
- ✅ Sauvegarder l'ID pour éviter les doublons

### Pour arrêter :
Appuyez sur `Ctrl+C`

---

## 📊 Que reçoit votre API ?

Votre API va recevoir un **POST JSON** comme ceci :

```json
{
  "prix": "750000",
  "adresse": "220Z-226BZ Boul. Pierre-Bertrand",
  "ville": "Québec",
  "numero_centris": "23326443",
  "source": "RE/MAX 1ER CHOIX INC., Agence immobilière",
  "photo_urls": [
    "https://mspublic.centris.ca/media.ashx?id=...",
    ... (9 photos)
  ],
  "donnees_financieres": { ... },
  "unites": { ... },
  ...
}
```

**Plus de 70 champs extraits par annonce !**

---

## 📚 Documentation Complète

- `DEPLOIEMENT.md` - Guide complet de déploiement
- `GUIDE_API.md` - Exemples d'API (Node.js, Python, PHP)
- `RECAPITULATIF.md` - Vue d'ensemble du système

---

## ⚙️ Configuration Avancée

Dans `config_api.py` vous pouvez modifier :

```python
MONITORING_INTERVAL = 60  # Minutes entre chaque cycle (défaut : 1 heure)
SAVE_JSON_LOCALLY = True  # Sauvegarder les JSON localement
MAX_LISTINGS_PER_CYCLE = 0  # 0 = illimité, ou limiter à X annonces
```

---

## 🎯 Prêt en 3 Minutes !

1. Configurez l'API → `config_api.py`
2. Testez → `python test_api.py`
3. Lancez → `start_monitoring.bat` (Windows) ou `start_monitoring.sh` (Linux/Mac)

**C'est tout ! Le système tourne maintenant automatiquement ! 🚀**




