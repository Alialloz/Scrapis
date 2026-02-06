#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Scrape TOUTES les annonces de la page Matrix, sauvegarde en property_XXXXX.json,
SANS envoyer à l'API et SANS extraire les photos (pour aller plus vite).

Usage: python scraper_toutes_annonces_sans_api.py
"""

import json
import re
import sys
import time

try:
    from config_api import MATRIX_URL
except ImportError:
    print("Erreur: config_api.py introuvable")
    sys.exit(1)

from bs4 import BeautifulSoup
from scraper_with_list_info import CentrisScraperWithListInfo


def main():
    print("=" * 60)
    print("SCRAPING DE TOUTES LES ANNONCES (sans API, sans photos)")
    print("=" * 60)

    scraper = CentrisScraperWithListInfo()
    if not scraper.init_driver():
        print("[ERREUR] Impossible d'initialiser le driver")
        return

    try:
        print(f"\nChargement de la page: {MATRIX_URL}")
        scraper.driver.get(MATRIX_URL)
        time.sleep(5)

        print("Défilement de la page...")
        scraper.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        scraper.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)

        html = scraper.driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        all_text_blocks = soup.find_all(string=re.compile(r"No\s*Centris", re.IGNORECASE))

        centris_to_index = {}
        index = 0
        for text_block in all_text_blocks:
            parent = text_block.parent
            if parent:
                parent_text = parent.get_text()
                match = re.search(r"No\s*Centris\s*[:\-]?\s*(\d+)", parent_text, re.IGNORECASE)
                if match:
                    found_id = match.group(1)
                    if found_id not in centris_to_index:
                        centris_to_index[found_id] = index
                        index += 1

        n = len(centris_to_index)
        if n == 0:
            print("[ERREUR] Aucune annonce trouvée sur la page")
            scraper.close()
            return

        print(f"\n{n} annonce(s) trouvée(s) sur la page. Scraping sans photos, sans envoi API.\n")

        saved = 0
        errors = 0
        for idx in range(n):
            centris_id = next(id for id, i in centris_to_index.items() if i == idx)
            print(f"\n--- Annonce {idx + 1}/{n} : No Centris {centris_id} ---")
            try:
                property_data = scraper.scrape_property_with_list_info(index=idx, skip_photos=True)
                if property_data:
                    filename = f"property_{centris_id}.json"
                    with open(filename, "w", encoding="utf-8") as f:
                        json.dump(property_data, f, indent=2, ensure_ascii=False)
                    saved += 1
                    print(f"[OK] Sauvegardé: {filename}")
                else:
                    errors += 1
                    print(f"[WARNING] Aucune donnée pour {centris_id}")
            except Exception as e:
                errors += 1
                print(f"[ERREUR] {centris_id}: {e}")

            # Pause entre chaque annonce (sauf après la dernière)
            if idx < n - 1:
                time.sleep(2)

        scraper.close()

        print("\n" + "=" * 60)
        print(f"TERMINÉ : {saved} JSON sauvegardé(s), {errors} erreur(s)")
        print("=" * 60)

    except Exception as e:
        print(f"[ERREUR] {e}")
        import traceback
        traceback.print_exc()
        try:
            scraper.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
