# Système de Logging

Documentation du système de logging du scraper Centris.

## 📁 Structure des logs

```
logs/
├── scraper.log         # Log principal avec rotation (10 MB max)
├── scraper.log.1       # Backup 1
├── scraper.log.2       # Backup 2
├── ...
├── scraper.log.7       # Backup 7 (7 jours d'historique)
└── errors.log          # Erreurs uniquement
```

## 🔧 Configuration

Le système de logging est configuré dans `logger_config.py` :

- **Rotation automatique** : 10 MB par fichier
- **Rétention** : 7 fichiers de backup (environ 1 semaine)
- **Format** : `YYYY-MM-DD HH:MM:SS | LEVEL | LOGGER | MESSAGE`
- **Encodage** : UTF-8

## 📊 Niveaux de log

- **DEBUG** : Informations détaillées (développement)
- **INFO** : Informations générales (production)
- **WARNING** : Avertissements
- **ERROR** : Erreurs récupérables
- **CRITICAL** : Erreurs critiques

## 💻 Utilisation dans le code

### Configuration basique

```python
from logger_config import setup_logger

# Logger principal
logger = setup_logger('scraper', level='INFO')

logger.info("Démarrage du scraping...")
logger.warning("Attention : pas d'inclusions trouvées")
logger.error("Erreur lors de l'extraction")
```

### Logger d'erreurs

```python
from logger_config import setup_error_logger

error_logger = setup_error_logger()
error_logger.error("Erreur critique capturée")
```

### Logs structurés

```python
from logger_config import log_scraping_stats, log_extraction_result

# Statistiques
stats = {
    'Nouvelles annonces': 5,
    'Annonces scrapées': 5,
    'Durée': '3m 45s'
}
log_scraping_stats(logger, stats)

# Résultat d'extraction
property_data = {...}
log_extraction_result(logger, property_data, success=True)
```

## 🔍 Analyse des logs

### Script d'analyse automatique

```bash
# Analyser les dernières 24 heures
python analyze_logs.py

# Analyser les dernières 48 heures
python analyze_logs.py 48
```

Le script affiche :
- ✅ Taux de réussite des extractions
- 📊 Messages par niveau (INFO, WARNING, ERROR)
- 📸 Statistiques photos
- ❌ Dernières erreurs
- ⏰ Activité par heure
- ⚠️  Problèmes détectés

### Commandes utiles (Serveur)

```bash
# Voir les logs en temps réel
tail -f logs/scraper.log

# Voir les 100 dernières lignes
tail -100 logs/scraper.log

# Voir uniquement les erreurs
grep "ERROR" logs/scraper.log

# Chercher un pattern spécifique
grep "Centris #24886125" logs/scraper.log

# Compter les extractions réussies aujourd'hui
grep "$(date +%Y-%m-%d)" logs/scraper.log | grep "Extraction réussie" | wc -l

# Voir les erreurs du jour
grep "$(date +%Y-%m-%d)" logs/errors.log
```

## 📈 Surveillance Production

### Sur le serveur DigitalOcean

Les logs sont également capturés par systemd :

```bash
# Logs systemd (sortie standard)
journalctl -u scraper-centris -f

# Logs systemd (dernières 100 lignes)
journalctl -u scraper-centris -n 100

# Logs systemd + fichiers
tail -f /var/log/scraper-centris.log
tail -f logs/scraper.log
```

### Rotation automatique

Le système utilise `RotatingFileHandler` de Python :
- Crée automatiquement les backups `.1`, `.2`, etc.
- Supprime automatiquement les anciens fichiers
- Pas besoin de logrotate

## 🚨 Détection de problèmes

Le script `analyze_logs.py` détecte automatiquement :

- ⚠️  Taux d'échec > 10%
- ⚠️  Plus de 10 erreurs
- ⚠️  Pas d'activité depuis > 2h
- ⚠️  Moyenne de photos < 10

## 🛠️ Développement vs Production

### Développement (local)
```python
logger = setup_logger('scraper', level='DEBUG', log_to_console=True)
```
- Niveau DEBUG pour tout voir
- Affichage console + fichier

### Production (serveur)
```python
logger = setup_logger('scraper', level='INFO', log_to_console=True)
```
- Niveau INFO pour éviter trop de verbosité
- Console capturée par systemd
- Fichiers avec rotation

## 📝 Exemples de logs

```
2026-01-25 08:30:45 | INFO     | scraper | Démarrage du monitoring...
2026-01-25 08:30:46 | INFO     | scraper | Chargement de la page Matrix
2026-01-25 08:30:50 | INFO     | scraper | ✓ Extraction réussie - Centris #24886125
2026-01-25 08:30:50 | DEBUG    | scraper |   Adresse: 390 Rue des Lilas E.
2026-01-25 08:30:50 | DEBUG    | scraper |   Prix: 699000 $
2026-01-25 08:30:50 | DEBUG    | scraper |   Photos: 48
2026-01-25 08:30:50 | DEBUG    | scraper |   Source: RE/MAX 1ER CHOIX INC., Agence immobilière
2026-01-25 08:31:15 | WARNING  | scraper | Pas d'inclusions trouvées
2026-01-25 08:31:45 | ERROR    | scraper | Impossible de cliquer sur la propriété
```

## 🔄 Migration depuis print()

Remplacer progressivement :
```python
# Ancien
print("[OK] Chrome initialise")
print(f"[ERREUR] {e}")

# Nouveau
logger.info("Chrome initialise")
logger.error(f"Erreur: {e}", exc_info=True)
```

L'argument `exc_info=True` ajoute automatiquement le traceback complet.
