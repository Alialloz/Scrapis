#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test avec affichage debug complet
"""

import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

MATRIX_URL = "https://matrix.centris.ca/Matrix/Public/Portal.aspx?ID=0-3319143035-10&eml=Y2JlYXVkZXRAcmF5aGFydmV5LmNh&L=2"

print("="*80)
print("TEST DEBUG EXTRACTION")
print("="*80)

chrome_options = Options()
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--no-sandbox')

driver = webdriver.Chrome(options=chrome_options)

try:
    print("\nChargement...")
    driver.get(MATRIX_URL)
    time.sleep(5)
    
    driver.execute_script("window.scrollTo(0, 1000);")
    time.sleep(2)
    
    print("Clic sur annonce...")
    links = driver.find_elements(By.XPATH, "//a[contains(text(), 'Rue') or contains(text(), 'Boul')]")
    if links:
        links[0].click()
        time.sleep(5)
        
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()
        
        print("\n" + "="*80)
        print("ANALYSE DES SECTIONS:")
        print("="*80)
        
        # 1. Inclusions
        print("\n1. INCLUSIONS:")
        print("-" * 40)
        incl_match = re.search(r'Inclusions?\s*([^\\n]+(?:\\n(?!Exclusions)[^\\n]+)*)', text, re.IGNORECASE | re.DOTALL)
        if incl_match:
            inclusions = incl_match.group(1).strip()[:300]
            print(f"Trouve: {inclusions}")
        else:
            print("Non trouve")
        
        # 2. Exclusions
        print("\n2. EXCLUSIONS:")
        print("-" * 40)
        excl_match = re.search(r'Exclusions?\s*([^\\n]+(?:\\n(?!Remarques)[^\\n]+)*)', text, re.IGNORECASE | re.DOTALL)
        if excl_match:
            exclusions = excl_match.group(1).strip()[:300]
            print(f"Trouve: {exclusions}")
        else:
            print("Non trouve")
        
        # 3. Remarques
        print("\n3. REMARQUES:")
        print("-" * 40)
        rem_match = re.search(r'Remarques?\s*((?:.|\n)+?)(?:Addenda|Source|$)', text, re.IGNORECASE)
        if rem_match:
            remarques = rem_match.group(1).strip()[:300]
            print(f"Trouve: {remarques}")
        else:
            print("Non trouve")
        
        # 4. Source - Analyse détaillée
        print("\n4. SOURCE - ANALYSE DETAILLEE:")
        print("-" * 40)
        
        # Chercher le contexte autour de "Source"
        source_context = re.search(r'.{0,100}Source.{0,300}', text, re.IGNORECASE | re.DOTALL)
        if source_context:
            context = re.sub(r'\s+', ' ', source_context.group(0))
            print(f"Contexte: {context}")
        
        # Test de différents patterns
        patterns = [
            (r'Source\s*[:\-]?\s*([A-ZÀ-Ÿ][^\\n]{10,150})', "Pattern 1: Standard"),
            (r'Source\s*(.+?)(?:Inscription|Dernière|$)', "Pattern 2: Jusqu'à Inscription"),
            (r'Source[^A-Z]*([A-ZÀ-Ÿ][A-Za-zÀ-ÿ\s&\-\',]{5,100})', "Pattern 3: Nom propre"),
        ]
        
        for pattern, desc in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                result = match.group(1).strip()
                result = re.sub(r'\s+', ' ', result)
                print(f"\n{desc}:")
                print(f"  -> {result[:150]}")
        
        # Chercher RAY HARVEY spécifiquement
        print("\n5. RECHERCHE 'RAY HARVEY':")
        print("-" * 40)
        harvey = re.search(r'(RAY HARVEY[^\\n]{0,100})', text, re.IGNORECASE)
        if harvey:
            result = re.sub(r'\s+', ' ', harvey.group(1))
            print(f"Trouve: {result}")
        else:
            print("Non trouve")
        
finally:
    time.sleep(2)
    driver.quit()

print("\n" + "="*80)
print("FIN")
print("="*80)
