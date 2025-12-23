"""
Scraper pour extraire les informations détaillées d'une annonce Centris
"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json
import re


class CentrisDetailScraper:
    def __init__(self, headless=False):
        """Initialise le scraper pour les pages de détail"""
        self.setup_driver(headless)
        self.current_property = {}
    
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
    
    def wait_for_detail_panel(self, timeout=10):
        """Attend que le panneau de détail soit chargé"""
        try:
            # Attendre que l'URL change pour inclure un hash (#)
            WebDriverWait(self.driver, timeout).until(
                lambda d: '#' in d.current_url
            )
            time.sleep(2)  # Attente supplémentaire pour le chargement du contenu dynamique
            return True
        except Exception as e:
            print(f"Erreur lors de l'attente du panneau de détail: {e}")
            return False
    
    def click_on_property(self, property_link_element):
        """
        Clique sur le lien d'une propriété pour ouvrir le panneau de détail
        
        Args:
            property_link_element: Élément Selenium du lien de la propriété
            
        Returns:
            bool: True si le clic a réussi, False sinon
        """
        try:
            print(f"Clic sur la propriété: {property_link_element.text[:50]}")
            
            # Sauvegarder l'URL actuelle
            current_url = self.driver.current_url
            
            # Cliquer sur le lien
            self.driver.execute_script("arguments[0].scrollIntoView(true);", property_link_element)
            time.sleep(0.5)
            property_link_element.click()
            
            # Attendre que le panneau se charge
            if self.wait_for_detail_panel():
                print("Panneau de détail chargé avec succès")
                return True
            else:
                print("Échec du chargement du panneau de détail")
                return False
                
        except Exception as e:
            print(f"Erreur lors du clic sur la propriété: {e}")
            return False
    
    def extract_detail_info(self):
        """
        Extrait toutes les informations de la page de détail
        
        Returns:
            dict: Dictionnaire contenant toutes les informations extraites
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
            'description': None,
            'caracteristiques': {},
            'pieces': {},
            'dimensions': {},
            'equipements': [],
            'photos': [],
            'courtier': {},
            'communaute': {},
            'financier': {},
            'url': self.driver.current_url
        }
        
        try:
            # Obtenir le HTML de la page
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extraire le texte complet de la page
            page_text = soup.get_text()
            
            print("\n=== EXTRACTION DES INFORMATIONS ===")
            
            # 1. Extraire le prix
            prix_patterns = [
                r'(\d[\d\s,]+)\s*\$\s*(?:\+\s*TPS/TVQ)?',
                r'Prix\s*[:\-]\s*(\d[\d\s,]+)\s*\$',
            ]
            for pattern in prix_patterns:
                prix_match = re.search(pattern, page_text)
                if prix_match:
                    property_data['prix'] = prix_match.group(1).strip()
                    print(f"Prix: {property_data['prix']}")
                    break
            
            # 2. Extraire l'adresse (chercher dans les éléments en gras ou les liens)
            try:
                # Chercher les adresses dans le texte (format typique: numéro + nom de rue)
                adresse_pattern = r'(\d+[A-Z]?(?:-\d+[A-Z]?)?\s+(?:Boul\.|Av\.|Rue|Ch\.|Route)\s+[A-Za-zÀ-ÿ\s\-\.]+)'
                adresse_matches = re.findall(adresse_pattern, page_text)
                if adresse_matches:
                    property_data['adresse'] = adresse_matches[0].strip()
                    print(f"Adresse: {property_data['adresse']}")
            except Exception as e:
                print(f"Erreur extraction adresse: {e}")
            
            # 3. Extraire le numéro Centris
            centris_match = re.search(r'No\s*Centris\s*[:\-]?\s*(\d+)', page_text, re.IGNORECASE)
            if centris_match:
                property_data['numero_centris'] = centris_match.group(1)
                print(f"Numéro Centris: {property_data['numero_centris']}")
            
            # 4. Extraire la date d'envoi
            date_match = re.search(r"Date\s*d['']envoi\s*[:\-]?\s*(\d{4}-\d{2}-\d{2})", page_text)
            if date_match:
                property_data['date_envoi'] = date_match.group(1)
                print(f"Date d'envoi: {property_data['date_envoi']}")
            
            # 5. Extraire le type de propriété
            types = ['Quintuplex', 'Duplex', 'Triplex', 'Quadruplex', 'Autre', 'Maison', 'Condominium', 'Terrain']
            for type_prop in types:
                if type_prop in page_text:
                    property_data['type_propriete'] = type_prop
                    print(f"Type: {property_data['type_propriete']}")
                    break
            
            # 6. Extraire l'année de construction
            year_match = re.search(r'construit\s+en\s+(\d{4})', page_text, re.IGNORECASE)
            if year_match:
                property_data['annee_construction'] = year_match.group(1)
                print(f"Année de construction: {property_data['annee_construction']}")
            
            # 7. Extraire le quartier et la ville
            ville_match = re.search(r'Québec\s*\(([^)]+)\)', page_text)
            if ville_match:
                property_data['ville'] = ville_match.group(1).strip()
                print(f"Ville/Arrondissement: {property_data['ville']}")
            
            quartier_match = re.search(r'dans\s+le\s+quartier\s+([^c]+?)(?:construit|$)', page_text)
            if quartier_match:
                property_data['quartier'] = quartier_match.group(1).strip()
                print(f"Quartier: {property_data['quartier']}")
            
            # 8. Extraire le statut
            if 'Nouvelle annonce' in page_text:
                property_data['statut'] = 'Nouvelle annonce'
            elif 'Nouveau prix' in page_text:
                property_data['statut'] = 'Nouveau prix'
            
            # 9. Extraire le nombre de photos
            photo_match = re.search(r'(?:Voir\s+toutes?\s+les?\s+)?photo[s]?\s*\((\d+)\)', page_text, re.IGNORECASE)
            if photo_match:
                nb_photos = int(photo_match.group(1))
                property_data['photos'] = [f"Photo {i+1}" for i in range(nb_photos)]
                print(f"Nombre de photos: {nb_photos}")
            
            # 10. Extraire les caractéristiques principales
            # Chambres
            chambres_patterns = [
                r'(\d+)\s+chambre[s]?',
                r'Chambre[s]?\s*[:\-]\s*(\d+)',
            ]
            for pattern in chambres_patterns:
                chambres_match = re.search(pattern, page_text, re.IGNORECASE)
                if chambres_match:
                    property_data['pieces']['chambres'] = chambres_match.group(1)
                    print(f"Chambres: {property_data['pieces']['chambres']}")
                    break
            
            # Salles de bain
            sdb_patterns = [
                r'(\d+)\s+salle[s]?\s+de\s+bain[s]?',
                r'Salle[s]?\s+de\s+bain\s*[:\-]\s*(\d+)',
            ]
            for pattern in sdb_patterns:
                sdb_match = re.search(pattern, page_text, re.IGNORECASE)
                if sdb_match:
                    property_data['pieces']['salles_bain'] = sdb_match.group(1)
                    print(f"Salles de bain: {property_data['pieces']['salles_bain']}")
                    break
            
            # Superficie
            superficie_patterns = [
                r'Superficie\s*[:\-]?\s*([\d\s,]+)\s*(?:pi²|m²)',
                r'([\d\s,]+)\s*(?:pi²|m²)',
            ]
            for pattern in superficie_patterns:
                superficie_match = re.search(pattern, page_text)
                if superficie_match:
                    property_data['dimensions']['superficie'] = superficie_match.group(1).strip()
                    print(f"Superficie: {property_data['dimensions']['superficie']}")
                    break
            
            # Terrain
            terrain_patterns = [
                r'Terrain\s*[:\-]?\s*([\d\s,]+)\s*(?:pi²|m²)',
                r'Lot\s*[:\-]?\s*([\d\s,]+)\s*(?:pi²|m²)',
            ]
            for pattern in terrain_patterns:
                terrain_match = re.search(pattern, page_text)
                if terrain_match:
                    property_data['dimensions']['terrain'] = terrain_match.group(1).strip()
                    print(f"Terrain: {property_data['dimensions']['terrain']}")
                    break
            
            # 11. Extraire la description (si disponible dans un élément spécifique)
            description_elements = soup.find_all(['div', 'p'], class_=lambda x: x and ('description' in x.lower() or 'remarque' in x.lower()))
            if description_elements:
                description_text = ' '.join([elem.get_text().strip() for elem in description_elements])
                if len(description_text) > 50:
                    property_data['description'] = description_text[:500]
                    print(f"Description: {description_text[:100]}...")
            
            # 12. Extraire les informations du courtier
            courtier_patterns = [
                r'(?:Courtier|Agent)\s*[:\-]\s*([A-Za-zÀ-ÿ\s\-]+)',
                r'([A-Za-zÀ-ÿ\s]+)(?:\s+Courtier|\s+Agent)',
            ]
            for pattern in courtier_patterns:
                courtier_match = re.search(pattern, page_text)
                if courtier_match:
                    property_data['courtier']['nom'] = courtier_match.group(1).strip()
                    break
            
            # Email et téléphone
            email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', page_text)
            if email_match:
                property_data['courtier']['email'] = email_match.group(1)
            
            tel_match = re.search(r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})', page_text)
            if tel_match:
                property_data['courtier']['telephone'] = tel_match.group(1)
            
            # 13. Chercher des équipements/caractéristiques supplémentaires
            equipements_keywords = [
                'Garage', 'Stationnement', 'Piscine', 'Climatisation', 'Chauffage',
                'Électroménagers', 'Cuisine', 'Sous-sol', 'Balcon', 'Terrasse'
            ]
            for keyword in equipements_keywords:
                if keyword in page_text:
                    property_data['equipements'].append(keyword)
            
            if property_data['equipements']:
                print(f"Équipements: {', '.join(property_data['equipements'])}")
            
            print("\n=== FIN DE L'EXTRACTION ===\n")
            
        except Exception as e:
            print(f"Erreur lors de l'extraction des informations: {e}")
            import traceback
            traceback.print_exc()
        
        return property_data
    
    def scrape_property_detail(self, property_link_element):
        """
        Fonction principale: clique sur une propriété et extrait toutes les informations
        
        Args:
            property_link_element: Élément Selenium du lien de la propriété
            
        Returns:
            dict: Toutes les informations de la propriété
        """
        if self.click_on_property(property_link_element):
            return self.extract_detail_info()
        else:
            return None
    
    def close_detail_panel(self):
        """Ferme le panneau de détail en cliquant sur 'Retour aux résultats'"""
        try:
            # Chercher le bouton "Retour aux résultats"
            retour_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Retour')]"))
            )
            retour_button.click()
            time.sleep(1)
            return True
        except:
            # Alternative: supprimer le hash de l'URL
            current_url = self.driver.current_url.split('#')[0]
            self.driver.get(current_url)
            time.sleep(2)
            return True
    
    def close(self):
        """Ferme le navigateur"""
        self.driver.quit()


