#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Corrige les annonces du robot qui n'ont qu'une seule photo.

Pour chaque annonce : retrouve sa page Matrix, ré-extrait toutes les photos,
puis demande à l'API de remplacer les photos du mandat « Test » correspondant
(POST /robot/api/refresh-photos).

Usage :
    python3.12 corriger_photos.py --dry-run          # liste seulement
    python3.12 corriger_photos.py                    # corrige toutes les annonces à 1 photo
    python3.12 corriger_photos.py 27619960 22291789  # corrige ces numéros seulement

Les annonces candidates sont les fichiers property_*.json locaux dont
photo_urls contient 0 ou 1 URL. Arrêter le service avant (systemctl stop
scraper-centris) pour éviter deux navigateurs en même temps.
"""

import glob
import json
import os
import sys
import time

import requests

from config_api import API_ENDPOINT, API_HEADERS, API_TIMEOUT, MATRIX_SOURCES
from scraper_monitor import CentrisMonitor
from scraper_with_list_info import CentrisScraperWithListInfo

REFRESH_ENDPOINT = API_ENDPOINT.rsplit('/', 1)[0] + '/refresh-photos'
DELAY_BETWEEN_LISTINGS = 5


def find_candidates():
    """Numéros Centris dont le JSON local a 0 ou 1 photo."""
    candidates = []
    for path in glob.glob('property_*.json'):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"[WARN] Lecture impossible {path}: {e}")
            continue
        centris_id = str(data.get('numero_centris') or path[len('property_'):-len('.json')])
        if len(data.get('photo_urls') or []) <= 1:
            candidates.append(centris_id)
    return sorted(set(candidates))


def refresh_one(centris_id):
    """Retourne (ok, message)."""
    for source in MATRIX_SOURCES:
        monitor = CentrisMonitor(url=source['url'], storage_file=os.devnull)
        scraper = CentrisScraperWithListInfo()
        scraper.init_driver()
        try:
            scraper.driver.get(monitor.url)
            time.sleep(5)
            if not monitor.load_results(scraper.driver, centris_id):
                continue
            print(f"  Trouvée sur la page {source['name']}")
            if not scraper.click_on_property_by_centris_id(centris_id):
                return False, "panneau de détail non ouvert"
            time.sleep(3)
            photo_urls = scraper.extract_photo_urls()
        finally:
            try:
                scraper.close()
            except Exception:
                pass

        if len(photo_urls) <= 1:
            return False, f"seulement {len(photo_urls)} photo extraite, rien envoyé"

        response = requests.post(
            REFRESH_ENDPOINT,
            json={'numero_centris': centris_id, 'photo_urls': photo_urls},
            headers=API_HEADERS,
            timeout=max(API_TIMEOUT, 300),
        )
        if response.status_code not in (200, 201):
            return False, f"API {response.status_code}: {response.text[:200]}"
        body = response.json()
        if not body.get('success'):
            return False, body.get('message', 'refus de l\'API')

        # Garder le JSON local à jour
        path = f"property_{centris_id}.json"
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                data['photo_urls'] = photo_urls
                data['nb_photos'] = len(photo_urls)
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"  [WARN] JSON local non mis à jour: {e}")

        saved = (body.get('data') or {}).get('saved')
        return True, f"{len(photo_urls)} photos extraites, {saved} enregistrées"

    return False, "introuvable sur les 4 pages Matrix (annonce retirée ?)"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    dry_run = '--dry-run' in sys.argv

    ids = args or find_candidates()
    print(f"{len(ids)} annonce(s) à corriger")
    for centris_id in ids:
        print(f"  - {centris_id}")
    if dry_run or not ids:
        return

    ok_count = 0
    failures = []
    for idx, centris_id in enumerate(ids, 1):
        print(f"[{idx}/{len(ids)}] Annonce {centris_id}")
        try:
            ok, message = refresh_one(centris_id)
        except Exception as e:
            ok, message = False, f"erreur: {e}"
        print(f"  {'OK' if ok else 'ÉCHEC'} — {message}")
        if ok:
            ok_count += 1
        else:
            failures.append((centris_id, message))
        time.sleep(DELAY_BETWEEN_LISTINGS)

    print(f"\nTerminé : {ok_count}/{len(ids)} corrigées")
    for centris_id, message in failures:
        print(f"  ÉCHEC {centris_id}: {message}")


if __name__ == '__main__':
    main()
