# Fonction de Scraping des Pages de Détail - Centris Matrix

## Résumé de ce qui a été créé

### Fichier: `scraper_detail_page.py`

Contient une classe `CentrisDetailScraper` avec les fonctionnalités suivantes :

## Fonctions Principales

### 1. `click_on_property(property_link_element)`
**But**: Clique sur le lien d'une propriété pour ouvrir le panneau de détail

**Processus**:
- Fait défiler pour rendre l'élément visible
- Clique sur le lien de la propriété
- Attend que l'URL change (#1, #2, etc.)
- Attend 2 secondes supplémentaires pour le chargement du contenu dynamique

**Retour**: `True` si succès, `False` sinon

### 2. `extract_detail_info()`
**But**: Extrait toutes les informations disponibles dans le panneau de détail

**Informations extraites**:

#### Informations de base:
- **Prix** (avec ou sans TPS/TVQ)
- **Adresse** complète
- **Ville/Arrondissement** (format: Québec (XXX))
- **Quartier**
- **Type de propriété** (Autre, Quintuplex, Duplex, etc.)
- **Année de construction**
- **Numéro Centris** (ID unique)
- **Date d'envoi**
- **Statut** (Nouvelle annonce, Nouveau prix)

#### Caractéristiques détaillées:
- **Nombre de chambres**
- **Nombre de salles de bain**
- **Superficie** (pi² ou m²)
- **Terrain** (dimensions)

#### Informations supplémentaires:
- **Description** de la propriété
- **Nombre de photos** disponibles
- **Équipements** (Garage, Piscine, Climatisation, etc.)

#### Informations du courtier:
- **Nom** du courtier/agent
- **Email**
- **Téléphone**

#### Autres sections:
- **Communauté** (informations sur le quartier)
- **Financier** (calculatrice hypothécaire)

**Retour**: Dictionnaire avec toutes les informations

### 3. `scrape_property_detail(property_link_element)`
**But**: Fonction principale qui combine le clic et l'extraction

**Processus**:
1. Clique sur la propriété
2. Attend le chargement
3. Extrait toutes les informations
4. Retourne le dictionnaire complet

### 4. `close_detail_panel()`
**But**: Ferme le panneau de détail pour revenir à la liste

