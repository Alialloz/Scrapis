#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script simple pour voir le JSON exact qui serait envoyé à l'API
"""

import time
import json
from scraper_with_list_info import CentrisScraperWithListInfo

MATRIX_URL = "https://matrix.centris.ca/Matrix/Public/Portal.aspx?ID=0-3319143035-10&eml=Y2JlYXVkZXRAcmF5aGFydmV5LmNh&L=2"

print("="*80)
print("TEST RAPIDE - EXTRACTION ET AFFICHAGE DU JSON")
print("="*80)

scraper = CentrisScraperWithListInfo()

if not scraper.init_driver():
    print("ERREUR: Impossible d'initialiser le driver")
    exit(1)

try:
    print("\n[1/3] Chargement de la page...")
    scraper.driver.get(MATRIX_URL)
    time.sleep(5)
    
    print("[2/3] Extraction de l'annonce (environ 30-60 secondes)...")
    property_data = scraper.scrape_property_with_list_info(index=0)
    
    if not property_data:
        print("ERREUR: Extraction échouée")
        exit(1)
    
    print("[3/3] Génération du JSON...")
    
    # Enlever les données internes avant l'envoi à l'API
    api_data = property_data.copy()
    if '_donnees_liste' in api_data:
        del api_data['_donnees_liste']
    
    # Afficher le JSON formaté
    json_string = json.dumps(api_data, indent=2, ensure_ascii=False)
    
    print("\n" + "="*80)
    print("JSON QUI SERAIT ENVOYÉ À L'API:")
    print("="*80)
    print(json_string)
    print("="*80)
    
    # Sauvegarder
    filename = f"api_payload_{property_data.get('numero_centris', 'test')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(json_string)
    
    print(f"\n✅ JSON sauvegardé dans: {filename}")
    print(f"📊 Taille: {len(json_string)} caractères")
    print(f"🔢 Numéro Centris: {property_data.get('numero_centris')}")
    
finally:
    scraper.close()
