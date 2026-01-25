# TODO : Intégration complète du logging

##  Statut actuel

✅ **Système de logging créé** (`logger_config.py`)
✅ **Script d'analyse créé** (`analyze_logs.py`)  
✅ **Documentation créée** (`LOGGING.md`)
🔄 **Intégration partielle** dans `scraper_production.py`
❌ **Non intégré** dans les autres fichiers

## ✅ Déjà fait

- `scraper_production.py` : 
  - Logger configuré en haut du fichier
  - `send_to_api()` : Migré vers logging
  - Résumé du cycle : Utilise `log_scraping_stats()`
  - Import des erreurs config : Migré vers logging

## ❌ À faire : scraper_production.py

Remplacer les `print()` restants (environ 60) par des appels au logger :

### Priorité HAUTE

- `run_monitoring_cycle()` : 
  - Ligne 124-126 : En-tête du cycle
  - Ligne 150 : Info limite annonces
  - Ligne 155 : Traitement annonce
  - Ligne 168-180 : Sauvegarde et erreurs
  - Ligne 190 : Pause
  - Ligne 210-212 : Erreur critique du cycle

- `start_monitoring()` :
  - Ligne 377-385 : En-tête de démarrage
  - Ligne 392 : Numéro de cycle
  - Ligne 405-407 : Fin de cycle
  - Ligne 413-416 : Arrêt monitoring

- `main()` :
  - Ligne 423-447 : Vérification configuration
  - Ligne 453-455 : Lancement monitoring
  - Ligne 460-464 : Erreur critique

### Priorité MOYENNE

- `cleanup_json_files()` : Tous les print() (ligne 293-367)
- `backup_scraped_ids()` : Tous les print() (ligne 257-270)
- `save_stats()` : Ligne 239

### Guide de migration

```python
# Remplacements à faire:

print("[ERREUR]...")      → logger.error("...")
print("[WARNING]...")     → logger.warning("...")
print("[INFO]...")        → logger.info("...")
print("[OK]...")          → logger.info("✓ ...")
print(f"[ERREUR]...{var}") → logger.error(f"...{var}")

# Pour les traceback:
except Exception as e:
    print(f"[ERREUR] {e}")
    traceback.print_exc()

# Devient:
except Exception as e:
    logger.error(f"Erreur: {e}", exc_info=True)
```

## ❌ À faire : scraper_monitor.py

Ce fichier est utilisé par `scraper_production.py`, il DOIT aussi avoir du logging :

1. Ajouter en haut :
```python
from logger_config import setup_logger, log_extraction_result

logger = setup_logger('monitor', level='INFO')
```

2. Remplacer tous les `print()` dans :
   - `__init__()` 
   - `get_new_listings()`
   - `scrape_listing()`
   - `run_once()`

## ❌ À faire : scraper_detail_complete.py

Moins urgent, mais améliorerait le debug :

- Garder les `print()` actuels OU
- Ajouter du logging en parallèle pour le développement

## 🧪 Tests

Une fois l'intégration terminée :

```bash
# Test local
python tests/test_logging.py

# Lancer le scraper en production (test)
python scraper_production.py

# Analyser les logs
python analyze_logs.py

# Vérifier les logs
tail -f logs/production.log
tail -f logs/monitor.log
```

## 📝 Checklist finale

- [ ] `scraper_production.py` : 100% migré
- [ ] `scraper_monitor.py` : 100% migré
- [ ] Tests locaux passent
- [ ] Logs créés dans `logs/`
- [ ] `analyze_logs.py` fonctionne
- [ ] Commit + push
- [ ] Déployer sur droplet
- [ ] Vérifier logs sur serveur

## 🚀 Déploiement

```bash
git add -A
git commit -m "Feat: Intégration logging dans scraper_production"
git push origin main

# Sur le serveur
ssh root@IP
cd /opt/scraper-centris
git pull
systemctl restart scraper-centris

# Vérifier les logs
tail -f logs/production.log
python analyze_logs.py
```
