"""
Scraper fonctionnel pour extraire les informations détaillées d'une annonce Centris
Version qui fonctionne réellement avec Selenium
"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json
import re


class CentrisDetailScraperFunctional:
    def __init__(self):
        """Initialise le scraper pour les pages de détail"""
        self.driver = None
        self.current_property = {}
    
    def init_driver(self):
        """Initialise le driver Chrome"""
        try:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            chrome_options.binary_location = "/usr/bin/google-chrome"
            
            # Essayer d'initialiser Chrome directement
            self.driver = webdriver.Chrome(options=chrome_options)
            return True
        except Exception as e:
            print(f"Erreur d'initialisation du driver: {e}")
            return False
    
    def click_on_property_by_index(self, index=0):
        """
        Clique sur une propriété par son index dans la liste
        
        Args:
            index: Index de la propriété (0 = première)
            
        Returns:
            bool: True si succès
        """
        try:
            print(f"\n=== Clic sur la propriete #{index+1} ===")
            
            # Attendre que la page soit chargée
            time.sleep(3)
            
            # Faire défiler pour charger le contenu
            self.driver.execute_script("window.scrollTo(0, 1000);")
            time.sleep(2)
            
            # Méthode 1: Chercher les liens vers les adresses
            property_links = self.driver.find_elements(
                By.XPATH, 
                "//a[contains(text(), 'Boul.') or contains(text(), 'Rue') or contains(text(), 'Av.') or contains(text(), 'Ch.')]"
            )
            
            if not property_links:
                print("Methode 1 echouee, essai methode 2...")
                # Méthode 2: Chercher tous les liens et filtrer
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                property_links = [link for link in all_links 
                                if link.text and len(link.text) > 15 
                                and any(char.isdigit() for char in link.text)
                                and ('Boul' in link.text or 'Rue' in link.text or 'Av.' in link.text)]
            
            if not property_links:
                print("Methode 2 echouee, essai methode 3...")
                # Méthode 3: Chercher via JavaScript
                property_links = self.driver.execute_script("""
                    let links = [];
                    document.querySelectorAll('a').forEach(function(link) {
                        let text = link.textContent;
                        if (text && text.length > 15 && /\\d/.test(text) && 
                            (text.includes('Boul') || text.includes('Rue') || text.includes('Av.') || text.includes('Ch.'))) {
                            links.push(link);
                        }
                    });
                    return links;
                """)

            
            print(f"Nombre de liens trouves: {len(property_links)}")
            
            if not property_links or len(property_links) == 0:
                print("ERREUR: Aucun lien de propriete trouve!")
                print("Peut-etre que le contenu est charge dynamiquement...")
                print("Sauvegarde du HTML pour debug...")
                with open('page_debug.html', 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                print("HTML sauvegarde dans 'page_debug.html'")
                return False
            
            if index >= len(property_links):
                print(f"Index {index} hors limites (max: {len(property_links)-1})")
                return False
            
            # Obtenir le lien ciblé
            target_link = property_links[index]
            link_text = target_link.text if hasattr(target_link, 'text') else str(target_link)
            print(f"Clic sur: {link_text[:60]}")
            
            # Sauvegarder l'URL actuelle
            url_before = self.driver.current_url
            
            # Faire défiler vers l'élément
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target_link)
            time.sleep(0.5)
            
            # Cliquer
            target_link.click()
            
            # Attendre que l'URL change
            print("Attente du chargement du panneau...")
            for i in range(10):
                time.sleep(0.5)
                if '#' in self.driver.current_url and self.driver.current_url != url_before:
                    print(f"Panneau charge! URL: {self.driver.current_url}")
                    time.sleep(2)  # Attente supplémentaire pour le contenu
                    return True
            
            print("Timeout: le panneau ne s'est pas ouvert")
            return False
            
        except Exception as e:
            print(f"Erreur lors du clic: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def extract_all_info(self):
        """
        Extrait TOUTES les informations disponibles dans le panneau de détail
        
        Returns:
            dict: Dictionnaire avec toutes les informations
        """
        print("\n=== EXTRACTION DES INFORMATIONS ===")
        
        property_data = {
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
            'description': None,
            'chambres': None,
            'salles_bain': None,
            'salles_eau': None,
            'stationnements': None,
            'superficie_habitable': None,
            'superficie_terrain': None,
            'dimensions_terrain': None,
            'nb_etages': None,
            'equipements': [],
            'caracteristiques': [],
            'nb_photos': 0,
            'url_photos': [],
            'courtier_nom': None,
            'courtier_email': None,
            'courtier_telephone': None,
            'courtier_agence': None,
            'taxes_municipales': None,
            'taxes_scolaires': None,
            'evaluation_municipale': None,
            'prix_par_pi2': None,
            'url': self.driver.current_url,
            'raw_text': None
        }
        
        try:
            # Obtenir tout le HTML
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # Obtenir tout le texte visible
            page_text = soup.get_text()
            property_data['raw_text'] = page_text[:1000]  # Sauvegarder les 1000 premiers caractères
            
            # === INFORMATIONS DE BASE ===
            
            # Prix
            prix_patterns = [
                r'(\d[\d\s]+)\s*\$\s*(?:\+\s*(?:TPS|TVQ|taxes))?',
                r'Prix[:\s]+(\d[\d\s]+)\s*\$',
            ]
            for pattern in prix_patterns:
                match = re.search(pattern, page_text)
                if match:
                    prix = match.group(1).replace(' ', '').strip()
                    property_data['prix'] = prix
                    print(f"[OK] Prix: {prix} $")
                    break
            
            # Adresse
            adresse_patterns = [
                r'(\d+[A-Z]?(?:-\d+[A-Z]?)?\s+(?:Boul\.|Av\.|Rue|Ch\.|Route|Chemin)\s+[A-Za-zÀ-ÿ\'\-\s\.]+?)(?:\n|Québec)',
            ]
            for pattern in adresse_patterns:
                match = re.search(pattern, page_text)
                if match:
                    property_data['adresse'] = match.group(1).strip()
                    print(f"[OK] Adresse: {property_data['adresse']}")
                    break
            
            # Ville et Arrondissement
            ville_pattern = r'Québec\s*\(([^)]+)\)'
            match = re.search(ville_pattern, page_text)
            if match:
                property_data['arrondissement'] = match.group(1).strip()
                property_data['ville'] = 'Québec'
                print(f"[OK] Ville: Québec ({property_data['arrondissement']})")
            
            # Quartier
            quartier_pattern = r'(?:dans le quartier|quartier)\s+([A-Za-zÀ-ÿ\s\-\/]+?)(?:\s+construit|\s+\d{4}|$)'
            match = re.search(quartier_pattern, page_text, re.IGNORECASE)
            if match:
                property_data['quartier'] = match.group(1).strip()
                print(f"[OK] Quartier: {property_data['quartier']}")
            
            # Type de propriété
            types = ['Quintuplex', 'Quadruplex', 'Triplex', 'Duplex', 'Maison', 'Condominium', 'Terrain', 'Autre']
            for type_prop in types:
                if type_prop in page_text:
                    property_data['type_propriete'] = type_prop
                    print(f"[OK] Type: {type_prop}")
                    break
            
            # Année de construction
            year_match = re.search(r'construit\s+en\s+(\d{4})', page_text, re.IGNORECASE)
            if year_match:
                property_data['annee_construction'] = year_match.group(1)
                print(f"[OK] Année: {property_data['annee_construction']}")
            
            # Numéro Centris
            centris_match = re.search(r'(?:No|Numéro)\s*Centris\s*[:\-]?\s*(\d+)', page_text, re.IGNORECASE)
            if centris_match:
                property_data['numero_centris'] = centris_match.group(1)
                print(f"[OK] Numéro Centris: {property_data['numero_centris']}")
            
            # Date d'envoi
            date_match = re.search(r"Date\s*d['']envoi\s*[:\-]?\s*(\d{4}-\d{2}-\d{2})", page_text)
            if date_match:
                property_data['date_envoi'] = date_match.group(1)
                print(f"[OK] Date d'envoi: {property_data['date_envoi']}")
            
            # Statut
            if 'Nouvelle annonce' in page_text:
                property_data['statut'] = 'Nouvelle annonce'
                print(f"[OK] Statut: Nouvelle annonce")
            elif 'Nouveau prix' in page_text:
                property_data['statut'] = 'Nouveau prix'
                print(f"[OK] Statut: Nouveau prix")
            
            # === CARACTÉRISTIQUES ===
            
            # Chambres
            chambres_patterns = [
                r'(\d+)\s+chambre[s]?(?:\s+à\s+coucher)?',
                r'Chambre[s]?\s*[:\-]\s*(\d+)',
            ]
            for pattern in chambres_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    property_data['chambres'] = match.group(1)
                    print(f"[OK] Chambres: {property_data['chambres']}")
                    break
            
            # Salles de bain
            sdb_patterns = [
                r'(\d+)\s+salle[s]?\s+de\s+bain[s]?',
                r'Salle[s]?\s+de\s+bain\s*[:\-]\s*(\d+)',
            ]
            for pattern in sdb_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    property_data['salles_bain'] = match.group(1)
                    print(f"[OK] Salles de bain: {property_data['salles_bain']}")
                    break
            
            # Salles d'eau
            sde_patterns = [
                r"(\d+)\s+salle[s]?\s+d['']eau",
            ]
            for pattern in sde_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    property_data['salles_eau'] = match.group(1)
                    print(f"[OK] Salles d'eau: {property_data['salles_eau']}")
                    break
            
            # Stationnements
            stat_patterns = [
                r'(\d+)\s+stationnement[s]?',
                r'Stationnement[s]?\s*[:\-]\s*(\d+)',
            ]
            for pattern in stat_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    property_data['stationnements'] = match.group(1)
                    print(f"[OK] Stationnements: {property_data['stationnements']}")
                    break
            
            # Superficie habitable
            sup_patterns = [
                r'Superficie\s+habitable\s*[:\-]?\s*([\d\s,]+)\s*(?:pi²|m²)',
                r'([\d\s,]+)\s*pi²(?:\s+habitable)?',
            ]
            for pattern in sup_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    property_data['superficie_habitable'] = match.group(1).replace(' ', '').replace(',', '').strip()
                    print(f"[OK] Superficie: {property_data['superficie_habitable']} pi²")
                    break
            
            # Superficie terrain
            terrain_patterns = [
                r'(?:Superficie|Terrain)\s*[:\-]?\s*([\d\s,]+)\s*(?:pi²|m²)',
                r'Lot\s*[:\-]?\s*([\d\s,]+)\s*(?:pi²|m²)',
            ]
            for pattern in terrain_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    property_data['superficie_terrain'] = match.group(1).replace(' ', '').replace(',', '').strip()
                    print(f"[OK] Terrain: {property_data['superficie_terrain']} pi²")
                    break
            
            # Photos
            photo_match = re.search(r'(?:Voir\s+toutes?\s+les?\s+)?photo[s]?\s*\((\d+)\)', page_text, re.IGNORECASE)
            if photo_match:
                property_data['nb_photos'] = int(photo_match.group(1))
                print(f"[OK] Photos: {property_data['nb_photos']}")
            
            # === INFORMATIONS COURTIER ===
            
            # Email du courtier
            email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', page_text)
            if email_match:
                property_data['courtier_email'] = email_match.group(1)
                print(f"[OK] Email courtier: {property_data['courtier_email']}")
            
            # Téléphone
            tel_match = re.search(r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})', page_text)
            if tel_match:
                property_data['courtier_telephone'] = tel_match.group(1)
                print(f"[OK] Téléphone: {property_data['courtier_telephone']}")
            
            # === ÉQUIPEMENTS ===
            equipements_keywords = [
                'Garage', 'Stationnement', 'Piscine', 'Spa', 'Climatisation', 'Chauffage',
                'Électroménagers', 'Cuisine', 'Sous-sol', 'Balcon', 'Terrasse', 'Cour',
                'Foyer', 'Cheminée', 'Fenestration', 'Isolation'
            ]
            
            for keyword in equipements_keywords:
                if keyword.lower() in page_text.lower():
                    property_data['equipements'].append(keyword)
            
            if property_data['equipements']:
                print(f"[OK] Équipements: {', '.join(property_data['equipements'][:5])}...")
            
            print("\n=== FIN DE L'EXTRACTION ===")
            
        except Exception as e:
            print(f"[ERREUR] Erreur lors de l'extraction: {e}")
            import traceback
            traceback.print_exc()
        
        return property_data
    
    def close_panel(self):
        """Ferme le panneau de détail"""
        try:
            # Supprimer le hash de l'URL
            current_url = self.driver.current_url.split('#')[0]
            self.driver.get(current_url)
            time.sleep(2)
            return True
        except:
            return False
    
    def scrape_property(self, index=0):
        """
        Fonction principale: clique sur une propriété et extrait toutes les infos
        
        Args:
            index: Index de la propriété à scraper
            
        Returns:
            dict: Toutes les informations extraites
        """
        if self.click_on_property_by_index(index):
            return self.extract_all_info()
        return None
    
    def close(self):
        """Ferme le navigateur"""
        if self.driver:
            self.driver.quit()


def test_functional_scraper():
    """Test du scraper fonctionnel"""
    url = "https://matrix.centris.ca/Matrix/Public/Portal.aspx?ID=0-3319143035-10&eml=Y2JlYXVkZXRAcmF5aGFydmV5LmNh&L=2"
    
    print("="*80)
    print("TEST DU SCRAPER FONCTIONNEL")
    print("="*80)
    
    scraper = CentrisDetailScraperFunctional()
    
    if not scraper.init_driver():
        print("[ERREUR] Impossible d'initialiser le driver Chrome")
        return
    
    try:
        print(f"\nChargement de la page: {url}")
        scraper.driver.get(url)
        print("Attente du chargement de la page...")
        time.sleep(5)
        
        print(f"\nTitre de la page: {scraper.driver.title}")
        
        # Scraper la première propriété
        print("\n" + "="*80)
        print("SCRAPING DE LA PREMIÈRE PROPRIÉTÉ")
        print("="*80)
        
        property_data = scraper.scrape_property(index=0)
        
        if property_data:
            print("\n" + "="*80)
            print("RÉSULTAT DU SCRAPING")
            print("="*80)
            
            # Afficher les données
            for key, value in property_data.items():
                if value and key != 'raw_text':
                    if isinstance(value, list):
                        if value:
                            print(f"{key}: {value}")
                    else:
                        print(f"{key}: {value}")
            
            # Sauvegarder en JSON
            output_file = 'property_scraped.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(property_data, f, indent=2, ensure_ascii=False)
            
            print(f"\n[OK] Données sauvegardées dans '{output_file}'")
            
            return property_data
        else:
            print("[ERREUR] Échec du scraping")
            
    except Exception as e:
        print(f"[ERREUR] Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nFermeture du navigateur dans 5 secondes...")
        time.sleep(5)
        scraper.close()


if __name__ == "__main__":
    test_functional_scraper()

