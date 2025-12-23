#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test du filtre de date
"""

# Test de comparaison de dates
min_date = '2025-10-29'

test_dates = [
    ('2025-10-28', False),  # Trop ancienne
    ('2025-10-29', True),   # Exactement la limite
    ('2025-10-30', True),   # OK
    ('2025-11-01', True),   # OK
    ('2025-12-15', True),   # OK
    ('2024-12-31', False),  # Trop ancienne
]

print("=" * 80)
print("TEST DU FILTRE DE DATE")
print(f"Date minimale: {min_date}")
print("=" * 80)
print()

for date_test, expected in test_dates:
    result = date_test >= min_date
    status = "[OK]" if result == expected else "[ERREUR]"
    action = "ACCEPTEE" if result else "REJETEE"
    
    print(f"{status} {date_test} -> {action} (attendu: {'ACCEPTEE' if expected else 'REJETEE'})")

print()
print("=" * 80)
print("VERIFICATION DES ANNONCES EXISTANTES")
print("=" * 80)
print()

import json
import glob

fichiers = sorted(glob.glob("property_*.json"))
if fichiers:
    print(f"Analyse de {len(fichiers)} fichiers...\n")
    
    acceptees = []
    rejetees = []
    sans_date = []
    
    for fichier in fichiers:
        try:
            with open(fichier, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            date_envoi = data.get('date_envoi')
            numero = data.get('numero_centris', 'N/A')
            
            if date_envoi:
                if date_envoi >= min_date:
                    acceptees.append((fichier, numero, date_envoi))
                else:
                    rejetees.append((fichier, numero, date_envoi))
            else:
                sans_date.append((fichier, numero))
        except:
            pass
    
    print(f"ANNONCES QUI SERAIENT ACCEPTEES: {len(acceptees)}")
    for f, num, date in acceptees[:5]:
        print(f"  - {num} ({date}) - {f}")
    if len(acceptees) > 5:
        print(f"  ... et {len(acceptees) - 5} autres")
    
    print()
    print(f"ANNONCES QUI SERAIENT REJETEES: {len(rejetees)}")
    for f, num, date in rejetees[:5]:
        print(f"  - {num} ({date}) - {f}")
    if len(rejetees) > 5:
        print(f"  ... et {len(rejetees) - 5} autres")
    
    if sans_date:
        print()
        print(f"ANNONCES SANS DATE: {len(sans_date)}")
        for f, num in sans_date[:5]:
            print(f"  - {num} - {f}")

print()
print("=" * 80)

