#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test COMPLET Windows - Extraction de TOUTES les données comme en production
"""

import time
import json
import sys
import os

# Ajouter le répertoire courant au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper_with_list_info import CentrisScraperWithListInfo

# Configuration
MATRIX_URL = "https://matrix.centris.ca/Matrix/Public/Portal.aspx?ID=0-3319143035-10&eml=Y2JlYXVkZXRAcmF5aGFydmV5LmNh&L=2"


def print_section(title):
    """Affiche un titre de section"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def display_complete_data(data):
    """Affiche TOUTES les données extraites"""
    
    print_section("INFORMATIONS DE BASE")
    base_fields = {
        'prix': 'Prix',
        'adresse': 'Adresse',
        'ville': 'Ville',
        'arrondissement': 'Arrondissement',
        'quartier': 'Quartier',
        'type_propriete': 'Type de propriete',
        'annee_construction': 'Annee de construction',
        'numero_centris': 'Numero Centris',
        'date_envoi': 'Date d\'envoi',
        'statut': 'Statut',
        'superficie_habitable': 'Superficie habitable',
        'superficie_terrain': 'Superficie terrain'
    }
    
    for key, label in base_fields.items():
        value = data.get(key)
        if value:
            print(f"  [OK] {label:30s}: {value}")
        else:
            print(f"  [ ] {label:30s}: Non disponible")
    
    print_section("DONNEES FINANCIERES")
    financieres = data.get('donnees_financieres', {})
    
    if financieres:
        # Revenus bruts potentiels
        revenus = financieres.get('revenus_bruts_potentiels', {})
        if any(revenus.values()):
            print("  Revenus bruts potentiels:")
            for key, value in revenus.items():
                if value:
                    print(f"    - {key:20s}: {value:>12s} $")
        
        # Revenus bruts effectifs
        revenus_effectifs = financieres.get('revenus_bruts_effectifs')
        if revenus_effectifs:
            print(f"\n  Revenus bruts effectifs: {revenus_effectifs:>12s} $")
        
        # Dépenses d'exploitation
        depenses = financieres.get('depenses_exploitation', {})
        depenses_filled = {k: v for k, v in depenses.items() if v}
        if depenses_filled:
            print(f"\n  Depenses d'exploitation ({len(depenses_filled)} postes):")
            for key, value in list(depenses_filled.items())[:10]:
                print(f"    - {key:25s}: {value:>12s} $")
            if len(depenses_filled) > 10:
                print(f"    ... et {len(depenses_filled) - 10} autres postes")
        
        # Revenus nets
        revenus_nets = financieres.get('revenus_nets_exploitation')
        if revenus_nets:
            print(f"\n  Revenus nets d'exploitation: {revenus_nets:>12s} $")
    else:
        print("  Aucune donnee financiere disponible")
    
    print_section("UNITES")
    unites = data.get('unites', {})
    
    if unites:
        residentielles = unites.get('residentielles', [])
        if residentielles:
            print("  Unites residentielles:")
            for unite in residentielles:
                print(f"    - {unite.get('type')}: {unite.get('nombre')} unite(s)")
            print(f"  Total residentiel: {unites.get('total_residentiel', 0)} unites")
        
        commerciales = unites.get('commerciales', [])
        if commerciales:
            print("\n  Unites commerciales:")
            for unite in commerciales:
                print(f"    - {unite.get('type')}: {unite.get('nombre')} unite(s)")
            print(f"  Total commercial: {unites.get('total_commercial', 0)} unites")
    else:
        print("  Aucune information sur les unites")
    
    print_section("CARACTERISTIQUES DETAILLEES")
    carac = data.get('caracteristiques_detaillees', {})
    
    if carac:
        carac_fields = {
            'systeme_egouts': 'Systeme d\'egouts',
            'approv_eau': 'Approvisionnement en eau',
            'stationnement_detail': 'Stationnement',
            'chauffage': 'Chauffage'
        }
        
        for key, label in carac_fields.items():
            value = carac.get(key)
            if value:
                print(f"  [OK] {label:30s}: {value}")
    else:
        print("  Aucune caracteristique detaillee")
    
    print_section("INCLUSIONS / EXCLUSIONS / REMARQUES")
    
    inclusions = data.get('inclusions')
    if inclusions:
        print(f"  Inclusions: {inclusions[:200]}...")
    
    exclusions = data.get('exclusions')
    if exclusions:
        print(f"\n  Exclusions: {exclusions[:200]}...")
    
    remarques = data.get('remarques')
    if remarques:
        print(f"\n  Remarques: {remarques[:200]}...")
    
    addenda = data.get('addenda')
    if addenda:
        print(f"\n  Addenda: {addenda[:200]}...")
    
    print_section("PHOTOS")
    photo_urls = data.get('photo_urls', [])
    nb_photos = data.get('nb_photos', 0)
    
    print(f"  Nombre de photos: {nb_photos}")
    print(f"  URLs extraites: {len(photo_urls)}")
    
    if photo_urls:
        print("\n  Apercu des 3 premieres photos:")
        for i, url in enumerate(photo_urls[:3], 1):
            print(f"    {i}. {url[:75]}...")
    
    print_section("COURTIER")
    courtier_fields = {
        'courtier_email': 'Email',
        'courtier_telephone': 'Telephone',
        'courtier_nom': 'Nom',
        'courtier_agence': 'Agence'
    }
    
    for key, label in courtier_fields.items():
        value = data.get(key)
        if value:
            print(f"  [OK] {label:15s}: {value}")


