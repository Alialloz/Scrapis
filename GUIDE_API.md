# 🔌 Configuration de l'API

## Configuration Rapide

### 1. Dans `scraper_monitor.py`

Ligne 286, remplacez `None` par l'URL de votre API :

```python
API_ENDPOINT = "https://votre-api.com/api/properties"
```

### 2. Personnaliser les Headers (optionnel)

Dans la méthode `send_to_api()` (ligne ~156), ajoutez vos headers :

```python
headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer VOTRE_TOKEN_ICI',
    'X-API-Key': 'votre_cle_api',
    'User-Agent': 'CentrisMonitor/1.0'
}
```

## Format des Données Envoyées

Le scraper envoie un **POST JSON** avec toutes les données de la propriété :

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
  "chambres": null,
  "salles_bain": null,
  "superficie_habitable": null,
  "superficie_terrain": "4940",
  "nb_photos": 9,
  "courtier_email": "mguimont@rayharvey.ca",
  "courtier_telephone": "418-849-7777",
  "donnees_financieres": {
    "revenus_bruts_potentiels": {
      "residentiel": "18000",
      "commercial": "3",
      "stationnements": null,
      "autres": null,
      "total": null
    },
    "inoccupation_mauvaises_creances": {
      "residentiel": null,
      "commercial": null,
      "stationnements": null,
      "autres": null,
      "total": null
    },
    "revenus_bruts_effectifs": "18003",
    "depenses_exploitation": {
      "taxes_municipales": "12355",
      "taxe_scolaire": "357",
      "taxes_secteur": null,
      "taxes_affaires": null,
      "taxes_eau": null,
      "electricite": "1975",
      "mazout": "1829",
      "gaz": null,
      "ascenseur": null,
      "assurances": null,
      "cable": null,
      "concierge": null,
      "contenant_sanitaire": null,
      "deneigement": null,
      "entretien": null,
      "equipement_location": null,
      "frais_communs": null,
      "gestion_administration": null,
      "ordures": null,
      "pelouse": null,
      "publicite": null,
      "securite": null,
      "recuperation_depenses": null,
      "total": "18003"
    },
    "revenus_nets_exploitation": "1487"
  },
  "unites": {
    "residentielles": [
      { "type": "3 1/2", "nombre": "3" },
      { "type": "4 1/2", "nombre": "2" }
    ],
    "commerciales": [
      { "type": "Commercial", "nombre": "3" }
    ],
    "total_residentiel": 10,
    "total_commercial": 3
  },
  "caracteristiques_detaillees": {
    "systeme_egouts": "Municipalité",
    "approv_eau": "Municipalité",
    "stationnement_detail": "Allée (8), Garage (1)",
    "chauffage": "Eau chaude",
    "eau_acces": null,
    "commodites_propriete": null,
    "commodites_batiment": null,
    "renovations": null
  },
  "inclusions": "Lumières, rideaux, stores...",
  "exclusions": "Effets personnels du locataire",
  "remarques": "Actif clé dans un assemblage à fort potentiel...",
  "addenda": "L'ensemble forme un package promoteur rare...",
  "source": "Centris",
  "url": "https://matrix.centris.ca/...",
  "photo_urls": [
    "https://mspublic.centris.ca/media.ashx?id=ADDD250DE7B47E3DDDDDDD1DD4&t=pi&sm=m&w=1260&h=1024",
    "https://mspublic.centris.ca/media.ashx?id=ADDD250DE7B4C20DDDDDDD2DDC&t=pi&f=I",
    "https://mspublic.centris.ca/media.ashx?id=ADDD250DE7B4CC8DDDDDDD0DDF&t=pi&f=I",
    "https://mspublic.centris.ca/media.ashx?id=ADDD250DE7B4CC7DDDDDDDFDD2&t=pi&f=I",
    "https://mspublic.centris.ca/media.ashx?id=ADDD250DE7B4CC3DDDDDDD4DD0&t=pi&f=I",
    "https://mspublic.centris.ca/media.ashx?id=ADDD250DE7B4C23DDDDDDDCDDB&t=pi&f=I",
    "https://mspublic.centris.ca/media.ashx?id=ADDD250DE7B4CC9DDDDDDDBDD1&t=pi&f=I",
    "https://mspublic.centris.ca/media.ashx?id=ADDD250DE7B4CCFDDDDDDDADDD&t=pi&f=I",
    "https://mspublic.centris.ca/media.ashx?id=ADDD250DE7B4CCBDDDDDDDEDDB&t=pi&f=I"
  ]
}
```

## Exemples d'Implémentation API

### Node.js (Express)

```javascript
const express = require('express');
const app = express();

app.use(express.json());

