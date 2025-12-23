"""
Scraper pour extraire les données des propriétés immobilières depuis Centris Matrix
"""
import time
import json
import csv
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd


class CentrisScraper:
    def __init__(self, url, headless=False):
        """
        Initialise le scraper Centris
        
        Args:
            url: URL de la page Centris à scraper
            headless: Mode headless (sans interface graphique)
        """
        self.url = url
        self.properties = []
        self.setup_driver(headless)
    
    def setup_driver(self, headless):
        """Configure le driver Selenium"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.binary_location = "/usr/bin/google-chrome"
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def wait_for_page_load(self, timeout=30):
        """Attend que la page soit complètement chargée"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(3)  # Attente supplémentaire pour le chargement dynamique
        except Exception as e:
            print(f"Erreur lors du chargement de la page: {e}")
    
    def scroll_to_load_all(self):
        """Fait défiler la page pour charger toutes les propriétés"""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_scrolls = 10
        
        while scroll_attempts < max_scrolls:
            # Scroll jusqu'en bas
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Vérifier si de nouveaux éléments ont été chargés
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            scroll_attempts += 1
        
        # Scroll vers le haut pour revenir au début
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
    
    def extract_property_data(self, element):
        """
        Extrait les données d'une propriété depuis un élément HTML
        
        Args:
            element: Élément BeautifulSoup contenant les données d'une propriété
            
        Returns:
            dict: Dictionnaire contenant les données de la propriété
        """
        property_data = {
            'prix': None,
            'adresse': None,
            'ville': None,
            'quartier': None,
            'type_propriete': None,
            'annee_construction': None,
            'numero_centris': None,
            'date_envoi': None,
            'statut': None,
            'url': None
        }
        
        try:
            # Extraire le prix
            prix_elem = element.find(class_=lambda x: x and ('price' in x.lower() or 'prix' in x.lower()))
            if not prix_elem:
                prix_elem = element.find(string=lambda x: x and '$' in str(x))
            if prix_elem:
                prix_text = prix_elem.get_text() if hasattr(prix_elem, 'get_text') else str(prix_elem)
                property_data['prix'] = prix_text.strip()
            
            # Extraire l'adresse
            adresse_elem = element.find(class_=lambda x: x and ('address' in x.lower() or 'adresse' in x.lower()))
            if not adresse_elem:
                # Chercher dans les liens ou textes en gras
                adresse_elem = element.find('a', class_=lambda x: x and ('property' in x.lower() or 'listing' in x.lower()))
            if adresse_elem:
                property_data['adresse'] = adresse_elem.get_text().strip()
            
            # Extraire le numéro Centris
            centris_elem = element.find(string=lambda x: x and 'Centris' in str(x) or 'No Centris' in str(x))
            if centris_elem:
                parent = centris_elem.parent if hasattr(centris_elem, 'parent') else None
                if parent:
                    centris_text = parent.get_text()
                    # Extraire le numéro après "No Centris :"
                    if 'No Centris' in centris_text:
                        parts = centris_text.split('No Centris')
                        if len(parts) > 1:
                            property_data['numero_centris'] = parts[1].split()[0] if parts[1].split() else None
            
            # Extraire la date d'envoi
            date_elem = element.find(string=lambda x: x and 'Date d\'envoi' in str(x) or 'Date d\'envoi' in str(x))
            if date_elem:
                parent = date_elem.parent if hasattr(date_elem, 'parent') else None
                if parent:
                    date_text = parent.get_text()
                    if 'Date d\'envoi' in date_text:
                        parts = date_text.split('Date d\'envoi')
                        if len(parts) > 1:
                            property_data['date_envoi'] = parts[1].strip().split()[0] if parts[1].strip().split() else None
            
            # Extraire le type de propriété et autres infos depuis le texte
            text_content = element.get_text()
            
            # Chercher le type (Autre, Quintuplex, etc.)
            if 'Autre' in text_content:
                property_data['type_propriete'] = 'Autre'
            elif 'Quintuplex' in text_content:
                property_data['type_propriete'] = 'Quintuplex'
            elif 'Duplex' in text_content:
                property_data['type_propriete'] = 'Duplex'
            elif 'Triplex' in text_content:
                property_data['type_propriete'] = 'Triplex'
            
            # Extraire l'année de construction
            import re
            year_match = re.search(r'construit en (\d{4})', text_content)
            if year_match:
                property_data['annee_construction'] = year_match.group(1)
            
            # Extraire le quartier
            quartier_match = re.search(r'dans le quartier ([^c]+?)(?:construit|$)', text_content)
            if quartier_match:
                property_data['quartier'] = quartier_match.group(1).strip()
            
            # Extraire la ville (format: Québec (XXX))
            ville_match = re.search(r'Québec\s*\(([^)]+)\)', text_content)
            if ville_match:
                property_data['ville'] = ville_match.group(1).strip()
            
            # Vérifier le statut (Nouvelle annonce, Nouveau prix)
            if 'Nouvelle annonce' in text_content:
                property_data['statut'] = 'Nouvelle annonce'
            elif 'Nouveau prix' in text_content:
                property_data['statut'] = 'Nouveau prix'
            
            # Extraire l'URL si disponible
            link = element.find('a', href=True)
            if link:
                href = link.get('href')
                if href:
                    if href.startswith('http'):
                        property_data['url'] = href
                    else:
                        property_data['url'] = f"https://matrix.centris.ca{href}"
        
        except Exception as e:
            print(f"Erreur lors de l'extraction des données: {e}")
        
        return property_data
    
    def find_property_elements_with_selenium(self):
        """Trouve les éléments de propriétés en utilisant Selenium"""
        property_elements = []
        seen_texts = set()
        
        try:
            # Stratégie 1: Chercher les éléments qui contiennent "No Centris"
            centris_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'No Centris')]")
            for elem in centris_elements:
                try:
                    # Remonter jusqu'à l'élément parent contenant toute la propriété
                    parent = elem
                    for _ in range(5):  # Remonter jusqu'à 5 niveaux
                        try:
                            parent = parent.find_element(By.XPATH, "./..")
                            text = parent.text.strip()
                            if text and '$' in text and len(text) > 50:
                                if text not in seen_texts:
                                    property_elements.append(parent)
                                    seen_texts.add(text)
                                    break
                        except:
                            break
                except:
                    continue
            
            # Stratégie 2: Si pas assez d'éléments, chercher par prix
            if len(property_elements) < 10:
                price_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '$') and string-length(text()) > 10]")
                for elem in price_elements:
                    try:
                        text = elem.text.strip()
                        if text and '$' in text and 'Centris' in text and len(text) > 50:
                            if text not in seen_texts:
                                # Essayer de trouver le parent contenant toute la propriété
                                parent = elem
                                for _ in range(3):
                                    try:
                                        parent = parent.find_element(By.XPATH, "./..")
                                        parent_text = parent.text.strip()
                                        if len(parent_text) > len(text) and 'Centris' in parent_text:
                                            text = parent_text
                                            break
                                    except:
                                        break
                                
                                if text not in seen_texts:
                                    property_elements.append(elem)
                                    seen_texts.add(text)
                    except:
                        continue
            
            # Stratégie 3: Chercher les list items ou divs avec des classes spécifiques
            if len(property_elements) < 10:
                try:
                    list_items = self.driver.find_elements(By.TAG_NAME, "li")
                    for li in list_items:
                        text = li.text.strip()
                        if text and '$' in text and 'Centris' in text and len(text) > 50:
                            if text not in seen_texts:
                                property_elements.append(li)
                                seen_texts.add(text)
                except:
                    pass
        
        except Exception as e:
            print(f"Erreur lors de la recherche d'éléments: {e}")
        
        return property_elements
    
    def extract_property_data_from_selenium(self, element):
        """Extrait les données d'une propriété depuis un élément Selenium"""
        property_data = {
            'prix': None,
            'adresse': None,
            'ville': None,
            'quartier': None,
            'type_propriete': None,
            'annee_construction': None,
            'numero_centris': None,
            'date_envoi': None,
            'statut': None,
            'url': None
        }
        
        try:
            text_content = element.text
            
            # Extraire le prix (format: "750 000 $" ou "1 050 000 $")
            import re
            prix_match = re.search(r'([\d\s]+)\s*\$', text_content)
            if prix_match:
                prix = prix_match.group(1).replace(' ', '').strip()
                property_data['prix'] = prix
            
            # Extraire l'adresse (généralement en gras ou dans un lien)
            try:
                # Chercher les éléments en gras qui contiennent une adresse
                bold_elements = element.find_elements(By.TAG_NAME, "strong")
                for bold in bold_elements:
                    text = bold.text.strip()
                    if text and len(text) > 5 and any(char.isdigit() for char in text):
                        property_data['adresse'] = text
                        break
                
                # Si pas trouvé, chercher dans les liens
                if not property_data['adresse']:
                    links = element.find_elements(By.TAG_NAME, "a")
                    for link in links:
                        href = link.get_attribute('href')
                        text = link.text.strip()
                        if text and len(text) > 5:
                            property_data['adresse'] = text
                            if href:
                                property_data['url'] = href
                            break
            except:
                pass
            
            # Extraire le numéro Centris
            centris_match = re.search(r'No Centris\s*:\s*(\d+)', text_content)
            if centris_match:
                property_data['numero_centris'] = centris_match.group(1)
            
            # Extraire la date d'envoi
            date_match = re.search(r'Date d\'envoi\s*:\s*(\d{4}-\d{2}-\d{2})', text_content)
            if date_match:
                property_data['date_envoi'] = date_match.group(1)
            
            # Extraire le type de propriété
            if 'Quintuplex' in text_content:
                property_data['type_propriete'] = 'Quintuplex'
            elif 'Duplex' in text_content:
                property_data['type_propriete'] = 'Duplex'
            elif 'Triplex' in text_content:
                property_data['type_propriete'] = 'Triplex'
            elif 'Autre' in text_content:
                property_data['type_propriete'] = 'Autre'
            
            # Extraire l'année de construction
            year_match = re.search(r'construit en (\d{4})', text_content)
            if year_match:
                property_data['annee_construction'] = year_match.group(1)
            
            # Extraire le quartier
            quartier_match = re.search(r'dans le quartier ([^c]+?)(?:construit|$)', text_content)
            if quartier_match:
                property_data['quartier'] = quartier_match.group(1).strip()
            
            # Extraire la ville (format: Québec (XXX))
            ville_match = re.search(r'Québec\s*\(([^)]+)\)', text_content)
            if ville_match:
                property_data['ville'] = ville_match.group(1).strip()
            
            # Vérifier le statut
            if 'Nouvelle annonce' in text_content:
                property_data['statut'] = 'Nouvelle annonce'
            elif 'Nouveau prix' in text_content:
                property_data['statut'] = 'Nouveau prix'
        
        except Exception as e:
            print(f"Erreur lors de l'extraction: {e}")
        
        return property_data
    
    def scrape(self):
        """Méthode principale pour scraper la page"""
        print(f"Chargement de la page: {self.url}")
        self.driver.get(self.url)
        self.wait_for_page_load()
        
        print("Défilement de la page pour charger toutes les propriétés...")
        self.scroll_to_load_all()
        
        print("Recherche des éléments de propriétés...")
        # Utiliser Selenium pour trouver les éléments
        property_elements = self.find_property_elements_with_selenium()
        
        # Si pas trouvé avec Selenium, utiliser BeautifulSoup comme fallback
        if not property_elements:
            print("Tentative avec BeautifulSoup...")
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # Chercher les éléments qui contiennent des prix et des infos Centris
            all_divs = soup.find_all(['div', 'li', 'article'])
            seen_texts = set()
            
            for div in all_divs:
                text = div.get_text()
                if '$' in text and 'Centris' in text and len(text) > 50:
                    if text not in seen_texts:
                        property_elements.append(div)
                        seen_texts.add(text)
        
        print(f"Nombre total d'éléments trouvés: {len(property_elements)}")
        
        # Extraire les données de chaque propriété
        for i, element in enumerate(property_elements):
            print(f"Traitement de la propriété {i+1}/{len(property_elements)}...")
            
            # Essayer d'abord avec Selenium
            try:
                if hasattr(element, 'text'):  # C'est un élément Selenium
                    property_data = self.extract_property_data_from_selenium(element)
                else:  # C'est un élément BeautifulSoup
                    property_data = self.extract_property_data(element)
            except:
                property_data = self.extract_property_data(element)
            
            if property_data.get('prix') or property_data.get('adresse') or property_data.get('numero_centris'):
                self.properties.append(property_data)
        
        print(f"\n{len(self.properties)} propriétés extraites avec succès!")
        return self.properties
    
    def save_to_csv(self, filename=None):
        """Sauvegarde les données en CSV"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"centris_properties_{timestamp}.csv"
        
        if not self.properties:
            print("Aucune donnée à sauvegarder")
            return
        
        df = pd.DataFrame(self.properties)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"Données sauvegardées dans {filename}")
    
    def save_to_json(self, filename=None):
        """Sauvegarde les données en JSON"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"centris_properties_{timestamp}.json"
        
        if not self.properties:
            print("Aucune donnée à sauvegarder")
            return
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.properties, f, ensure_ascii=False, indent=2)
        print(f"Données sauvegardées dans {filename}")
    
    def print_summary(self):
        """Affiche un résumé des données extraites"""
        if not self.properties:
            print("Aucune propriété extraite")
            return
        
        print(f"\n{'='*60}")
        print(f"RÉSUMÉ DE L'EXTRACTION")
        print(f"{'='*60}")
        print(f"Nombre total de propriétés: {len(self.properties)}")
        
        # Statistiques sur les prix
        prix_list = []
        for prop in self.properties:
            if prop.get('prix'):
                try:
                    prix_clean = prop['prix'].replace(' ', '').replace('$', '').replace(',', '')
                    if prix_clean.isdigit():
                        prix_list.append(int(prix_clean))
                except:
                    pass
        
        if prix_list:
            print(f"\nPrix:")
            print(f"  Minimum: ${min(prix_list):,}")
            print(f"  Maximum: ${max(prix_list):,}")
            print(f"  Moyenne: ${sum(prix_list)//len(prix_list):,}")
        
        # Statistiques sur les types
        types = {}
        for prop in self.properties:
            type_prop = prop.get('type_propriete', 'Non spécifié')
            types[type_prop] = types.get(type_prop, 0) + 1
        
        if types:
            print(f"\nTypes de propriétés:")
            for type_prop, count in sorted(types.items(), key=lambda x: x[1], reverse=True):
                print(f"  {type_prop}: {count}")
        
        # Statistiques sur les quartiers
        quartiers = {}
        for prop in self.properties:
            quartier = prop.get('quartier', 'Non spécifié')
            if quartier:
                quartiers[quartier] = quartiers.get(quartier, 0) + 1
        
        if quartiers:
            print(f"\nTop 5 quartiers:")
            for quartier, count in sorted(quartiers.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {quartier}: {count}")
        
        print(f"{'='*60}\n")
    
    def close(self):
        """Ferme le navigateur"""
        self.driver.quit()


def main():
    """Fonction principale"""
    url = "https://matrix.centris.ca/Matrix/Public/Portal.aspx?ID=0-3319143035-10&eml=Y2JlYXVkZXRAcmF5aGFydmV5LmNh&L=2"
    
    scraper = CentrisScraper(url, headless=False)
    
    try:
        properties = scraper.scrape()
        
        # Afficher un résumé détaillé
        scraper.print_summary()
        
        # Afficher quelques exemples
        if properties:
            print("\nExemples de propriétés extraites:")
            for i, prop in enumerate(properties[:3], 1):
                print(f"\nPropriété {i}:")
                for key, value in prop.items():
                    if value:
                        print(f"  {key}: {value}")
        
        # Sauvegarder les données
        scraper.save_to_csv()
        scraper.save_to_json()
        
    except Exception as e:
        print(f"Erreur lors du scraping: {e}")
        import traceback
        traceback.print_exc()
    finally:
        scraper.close()


if __name__ == "__main__":
    main()

