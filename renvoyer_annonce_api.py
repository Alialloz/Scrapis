#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Renvoie une annonce (JSON local) à l'API pour tester et voir les logs API en direct.
Usage: python renvoyer_annonce_api.py [numero_centris]
Exemple: python renvoyer_annonce_api.py 21609160
"""

import json
import sys
import time

try:
    from config_api import API_ENDPOINT, API_HEADERS, API_TIMEOUT
except ImportError:
    print("Erreur: config_api.py introuvable")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("Erreur: pip install requests")
    sys.exit(1)


def _normalize_for_api(data):
    """
    L'API exige des chaînes pour quartier, annee_construction, statut.
    Convertit null en "" pour éviter les erreurs 400.
    """
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


def renvoyer_annonce(numero_centris):
    filename = f"property_{numero_centris}.json"
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Fichier introuvable: {filename}")
        print("Assurez-vous d'avoir ce fichier dans le dossier du projet.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Erreur lecture JSON: {e}")
        sys.exit(1)

    print(f"Fichier charge: {filename}")
    print(f"API: {API_ENDPOINT}")
    print()
    print(">>> Envoi dans 5 secondes - ouvrez vos logs API maintenant <<<")
    time.sleep(5)

    # Normalisation pour l'API (quartier, annee_construction, statut en string, pas null)
    payload = dict(data)
    if "_donnees_liste" in payload and isinstance(payload.get("_donnees_liste"), dict):
        payload["_donnees_liste"] = dict(payload["_donnees_liste"])
    payload = _normalize_for_api(payload)

    try:
        response = requests.post(
            API_ENDPOINT,
            json=payload,
            headers=API_HEADERS,
            timeout=API_TIMEOUT,
        )
    except Exception as e:
        print(f"Erreur requete: {e}")
        sys.exit(1)

    print()
    print("=" * 60)
    print("REPONSE API")
    print("=" * 60)
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print()
    print("Body (texte brut):")
    print(response.text)
    print("=" * 60)

    if response.status_code in (200, 201):
        print("OK - Annonce acceptee par l'API")
    else:
        print(f"KO - L'API a refuse (status {response.status_code})")
        print("Verifiez les logs de votre API pour le detail.")


if __name__ == "__main__":
    numero = sys.argv[1] if len(sys.argv) > 1 else "21609160"
    renvoyer_annonce(numero)
