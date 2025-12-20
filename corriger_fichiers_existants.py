#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour corriger les données financières dans les fichiers existants
"""

import json
from pathlib import Path
import shutil
from datetime import datetime

def corriger_donnees_financieres(property_data):
    """
    Corrige les données financières en recalculant le total des dépenses
    
    Returns:
        tuple: (data_corrigee, corrections_apportees)
    """
    corrections = []
    
    if not property_data.get('donnees_financieres'):
        return property_data, ["Aucune donnee financiere"]
    
    df = property_data['donnees_financieres']
    depenses = df.get('depenses_exploitation', {})
    
    if not depenses:
        return property_data, ["Aucune depense d'exploitation"]
    
    # Calculer le total correct à partir des dépenses individuelles
    total_calcule = 0
    depenses_comptees = []
    
    for key, value in depenses.items():
        if key != 'total' and value:
            try:
                montant = float(value)
                total_calcule += montant
                depenses_comptees.append(f"{key}: {montant:.0f}")
            except (ValueError, TypeError):
                pass
    
    if depenses_comptees:
        ancien_total = depenses.get('total')
        nouveau_total = str(int(total_calcule))
        
        if ancien_total != nouveau_total:
            corrections.append(f"Correction total depenses: {ancien_total} -> {nouveau_total}")
            corrections.append(f"  Base: {' + '.join(depenses_comptees[:3])}")
            if len(depenses_comptees) > 3:
                corrections.append(f"  ... et {len(depenses_comptees)-3} autres depenses")
            
            # Appliquer la correction
            property_data['donnees_financieres']['depenses_exploitation']['total'] = nouveau_total
        else:
            corrections.append(f"Total deja correct: {nouveau_total}")
    
    # Vérifier la cohérence finale
    try:
        revenus_bruts = float(df.get('revenus_bruts_effectifs', 0) or 0)
        depenses_total = float(property_data['donnees_financieres']['depenses_exploitation'].get('total', 0) or 0)
        revenus_nets = float(df.get('revenus_nets_exploitation', 0) or 0)
        
        revenus_nets_calcules = revenus_bruts - depenses_total
        
        if abs(revenus_nets_calcules - revenus_nets) <= 5:
            corrections.append(f"[OK] Coherence verifiee: {revenus_bruts:.0f} - {depenses_total:.0f} = {revenus_nets:.0f}")
        else:
            corrections.append(f"[ATTENTION] Encore une incoherence:")
            corrections.append(f"  {revenus_bruts:.0f} - {depenses_total:.0f} = {revenus_nets_calcules:.0f}")
            corrections.append(f"  Mais revenus_nets = {revenus_nets:.0f}")
    except:
        pass
    
    return property_data, corrections


def corriger_tous_les_fichiers():
    """
    Corrige tous les fichiers property_*.json
    """
    print("=" * 80)
    print("CORRECTION DES FICHIERS EXISTANTS")
    print("=" * 80)
    print()
    
    # Trouver tous les fichiers
    fichiers_json = list(Path('.').glob('property_*.json'))
    
    if not fichiers_json:
        print("Aucun fichier property_*.json trouve")
        return
    
    print(f"[INFO] {len(fichiers_json)} fichiers trouves\n")
    
    # Créer un dossier de backup
    backup_dir = Path(f'backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
    backup_dir.mkdir(exist_ok=True)
    print(f"[BACKUP] Sauvegarde dans: {backup_dir}/\n")
    
    fichiers_corriges = 0
    fichiers_inchanges = 0
    fichiers_erreur = 0
    
    for fichier in fichiers_json:
        print(f"Traitement de {fichier.name}:")
        
        try:
            # Charger le fichier
            with open(fichier, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Faire un backup
            shutil.copy2(fichier, backup_dir / fichier.name)
            
            # Corriger
            data_corrigee, corrections = corriger_donnees_financieres(data)
            
            # Afficher les corrections
            for correction in corrections:
                print(f"  {correction}")
            
            # Sauvegarder le fichier corrigé
            if corrections and any('Correction' in c for c in corrections):
                with open(fichier, 'w', encoding='utf-8') as f:
                    json.dump(data_corrigee, f, indent=2, ensure_ascii=False)
                fichiers_corriges += 1
                print(f"  [OK] Fichier corrige et sauvegarde\n")
            else:
                fichiers_inchanges += 1
                print(f"  [INFO] Aucune correction necessaire\n")
                
        except Exception as e:
            print(f"  [ERREUR] {e}\n")
            fichiers_erreur += 1
    
    # Résumé
    print("=" * 80)
    print("RESUME")
    print("=" * 80)
    print(f"Fichiers corriges: {fichiers_corriges}")
    print(f"Fichiers inchanges: {fichiers_inchanges}")
    print(f"Erreurs: {fichiers_erreur}")
    print(f"Total: {len(fichiers_json)}")
    print()
    print(f"[BACKUP] Fichiers originaux sauvegardes dans: {backup_dir}/")
    print("=" * 80)


if __name__ == '__main__':
    corriger_tous_les_fichiers()

