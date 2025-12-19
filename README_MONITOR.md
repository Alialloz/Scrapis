# 📊 Système de Monitoring Centris

Ce système détecte automatiquement les nouvelles annonces sur Centris, les scrape et envoie les données à votre API.

## 🎯 Fonctionnalités

- ✅ **Détection automatique** des nouvelles annonces
- ✅ **Mémoire persistante** des annonces déjà scrapées
- ✅ **Scraping complet** : toutes les données + photos
- ✅ **Envoi automatique** à votre API
- ✅ **Monitoring continu** avec intervalle configurable
- ✅ **Sauvegarde locale** de chaque annonce en JSON

## 📁 Fichiers

- `scraper_monitor.py` : Script principal de monitoring
- `config_monitor.json` : Configuration (URL, API endpoint, etc.)
- `scraped_properties.json` : Liste des annonces déjà scrapées (créé automatiquement)
- `property_XXXXXXXX.json` : Données individuelles de chaque propriété scrapée

## 🚀 Utilisation

### 1. Configuration de l'API

Éditez `scraper_monitor.py` ligne 286 :

```python
API_ENDPOINT = "https://votre-api.com/api/properties"
```

Ou configurez directement dans le code :

```python
monitor = CentrisMonitor(
    url=MATRIX_URL,
    api_endpoint="https://votre-api.com/api/properties",
    storage_file='scraped_properties.json'
)
```

### 2. Mode: Cycle Unique

Lance un seul cycle de monitoring (scan + scrape les nouvelles annonces) :

```bash
python scraper_monitor.py
```

### 3. Mode: Monitoring Continu

Pour un monitoring continu, modifiez la fonction `main()` dans `scraper_monitor.py` :

```python
def main():
    MATRIX_URL = "https://matrix.centris.ca/..."
    API_ENDPOINT = "https://votre-api.com/api/properties"
    
    monitor = CentrisMonitor(
        url=MATRIX_URL,
        api_endpoint=API_ENDPOINT
    )
    
    # Monitoring continu toutes les 60 minutes
    monitor.run_continuous_monitoring(interval_minutes=60)
```

Puis lancez :

```bash
python scraper_monitor.py
```

Pour arrêter : `Ctrl+C`

## 📊 Flux de Données

```
1. Scan de la page Matrix
   ↓
2. Extraction de tous les numéros Centris
   ↓
3. Comparaison avec scraped_properties.json
   ↓
4. Si nouvelles annonces détectées:
   - Scraping complet (données + 9 photos)
   - Sauvegarde dans property_XXXXXXXX.json
   - Envoi à l'API (POST JSON)
   - Ajout à scraped_properties.json
```

## 📦 Format JSON envoyé à l'API

```json
{
  "prix": "750000",
  "adresse": "220Z-226BZ Boul. Pierre-Bertrand",
  "ville": "Québec",
  "arrondissement": "Les Rivières",
  "quartier": "Neufchâtel-Est/Lebourgneuf",
  "type_propriete": "Autre",
  "annee_construction": "1949",
  "numero_centris": "23326443",
  "date_envoi": "2025-12-15",
  "statut": "Nouvelle annonce",
  "donnees_financieres": { ... },
  "unites": { ... },
  "caracteristiques_detaillees": { ... },
  "inclusions": "...",
  "exclusions": "...",
  "remarques": "...",
  "addenda": "...",
  "photo_urls": [
    "https://mspublic.centris.ca/media.ashx?id=...",
    ...
  ],
  "nb_photos": 9,
  "courtier_email": "mguimont@rayharvey.ca",
  "courtier_telephone": "418-849-7777"
}
```

## 🔧 API Requirements

Votre API doit accepter :
- **Méthode**: POST
- **Content-Type**: application/json
- **Body**: JSON complet de la propriété
- **Réponse attendue**: Status 200 ou 201 pour succès

Exemple d'endpoint (Node.js/Express) :

