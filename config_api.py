#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Configuration de l'API pour le monitoring Centris
À CONFIGURER AVANT LE DÉPLOIEMENT
"""

# ============================================================================
# CONFIGURATION API - MODIFIER ICI
# ============================================================================

# URL de votre API (endpoint pour recevoir les données des propriétés)
API_ENDPOINT = "https://api.rayharvey.ca/robot/api/scraping"  # ← MODIFIER ICI

# Headers HTTP pour l'API (optionnel)
API_HEADERS = {
    'Content-Type': 'application/json',
    'User-Agent': 'CentrisMonitor/1.0',
    # Décommenter et configurer si votre API nécessite une authentification :
    # 'Authorization': 'Bearer VOTRE_TOKEN_ICI',
    # 'X-API-Key': 'votre_cle_api',
}

# Timeout pour les requêtes API (en secondes)
API_TIMEOUT = 30

# ============================================================================
# ÉCHANGES AVEC LE CRM (Analyse IA)
# ============================================================================
# Le robot n'ouvre aucun port : il envoie sa liste d'annonces Centris à l'API
# et vient y chercher les tâches demandées depuis le CRM (Outils > Analyse IA).
# La clé partagée (ROBOT_API_KEY de l'API) se lit dans la variable
# d'environnement ROBOT_API_KEY, ou dans le fichier robot_api_key.txt placé à
# côté de ce fichier (jamais commité).
import os as _os

ROBOT_API_BASE = API_ENDPOINT.rsplit('/', 1)[0]  # https://.../robot/api


def _read_robot_api_key():
    key = _os.environ.get('ROBOT_API_KEY', '').strip()
    if key:
        return key
    path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'robot_api_key.txt')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except OSError:
        return ''


ROBOT_API_KEY = _read_robot_api_key()

# Fréquence de vérification des tâches du CRM (en secondes)
JOB_POLL_INTERVAL = 60

# ============================================================================
# CONFIGURATION MONITORING
# ============================================================================

# Pages Matrix Centris à surveiller (une alerte par catégorie et par région).
# L'ancienne page combinée « Alerte - 5+ Qc » n'est plus lue.
_MATRIX_EMAIL = "Y2JlYXVkZXRAcmF5aGFydmV5LmNh"
_MATRIX_PORTAL = "https://matrix.centris.ca/Matrix/Public/Portal.aspx"

def _matrix_url(portal_id):
    return f"{_MATRIX_PORTAL}?ID={portal_id}&eml={_MATRIX_EMAIL}&L=2"

MATRIX_SOURCES = [
    {"name": "3-4 Capitale-Nationale", "url": _matrix_url("0-3755465862-10")},
    {"name": "3-4 Chaudière-Appalaches", "url": _matrix_url("0-3755467574-10")},
    {"name": "5+ Capitale-Nationale", "url": _matrix_url("0-3755464753-10")},
    {"name": "5+ Chaudière-Appalaches", "url": _matrix_url("0-3755468641-10")},
]

# Conservé pour les scripts qui n'utilisent qu'une page.
MATRIX_URL = MATRIX_SOURCES[0]["url"]

# Intervalle de monitoring (en minutes)
MONITORING_INTERVAL = 60  # 1 heure

# Fichier de stockage des IDs scrapés
STORAGE_FILE = 'scraped_properties.json'

# ============================================================================
# CONFIGURATION AVANCÉE (optionnel)
# ============================================================================

# Délai entre chaque scraping d'annonce (en secondes)
DELAY_BETWEEN_LISTINGS = 5

# Mode headless (True = pas d'interface graphique)
HEADLESS_MODE = True

# Activer les logs détaillés
VERBOSE_LOGS = True

# Sauvegarder les JSON localement (en plus de l'envoi à l'API)
SAVE_JSON_LOCALLY = True

# Nombre maximum d'annonces à scraper par cycle (0 = illimité)
MAX_LISTINGS_PER_CYCLE = 0  # 0 = toutes les nouvelles annonces

# ============================================================================
# NETTOYAGE AUTOMATIQUE DES FICHIERS JSON
# ============================================================================

# Activer la suppression automatique des JSON locaux
AUTO_CLEANUP_ENABLED = True  # True = supprimer automatiquement les JSON

# Jour de la semaine pour le nettoyage (0=Lundi, 6=Dimanche)
CLEANUP_DAY = 6  # Dimanche

# Heure du nettoyage (0-23)
CLEANUP_HOUR = 23  # 23h00 (11 PM)

# Garder les fichiers de cette semaine (True) ou tout supprimer (False)
KEEP_CURRENT_WEEK = True  # True = garder les JSON de la semaine en cours

# Fichiers à ne jamais supprimer (CRITIQUE !)
PROTECTED_FILES = [
    'scraped_properties.json',       # ⚠️ CRITIQUE - Liste des numéros Centris déjà scrapés
    'monitoring_stats.json',          # Statistiques de monitoring
    'property_with_list_info.json'    # Fichier de test
]

# Créer une sauvegarde du fichier scraped_properties.json
AUTO_BACKUP_SCRAPED_IDS = True  # Sauvegarde automatique avant nettoyage

