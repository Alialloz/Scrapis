# Scraper Centris Matrix

Scraper pour extraire les données des propriétés immobilières depuis le portail Centris Matrix.

## Installation

1. Installer les dépendances :
```bash
pip install -r requirements.txt
```

2. S'assurer que Chrome est installé sur votre système (le scraper utilise ChromeDriver automatiquement).

## Utilisation

### Utilisation de base

```python
from scraper_centris import CentrisScraper

url = "https://matrix.centris.ca/Matrix/Public/Portal.aspx?ID=0-3319143035-10&eml=Y2JlYXVkZXRAcmF5aGFydmV5LmNh&L=2"

scraper = CentrisScraper(url, headless=False)
try:
    properties = scraper.scrape()
    scraper.save_to_csv()
    scraper.save_to_json()
finally:
    scraper.close()
```

### Exécution directe

```bash
python scraper_centris.py
```

## Données extraites

Le scraper extrait les informations suivantes pour chaque propriété :

- **Prix** : Prix de la propriété
- **Adresse** : Adresse complète
- **Ville** : Ville et arrondissement
- **Quartier** : Quartier de la propriété
- **Type de propriété** : Autre, Quintuplex, Duplex, Triplex, etc.
- **Année de construction** : Année de construction
- **Numéro Centris** : Numéro d'identification Centris
- **Date d'envoi** : Date d'envoi de l'annonce
- **Statut** : Nouvelle annonce, Nouveau prix, etc.
- **URL** : Lien vers la page de détail de la propriété

## Fichiers de sortie

Les données sont sauvegardées dans deux formats :

- **CSV** : `centris_properties_YYYYMMDD_HHMMSS.csv`
- **JSON** : `centris_properties_YYYYMMDD_HHMMSS.json`

## Notes

- Le scraper fait défiler automatiquement la page pour charger toutes les propriétés
- Il gère le contenu JavaScript dynamique avec Selenium
- Les données sont extraites à la fois avec Selenium et BeautifulSoup pour une meilleure robustesse

## Avertissement

Ce scraper est destiné à un usage personnel et éducatif. Assurez-vous de respecter les conditions d'utilisation du site Centris et les lois sur le web scraping.


