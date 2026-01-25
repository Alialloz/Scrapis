# Tests

Ce dossier contient tous les scripts de test et de debug du scraper Centris.

## Scripts de test principaux

- **test_simple_3_annonces.py** : Test complet de 3 annonces consécutives (recommandé)
- **test_complet_windows.py** : Test complet d'une seule annonce sur Windows
- **test_debug_extraction.py** : Debug de l'extraction des champs spécifiques

## Tests API

- **test_api.py** : Test de l'envoi de données à l'API
- **test_extraction_api.py** : Test extraction + envoi API
- **test_json_api.py** : Test du format JSON envoyé à l'API

## Tests spécifiques

- **test_properties.py** : Test des propriétés extraites
- **test_filtre_date.py** : Test du filtrage par date
- **test_extraction_windows.py** : Test extraction basique Windows
- **test_multiple_annonces.py** : Test multi-annonces (version ancienne)

## Debug

- **debug_source.py** : Debug de l'extraction du champ "source"

## Fichiers JSON

- **test_simple_*.json** : Résultats de tests sauvegardés

## Usage

```bash
# Test recommandé (3 annonces)
python tests/test_simple_3_annonces.py

# Test d'une seule annonce
python tests/test_complet_windows.py

# Debug d'un champ spécifique
python tests/debug_source.py
```

**Note** : Ces fichiers ne sont pas déployés en production.
