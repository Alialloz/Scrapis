#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Réinitialise le scraping : supprime tous les property_*.json et vide la liste
des annonces déjà scrapées (scraped_properties.json) pour relancer de zéro.

Usage: python reset_scraping.py
"""

import json
import os
import glob

# Dossier du projet (où se trouve le script)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

def main():
    # 1. Supprimer tous les property_*.json
    pattern = "property_*.json"
    deleted = 0
    for filepath in glob.glob(pattern):
        try:
            os.remove(filepath)
            deleted += 1
            print(f"  Supprimé: {filepath}")
        except Exception as e:
            print(f"  Erreur {filepath}: {e}")
    
    print(f"\n{deleted} fichier(s) property_*.json supprimé(s).")
    
    # 2. Réinitialiser scraped_properties.json (liste vide = aucune annonce déjà scrapée)
    storage_file = "scraped_properties.json"
    try:
        with open(storage_file, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=2, ensure_ascii=False)
        print(f"\n{storage_file} réinitialisé (liste vide).")
    except Exception as e:
        print(f"\nErreur écriture {storage_file}: {e}")
        return
    
    print("\n" + "=" * 60)
    print("RÉINITIALISATION TERMINÉE - Vous pouvez relancer le scraping.")
    print("=" * 60)


if __name__ == "__main__":
    main()