```javascript
app.post('/api/properties', (req, res) => {
  const propertyData = req.body;
  
  // Sauvegarder dans votre base de données
  db.properties.insert(propertyData);
  
  res.status(201).json({ 
    success: true, 
    message: 'Propriété enregistrée',
    numero_centris: propertyData.numero_centris 
  });
});
```

## 📈 Monitoring et Logs

Le script affiche :
- Nombre total d'annonces sur la page
- Nombre de nouvelles annonces détectées
- Statut du scraping pour chaque annonce
- Statut de l'envoi à l'API
- Résumé du cycle

Exemple de sortie :

```
=== CYCLE DE MONITORING - 2025-12-18 15:30:00 ===
[OK] 24 annonces trouvées sur la page
[NOUVEAU] 3 nouvelle(s) annonce(s) détectée(s):
  - No Centris: 23326443
  - No Centris: 23326444
  - No Centris: 23326445

SCRAPING DE L'ANNONCE No Centris: 23326443
[OK] Données sauvegardées dans property_23326443.json
[API] Envoi des données à https://votre-api.com/api/properties...
[OK] Données envoyées avec succès (Status: 201)

RÉSUMÉ DU CYCLE
Total annonces sur la page: 24
Nouvelles annonces: 3
Scrapées avec succès: 3
Envoyées à l'API: 3
Erreurs: 0
```

## ⚙️ Personnalisation

### Changer l'intervalle de monitoring

```python
monitor.run_continuous_monitoring(interval_minutes=30)  # Toutes les 30 min
```

### Ajouter des headers personnalisés à l'API

Modifiez la méthode `send_to_api()` :

```python
headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer VOTRE_TOKEN',
    'X-Custom-Header': 'valeur'
}
```

### Filtrer certains types de propriétés

Dans `identify_new_listings()`, ajoutez des conditions :

```python
# Scraper seulement les propriétés > 500 000$
if property_data['prix'] > 500000:
    self.send_to_api(property_data)
```

## 🐛 Dépannage

### Problème: L'API ne reçoit pas les données

1. Vérifiez que `API_ENDPOINT` est correctement configuré
2. Vérifiez les logs pour voir la réponse de l'API
3. Testez votre endpoint avec curl :
   ```bash
   curl -X POST https://votre-api.com/api/properties \
     -H "Content-Type: application/json" \
     -d @property_23326443.json
   ```

### Problème: Certaines annonces ne sont pas détectées

1. Vérifiez que la page a bien chargé (augmentez les `time.sleep`)
2. Vérifiez le fichier `scraped_properties.json` pour voir quels IDs sont déjà enregistrés
3. Supprimez `scraped_properties.json` pour tout rescraper

### Problème: Le scraping est trop lent

1. Le scraping complet (avec photos) prend ~60 secondes par annonce
2. Désactivez le scraping des photos pour accélérer (à implémenter si besoin)

## 📝 Notes Importantes

- ⚠️ **Respect du serveur** : Un délai de 5 secondes est imposé entre chaque scraping
- 💾 **Stockage** : Chaque annonce génère un fichier JSON (~5-10 KB)
- 🔄 **Idempotence** : Une annonce scrapée ne sera jamais re-scrapée (sauf si vous supprimez `scraped_properties.json`)
- 📷 **Photos** : Les 9 URLs de photos sont incluses dans le JSON (liens directs vers les images)

## 🚀 Déploiement en Production

Pour un monitoring 24/7, utilisez :

### Option 1: Cron (Linux)

```bash
# Éditer crontab
crontab -e

# Ajouter (exécuter toutes les heures)
0 * * * * cd /path/to/Scrapis && python scraper_monitor.py
```

### Option 2: Service Windows

Créez une tâche planifiée Windows qui exécute `scraper_monitor.py` toutes les heures.

### Option 3: Docker

```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "scraper_monitor.py"]
```

## 📞 Support

Pour toute question ou problème, consultez les logs du script ou contactez le développeur.

