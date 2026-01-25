#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST SIMPLE - 3 ANNONCES
Teste exactement comme test_complet_windows.py mais pour 3 annonces différentes (index 0, 1, 2)
"""

import time
from scraper_with_list_info import CentrisScraperWithListInfo
import json

def test_annonce_unique(index_annonce):
    """Teste UNE annonce avec UN nouveau navigateur (comme test_complet_windows.py)"""
    
    print(f"\n{'='*80}")
    print(f"  TEST ANNONCE INDEX {index_annonce}")
    print(f"{'='*80}\n")
    
    scraper = CentrisScraperWithListInfo()
    
    try:
        print("Initialisation du navigateur...")
        if not scraper.init_driver():
            print("[ERREUR] Impossible d'initialiser le driver")
            return None
        print("[OK] Chrome initialise\n")
        
        print("Chargement de la page Matrix...")
        scraper.driver.get('https://matrix.centris.ca/Matrix/Public/Portal.aspx?ID=0-3319143035-10&eml=Y2JlYXVkZXRAcmF5aGFydmV5LmNh&L=2#1')
        time.sleep(3)
        print("[OK] Page chargee\n")
        
        print(f"Extraction COMPLETE de l'annonce #{index_annonce}...\n")
        start_time = time.time()
        
        # SCRAPING COMPLET (comme en production)
        property_data = scraper.scrape_property_with_list_info(index=index_annonce)
        
        elapsed_time = time.time() - start_time
        
        if not property_data:
            print("[ERREUR] Extraction echouee")
            return None
        
        print(f"\n[OK] Extraction complete reussie en {elapsed_time:.1f} secondes\n")
        
        # Afficher résumé
        print(f"{'='*80}")
        print(f"  RESULTATS")
        print(f"{'='*80}\n")
        print(f"  Prix          : {property_data.get('prix', 'N/A')} $")
        print(f"  Adresse       : {property_data.get('adresse', 'N/A')}")
        print(f"  Ville         : {property_data.get('ville', 'N/A')}")
        print(f"  Type          : {property_data.get('type_propriete', 'N/A')}")
        print(f"  Numero Centris: {property_data.get('numero_centris', 'N/A')}")
        
        # Gérer les valeurs None pour les champs texte
        inclusions = property_data.get('inclusions')
        if inclusions:
            print(f"  Inclusions    : {inclusions[:60]}...")
        else:
            print(f"  Inclusions    : N/A")
        
        exclusions = property_data.get('exclusions')
        if exclusions:
            print(f"  Exclusions    : {exclusions[:60]}...")
        else:
            print(f"  Exclusions    : N/A")
        
        print(f"  Source        : {property_data.get('source', 'N/A')}")
        print(f"  Photos        : {len(property_data.get('photo_urls', []))} URLs")
        print(f"  Unites        : {property_data.get('unites', {}).get('total_residentiel', 0)} resid.")
        
        # Sauvegarder
        numero = property_data.get('numero_centris', f'index_{index_annonce}')
        filename = f"test_simple_{numero}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(property_data, f, indent=2, ensure_ascii=False)
        print(f"\n  Fichier sauvegarde: {filename}")
        
        return property_data
        
    except Exception as e:
        print(f"[ERREUR] Exception: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        print("\nFermeture du navigateur...")
        scraper.close()
        print("[OK] Navigateur ferme\n")


def main():
    print("\n" + "="*80)
    print("  TEST SIMPLE - 3 ANNONCES")
    print("  Teste les annonces aux index 0, 1, 2")
    print("="*80)
    
    resultats = []
    
    # Tester les 3 premières annonces (index 0, 1, 2)
    for index in [0, 1, 2]:
        resultat = test_annonce_unique(index)
        if resultat:
            resultats.append(resultat)
        
        # Délai entre annonces
        if index < 2:
            print(f"Attente de 5 secondes avant l'annonce suivante...")
            time.sleep(5)
    
    # Résumé
    print("\n" + "="*80)
    print("  RESUME FINAL")
    print("="*80 + "\n")
    print(f"  Annonces extraites : {len(resultats)}/3")
    print()
    
    for i, r in enumerate(resultats):
        print(f"  Annonce #{i} - Centris {r.get('numero_centris', 'N/A')}")
        print(f"    Adresse    : {r.get('adresse', 'N/A')}")
        print(f"    Prix       : {r.get('prix', 'N/A')} $")
        print(f"    Inclusions : {r.get('inclusions', 'N/A')[:50] if r.get('inclusions') else 'N/A'}...")
        print(f"    Source     : {r.get('source', 'N/A')}")
        print()
    
    print("="*80)
    if len(resultats) == 3:
        print("  TEST REUSSI ! 3/3 annonces extraites avec succes")
    else:
        print(f"  TEST PARTIEL: {len(resultats)}/3 annonces extraites")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
