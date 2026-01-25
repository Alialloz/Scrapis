#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test du système de logging
"""

import sys
import os

# Ajouter le dossier parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logger_config import setup_logger, log_scraping_stats, log_extraction_result
import time

def test_logging():
    """Test du système de logging"""
    
    # Configurer le logger
    logger = setup_logger('test_scraper', level='DEBUG')
    
    logger.info("="*80)
    logger.info("TEST DU SYSTÈME DE LOGGING")
    logger.info("="*80)
    
    # Test des différents niveaux
    logger.debug("Message de debug - utile en développement")
    logger.info("Message d'information - normal")
    logger.warning("Message d'avertissement - attention!")
    logger.error("Message d'erreur - quelque chose ne va pas")
    
    # Simuler une extraction
    logger.info("\nSimulation d'une extraction...")
    time.sleep(1)
    
    property_data = {
        'numero_centris': '24886125',
        'adresse': '390 Rue des Lilas E.',
        'prix': '699000',
        'nb_photos': 48,
        'source': 'RE/MAX 1ER CHOIX INC., Agence immobilière'
    }
    
    log_extraction_result(logger, property_data, success=True)
    
    # Simuler des stats
    stats = {
        'Nouvelles annonces': 5,
        'Annonces scrapées': 5,
        'Erreurs': 0,
        'Durée totale': '3m 45s',
        'Photos moyennes': 35.2
    }
    
    log_scraping_stats(logger, stats)
    
    # Test d'erreur avec traceback
    try:
        result = 1 / 0
    except Exception as e:
        logger.error(f"Erreur capturée: {e}", exc_info=True)
    
    logger.info("\n✅ Test terminé! Consultez les logs dans: logs/test_scraper.log")
    logger.info("Analysez avec: python analyze_logs.py")

if __name__ == "__main__":
    test_logging()
