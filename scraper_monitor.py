#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Scraper Monitor - Détecte et scrape les nouvelles annonces Centris
"""

import time
import json
import os
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import requests
from bs4 import BeautifulSoup
from scraper_with_list_info import CentrisScraperWithListInfo
from logger_config import setup_logger, log_extraction_result, log_scraping_stats

# Configuration du logger
logger = setup_logger('monitor', level='INFO')


class CentrisMonitor:
    """
    Moniteur pour détecter les nouvelles annonces et les scraper automatiquement
    """
    
    def __init__(self, url, api_endpoint=None, storage_file='scraped_properties.json', min_date='2025-12-20', skip_photos=False):
        """
        Initialise le moniteur
        
        Args:
            url: URL de la page Matrix Centris à surveiller
            api_endpoint: URL de l'API où envoyer les données (optionnel)
            storage_file: Fichier pour stocker les numéros Centris déjà scrapés
            min_date: Date minimale pour les annonces (format: YYYY-MM-DD)
            skip_photos: Si True, ne pas extraire les URLs des photos (plus rapide)
        """
        self.url = url
        self.api_endpoint = api_endpoint
        self.storage_file = storage_file
        self.min_date = min_date
        self.skip_photos = skip_photos
        self.scraped_ids = self.load_scraped_ids()
        logger.info(f"Filtre de date actif: annonces >= {self.min_date}")
        if self.skip_photos:
            logger.info("Mode skip_photos activé: extraction des photos désactivée")
        
    def load_scraped_ids(self):
        """
        Charge la liste des numéros Centris déjà scrapés
        
        Returns:
            dict: Dictionnaire {numero_centris: date_scraping}
        """
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # S'assurer que c'est un dict, pas une liste
                    if isinstance(data, list):
                        logger.warning(f"Format liste détecté dans {self.storage_file}, conversion en dict")
                        data = {str(sid): "" for sid in data}
                    elif not isinstance(data, dict):
                        logger.warning(f"Format inattendu dans {self.storage_file}, réinitialisation")
                        data = {}
                    logger.info(f"{len(data)} annonces déjà scrapées chargées depuis {self.storage_file}")
                    return data
            except Exception as e:
                logger.warning(f"Erreur lecture {self.storage_file}: {e}")
                return {}
        else:
            logger.info(f"Nouveau fichier {self.storage_file} sera créé")
            return {}
    
    def save_scraped_ids(self):
        """
        Sauvegarde la liste des numéros Centris scrapés
        """
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.scraped_ids, f, indent=2, ensure_ascii=False)
            logger.debug(f"{len(self.scraped_ids)} IDs sauvegardés dans {self.storage_file}")
        except Exception as e:
            logger.error(f"Impossible de sauvegarder {self.storage_file}: {e}")
    
    def get_all_listing_ids(self):
        """
        Récupère tous les numéros Centris disponibles sur la page
        
        Returns:
            list: Liste des numéros Centris trouvés
        """
        logger.info("=== RÉCUPÉRATION DE TOUS LES NUMÉROS CENTRIS ===")
        
        # Configurer Chrome (même config que scraper_with_list_info.py)
        import platform
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Spécifier le chemin Chrome uniquement sur Linux
        if platform.system() == 'Linux':
            chrome_options.binary_location = "/usr/bin/google-chrome"

        try:
            driver = webdriver.Chrome(options=chrome_options)
        except:
            # Fallback avec service explicite
            from selenium.webdriver.chrome.service import Service as ChromeService
            service = ChromeService()
            driver = webdriver.Chrome(service=service, options=chrome_options)
        
        listing_ids = []
        
        try:
            logger.info(f"Chargement de la page: {self.url}")
            driver.get(self.url)
            time.sleep(5)
            
            # Faire défiler pour charger toutes les annonces
            logger.info("Défilement pour charger toutes les annonces...")
            last_height = driver.execute_script("return document.body.scrollHeight")
            scroll_attempts = 0
            max_scrolls = 10
            
            while scroll_attempts < max_scrolls:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
                scroll_attempts += 1
                logger.debug(f"Scroll {scroll_attempts}/{max_scrolls}...")
            
            # Extraire tous les numéros Centris
            import re
            page_source = driver.page_source
            
            # Pattern pour trouver "No Centris : XXXXXXXX"
            pattern = r'No Centris\s*:\s*(\d+)'
            matches = re.findall(pattern, page_source)
            
            listing_ids = list(set(matches))  # Enlever les doublons
            
            logger.info(f"✓ {len(listing_ids)} annonces trouvées sur la page")
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des IDs: {e}", exc_info=True)
        finally:
            driver.quit()
        
        return listing_ids
    
    def identify_new_listings(self, current_ids):
        """
        Identifie les nouvelles annonces (non encore scrapées)
        
        Args:
            current_ids: Liste des IDs actuellement sur la page
            
        Returns:
            list: Liste des nouveaux IDs à scraper
        """
        new_ids = [id for id in current_ids if id not in self.scraped_ids]
        
        if new_ids:
            logger.info(f"{len(new_ids)} nouvelle(s) annonce(s) détectée(s):")
            for id in new_ids:
                logger.info(f"  - No Centris: {id}")
        else:
            logger.info(f"Aucune nouvelle annonce (toutes les {len(current_ids)} annonces ont déjà été scrapées)")
        
        return new_ids
    
    def send_to_api(self, property_data):
        """
        Envoie les données d'une propriété à l'API
        
        Args:
            property_data: Dictionnaire contenant les données de la propriété
            
        Returns:
            bool: True si l'envoi a réussi, False sinon
        """
        if not self.api_endpoint:
            logger.info("Pas d'endpoint API configuré, données non envoyées")
            return True
        
        try:
            centris_id = property_data.get('numero_centris', 'N/A')
            logger.info(f"Envoi des données à l'API - Centris #{centris_id}")
            
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'CentrisMonitor/1.0'
            }
            
            response = requests.post(
                self.api_endpoint,
                json=property_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"✓ Données envoyées avec succès (Status: {response.status_code}) - Centris #{centris_id}")
                return True
            else:
                logger.warning(f"API a retourné le status {response.status_code} - Centris #{centris_id}")
                logger.debug(f"Réponse: {response.text[:200]}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error(f"Timeout lors de l'envoi à l'API - Centris #{centris_id}")
            return False
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi à l'API - Centris #{centris_id}: {e}")
            return False
    
    def scrape_new_listing(self, centris_id):
        """
        Scrape une nouvelle annonce par son numéro Centris.
        Utilise la recherche directe par Centris ID (pas de mapping par index).
        
        Args:
            centris_id: Numéro Centris de l'annonce
            
        Returns:
            dict: Données de la propriété ou None si erreur
        """
        logger.info("="*80)
        logger.info(f"SCRAPING DE L'ANNONCE No Centris: {centris_id}")
        logger.info("="*80)
        
        try:
            # Utiliser le scraper existant
            scraper = CentrisScraperWithListInfo()
            scraper.init_driver()
            
            # Charger la page
            logger.info("Chargement de la page...")
            scraper.driver.get(self.url)
            time.sleep(5)
            
            # Faire défiler pour charger toutes les annonces
            logger.info("Défilement de la page...")
            scraper.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            scraper.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            # ÉTAPE 1: Extraire d'abord les infos de la LISTE (rapide, pas de clic)
            logger.info(f"Extraction rapide des infos liste pour Centris ID: {centris_id}")
            list_info = scraper.extract_info_from_list_by_centris_id(centris_id)
            
            # ÉTAPE 2: FILTRE DE DATE AVANT le scraping complet (économise le temps des photos)
            date_envoi = list_info.get('date_envoi')
            if date_envoi:
                try:
                    date_trop_ancienne = date_envoi < self.min_date
                except Exception as e:
                    logger.warning(f"Impossible de comparer la date: {e}")
                    date_trop_ancienne = False
                
                if date_trop_ancienne:
                    logger.info(f"Annonce trop ancienne: {date_envoi} < {self.min_date} (filtré AVANT scraping détail)")
                    logger.info(f"Annonce {centris_id} ignorée")
                    
                    # Marquer comme scrapée pour éviter la boucle infinie
                    try:
                        if isinstance(self.scraped_ids, list):
                            self.scraped_ids = {str(sid): "" for sid in self.scraped_ids}
                        self.scraped_ids[centris_id] = datetime.now().isoformat()
                        self.save_scraped_ids()
                        logger.info(f"✓ Annonce {centris_id} marquée comme scrapée (filtrée)")
                    except Exception as e:
                        logger.warning(f"Erreur sauvegarde scraped_ids: {e}")
                    
                    scraper.close()
                    return None
                else:
                    logger.info(f"Date valide: {date_envoi} >= {self.min_date} → scraping complet")
            else:
                logger.warning(f"Pas de date_envoi trouvée pour {centris_id}, scraping complet par précaution")
            
            # ÉTAPE 3: Scraping complet (détails + photos) seulement si date OK
            logger.info(f"Scraping complet par Centris ID: {centris_id}")
            property_data = scraper.scrape_property_by_centris_id(centris_id, skip_photos=self.skip_photos)
            
            # Vérifier que le numéro Centris correspond bien
            if property_data:
                scraped_centris = property_data.get('numero_centris')
                if scraped_centris and scraped_centris != centris_id:
                    logger.error(f"Numéro Centris ne correspond pas! Attendu: {centris_id}, Obtenu: {scraped_centris}")
                    logger.error(f"Données rejetées pour éviter de mélanger les propriétés")
                    scraper.close()
                    return None
                else:
                    logger.debug(f"Numéro Centris vérifié: {scraped_centris}")
            
            scraper.close()
            return property_data
            
        except Exception as e:
            logger.error(f"Erreur scraping annonce {centris_id}: {e}", exc_info=True)
            try:
                scraper.close()
            except:
                pass
            return None
    
    def run_monitoring_cycle(self):
        """
        Exécute un cycle de monitoring complet
        
        Returns:
            dict: Statistiques du cycle
        """
        cycle_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.info("="*80)
        logger.info(f"CYCLE DE MONITORING - {cycle_time}")
        logger.info("="*80)
        
        stats = {
            'timestamp': datetime.now().isoformat(),
            'total_listings': 0,
            'new_listings': 0,
            'scraped_successfully': 0,
            'sent_to_api': 0,
            'errors': 0
        }
        
        # 1. Récupérer tous les IDs actuels
        current_ids = self.get_all_listing_ids()
        stats['total_listings'] = len(current_ids)
        
        # 2. Identifier les nouvelles annonces
        new_ids = self.identify_new_listings(current_ids)
        stats['new_listings'] = len(new_ids)
        
        # 3. Scraper chaque nouvelle annonce
        for centris_id in new_ids:
            try:
                # Scraper l'annonce
                property_data = self.scrape_new_listing(centris_id)
                
                if property_data:
                    stats['scraped_successfully'] += 1
                    
                    # Sauvegarder dans un fichier individuel
                    filename = f"property_{centris_id}.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(property_data, f, indent=2, ensure_ascii=False)
                    logger.info(f"✓ Données sauvegardées dans {filename}")
                    
                    # Envoyer à l'API
                    if self.send_to_api(property_data):
                        stats['sent_to_api'] += 1
                    
                    # Marquer comme scrapé
                    self.scraped_ids[centris_id] = datetime.now().isoformat()
                    self.save_scraped_ids()
                    
                else:
                    stats['errors'] += 1
                    
            except Exception as e:
                logger.error(f"Erreur lors du traitement de {centris_id}: {e}", exc_info=True)
                stats['errors'] += 1
            
            # Pause entre chaque scraping pour ne pas surcharger le serveur
            time.sleep(5)
        
        # Résumé
        summary_stats = {
            'Total annonces sur la page': stats['total_listings'],
            'Nouvelles annonces': stats['new_listings'],
            'Scrapées avec succès': stats['scraped_successfully'],
            'Envoyées à l\'API': stats['sent_to_api'],
            'Erreurs': stats['errors'],
            'Total annonces en mémoire': len(self.scraped_ids)
        }
        log_scraping_stats(logger, summary_stats)
        
        return stats
    
    def run_continuous_monitoring(self, interval_minutes=60):
        """
        Exécute le monitoring en continu avec un intervalle défini
        
        Args:
            interval_minutes: Intervalle en minutes entre chaque cycle
        """
        logger.info("="*80)
        logger.info("DÉMARRAGE DU MONITORING CONTINU")
        logger.info(f"Intervalle: {interval_minutes} minutes")
        logger.info("="*80)
        
        cycle_number = 0
        
        try:
            while True:
                cycle_number += 1
                logger.info(f">>> CYCLE #{cycle_number} <<<")
                
                self.run_monitoring_cycle()
                
                logger.info(f"Prochain cycle dans {interval_minutes} minutes...")
                logger.info(f"Appuyez sur Ctrl+C pour arrêter le monitoring")
                
                time.sleep(interval_minutes * 60)
                
        except KeyboardInterrupt:
            logger.info("Arrêt du monitoring demandé par l'utilisateur")
            logger.info(f"Total de {cycle_number} cycles exécutés")
            logger.info(f"{len(self.scraped_ids)} annonces en mémoire")


def main():
    """
    Fonction principale - exemple d'utilisation
    """
    # Configuration
    MATRIX_URL = "https://matrix.centris.ca/Matrix/Public/Portal.aspx?ID=0-3319143035-10&eml=Y2JlYXVkZXRAcmF5aGFydmV5LmNh&L=2"
    API_ENDPOINT = None  # TODO: Remplacer par l'URL de votre API
    # Exemple: API_ENDPOINT = "https://votre-api.com/api/properties"
    
    # Créer le moniteur
    monitor = CentrisMonitor(
        url=MATRIX_URL,
        api_endpoint=API_ENDPOINT,
        storage_file='scraped_properties.json'
    )
    
    # Option 1: Exécuter un seul cycle
    logger.info("=== MODE: CYCLE UNIQUE ===")
    monitor.run_monitoring_cycle()
    
    # Option 2: Monitoring continu (décommenter pour activer)
    # logger.info("=== MODE: MONITORING CONTINU ===")
    # monitor.run_continuous_monitoring(interval_minutes=60)


if __name__ == "__main__":
    main()

