#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de nettoyage manuel des fichiers JSON
Utilisez ce script pour forcer un nettoyage immédiat
"""

import os
import glob
from datetime import datetime, timedelta

try:
    from config_api import KEEP_CURRENT_WEEK, PROTECTED_FILES
except ImportError:
    KEEP_CURRENT_WEEK = True
    PROTECTED_FILES = ['scraped_properties.json', 'monitoring_stats.json', 'property_with_list_info.json']

print("="*80)
print("NETTOYAGE MANUEL DES FICHIERS JSON")
print("="*80)

# Trouver tous les fichiers property_*.json
pattern = "property_*.json"
json_files = glob.glob(pattern)

if not json_files:
    print("\n[INFO] Aucun fichier JSON trouve")
    exit(0)

print(f"\n[INFO] {len(json_files)} fichiers JSON trouves")

# Calculer la date limite
now = datetime.now()
if KEEP_CURRENT_WEEK:
    days_since_monday = now.weekday()
    week_start = now - timedelta(days=days_since_monday)
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    print(f"[INFO] Conservation des fichiers depuis le {week_start.strftime('%Y-%m-%d')}")
else:
    print(f"[INFO] Suppression de TOUS les fichiers JSON")

# Demander confirmation
print(f"\nFichiers qui seront supprimes:")
to_delete = []

for json_file in json_files:
    if json_file in PROTECTED_FILES:
        continue
    
    try:
        file_time = datetime.fromtimestamp(os.path.getmtime(json_file))
        
        should_delete = False
        if KEEP_CURRENT_WEEK:
            if file_time < week_start:
                should_delete = True
        else:
            should_delete = True
        
        if should_delete:
            to_delete.append(json_file)
            print(f"  - {json_file} (date: {file_time.strftime('%Y-%m-%d %H:%M')})")
    except:
        pass

if not to_delete:
    print("  Aucun fichier a supprimer")
    exit(0)

print(f"\nTotal: {len(to_delete)} fichiers seront supprimes")
response = input("\nConfirmez-vous la suppression ? (o/n) : ")

if response.lower() != 'o':
    print("[INFO] Operation annulee")
    exit(0)

# Supprimer les fichiers
deleted_count = 0
for json_file in to_delete:
    try:
        os.remove(json_file)
        deleted_count += 1
        print(f"[OK] {json_file} supprime")
    except Exception as e:
        print(f"[ERREUR] Impossible de supprimer {json_file}: {e}")

print(f"\n[SUCCESS] {deleted_count} fichiers supprimes avec succes!")