**Méthodes**:
- Clique sur "Retour aux résultats"
- Ou supprime le hash (#) de l'URL

## Structure des Données Retournées

```python
{
    'prix': '750 000',
    'adresse': '220Z-226BZ Boul. Pierre-Bertrand',
    'ville': 'Les Rivières',
    'quartier': 'Neufchâtel-Est/Lebourgneuf',
    'type_propriete': 'Autre',
    'annee_construction': '1949',
    'numero_centris': '23326443',
    'date_envoi': '2025-12-15',
    'statut': 'Nouvelle annonce',
    'description': 'Description complète de la propriété...',
    'caracteristiques': {},
    'pieces': {
        'chambres': '4',
        'salles_bain': '2'
    },
    'dimensions': {
        'superficie': '1500',
        'terrain': '5000'
    },
    'equipements': ['Garage', 'Stationnement', 'Piscine'],
    'photos': ['Photo 1', 'Photo 2', ..., 'Photo 9'],
    'courtier': {
        'nom': 'Myriam Guimont',
        'email': 'mguimont@rayharvey.ca',
        'telephone': '418-849-7777'
    },
    'communaute': {},
    'financier': {},
    'url': 'https://matrix.centris.ca/...#1'
}
```

## Patterns Regex Utilisés

### Prix
```python
r'(\d[\d\s,]+)\s*\$\s*(?:\+\s*TPS/TVQ)?'
r'Prix\s*[:\-]\s*(\d[\d\s,]+)\s*\$'
```

### Adresse
```python
r'(\d+[A-Z]?(?:-\d+[A-Z]?)?\s+(?:Boul\.|Av\.|Rue|Ch\.|Route)\s+[A-Za-zÀ-ÿ\s\-\.]+)'
```

### Numéro Centris
```python
r'No\s*Centris\s*[:\-]?\s*(\d+)'
```

### Date d'envoi
```python
r"Date\s*d['']envoi\s*[:\-]?\s*(\d{4}-\d{2}-\d{2})"
```

### Année de construction
```python
r'construit\s+en\s+(\d{4})'
```

### Ville/Arrondissement
```python
r'Québec\s*\(([^)]+)\)'
```

### Quartier
```python
r'dans\s+le\s+quartier\s+([^c]+?)(?:construit|$)'
```

### Chambres
```python
r'(\d+)\s+chambre[s]?'
r'Chambre[s]?\s*[:\-]\s*(\d+)'
```

### Salles de bain
```python
r'(\d+)\s+salle[s]?\s+de\s+bain[s]?'
r'Salle[s]?\s+de\s+bain\s*[:\-]\s*(\d+)'
```

### Superficie
```python
r'Superficie\s*[:\-]?\s*([\d\s,]+)\s*(?:pi²|m²)'
r'([\d\s,]+)\s*(?:pi²|m²)'
```

## Utilisation

### Exemple de base
```python
from scraper_detail_page import CentrisDetailScraper

# Créer le scraper
scraper = CentrisDetailScraper(headless=False)

# Charger la page principale
scraper.driver.get("URL_DE_LA_PAGE")

# Trouver les liens de propriétés
property_links = scraper.driver.find_elements(By.XPATH, "//a[contains(text(), 'Boul.')]")

# Scraper une propriété
property_data = scraper.scrape_property_detail(property_links[0])

# Fermer le panneau
scraper.close_detail_panel()

# Scraper la suivante
property_data2 = scraper.scrape_property_detail(property_links[1])

# Fermer le navigateur
scraper.close()
```

### Exemple pour scraper toutes les propriétés
```python
all_properties = []

for i, link in enumerate(property_links):
    print(f"Scraping propriété {i+1}/{len(property_links)}")
    
    # Scraper la propriété
    data = scraper.scrape_property_detail(link)
    
    if data:
        all_properties.append(data)
    
    # Fermer le panneau et revenir à la liste
    scraper.close_detail_panel()
    
    # Pause entre chaque scraping
    time.sleep(2)

# Sauvegarder toutes les données
import json
with open('all_properties_detail.json', 'w', encoding='utf-8') as f:
    json.dump(all_properties, f, indent=2, ensure_ascii=False)
```

## Problèmes Connus et Solutions

### 1. ChromeDriver
**Problème**: Erreur WinError 193
**Solution temporaire**: Utiliser les outils MCP browser disponibles ou réinstaller ChromeDriver manuellement

### 2. Contenu Dynamique
**Problème**: Le contenu peut prendre du temps à charger
**Solution**: Ajuster les temps d'attente (actuellement 2 secondes)

### 3. Changement de Structure HTML
**Problème**: Centris peut modifier la structure de leur site
**Solution**: Les patterns regex sont flexibles et cherchent dans tout le texte

## Prochaines Étapes

1. **Cliquer sur "Voir toutes les photos"** pour extraire les URLs des images
2. **Explorer les onglets "Communauté" et "Fonction Financière"** pour plus d'informations
3. **Gérer la pagination** pour scraper toutes les propriétés (64+)
4. **Ajouter la gestion d'erreurs** pour les propriétés sans certaines informations
5. **Optimiser les temps d'attente** avec des conditions explicites
6. **Télécharger les images** des propriétés
7. **Extraire les données structurées** (JSON-LD) si disponibles

## Notes Importantes

- Le panneau de détail est un overlay/sidebar qui s'ouvre sans recharger la page
- L'URL change avec un hash (#1, #2, etc.) pour chaque propriété
- Le contenu est chargé dynamiquement via JavaScript
- Il faut attendre que le contenu soit chargé avant d'extraire les données
- Certaines informations peuvent ne pas être disponibles pour toutes les propriétés
- Les patterns regex sont conçus pour être robustes face aux variations

