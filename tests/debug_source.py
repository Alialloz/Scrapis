#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de debug pour analyser l'extraction de la source
"""

import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

MATRIX_URL = "https://matrix.centris.ca/Matrix/Public/Portal.aspx?ID=0-3319143035-10&eml=Y2JlYXVkZXRAcmF5aGFydmV5LmNh&L=2"

print("="*80)
print("DEBUG: Analyse de l'extraction de la source")
print("="*80)

# Initialiser Chrome
chrome_options = Options()
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--window-size=1920,1080')

driver = webdriver.Chrome(options=chrome_options)

try:
    print("\n1. Chargement de la page...")
    driver.get(MATRIX_URL)
    time.sleep(5)
    
    print("2. Clic sur la premiere annonce...")
    driver.execute_script("window.scrollTo(0, 1000);")
    time.sleep(2)
    
    # Trouver et cliquer sur la première annonce
    property_links = driver.find_elements(By.XPATH, "//a[contains(text(), 'Rue') or contains(text(), 'Boul')]")
    if property_links:
        property_links[0].click()
        time.sleep(5)
        
        print("3. Analyse du contenu...")
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        page_text = soup.get_text()
        
        # Chercher "Source" dans le texte
        print("\n" + "="*80)
        print("RECHERCHE DU MOT 'SOURCE' DANS LE TEXTE:")
        print("="*80)
        
        # Trouver toutes les occurrences de "Source"
        pattern = re.compile(r'.{0,200}Source.{0,300}', re.IGNORECASE | re.DOTALL)
        matches = pattern.findall(page_text)
        
        print(f"\nNombre d'occurrences trouvees: {len(matches)}\n")
        
        for i, match in enumerate(matches, 1):
            print(f"--- Occurrence {i} ---")
            # Nettoyer un peu pour l'affichage
            cleaned = re.sub(r'\s+', ' ', match)
            print(cleaned)
            print()
        
        # Chercher aussi dans le HTML brut
        print("\n" + "="*80)
        print("RECHERCHE DANS LE HTML BRUT:")
        print("="*80)
        
        html_pattern = re.compile(r'.{0,500}<[^>]*>[^<]*Source[^<]*<[^>]*>.{0,500}', re.IGNORECASE | re.DOTALL)
        html_matches = html_pattern.findall(html)
        
        print(f"\nNombre d'occurrences HTML trouvees: {len(html_matches)}\n")
        
        for i, match in enumerate(html_matches[:3], 1):  # Limiter à 3 pour ne pas surcharger
            print(f"--- Occurrence HTML {i} ---")
            print(match[:500])
            print()
        
        # Chercher spécifiquement RAY HARVEY
        print("\n" + "="*80)
        print("RECHERCHE DE 'RAY HARVEY':")
        print("="*80)
        
        harvey_pattern = re.compile(r'.{0,100}RAY HARVEY.{0,200}', re.IGNORECASE | re.DOTALL)
        harvey_matches = harvey_pattern.findall(page_text)
        
        print(f"\nNombre d'occurrences 'RAY HARVEY' trouvees: {len(harvey_matches)}\n")
        
        for i, match in enumerate(harvey_matches, 1):
            cleaned = re.sub(r'\s+', ' ', match)
            print(f"--- Occurrence {i} ---")
            print(cleaned)
            print()
        
        print("\n" + "="*80)
        print("FIN DE L'ANALYSE")
        print("="*80)
    else:
        print("ERREUR: Aucune annonce trouvee")
    
finally:
    print("\nFermeture du navigateur...")
    time.sleep(2)
    driver.quit()
    print("Termine!")
