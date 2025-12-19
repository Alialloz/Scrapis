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
# CONFIGURATION MONITORING
# ============================================================================

# URL de la page Matrix Centris à surveiller
MATRIX_URL = "https://matrix.centris.ca/Matrix/Public/Portal.aspx?ID=0-3319143035-10&eml=Y2JlYXVkZXRAcmF5aGFydmV5LmNh&L=2"

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

