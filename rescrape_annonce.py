#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Re-scrape une annonce par son numéro Centris pour récupérer les DÉTAILS complets
(quand le JSON local n'a que les infos liste = panneau détail non ouvert au 1er passage).

Usage: python rescrape_annonce.py 21609160 [--envoyer-api]
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


def rescrape_annonce(centris_id, envoyer_api=False):
    """
    Re-scrape une annonce pour obtenir les détails complets.
    Retourne le dict des données ou None en cas d'échec.
    """
    print("=" * 60)
    print(f"RE-SCRAPING ANNONCE No Centris: {centris_id}")
    print("=" * 60)

    scraper = CentrisScraperWithListInfo()
    if not scraper.init_driver():
        print("[ERREUR] Impossible d'initialiser le driver")
        return None

    try:
        print(f"Chargement de la page: {MATRIX_URL}")
        scraper.driver.get(MATRIX_URL)
        time.sleep(5)

        print("Défilement de la page...")
        scraper.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        scraper.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)

        print("Construction du mapping des annonces...")
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

        print(f"{len(centris_to_index)} annonces mappées")

        if centris_id not in centris_to_index:
            print(f"[ERREUR] Annonce {centris_id} non trouvée dans le mapping")
            scraper.close()
            return None

        target_index = centris_to_index[centris_id]
        print(f"Annonce {centris_id} trouvée à l'index {target_index}")
        print()

        property_data = scraper.scrape_property_with_list_info(index=target_index)

        if not property_data:
            print("[ERREUR] Aucune donnée retournée")
            scraper.close()
            return None

        scraper.close()

        # Vérifier si on a bien les détails cette fois
        has_detail = bool(
            property_data.get("donnees_financieres")
            or property_data.get("source")
            or (property_data.get("photo_urls") and len(property_data.get("photo_urls", [])) > 0)
        )
        if not has_detail:
            print("[WARNING] Toujours pas de détails (panneau peut-être pas ouvert)")
        else:
            print("[OK] Détails complets récupérés")

        # Sauvegarder
        filename = f"property_{centris_id}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(property_data, f, indent=2, ensure_ascii=False)
        print(f"Fichier sauvegardé: {filename}")

        # Envoyer à l'API si demandé
        if envoyer_api and has_detail and API_ENDPOINT and API_ENDPOINT != "https://votre-api.com/api/properties":
            try:
                import requests
                payload = dict(property_data)
                if "_donnees_liste" in payload and isinstance(payload.get("_donnees_liste"), dict):
                    payload["_donnees_liste"] = dict(payload["_donnees_liste"])
                payload = _normalize_for_api(payload)
                response = requests.post(API_ENDPOINT, json=payload, headers=API_HEADERS, timeout=API_TIMEOUT)
                if response.status_code in (200, 201):
                    print(f"[OK] Envoyé à l'API (status {response.status_code})")
                else:
                    print(f"[WARNING] API a retourné {response.status_code}: {response.text[:200]}")
            except Exception as e:
                print(f"[ERREUR] Envoi API: {e}")
        elif envoyer_api and not has_detail:
            print("[INFO] Non envoyé à l'API (détails manquants)")

        return property_data

    except Exception as e:
        print(f"[ERREUR] {e}")
        import traceback
        traceback.print_exc()
        try:
            scraper.close()
        except Exception:
            pass
        return None


if __name__ == "__main__":
    centris_id = sys.argv[1] if len(sys.argv) > 1 else "21609160"
    envoyer_api = "--envoyer-api" in sys.argv or "-a" in sys.argv

    if envoyer_api:
        print("Option: envoi à l'API après scrape activé")
    print()

    rescrape_annonce(centris_id, envoyer_api=envoyer_api)
