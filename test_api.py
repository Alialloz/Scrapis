#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test API - Envoie une propriété à l'API
"""

import json
import requests
from config_api import API_ENDPOINT, API_HEADERS, API_TIMEOUT

# Charger la propriété
property_file = 'property_20255300.json'

print("=" * 80)
print("TEST APPEL API")
print("=" * 80)
print()

print(f"[1/3] Chargement de {property_file}...")
with open(property_file, 'r', encoding='utf-8') as f:
    property_data = json.load(f)

# Corriger les null en "" pour compatibilité API
def fix_nulls(data):
    if isinstance(data, dict):
        for key, value in data.items():
            if value is None and key in ['statut', 'quartier', 'chambres', 'salles_bain',
                                         'superficie_habitable', 'superficie_terrain',
                                         'evaluation_terrain', 'evaluation_batiment', 
                                         'evaluation_totale']:
                data[key] = ""
            elif isinstance(value, dict):
                fix_nulls(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        fix_nulls(item)
    return data

property_data = fix_nulls(property_data)

print(f"[OK] Propriete chargee:")
print(f"      Adresse: {property_data.get('adresse')}")
print(f"      No Centris: {property_data.get('numero_centris')}")
print(f"      Prix: {property_data.get('prix')} $")
print()

# Envoyer
print(f"[2/3] Envoi a l'API...")
print(f"      Endpoint: {API_ENDPOINT}")
print()

try:
    response = requests.post(
        API_ENDPOINT,
        json=property_data,
        headers=API_HEADERS,
        timeout=API_TIMEOUT
    )
    
    print(f"[3/3] Reponse recue:")
    print(f"      Status Code: {response.status_code}")
    print()
    
    if response.status_code in [200, 201]:
        print("[OK] SUCCES - Donnees envoyees avec succes!")
        print()
        print("Reponse de l'API:")
        print("-" * 80)
        try:
            response_json = response.json()
            print(json.dumps(response_json, indent=2, ensure_ascii=False))
        except:
            print(response.text)
        print("-" * 80)
    else:
        print("[ERREUR] Echec de l'envoi")
        print()
        print("Reponse de l'API:")
        print("-" * 80)
        print(response.text)
        print("-" * 80)

except requests.exceptions.Timeout:
    print(f"[ERREUR] Timeout - L'API n'a pas repondu en {API_TIMEOUT}s")
except requests.exceptions.ConnectionError:
    print(f"[ERREUR] Impossible de se connecter a l'API")
    print(f"         URL: {API_ENDPOINT}")
except Exception as e:
    print(f"[ERREUR] {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
