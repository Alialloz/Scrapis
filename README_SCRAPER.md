# Scraper Centris - Documentation

## Scraper Fonctionnel : `scraper_detail_functional.py`

### ✅ Statut : FONCTIONNEL ET TESTÉ

Le scraper fonctionne et a été testé avec succès sur la page Centris Matrix.

## Résultats du Test

### Propriété scrapée avec succès :
- **Prix**: 750,000 $
- **Quartier**: Neufchâtel-Est/Lebourgneuf
- **Type**: Autre
- **Année**: 1949
- **Numéro Centris**: 21830586
- **Date d'envoi**: 2025-12-15
- **Statut**: Nouvelle annonce
- **Superficie**: 4,940 pi²
- **Photos**: 9 photos disponibles
- **Courtier**: mguimont@rayharvey.ca, 418-849-7777
- **Équipements**: Garage, Stationnement, Chauffage, Sous-sol, Cour

## Utilisation

### 1. Scraper une seule propriété

```python
from scraper_detail_functional import CentrisDetailScraperFunctional

# Créer le scraper
scraper = CentrisDetailScraperFunctional()
scraper.init_driver()

# Charger la page
url = "https://matrix.centris.ca/Matrix/Public/Portal.aspx?ID=0-3319143035-10&eml=Y2JlYXVkZXRAcmF5aGFydmV5LmNh&L=2"
scraper.driver.get(url)
time.sleep(5)

# Scraper la première propriété (index=0)
property_data = scraper.scrape_property(index=0)

# Afficher les données
print(json.dumps(property_data, indent=2))

# Fermer
scraper.close()
```

### 2. Scraper plusieurs propriétés

```python
from scraper_detail_functional import CentrisDetailScraperFunctional
import time
import json

scraper = CentrisDetailScraperFunctional()
scraper.init_driver()

# Charger la page
url = "https://matrix.centris.ca/Matrix/Public/Portal.aspx?ID=0-3319143035-10&eml=Y2JlYXVkZXRAcmF5aGFydmV5LmNh&L=2"
scraper.driver.get(url)
time.sleep(5)

# Scraper les 5 premières propriétés
all_properties = []
for i in range(5):
    print(f"\n=== Scraping propriété {i+1}/5 ===")
    
    # Scraper
    data = scraper.scrape_property(index=i)
    
    if data:
        all_properties.append(data)
    
    # Fermer le panneau et revenir à la liste
    scraper.close_panel()
    time.sleep(2)

# Sauvegarder toutes les données
with open('all_properties.json', 'w', encoding='utf-8') as f:
    json.dump(all_properties, f, indent=2, ensure_ascii=False)

print(f"\n{len(all_properties)} propriétés sauvegardées!")
scraper.close()
```

## Données Extraites

### Informations de base
- `prix`: Prix de la propriété (en dollars)
- `adresse`: Adresse complète
- `ville`: Ville (généralement Québec)
- `arrondissement`: Arrondissement de la ville
- `quartier`: Nom du quartier
- `type_propriete`: Type (Autre, Quintuplex, Duplex, etc.)
- `annee_construction`: Année de construction
- `numero_centris`: Numéro d'identification Centris (unique)
- `date_envoi`: Date de publication de l'annonce
- `statut`: "Nouvelle annonce" ou "Nouveau prix"

### Caractéristiques
- `chambres`: Nombre de chambres
- `salles_bain`: Nombre de salles de bain
- `salles_eau`: Nombre de salles d'eau
- `stationnements`: Nombre de stationnements
- `superficie_habitable`: Superficie en pi²
- `superficie_terrain`: Superficie du terrain en pi²
- `equipements`: Liste des équipements (Garage, Piscine, etc.)

### Photos
- `nb_photos`: Nombre de photos disponibles
- `url_photos`: Liste des URLs des photos (à implémenter)

### Courtier
- `courtier_nom`: Nom du courtier
- `courtier_email`: Email du courtier
- `courtier_telephone`: Téléphone du courtier
- `courtier_agence`: Nom de l'agence

