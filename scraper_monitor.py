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


class CentrisMonitor:
    """
    Moniteur pour détecter les nouvelles annonces et les scraper automatiquement
    """
    
    def __init__(self, url, api_endpoint=None, storage_file='scraped_properties.json', min_date='2025-12-21'):
        """
        Initialise le moniteur
        
        Args:
            url: URL de la page Matrix Centris à surveiller
            api_endpoint: URL de l'API où envoyer les données (optionnel)
            storage_file: Fichier pour stocker les numéros Centris déjà scrapés
            min_date: Date minimale pour les annonces (format: YYYY-MM-DD)
        """
        self.url = url
        self.api_endpoint = api_endpoint
        self.storage_file = storage_file
        self.min_date = min_date
        self.scraped_ids = self.load_scraped_ids()
        print(f"[CONFIG] Filtre de date active: annonces >= {self.min_date}")
        
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
                    print(f"[INFO] {len(data)} annonces deja scrapees chargees depuis {self.storage_file}")
                    return data
            except Exception as e:
                print(f"[WARNING] Erreur lecture {self.storage_file}: {e}")
                return {}
        else:
            print(f"[INFO] Nouveau fichier {self.storage_file} sera cree")
            return {}
    
    def save_scraped_ids(self):
        """
        Sauvegarde la liste des numéros Centris scrapés
        """
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.scraped_ids, f, indent=2, ensure_ascii=False)
            print(f"[OK] {len(self.scraped_ids)} IDs sauvegardes dans {self.storage_file}")
        except Exception as e:
            print(f"[ERREUR] Impossible de sauvegarder {self.storage_file}: {e}")
    
    def get_all_listing_ids(self):
        """
        Récupère tous les numéros Centris disponibles sur la page
        
        Returns:
            list: Liste des numéros Centris trouvés
        """
        print("\n=== RECUPERATION DE TOUS LES NUMEROS CENTRIS ===")
        
        # Configurer Chrome (même config que scraper_with_list_info.py)
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
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
            print(f"Chargement de la page: {self.url}")
            driver.get(self.url)
            time.sleep(5)
            
            # Faire défiler pour charger toutes les annonces
            print("Defilement pour charger toutes les annonces...")
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
                print(f"  Scroll {scroll_attempts}/{max_scrolls}...")
            
            # Extraire tous les numéros Centris
            import re
            page_source = driver.page_source
            
            # Pattern pour trouver "No Centris : XXXXXXXX"
            pattern = r'No Centris\s*:\s*(\d+)'
            matches = re.findall(pattern, page_source)
            
            listing_ids = list(set(matches))  # Enlever les doublons
            
            print(f"[OK] {len(listing_ids)} annonces trouvees sur la page")
            
        except Exception as e:
            print(f"[ERREUR] Erreur lors de la recuperation des IDs: {e}")
            import traceback
            traceback.print_exc()
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
            print(f"\n[NOUVEAU] {len(new_ids)} nouvelle(s) annonce(s) detectee(s):")
            for id in new_ids:
                print(f"  - No Centris: {id}")
        else:
            print(f"\n[INFO] Aucune nouvelle annonce (toutes les {len(current_ids)} annonces ont deja ete scrapees)")
        
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
            print("[INFO] Pas d'endpoint API configure, donnees non envoyees")
            return True
        
        try:
            print(f"[API] Envoi des donnees a {self.api_endpoint}...")
            
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
                print(f"[OK] Donnees envoyees avec succes (Status: {response.status_code})")
                return True
            else:
                print(f"[WARNING] API a retourne le status {response.status_code}")
                print(f"  Reponse: {response.text[:200]}")
                return False
                
        except requests.exceptions.Timeout:
            print("[ERREUR] Timeout lors de l'envoi a l'API")
            return False
        except Exception as e:
            print(f"[ERREUR] Erreur lors de l'envoi a l'API: {e}")
            return False
    
    def scrape_new_listing(self, centris_id):
        """
        Scrape une nouvelle annonce par son numéro Centris
        
        Args:
            centris_id: Numéro Centris de l'annonce
            
        Returns:
            dict: Données de la propriété ou None si erreur
        """
        print(f"\n{'='*80}")
        print(f"SCRAPING DE L'ANNONCE No Centris: {centris_id}")
        print(f"{'='*80}")
        
        try:
            # Utiliser le scraper existant
            scraper = CentrisScraperWithListInfo()
            scraper.init_driver()
            
            # Charger la page
            print(f"Chargement de la page...")
            scraper.driver.get(self.url)
            time.sleep(5)
            
            # Faire défiler pour charger toutes les annonces
            print(f"Defilement de la page...")
            scraper.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            scraper.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            # APPROCHE SIMPLE: Construire un mapping ID Centris -> Index
            # En parcourant la page source
            print(f"Construction du mapping des annonces...")
            html = scraper.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # Trouver tous les conteneurs d'annonces
            all_text_blocks = soup.find_all(string=re.compile(r'No\s*Centris', re.IGNORECASE))
            
            centris_to_index = {}
            index = 0
            
            for text_block in all_text_blocks:
                # Extraire le numéro Centris de ce bloc
                parent = text_block.parent
                if parent:
                    parent_text = parent.get_text()
                    match = re.search(r'No\s*Centris\s*[:\-]?\s*(\d+)', parent_text, re.IGNORECASE)
                    if match:
                        found_id = match.group(1)
                        if found_id not in centris_to_index:
                            centris_to_index[found_id] = index
                            index += 1
                            print(f"  [{index}] No Centris: {found_id}")
            
            print(f"\n[INFO] {len(centris_to_index)} annonces mappees")
            
            # Trouver l'index de notre annonce cible
            if centris_id not in centris_to_index:
                print(f"[ERREUR] Annonce {centris_id} non trouvee dans le mapping")
                scraper.close()
                return None
            
            target_index = centris_to_index[centris_id]
            print(f"[OK] Annonce {centris_id} trouvee a l'index {target_index}")
            
            # Utiliser l'approche simple par index qui fonctionne
            property_data = scraper.scrape_property_with_list_info(index=target_index)
            
            # Vérifier que le numéro Centris correspond bien
            if property_data:
                scraped_centris = property_data.get('numero_centris')
                if scraped_centris != centris_id:
                    print(f"[WARNING] Numero Centris ne correspond pas!")
                    print(f"  Attendu: {centris_id}")
                    print(f"  Obtenu: {scraped_centris}")
                    # Forcer le bon numéro Centris
                    property_data['numero_centris'] = centris_id
                    if property_data.get('_donnees_liste'):
                        property_data['_donnees_liste']['numero_centris'] = centris_id
                else:
                    print(f"[OK] Numero Centris verifie: {scraped_centris}")
                
                # FILTRE DE DATE: Vérifier que l'annonce est assez récente
                date_envoi = property_data.get('date_envoi')
                if date_envoi:
                    try:
                        # Comparer les dates
                        if date_envoi < self.min_date:
                            print(f"[FILTRE] Annonce trop ancienne: {date_envoi} < {self.min_date}")
                            print(f"[FILTRE] Annonce {centris_id} ignoree")
                            scraper.close()
                            return None
                        else:
                            print(f"[OK] Date valide: {date_envoi} >= {self.min_date}")
                    except Exception as e:
                        print(f"[WARNING] Impossible de verifier la date: {e}")
                else:
                    print(f"[WARNING] Pas de date_envoi trouvee pour {centris_id}")
            
            scraper.close()
            return property_data
            
        except Exception as e:
            print(f"[ERREUR] Erreur scraping annonce {centris_id}: {e}")
            import traceback
            traceback.print_exc()
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
        print(f"\n{'='*80}")
        print(f"CYCLE DE MONITORING - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}")
        
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
                    print(f"[OK] Donnees sauvegardees dans {filename}")
                    
                    # Envoyer à l'API
                    if self.send_to_api(property_data):
                        stats['sent_to_api'] += 1
                    
                    # Marquer comme scrapé
                    self.scraped_ids[centris_id] = datetime.now().isoformat()
                    self.save_scraped_ids()
                    
                else:
                    stats['errors'] += 1
                    
            except Exception as e:
                print(f"[ERREUR] Erreur lors du traitement de {centris_id}: {e}")
                stats['errors'] += 1
            
            # Pause entre chaque scraping pour ne pas surcharger le serveur
            time.sleep(5)
        
        # Résumé
        print(f"\n{'='*80}")
        print(f"RESUME DU CYCLE")
        print(f"{'='*80}")
        print(f"Total annonces sur la page: {stats['total_listings']}")
        print(f"Nouvelles annonces: {stats['new_listings']}")
        print(f"Scrapees avec succes: {stats['scraped_successfully']}")
        print(f"Envoyees a l'API: {stats['sent_to_api']}")
        print(f"Erreurs: {stats['errors']}")
        print(f"Total annonces en memoire: {len(self.scraped_ids)}")
        
        return stats
    
    def run_continuous_monitoring(self, interval_minutes=60):
        """
        Exécute le monitoring en continu avec un intervalle défini
        
        Args:
            interval_minutes: Intervalle en minutes entre chaque cycle
        """
        print(f"\n{'='*80}")
        print(f"DEMARRAGE DU MONITORING CONTINU")
        print(f"Intervalle: {interval_minutes} minutes")
        print(f"{'='*80}")
        
        cycle_number = 0
        
        try:
            while True:
                cycle_number += 1
                print(f"\n>>> CYCLE #{cycle_number} <<<")
                
                self.run_monitoring_cycle()
                
                print(f"\n[INFO] Prochain cycle dans {interval_minutes} minutes...")
                print(f"[INFO] Appuyez sur Ctrl+C pour arreter le monitoring")
                
                time.sleep(interval_minutes * 60)
                
        except KeyboardInterrupt:
            print(f"\n\n[INFO] Arret du monitoring demande par l'utilisateur")
            print(f"[INFO] Total de {cycle_number} cycles executes")
            print(f"[INFO] {len(self.scraped_ids)} annonces en memoire")


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
    print("=== MODE: CYCLE UNIQUE ===")
    monitor.run_monitoring_cycle()
    
    # Option 2: Monitoring continu (décommenter pour activer)
    # print("=== MODE: MONITORING CONTINU ===")
    # monitor.run_continuous_monitoring(interval_minutes=60)


if __name__ == "__main__":
    main()