app.post('/api/properties', (req, res) => {
  const property = req.body;
  
  console.log('Nouvelle propriété reçue:', property.numero_centris);
  console.log('Adresse:', property.adresse);
  console.log('Prix:', property.prix);
  console.log('Photos:', property.photo_urls.length);
  
  // TODO: Sauvegarder dans votre base de données
  // db.properties.insertOne(property);
  
  res.status(201).json({
    success: true,
    message: 'Propriété enregistrée',
    numero_centris: property.numero_centris
  });
});

app.listen(3000, () => {
  console.log('API listening on port 3000');
});
```

### Python (Flask)

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/properties', methods=['POST'])
def create_property():
    property_data = request.get_json()
    
    print(f"Nouvelle propriété: {property_data['numero_centris']}")
    print(f"Adresse: {property_data['adresse']}")
    print(f"Prix: {property_data['prix']}")
    print(f"Photos: {len(property_data['photo_urls'])}")
    
    # TODO: Sauvegarder dans votre base de données
    # db.properties.insert_one(property_data)
    
    return jsonify({
        'success': True,
        'message': 'Propriété enregistrée',
        'numero_centris': property_data['numero_centris']
    }), 201

if __name__ == '__main__':
    app.run(port=5000)
```

### PHP (Laravel)

```php
<?php

Route::post('/api/properties', function (Request $request) {
    $property = $request->all();
    
    Log::info('Nouvelle propriété: ' . $property['numero_centris']);
    
    // TODO: Sauvegarder dans votre base de données
    // Property::create($property);
    
    return response()->json([
        'success' => true,
        'message' => 'Propriété enregistrée',
        'numero_centris' => $property['numero_centris']
    ], 201);
});
```

## Test de votre API

### Avec curl

```bash
curl -X POST https://votre-api.com/api/properties \
  -H "Content-Type: application/json" \
  -d @property_23326443.json
```

### Avec Python

```python
import requests
import json

with open('property_23326443.json', 'r', encoding='utf-8') as f:
    property_data = json.load(f)

response = requests.post(
    'https://votre-api.com/api/properties',
    json=property_data,
    headers={'Content-Type': 'application/json'}
)

print(f"Status: {response.status_code}")
print(f"Réponse: {response.json()}")
```

## Gestion des Erreurs

Le scraper considère que l'envoi est réussi si l'API retourne :
- Status 200 (OK)
- Status 201 (Created)

Tout autre status code est considéré comme une erreur et sera loggé.

## Schema MongoDB (Exemple)

```javascript
{
  numero_centris: { type: String, unique: true, required: true, index: true },
  prix: String,
  adresse: String,
  ville: String,
  arrondissement: String,
  quartier: String,
  type_propriete: String,
  annee_construction: String,
  date_envoi: String,
  statut: String,
  chambres: String,
  salles_bain: String,
  superficie_habitable: String,
  superficie_terrain: String,
  nb_photos: Number,
  courtier_email: String,
  courtier_telephone: String,
  donnees_financieres: {
    revenus_bruts_potentiels: {
      residentiel: String,
      commercial: String,
      stationnements: String,
      autres: String,
      total: String
    },
    inoccupation_mauvaises_creances: {
      residentiel: String,
      commercial: String,
      stationnements: String,
      autres: String,
      total: String
    },
    revenus_bruts_effectifs: String,
    depenses_exploitation: {
      taxes_municipales: String,
      taxe_scolaire: String,
      // ... 22 autres champs
      total: String
    },
    revenus_nets_exploitation: String
  },
  unites: {
    residentielles: [{ type: String, nombre: String }],
    commerciales: [{ type: String, nombre: String }],
    total_residentiel: Number,
    total_commercial: Number
  },
  caracteristiques_detaillees: Object,
  inclusions: String,
  exclusions: String,
  remarques: String,
  addenda: String,
  source: String,
  url: String,
  photo_urls: [String],
  created_at: { type: Date, default: Date.now },
  scraped_at: Date
}
```

## Troubleshooting

### L'API ne reçoit rien

1. Vérifiez que `API_ENDPOINT` est correct dans `scraper_monitor.py`
2. Vérifiez les logs du scraper
3. Testez votre endpoint avec curl

### L'API reçoit des données mais ne les enregistre pas

1. Vérifiez les logs de votre API
2. Vérifiez que votre base de données est accessible
3. Vérifiez les permissions d'écriture

### Status 401/403

Ajoutez l'authentification dans les headers (voir section 2)

### Status 500

Erreur côté serveur - vérifiez les logs de votre API

## 🚀 Prêt à utiliser !

Une fois l'API configurée, lancez simplement :

```bash
python scraper_monitor.py
```

Le scraper va :
1. Détecter les nouvelles annonces
2. Les scraper une par une
3. Envoyer chaque annonce à votre API
4. Sauvegarder l'ID dans `scraped_properties.json`

**Chaque nouvelle annonce sera automatiquement envoyée à votre API ! 🎉**






