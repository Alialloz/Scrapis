#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Configuration centralisée du système de logging pour le Scraper Centris
"""

import logging
import logging.handlers
import os
from datetime import datetime

# Dossier pour les logs
LOG_DIR = "logs"

# Créer le dossier logs s'il n'existe pas
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Configuration des niveaux de log
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

# Format des logs
LOG_FORMAT = '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Configuration de la rotation des logs
MAX_BYTES = 10 * 1024 * 1024  # 10 MB par fichier
BACKUP_COUNT = 7  # Garder 7 fichiers de backup (environ 1 semaine)


def setup_logger(name='scraper', level='INFO', log_to_file=True, log_to_console=True):
    """
    Configure et retourne un logger avec rotation de fichiers
    
    Args:
        name: Nom du logger (ex: 'scraper', 'monitor', 'api')
        level: Niveau de log ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        log_to_file: Si True, écrit dans un fichier avec rotation
        log_to_console: Si True, affiche aussi dans la console
    
    Returns:
        Logger configuré
    """
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVELS.get(level, logging.INFO))
    
    # Éviter les handlers dupliqués
    if logger.handlers:
        return logger
    
    # Formateur pour tous les handlers
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    
    # Handler pour fichier avec rotation
    if log_to_file:
        log_file = os.path.join(LOG_DIR, f'{name}.log')
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=MAX_BYTES,
            backupCount=BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)  # Tout capturer dans le fichier
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Handler pour console
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)  # Moins verbeux en console
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


def setup_error_logger(name='scraper_errors'):
    """
    Configure un logger spécifique pour les erreurs critiques
    
    Returns:
        Logger configuré pour les erreurs uniquement
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.ERROR)
    
    if logger.handlers:
        return logger
    
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s',
        DATE_FORMAT
    )
    
    error_file = os.path.join(LOG_DIR, 'errors.log')
    error_handler = logging.handlers.RotatingFileHandler(
        error_file,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    return logger


def log_scraping_stats(logger, stats_dict):
    """
    Log les statistiques de scraping de manière structurée
    
    Args:
        logger: Logger à utiliser
        stats_dict: Dictionnaire contenant les statistiques
    """
    logger.info("="*80)
    logger.info("STATISTIQUES DE SCRAPING")
    logger.info("="*80)
    
    for key, value in stats_dict.items():
        logger.info(f"  {key}: {value}")
    
    logger.info("="*80)


def log_extraction_result(logger, property_data, success=True):
    """
    Log le résultat d'une extraction de propriété
    
    Args:
        logger: Logger à utiliser
        property_data: Données extraites
        success: Si l'extraction a réussi
    """
    if success:
        logger.info(f"✓ Extraction réussie - Centris #{property_data.get('numero_centris', 'N/A')}")
        logger.debug(f"  Adresse: {property_data.get('adresse', 'N/A')}")
        logger.debug(f"  Prix: {property_data.get('prix', 'N/A')} $")
        logger.debug(f"  Photos: {property_data.get('nb_photos', 0)}")
        logger.debug(f"  Source: {property_data.get('source', 'N/A')}")
    else:
        logger.error(f"✗ Échec extraction - Centris #{property_data.get('numero_centris', 'N/A')}")


# Exemple d'utilisation
if __name__ == "__main__":
    # Logger principal
    logger = setup_logger('test', level='DEBUG')
    
    logger.debug("Message de debug (développement)")
    logger.info("Message d'information (normal)")
    logger.warning("Message d'avertissement")
    logger.error("Message d'erreur")
    logger.critical("Message critique")
    
    # Logger d'erreurs
    error_logger = setup_error_logger()
    error_logger.error("Ceci est une erreur capturée")
    
    # Stats exemple
    stats = {
        'Nouvelles annonces': 5,
        'Annonces scrapées': 5,
        'Erreurs': 0,
        'Durée totale': '3m 45s'
    }
    log_scraping_stats(logger, stats)
    
    print(f"\nLogs sauvegardés dans: {os.path.abspath(LOG_DIR)}/")