### Autres
- `url`: URL de la propriété
- `raw_text`: Extrait du texte brut (pour debug)

## Fonctions Principales

### `scrape_property(index)`
Fonction principale qui :
1. Clique sur la propriété à l'index spécifié
2. Attend le chargement du panneau de détail
3. Extrait toutes les informations
4. Retourne un dictionnaire avec les données

**Paramètres** :
- `index` : Index de la propriété dans la liste (0 = première)

**Retour** :
- `dict` : Dictionnaire avec toutes les informations ou `None` en cas d'erreur

### `click_on_property_by_index(index)`
Clique sur une propriété spécifique

### `extract_all_info()`
Extrait toutes les informations du panneau de détail ouvert

### `close_panel()`
Ferme le panneau de détail pour revenir à la liste

## Format de Sortie (JSON)

```json
{
  "prix": "750000",
  "adresse": null,
  "ville": null,
  "arrondissement": null,
  "quartier": "Neufchâtel-Est/Lebourgneuf",
  "type_propriete": "Autre",
  "annee_construction": "1949",
  "numero_centris": "21830586",
  "date_envoi": "2025-12-15",
  "statut": "Nouvelle annonce",
  "description": null,
  "chambres": null,
  "salles_bain": null,
  "salles_eau": null,
  "stationnements": null,
  "superficie_habitable": "4940",
  "superficie_terrain": null,
  "dimensions_terrain": null,
  "nb_etages": null,
  "equipements": ["Garage", "Stationnement", "Chauffage", "Sous-sol", "Cour"],
  "caracteristiques": [],
  "nb_photos": 9,
  "url_photos": [],
  "courtier_nom": null,
  "courtier_email": "mguimont@rayharvey.ca",
  "courtier_telephone": "418-849-7777",
  "courtier_agence": null,
  "taxes_municipales": null,
  "taxes_scolaires": null,
  "evaluation_municipale": null,
  "prix_par_pi2": null,
  "url": "https://matrix.centris.ca/Matrix/Public/Portal.aspx?ID=0-3319143035-10&eml=Y2JlYXVkZXRAcmF5aGFydmV5LmNh&L=2#1",
  "raw_text": "..."
}
```

## Prochaines Étapes

### À implémenter pour v2.0 :
1. **Extraction de l'adresse complète** - améliorer le regex
2. **Extraction des URLs des photos** - cliquer sur "Voir toutes les photos"
3. **Onglets "Communauté" et "Financier"** - extraire plus d'infos
4. **Gestion de la pagination** - scraper les 64 propriétés
5. **Gestion des erreurs** - retry en cas d'échec
6. **Mode headless** - pour exécuter sans interface
7. **Export vers API** - envoyer les données à une API REST
8. **Base de données** - sauvegarder dans une BDD

### Intégration API
Pour envoyer les données à une API :

```python
import requests

def send_to_api(property_data):
    """Envoie les données à une API"""
    api_url = "https://votre-api.com/properties"
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(api_url, json=property_data, headers=headers)
    
    if response.status_code == 200:
        print("Données envoyées avec succès")
        return response.json()
    else:
        print(f"Erreur: {response.status_code}")
        return None

# Utilisation
property_data = scraper.scrape_property(index=0)
if property_data:
    send_to_api(property_data)
```

## Notes Techniques

- Le scraper utilise Selenium avec Chrome
- Temps d'attente : 2-5 secondes entre les actions
- Le panneau de détail s'ouvre sans recharger la page (SPA)
- L'URL change avec un hash (#1, #2, etc.)
- Le contenu est chargé dynamiquement via JavaScript
- Certaines informations peuvent être absentes pour certaines propriétés

## Dépendances

```txt
selenium==4.15.2
beautifulsoup4==4.12.2
lxml==4.9.3
```

## Commande pour tester

```bash
python scraper_detail_functional.py
```

Les résultats seront sauvegardés dans `property_scraped.json`.

