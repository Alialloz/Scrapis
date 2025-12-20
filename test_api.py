#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test de connexion à l'API
"""

import json
import sys

try:
    from config_api import API_ENDPOINT, API_HEADERS, API_TIMEOUT
except ImportError:
    print("[ERREUR] Fichier config_api.py introuvable!")
    sys.exit(1)

print("="*80)
print("TEST DE CONNEXION API")
print("="*80)

# Vérifier la configuration
print(f"\nEndpoint API: {API_ENDPOINT}")

if API_ENDPOINT == "https://votre-api.com/api/properties":
    print("\n[ERREUR] L'API n'est pas configuree!")
    print("Veuillez editer config_api.py et configurer API_ENDPOINT")
    sys.exit(1)

# Créer un JSON de test
test_data = {
    "prix": "750000",
    "adresse": "TEST - 123 Rue de Test",
    "ville": "Québec",
    "numero_centris": "99999999",
    "source": "TEST - Agence de test",
    "nb_photos": 9,
    "photo_urls": [
        "https://example.com/photo1.jpg",
        "https://example.com/photo2.jpg"
    ],
    "_test": True,
    "_timestamp": "2025-12-19T12:00:00"
}

print("\nJSON de test:")
print(json.dumps(test_data, indent=2, ensure_ascii=False))

# Tester l'envoi
print("\n" + "="*80)
print("ENVOI DU JSON DE TEST")
print("="*80)

try:
    import requests
    
    print(f"\n[INFO] Envoi POST vers {API_ENDPOINT}...")
    
    response = requests.post(
        API_ENDPOINT,
        json=test_data,
        headers=API_HEADERS,
        timeout=API_TIMEOUT
    )
    
    print(f"\n[OK] Reponse recue!")
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    
    if response.status_code in [200, 201]:
        print("\n[SUCCESS] L'API a accepte les donnees!")
        try:
            response_json = response.json()
            print(f"Reponse JSON:")
            print(json.dumps(response_json, indent=2, ensure_ascii=False))
        except:
            print(f"Reponse texte: {response.text}")
    else:
        print(f"\n[WARNING] L'API a retourne un code inattendu: {response.status_code}")
        print(f"Reponse: {response.text[:500]}")
    
except requests.exceptions.ConnectionError as e:
    print(f"\n[ERREUR] Impossible de se connecter a l'API!")
    print(f"URL: {API_ENDPOINT}")
    print(f"Erreur: {e}")
    print("\nVerifiez que:")
    print("  1. L'URL est correcte")
    print("  2. L'API est demarree")
    print("  3. Vous avez acces au reseau")
    
except requests.exceptions.Timeout:
    print(f"\n[ERREUR] Timeout! L'API n'a pas repondu dans les {API_TIMEOUT} secondes")
    
except Exception as e:
    print(f"\n[ERREUR] Erreur inattendue: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("FIN DU TEST")
print("="*80)


