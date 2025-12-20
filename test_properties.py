#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour analyser les 5 dernières propriétés
"""

import json
from pathlib import Path
from collections import defaultdict

def charger_propriete(fichier):
    """Charge un fichier JSON de propriété"""
    with open(fichier, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyser_proprietes():
    """Analyse les 5 dernières propriétés"""
    
    # Liste des 5 derniers fichiers
    fichiers = [
        'property_21796796.json',
        'property_21008469.json',
        'property_19312888.json',
        'property_12053552.json',
        'property_12273486.json'
    ]
    
    print("=" * 80)
    print("ANALYSE DES 5 DERNIÈRES PROPRIÉTÉS")
    print("=" * 80)
    print()
    
    proprietes = []
    for fichier in fichiers:
        try:
            prop = charger_propriete(fichier)
            proprietes.append((fichier, prop))
            print(f"[OK] {fichier} charge avec succes")
        except Exception as e:
            print(f"[ERREUR] Erreur lors du chargement de {fichier}: {e}")
    
    print()
    print("-" * 80)
    print("RÉSUMÉ DES PROPRIÉTÉS")
    print("-" * 80)
    print()
    
    # Analyser chaque propriété
    for fichier, prop in proprietes:
        print(f"\n[FICHIER] {fichier}")
        print(f"   Prix: {prop.get('prix', 'N/A')} $")
        print(f"   Adresse: {prop.get('adresse', 'N/A')}")
        print(f"   Ville: {prop.get('ville', 'N/A')}")
        print(f"   Type: {prop.get('type_propriete', 'N/A')}")
        print(f"   Numéro Centris: {prop.get('numero_centris', 'N/A')}")
        print(f"   Date d'envoi: {prop.get('date_envoi', 'N/A')}")
        print(f"   Statut: {prop.get('statut', 'N/A')}")
        print(f"   Nombre de photos: {prop.get('nb_photos', 'N/A')}")
        
        # Données financières
        if prop.get('donnees_financieres'):
            df = prop['donnees_financieres']
            print(f"   Revenus bruts effectifs: {df.get('revenus_bruts_effectifs', 'N/A')} $")
            print(f"   Revenus nets d'exploitation: {df.get('revenus_nets_exploitation', 'N/A')} $")
        
        # Unités
        if prop.get('unites'):
            unites = prop['unites']
            print(f"   Total résidentiel: {unites.get('total_residentiel', 'N/A')} unités")
            print(f"   Total commercial: {unites.get('total_commercial', 'N/A')} unités")
    
    print()
    print("-" * 80)
    print("DÉTECTION DES DUPLICATIONS")
    print("-" * 80)
    print()
    
    # Vérifier les duplications par numéro Centris
    numeros_centris = defaultdict(list)
    for fichier, prop in proprietes:
        numero = prop.get('numero_centris', 'N/A')
        numeros_centris[numero].append(fichier)
    
    duplications_trouvees = False
    for numero, fichiers_dupliques in numeros_centris.items():
        if len(fichiers_dupliques) > 1:
            duplications_trouvees = True
            print(f"[ATTENTION] DUPLICATION DETECTEE - Numero Centris {numero}:")
            for f in fichiers_dupliques:
                print(f"    - {f}")
    
    if not duplications_trouvees:
        print("[OK] Aucune duplication detectee")
    
    print()
    print("-" * 80)
    print("VALIDATION DES DONNÉES")
    print("-" * 80)
    print()
    
    for fichier, prop in proprietes:
        print(f"\n[VALIDATION] {fichier}:")
        
        # Vérifier les champs obligatoires
        champs_obligatoires = ['prix', 'adresse', 'ville', 'numero_centris']
        champs_manquants = []
        
        for champ in champs_obligatoires:
            if not prop.get(champ):
                champs_manquants.append(champ)
        
        if champs_manquants:
            print(f"   [ATTENTION] Champs manquants: {', '.join(champs_manquants)}")
        else:
            print(f"   [OK] Tous les champs obligatoires sont presents")
        
        # Vérifier la cohérence des données financières
        if prop.get('donnees_financieres'):
            df = prop['donnees_financieres']
            try:
                revenus = float(df.get('revenus_bruts_effectifs', 0) or 0)
                depenses_total = float(df.get('depenses_exploitation', {}).get('total', 0) or 0)
                revenus_nets = float(df.get('revenus_nets_exploitation', 0) or 0)
                
                revenus_nets_calcules = revenus - depenses_total
                
                if abs(revenus_nets_calcules - revenus_nets) > 1:  # Tolérance de 1$
                    print(f"   [ATTENTION] Incoherence dans les calculs financiers:")
                    print(f"       Revenus bruts: {revenus} $")
                    print(f"       Depenses: {depenses_total} $")
                    print(f"       Revenus nets (declare): {revenus_nets} $")
                    print(f"       Revenus nets (calcule): {revenus_nets_calcules:.2f} $")
                else:
                    print(f"   [OK] Coherence des donnees financieres verifiee")
            except (ValueError, TypeError) as e:
                print(f"   [ATTENTION] Erreur lors de la validation financiere: {e}")
        
        # Vérifier les URLs de photos
        if prop.get('photo_urls'):
            nb_urls = len(prop['photo_urls'])
            nb_photos_declare = prop.get('nb_photos', 0)
            if nb_urls != nb_photos_declare:
                print(f"   [ATTENTION] Incoherence: {nb_photos_declare} photos declarees mais {nb_urls} URLs trouvees")
            else:
                print(f"   [OK] Nombre de photos coherent ({nb_urls})")
    
    print()
    print("=" * 80)
    print("FIN DE L'ANALYSE")
    print("=" * 80)

if __name__ == '__main__':
    analyser_proprietes()

