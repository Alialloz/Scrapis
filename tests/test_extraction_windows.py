#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de test WINDOWS pour extraire une annonce complète et voir ce qui est envoyé à l'API
"""

import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import re

# Configuration
MATRIX_URL = "https://matrix.centris.ca/Matrix/Public/Portal.aspx?ID=0-3319143035-10&eml=Y2JlYXVkZXRAcmF5aGFydmV5LmNh&L=2"


class WindowsScraper:
    """Scraper adapté pour Windows"""
    
    def __init__(self):
        self.driver = None
        
    def init_driver(self):
        """Initialise Chrome pour Windows"""
        try:
            chrome_options = Options()
            # chrome_options.add_argument('--headless')  # Décommenter pour mode headless
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            # NE PAS spécifier binary_location sur Windows (auto-détection)
            
            self.driver = webdriver.Chrome(options=chrome_options)
            print("[OK] Chrome initialise avec succes")
            return True
        except Exception as e:
            print(f"[ERREUR] Erreur d'initialisation: {e}")
            return False
    
    def extract_basic_info(self):
        """Extrait les infos de base de la première annonce"""
        try:
            time.sleep(5)
            
            # Faire défiler
            self.driver.execute_script("window.scrollTo(0, 1000);")
            time.sleep(2)
            
            # Obtenir le HTML
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text()
            
            # Extraire les infos de base
            data = {
                'prix': None,
                'adresse': None,
                'ville': None,
                'arrondissement': None,
                'quartier': None,
                'type_propriete': None,
                'annee_construction': None,
                'numero_centris': None,
                'date_envoi': None,
                'statut': None,
                'url': self.driver.current_url
            }
            
            # Prix
            prix_match = re.search(r'([\d\s]+)\s*\$', text)
            if prix_match:
                data['prix'] = prix_match.group(1).replace(' ', '').strip()
            
            # Numéro Centris (premier trouvé)
            centris_match = re.search(r'No\s*Centris\s*[:\-]?\s*(\d+)', text, re.IGNORECASE)
            if centris_match:
                data['numero_centris'] = centris_match.group(1)
            
            # Date d'envoi
            date_match = re.search(r"Date\s*d['']envoi\s*[:\-]?\s*(\d{4}-\d{2}-\d{2})", text)
            if date_match:
                data['date_envoi'] = date_match.group(1)
            
            # Quartier
            quartier_match = re.search(r'(?:dans le quartier|quartier)\s+([A-Za-zÀ-ÿ\s\-\/]+?)\s+construit', text, re.IGNORECASE)
            if quartier_match:
                data['quartier'] = quartier_match.group(1).strip()
            
            # Type
            types = ['Quintuplex', 'Quadruplex', 'Triplex', 'Duplex', 'Autre']
            for type_prop in types:
                if type_prop in text:
                    data['type_propriete'] = type_prop
                    break
            
            # Année
            year_match = re.search(r'construit\s+en\s+(\d{4})', text, re.IGNORECASE)
            if year_match:
                data['annee_construction'] = year_match.group(1)
            
            # Ville/Arrondissement
            ville_match = re.search(r'Québec\s*\(([^)]+)\)', text)
            if ville_match:
                data['ville'] = 'Québec'
                data['arrondissement'] = ville_match.group(1).strip()
            
            # Statut
            if 'Nouvelle annonce' in text:
                data['statut'] = 'Nouvelle annonce'
            
            return data
            
        except Exception as e:
            print(f"[ERREUR] Erreur extraction: {e}")
            return None
    
    def close(self):
        if self.driver:
            self.driver.quit()


def print_section(title):
    """Affiche un titre de section"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def display_data(data):
    """Affiche les données extraites"""
    print_section("DONNEES EXTRAITES")
    
    for key, value in data.items():
        if value:
            print(f"  [OK] {key:25s}: {value}")
        else:
            print(f"  [ ] {key:25s}: Non disponible")


def test_extraction():
    """Test principal"""
    print("\n" + "="*80)
    print("  TEST D'EXTRACTION - VERSION WINDOWS")
    print("="*80)
    
    print("\nEtape 1/4: Initialisation du scraper...")
    scraper = WindowsScraper()
    
    if not scraper.init_driver():
        print("[ERREUR] Impossible d'initialiser Chrome")
        print("\nVerifiez que:")
        print("  1. Chrome est installe sur votre systeme")
        print("  2. ChromeDriver est installe (pip install webdriver-manager)")
        return None
    
    try:
        print("\nEtape 2/4: Chargement de la page Matrix...")
        print(f"   URL: {MATRIX_URL[:60]}...")
        scraper.driver.get(MATRIX_URL)
        print("[OK] Page chargee")
        
        print("\nEtape 3/4: Extraction des donnees de base...")
        print("   Cela peut prendre 10-15 secondes...")
        
        start_time = time.time()
        data = scraper.extract_basic_info()
        elapsed_time = time.time() - start_time
        
        if not data:
            print("[ERREUR] Impossible d'extraire les donnees")
            return None
        
        print(f"[OK] Extraction reussie en {elapsed_time:.1f} secondes")
        
        print("\nEtape 4/4: Affichage et sauvegarde...")
        display_data(data)
        
        # Sauvegarder
        filename = f"test_windows_{data.get('numero_centris', 'unknown')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print_section("SIMULATION ENVOI A L'API")
        
        try:
            from config_api import API_ENDPOINT
        except:
            API_ENDPOINT = "https://apidev.rayharvey.ca/robot/api/scraping"
        
        print(f"  Endpoint: {API_ENDPOINT}")
        print(f"  Content-Type: application/json")
        print(f"  Taille du JSON: {len(json.dumps(data))} caracteres")
        
        # Afficher le JSON
        print("\n  JSON qui serait envoye:")
        print("  " + "-"*76)
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        for line in json_str.split('\n'):
            print(f"  {line}")
        print("  " + "-"*76)
        
        print_section("TEST TERMINE AVEC SUCCES")
        print(f"  Fichier genere: {filename}")
        print(f"  Numero Centris: {data.get('numero_centris', 'N/A')}")
        print(f"  Prix: {data.get('prix', 'N/A')} $")
        print(f"  Temps total: {elapsed_time:.1f} secondes")
        
        print("\n  Note: Ceci est un test simplifie (infos de base uniquement)")
        print("  Pour l'extraction complete, utilisez le serveur Linux")
        
        return data
        
    except Exception as e:
        print(f"\n[ERREUR] {e}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        print("\nFermeture du navigateur dans 3 secondes...")
        time.sleep(3)
        scraper.close()
        print("[OK] Navigateur ferme")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("  SCRAPIS - TEST WINDOWS")
    print("  Test simplifie d'extraction pour Windows")
    print("="*80)
    
    result = test_extraction()
    
    if result:
        print("\n" + "="*80)
        print("  TEST REUSSI!")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("  TEST ECHOUE")
        print("="*80)
    
    input("\nAppuyez sur Entree pour quitter...")
