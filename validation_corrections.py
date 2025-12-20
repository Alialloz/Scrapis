#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validation des corrections apportées au scraper
"""

import json
import re
from pathlib import Path

def valider_donnees_financieres(property_data):
    """
    Valide la cohérence des données financières
    
    Returns:
        tuple: (est_valide, messages)
    """
    messages = []
    est_valide = True
    
    if not property_data.get('donnees_financieres'):
        return False, ["Aucune donnee financiere trouvee"]
    
    df = property_data['donnees_financieres']
    
    # Vérifier que les champs essentiels sont présents
    if not df.get('revenus_bruts_effectifs'):
        messages.append("[WARNING] Revenus bruts effectifs manquants")
        est_valide = False
    
    if not df.get('revenus_nets_exploitation'):
        messages.append("[WARNING] Revenus nets exploitation manquants")
        est_valide = False
    
    if not df.get('depenses_exploitation', {}).get('total'):
        messages.append("[WARNING] Total depenses manquant")
        est_valide = False
    
    # Vérifier la cohérence des calculs
    try:
        revenus_bruts = float(df.get('revenus_bruts_effectifs', 0) or 0)
        depenses_total = float(df.get('depenses_exploitation', {}).get('total', 0) or 0)
        revenus_nets = float(df.get('revenus_nets_exploitation', 0) or 0)
        
        # Calcul: Revenus nets = Revenus bruts - Dépenses
        revenus_nets_calcules = revenus_bruts - depenses_total
        
        # Tolérance de 5$ pour les arrondis
        if abs(revenus_nets_calcules - revenus_nets) > 5:
            messages.append(f"[ERREUR] Incoherence financiere:")
            messages.append(f"  Revenus bruts: {revenus_bruts:.2f} $")
            messages.append(f"  Depenses totales: {depenses_total:.2f} $")
            messages.append(f"  Revenus nets (declare): {revenus_nets:.2f} $")
            messages.append(f"  Revenus nets (calcule): {revenus_nets_calcules:.2f} $")
            messages.append(f"  Difference: {abs(revenus_nets_calcules - revenus_nets):.2f} $")
            est_valide = False
        else:
            messages.append(f"[OK] Coherence financiere verifiee")
            messages.append(f"  Formule: {revenus_bruts:.0f} - {depenses_total:.0f} = {revenus_nets:.0f} $")
    except (ValueError, TypeError) as e:
        messages.append(f"[ERREUR] Impossible de valider les calculs: {e}")
        est_valide = False
    
    return est_valide, messages


def valider_unicite_annonces():
    """
    Vérifie qu'il n'y a pas de duplications d'annonces
    
    Returns:
        tuple: (est_valide, messages)
    """
    messages = []
    est_valide = True
    
    # Trouver tous les fichiers property_*.json
    fichiers_json = list(Path('.').glob('property_*.json'))
    
    if not fichiers_json:
        return True, ["Aucun fichier property_*.json trouve"]
    
    messages.append(f"[INFO] {len(fichiers_json)} fichiers property_*.json trouves")
    
    # Grouper par numéro Centris
    annonces_par_centris = {}
    
    for fichier in fichiers_json:
        try:
            with open(fichier, 'r', encoding='utf-8') as f:
                data = json.load(f)
                numero_centris = data.get('numero_centris')
                
                if numero_centris:
                    if numero_centris not in annonces_par_centris:
                        annonces_par_centris[numero_centris] = []
                    annonces_par_centris[numero_centris].append(fichier.name)
        except Exception as e:
            messages.append(f"[WARNING] Erreur lecture {fichier.name}: {e}")
    
    # Vérifier les duplications
    duplications = {k: v for k, v in annonces_par_centris.items() if len(v) > 1}
    
    if duplications:
        messages.append(f"\n[ERREUR] {len(duplications)} duplication(s) detectee(s):")
        for numero, fichiers in duplications.items():
            messages.append(f"  Numero Centris {numero} ({len(fichiers)} fichiers):")
            for f in fichiers:
                messages.append(f"    - {f}")
        est_valide = False
    else:
        messages.append(f"[OK] Aucune duplication detectee")
        messages.append(f"  {len(annonces_par_centris)} annonces uniques")
    
    return est_valide, messages


def rapport_validation():
    """
    Génère un rapport de validation complet
    """
    print("=" * 80)
    print("RAPPORT DE VALIDATION DES CORRECTIONS")
    print("=" * 80)
    print()
    
    # Test 1: Vérifier les duplications
    print("TEST 1: VERIFICATION UNICITE DES ANNONCES")
    print("-" * 80)
    est_valide_unicite, messages_unicite = valider_unicite_annonces()
    for msg in messages_unicite:
        print(msg)
    print()
    
    # Test 2: Vérifier la cohérence financière de chaque fichier
    print("TEST 2: VERIFICATION COHERENCE FINANCIERE")
    print("-" * 80)
    
    fichiers_json = list(Path('.').glob('property_*.json'))
    total_fichiers = len(fichiers_json)
    fichiers_valides = 0
    fichiers_invalides = 0
    
    for fichier in fichiers_json:
        try:
            with open(fichier, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            numero_centris = data.get('numero_centris', 'N/A')
            print(f"\nValidation de {fichier.name} (No Centris: {numero_centris}):")
            
            est_valide, messages = valider_donnees_financieres(data)
            
            for msg in messages:
                print(f"  {msg}")
            
            if est_valide:
                fichiers_valides += 1
            else:
                fichiers_invalides += 1
                
        except Exception as e:
            print(f"  [ERREUR] Impossible de valider {fichier.name}: {e}")
            fichiers_invalides += 1
    
    # Résumé final
    print()
    print("=" * 80)
    print("RESUME FINAL")
    print("=" * 80)
    print(f"Total fichiers analyses: {total_fichiers}")
    print(f"Fichiers valides: {fichiers_valides}")
    print(f"Fichiers avec erreurs: {fichiers_invalides}")
    print()
    
    if est_valide_unicite and fichiers_invalides == 0:
        print("[OK] TOUTES LES VALIDATIONS REUSSIES!")
    else:
        print("[ATTENTION] CERTAINES VALIDATIONS ONT ECHOUE")
        print()
        print("ACTIONS RECOMMANDEES:")
        if not est_valide_unicite:
            print("  1. Supprimer les fichiers dupliques")
        if fichiers_invalides > 0:
            print("  2. Re-scraper les proprietes avec des donnees financieres incorrectes")
    
    print("=" * 80)


if __name__ == '__main__':
    rapport_validation()

