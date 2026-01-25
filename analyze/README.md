# Analyze

Ce dossier contient les scripts et résultats d'analyse de la structure des pages Centris.

## Scripts d'analyse

- **analyze_page.py** : Analyse la structure de la page de liste
- **analyze_detail_page.py** : Analyse la structure de la page de détails
- **analyze_snapshot.py** : Analyse d'un snapshot HTML

## Fichiers de résultats

- **analyse_page.txt** : Résultat de l'analyse de la page de liste
- **analyse_page_detail.txt** : Résultat de l'analyse de la page de détails

## Usage

Ces scripts sont utilisés pour comprendre la structure HTML des pages Centris et développer les regex d'extraction.

```bash
# Analyser la page de liste
python analyze/analyze_page.py

# Analyser la page de détails
python analyze/analyze_detail_page.py
```

**Note** : Ces fichiers sont utilisés uniquement en développement.
