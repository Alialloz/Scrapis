#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST MULTIPLE ANNONCES
Teste l'extraction sur plusieurs annonces pour vérifier la robustesse
"""

import sys
import time
from scraper_with_list_info import CentrisScraperWithListInfo
import json

def format_size(size_bytes):
    """Formatte la taille en Ko ou Mo"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

def test_annonce(index, total):
    """Teste une annonce spécifique"""
    print(f"\n{'='*80}")
    print(f"  TEST ANNONCE #{index+1}/{total}")
    print(f"{'='*80}\n")
    
    scraper = None
    try:
        # Créer un NOUVEAU scraper pour chaque annonce (comme en production)
        print("Initialisation d'un nouveau scraper...")
        scraper = CentrisScraperWithListInfo()
        if not scraper.init_driver():
            print(f"[ERREUR] Impossible d'initialiser le driver")
            return None
        
        # Charger la page
        scraper.driver.get('https://matrix.centris.ca/Matrix/Public/Portal.aspx?ID=0-3319143035-10&eml=Y2JlYXVkZXRAcmF5aGFydmV5LmNh&L=2#1')
        time.sleep(3)
        
        # Extraire les données (TOUJOURS index=0 car liste fraîche)
        start_time = time.time()
        data = scraper.scrape_property_with_list_info(index)
        duration = time.time() - start_time
        
        if not data:
            print(f"[ERREUR] Impossible d'extraire l'annonce #{index+1}")
            return None
        
        # Afficher les résultats clés
        print(f"\n{'='*80}")
        print(f"  RESULTATS ANNONCE #{index+1}")
        print(f"{'='*80}\n")
        
        print(f"  Prix                 : {data.get('prix', 'N/A')} $")
        print(f"  Adresse              : {data.get('adresse', 'N/A')}")
        print(f"  Ville                : {data.get('ville', 'N/A')}")
        print(f"  Type                 : {data.get('type_propriete', 'N/A')}")
        print(f"  Numero Centris       : {data.get('numero_centris', 'N/A')}")
        print(f"  Statut               : {data.get('statut', 'N/A')}")
        print(f"\n  --- CHAMPS CRITIQUES ---")
        
        # Vérifier les champs critiques
        inclusions = data.get('inclusions', 'N/A')
        exclusions = data.get('exclusions', 'N/A')
        source = data.get('source', 'N/A')
        remarques = data.get('remarques', 'N/A')
        
        # Afficher avec troncature
        print(f"  Inclusions           : {inclusions[:60] if inclusions != 'N/A' else 'N/A'}{'...' if len(str(inclusions)) > 60 else ''}")
        print(f"  Exclusions           : {exclusions[:60] if exclusions != 'N/A' else 'N/A'}{'...' if len(str(exclusions)) > 60 else ''}")
        print(f"  Source               : {source}")
        print(f"  Remarques            : {remarques[:60] if remarques != 'N/A' else 'N/A'}{'...' if len(str(remarques)) > 60 else ''}")
        
        print(f"\n  Photos               : {len(data.get('photo_urls', []))} URLs")
        print(f"  Unites               : {data.get('unites', {}).get('total_residentiel', 0)} resid., {data.get('unites', {}).get('total_commercial', 0)} comm.")
        
        # Données financières
        donnees_fin = data.get('donnees_financieres', {})
        if donnees_fin.get('revenus_bruts_effectifs'):
            print(f"  Revenus bruts        : {donnees_fin.get('revenus_bruts_effectifs')} $")
        if donnees_fin.get('revenus_nets_exploitation'):
            print(f"  Revenus nets         : {donnees_fin.get('revenus_nets_exploitation')} $")
        
        print(f"\n  Temps extraction     : {duration:.1f} secondes")
        
        # Sauvegarder
        numero = data.get('numero_centris', f'annonce_{index+1}')
        filename = f"test_annonce_{numero}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        file_size = len(json.dumps(data, ensure_ascii=False).encode('utf-8'))
        print(f"  Fichier sauvegarde   : {filename} ({format_size(file_size)})")
        
        # Vérifier la qualité
        score = 0
        total_checks = 0
        
        checks = [
            ('prix', data.get('prix')),
            ('adresse', data.get('adresse')),
            ('ville', data.get('ville')),
            ('type_propriete', data.get('type_propriete')),
            ('numero_centris', data.get('numero_centris')),
            ('inclusions', inclusions if inclusions != 'N/A' and len(str(inclusions)) > 5 else None),
            ('exclusions', exclusions if exclusions != 'N/A' and len(str(exclusions)) > 5 else None),
            ('source', source if source != 'N/A' and len(str(source)) > 10 else None),
            ('remarques', remarques if remarques != 'N/A' and len(str(remarques)) > 20 else None),
            ('photos', data.get('photo_urls') if len(data.get('photo_urls', [])) > 0 else None),
        ]
        
        for field, value in checks:
            total_checks += 1
            if value:
                score += 1
        
        quality = (score / total_checks) * 100
        print(f"\n  QUALITE EXTRACTION   : {quality:.0f}% ({score}/{total_checks} champs)")
        
        return data
        
    except Exception as e:
        print(f"[ERREUR] Exception lors de l'extraction de l'annonce #{index+1}: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        # Fermer le navigateur
        if scraper:
            print(f"\n[INFO] Fermeture du navigateur...")
            scraper.close()

def main():
    print("\n" + "="*80)
    print("  TEST EXTRACTION MULTIPLE ANNONCES")
    print("  Teste la robustesse sur plusieurs annonces")
    print("="*80 + "\n")
    
    # Nombre d'annonces à tester
    NB_ANNONCES = 3
    
    print(f"Configuration:")
    print(f"  - Nombre d'annonces : {NB_ANNONCES}")
    print(f"  - Temps estime      : {NB_ANNONCES * 60}-{NB_ANNONCES * 80} secondes")
    print(f"  - Mode              : UN navigateur par annonce (comme en production)")
    print(f"\nDemarrage du test...\n")
    
    # Tester chaque annonce (avec son propre scraper)
    resultats = []
    succes = 0
    
    start_total = time.time()
    
    for i in range(NB_ANNONCES):
        resultat = test_annonce(i, NB_ANNONCES)
        if resultat:
            resultats.append(resultat)
            succes += 1
        
        # Petit délai entre chaque annonce
        if i < NB_ANNONCES - 1:
            print(f"\nAttente de 5 secondes avant l'annonce suivante...")
            time.sleep(5)
    
    duration_total = time.time() - start_total
    
    # Résumé final
    print(f"\n{'='*80}")
    print(f"  RESUME FINAL")
    print(f"{'='*80}\n")
    
    print(f"  Annonces testees     : {NB_ANNONCES}")
    print(f"  Extractions reussies : {succes}")
    print(f"  Taux de succes       : {(succes/NB_ANNONCES)*100:.0f}%")
    print(f"  Temps total          : {duration_total:.1f} secondes")
    print(f"  Temps moyen/annonce  : {duration_total/NB_ANNONCES:.1f} secondes")
    
    # Analyse des champs critiques
    print(f"\n  --- ANALYSE DES CHAMPS CRITIQUES ---\n")
    
    champs_critiques = ['inclusions', 'exclusions', 'source', 'remarques']
    for champ in champs_critiques:
        count = sum(1 for r in resultats if r.get(champ) and len(str(r.get(champ))) > 5)
        print(f"  {champ.capitalize():20s} : {count}/{succes} annonces ({(count/succes)*100:.0f}%)")
    
    # Afficher un exemple de chaque champ critique
    print(f"\n  --- EXEMPLES EXTRAITS ---\n")
    
    for i, resultat in enumerate(resultats, 1):
        print(f"  Annonce #{i} (Centris {resultat.get('numero_centris', 'N/A')}):")
        print(f"    Inclusions : {str(resultat.get('inclusions', 'N/A'))[:70]}...")
        print(f"    Exclusions : {str(resultat.get('exclusions', 'N/A'))[:70]}...")
        print(f"    Source     : {resultat.get('source', 'N/A')}")
        print()
    
    print(f"\n{'='*80}")
    if succes == NB_ANNONCES:
        print(f"  TEST REUSSI ! Toutes les annonces ont ete extraites avec succes")
    else:
        print(f"  TEST PARTIEL: {succes}/{NB_ANNONCES} annonces extraites")
    print(f"{'='*80}\n")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n[INFO] Test interrompu par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERREUR] Exception fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