def test_extraction_complete():
    """Test d'extraction complète"""
    
    print("\n" + "="*80)
    print("  TEST D'EXTRACTION COMPLETE - VERSION WINDOWS")
    print("  Utilise le scraper complet comme en production")
    print("="*80)
    
    print("\nEtape 1/5: Initialisation du scraper complet...")
    
    # Créer le scraper
    scraper = CentrisScraperWithListInfo()
    
    # IMPORTANT: Modifier l'initialisation du driver pour Windows
    print("  Configuration Chrome pour Windows...")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        chrome_options = Options()
        # chrome_options.add_argument('--headless')  # Décommenter pour mode headless
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        # NE PAS spécifier binary_location sur Windows
        scraper.driver = webdriver.Chrome(options=chrome_options)
        
        print("[OK] Chrome initialise avec succes")
        
    except Exception as e:
        print(f"[ERREUR] Impossible d'initialiser Chrome: {e}")
        return None
    
    try:
        print("\nEtape 2/5: Chargement de la page Matrix...")
        print(f"  URL: {MATRIX_URL[:60]}...")
        scraper.driver.get(MATRIX_URL)
        time.sleep(5)
        print("[OK] Page chargee")
        
        print("\nEtape 3/5: Extraction COMPLETE de la premiere annonce...")
        print("  ATTENTION: Cela va prendre 30-60 secondes")
        print("  Le scraper va:")
        print("    1. Extraire les infos de la liste")
        print("    2. Cliquer sur l'annonce")
        print("    3. Extraire TOUTES les donnees financieres")
        print("    4. Extraire les unites et caracteristiques")
        print("    5. Extraire les inclusions/exclusions/remarques")
        print("    6. Extraire les 9 photos (URLs)")
        
        start_time = time.time()
        
        # SCRAPING COMPLET (comme en production)
        property_data = scraper.scrape_property_with_list_info(index=0)
        
        elapsed_time = time.time() - start_time
        
        if not property_data:
            print("[ERREUR] Extraction echouee")
            return None
        
        print(f"[OK] Extraction complete reussie en {elapsed_time:.1f} secondes")
        
        print("\nEtape 4/5: Affichage des donnees...")
        display_complete_data(property_data)
        
        print("\nEtape 5/5: Sauvegarde et simulation envoi API...")
        
        # Enlever les données internes
        api_data = property_data.copy()
        if '_donnees_liste' in api_data:
            del api_data['_donnees_liste']
        
        # Sauvegarder
        filename = f"test_complet_{property_data.get('numero_centris', 'unknown')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(api_data, f, indent=2, ensure_ascii=False)
        
        print_section("SIMULATION ENVOI A L'API")
        
        try:
            from config_api import API_ENDPOINT
        except:
            API_ENDPOINT = "https://apidev.rayharvey.ca/robot/api/scraping"
        
        print(f"  Endpoint: {API_ENDPOINT}")
        print(f"  Content-Type: application/json")
        
        json_str = json.dumps(api_data, ensure_ascii=False)
        print(f"  Taille du JSON: {len(json_str)} caracteres ({len(json_str)/1024:.1f} KB)")
        
        # Afficher un aperçu du JSON
        print("\n  Structure du JSON:")
        for key in api_data.keys():
            value = api_data[key]
            if isinstance(value, dict):
                print(f"    - {key}: {len(value)} champs")
            elif isinstance(value, list):
                print(f"    - {key}: {len(value)} elements")
            else:
                print(f"    - {key}: {str(value)[:50] if value else 'null'}")
        
        print_section("TEST TERMINE AVEC SUCCES")
        print(f"  Fichier genere: {filename}")
        print(f"  Numero Centris: {property_data.get('numero_centris', 'N/A')}")
        print(f"  Prix: {property_data.get('prix', 'N/A')} $")
        print(f"  Photos: {len(property_data.get('photo_urls', []))} URLs")
        print(f"  Taille JSON: {len(json_str)/1024:.1f} KB")
        print(f"  Temps total: {elapsed_time:.1f} secondes")
        
        print("\n  CECI EST LE FORMAT EXACT ENVOYE A L'API EN PRODUCTION")
        
        return property_data
        
    except Exception as e:
        print(f"\n[ERREUR] {e}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        print("\nFermeture du navigateur dans 3 secondes...")
        time.sleep(3)
        scraper.close()
        print("[OK] Navigateur ferme")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("  SCRAPIS - TEST COMPLET WINDOWS")
    print("  Extraction COMPLETE comme en production")
    print("="*80)
    
    result = test_extraction_complete()
    
    if result:
        print("\n" + "="*80)
        print("  TEST REUSSI!")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("  TEST ECHOUE")
        print("="*80)
    
    input("\nAppuyez sur Entree pour quitter...")
