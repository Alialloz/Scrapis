#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Scrape UNE annonce puis envoie-la à l'API (envoi unique).

Usage:
  python envoyer_une_annonce.py              → scrape la 1ère annonce, envoie à l'API
  python envoyer_une_annonce.py --index 1   → scrape la 2e annonce (index 1), envoie à l'API
  python envoyer_une_annonce.py 21609160    → scrape l'annonce 21609160, envoie à l'API
"""

import json
import re
import sys
import time

try:
    from config_api import MATRIX_URL, API_ENDPOINT, API_HEADERS, API_TIMEOUT
except ImportError:
    print("Erreur: config_api.py introuvable")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("Erreur: pip install requests")
    sys.exit(1)

from bs4 import BeautifulSoup
from scraper_with_list_info import CentrisScraperWithListInfo


def _normalize_for_api(data):
    """Convertit null en "" pour quartier, annee_construction, statut (exigence API)."""
    for key in ("quartier", "annee_construction", "statut"):
        if key in data and data[key] is None:
            data[key] = ""
        elif key in data and not isinstance(data[key], str):
            data[key] = str(data[key]) if data[key] is not None else ""
    if "_donnees_liste" in data and isinstance(data.get("_donnees_liste"), dict):
        for key in ("quartier", "annee_construction", "statut"):
            if key in data["_donnees_liste"] and data["_donnees_liste"][key] is None:
                data["_donnees_liste"][key] = ""
            elif key in data["_donnees_liste"] and not isinstance(data["_donnees_liste"][key], str):
                val = data["_donnees_liste"][key]
                data["_donnees_liste"][key] = str(val) if val is not None else ""
    return data


def envoyer_une_annonce(centris_id=None, index_page=None):
    """
    Scrape une annonce et l'envoie à l'API.
    centris_id: numéro Centris (ex. 21609160), ou None pour utiliser index_page.
    index_page: index sur la page (0=1ère, 1=2e, ...), utilisé si centris_id est None.
    """
    scraper = CentrisScraperWithListInfo()
    if not scraper.init_driver():
        print("[ERREUR] Impossible d'initialiser le driver")
        return

    try:
        print("Chargement de la page Matrix...")
        scraper.driver.get(MATRIX_URL)
        time.sleep(5)

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

        if not centris_to_index:
            print("[ERREUR] Aucune annonce trouvée sur la page")
            scraper.close()
            return

        # Déterminer quelle annonce scraper
        if centris_id is not None:
            centris_id = str(centris_id)
            if centris_id not in centris_to_index:
                print(f"[ERREUR] Annonce {centris_id} non trouvée sur la page")
                scraper.close()
                return
            target_index = centris_to_index[centris_id]
        else:
            # Par index sur la page (0=1ère, 1=2e, ...)
            idx_wanted = 0 if index_page is None else int(index_page)
            if idx_wanted < 0 or idx_wanted >= len(centris_to_index):
                print(f"[ERREUR] Index {idx_wanted} invalide (page a {len(centris_to_index)} annonces)")
                scraper.close()
                return
            centris_id = next(id for id, idx in centris_to_index.items() if idx == idx_wanted)
            target_index = idx_wanted
            print(f"Annonce à l'index {idx_wanted} (N°{idx_wanted + 1} sur la page): No Centris {centris_id}")

        print(f"Scraping annonce No Centris {centris_id} (index {target_index})...")
        print()

        property_data = scraper.scrape_property_with_list_info(index=target_index)
        scraper.close()

        if not property_data:
            print("[ERREUR] Aucune donnée extraite")
            return

        has_detail = bool(
            property_data.get("donnees_financieres")
            or property_data.get("source")
            or (property_data.get("photo_urls") and len(property_data.get("photo_urls", [])) > 0)
        )
        if not has_detail:
            print("[WARNING] Détails manquants (panneau peut-être pas ouvert) - envoi quand même si configuré.")

        # Sauvegarder localement
        filename = f"property_{centris_id}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(property_data, f, indent=2, ensure_ascii=False)
        print(f"Sauvegardé: {filename}")
        print()

        # Envoyer à l'API
        if not API_ENDPOINT or API_ENDPOINT == "https://votre-api.com/api/properties":
            print("API non configurée dans config_api.py - pas d'envoi.")
            return

        payload = dict(property_data)
        if "_donnees_liste" in payload and isinstance(payload.get("_donnees_liste"), dict):
            payload["_donnees_liste"] = dict(payload["_donnees_liste"])
        payload = _normalize_for_api(payload)

        print(f"Envoi à l'API: {API_ENDPOINT}")
        response = requests.post(API_ENDPOINT, json=payload, headers=API_HEADERS, timeout=API_TIMEOUT)
        print(f"Réponse: {response.status_code}")
        if response.status_code in (200, 201):
            print("OK - Annonce envoyée avec succès.")
        else:
            print(f"Body: {response.text[:300]}")
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
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--index" in sys.argv:
        try:
            i = sys.argv.index("--index")
            index_page = int(sys.argv[i + 1])
        except (ValueError, IndexError):
            index_page = 1
        centris_id = None
    else:
        index_page = None
        centris_id = args[0] if args else None
    envoyer_une_annonce(centris_id=centris_id, index_page=index_page)