def test_scraper():
    """Fonction de test du scraper de détail"""
    url = "https://matrix.centris.ca/Matrix/Public/Portal.aspx?ID=0-3319143035-10&eml=Y2JlYXVkZXRAcmF5aGFydmV5LmNh&L=2"
    
    scraper = CentrisDetailScraper(headless=False)
    
    try:
        print("Chargement de la page principale...")
        scraper.driver.get(url)
        time.sleep(5)
        
        # Trouver les liens vers les propriétés
        print("Recherche des propriétés...")
        property_links = scraper.driver.find_elements(By.XPATH, "//a[contains(text(), 'Boul.') or contains(text(), 'Rue') or contains(text(), 'Av.')]")
        
        if not property_links:
            print("Aucune propriété trouvée, essai avec une autre méthode...")
            # Chercher tous les liens et filtrer
            all_links = scraper.driver.find_elements(By.TAG_NAME, "a")
            property_links = [link for link in all_links if link.text and len(link.text) > 10 and any(char.isdigit() for char in link.text)]
        
        print(f"Trouvé {len(property_links)} propriétés")
        
        if property_links:
            # Tester sur la première propriété
            print(f"\nTest sur la première propriété...")
            property_data = scraper.scrape_property_detail(property_links[0])
            
            if property_data:
                print("\n" + "="*80)
                print("DONNÉES EXTRAITES:")
                print("="*80)
                print(json.dumps(property_data, indent=2, ensure_ascii=False))
                
                # Sauvegarder dans un fichier
                with open('property_detail_test.json', 'w', encoding='utf-8') as f:
                    json.dump(property_data, f, indent=2, ensure_ascii=False)
                print("\nDonnées sauvegardées dans 'property_detail_test.json'")
            
            # Fermer le panneau
            print("\nFermeture du panneau de détail...")
            scraper.close_detail_panel()
            
        else:
            print("Aucune propriété trouvée pour le test")
    
    except Exception as e:
        print(f"Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nFermeture du navigateur dans 5 secondes...")
        time.sleep(5)
        scraper.close()


if __name__ == "__main__":
    test_scraper()

