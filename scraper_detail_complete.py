"""
Scraper COMPLET pour extraire TOUTES les informations détaillées d'une annonce Centris
Incluant les données financières, caractéristiques, inclusions, exclusions, etc.
"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json
import re


class CentrisDetailScraperComplete:
    def __init__(self):
        """Initialise le scraper pour les pages de détail"""
        self.driver = None
        self.current_property = {}
    
    def init_driver(self):
        """Initialise le driver Chrome"""
        try:
            import platform
            
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            # Spécifier le chemin Chrome uniquement sur Linux
            if platform.system() == 'Linux':
                chrome_options.binary_location = "/usr/bin/google-chrome"
            
            self.driver = webdriver.Chrome(options=chrome_options)
            return True
        except Exception as e:
            print(f"Erreur d'initialisation du driver: {e}")
            return False
    
    def click_on_property_by_index(self, index=0):
        """Clique sur une propriété par son index"""
        try:
            print(f"\n=== Clic sur la propriete #{index+1} ===")
            
            time.sleep(3)
            self.driver.execute_script("window.scrollTo(0, 1000);")
            time.sleep(2)
            
            # Chercher les liens vers les adresses
            property_links = self.driver.find_elements(
                By.XPATH, 
                "//a[contains(text(), 'Boul.') or contains(text(), 'Rue') or contains(text(), 'Av.') or contains(text(), 'Ch.')]"
            )
            
            if not property_links:
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                property_links = [link for link in all_links 
                                if link.text and len(link.text) > 15 
                                and any(char.isdigit() for char in link.text)
                                and ('Boul' in link.text or 'Rue' in link.text or 'Av.' in link.text)]
            
            print(f"Nombre de liens trouves: {len(property_links)}")
            
            if not property_links or index >= len(property_links):
                print("Aucun lien trouve ou index invalide")
                return False
            
            target_link = property_links[index]
            print(f"Clic sur: {target_link.text[:60]}")
            
            url_before = self.driver.current_url
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target_link)
            time.sleep(0.5)
            target_link.click()
            
            # Attendre que l'URL change
            for i in range(10):
                time.sleep(0.5)
                if '#' in self.driver.current_url and self.driver.current_url != url_before:
                    print(f"Panneau charge! URL: {self.driver.current_url}")
                    time.sleep(3)  # Attente pour le chargement complet
                    return True
            
            return False
            
        except Exception as e:
            print(f"Erreur lors du clic: {e}")
            return False
    
    def scroll_in_panel(self):
        """Fait défiler dans le panneau de détail pour charger tout le contenu"""
        try:
            print("\nDefilement du panneau pour charger tout le contenu...")
            
            # Trouver le panneau de détail (peut être un div avec overflow)
            # Essayer de faire défiler plusieurs fois
            for i in range(5):
                # Défiler vers le bas
                self.driver.execute_script("window.scrollBy(0, 500);")
                time.sleep(0.5)
            
            # Remonter en haut
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            print("Defilement termine")
            return True
        except Exception as e:
            print(f"Erreur lors du defilement: {e}")
            return False
    
    def extract_financial_data(self, soup, page_text):
        """Extrait les données financières complètes"""
        financial_data = {
            'revenus_bruts_potentiels': {
                'residentiel': None,
                'commercial': None,
                'stationnements': None,
                'autres': None,
                'total': None
            },
            'inoccupation_mauvaises_creances': {
                'residentiel': None,
                'commercial': None,
                'stationnements': None,
                'autres': None,
                'total': None
            },
            'revenus_bruts_effectifs': None,
            'depenses_exploitation': {
                'taxes_municipales': None,
                'taxe_scolaire': None,
                'taxes_secteur': None,
                'taxes_affaires': None,
                'taxes_eau': None,
                'electricite': None,
                'mazout': None,
                'gaz': None,
                'ascenseur': None,
                'assurances': None,
                'cable': None,
                'concierge': None,
                'contenant_sanitaire': None,
                'deneigement': None,
                'entretien': None,
                'equipement_location': None,
                'frais_communs': None,
                'gestion_administration': None,
                'ordures': None,
                'pelouse': None,
                'publicite': None,
                'securite': None,
                'recuperation_depenses': None,
                'total': None
            },
            'revenus_nets_exploitation': None
        }
        
        try:
            # Revenus bruts potentiels
            patterns = {
                'residentiel': r'Résidentiel\s*([\d\s,]+)\s*\$',
                'commercial': r'Commercial\s*([\d\s,]+)\s*\$',
                'stationnements': r'Stationnements[/]Garages\s*([\d\s,]+)\s*\$',
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    value = match.group(1).replace(' ', '').replace(',', '').strip()
                    financial_data['revenus_bruts_potentiels'][key] = value
                    print(f"[OK] Revenus {key}: {value} $")
            
            # Revenus bruts effectifs
            match = re.search(r'Revenus?\s+bruts?\s+effectifs?\s*([\d\s,]+)\s*\$', page_text, re.IGNORECASE)
            if match:
                financial_data['revenus_bruts_effectifs'] = match.group(1).replace(' ', '').replace(',', '').strip()
                print(f"[OK] Revenus bruts effectifs: {financial_data['revenus_bruts_effectifs']} $")
            
            # Revenus nets d'exploitation
            match = re.search(r"Revenus?\s+nets?\s+d['']exploitation\s*([\d\s,]+)\s*\$", page_text, re.IGNORECASE)
            if match:
                financial_data['revenus_nets_exploitation'] = match.group(1).replace(' ', '').replace(',', '').strip()
                print(f"[OK] Revenus nets exploitation: {financial_data['revenus_nets_exploitation']} $")
            
            # Dépenses d'exploitation - patterns pour TOUS les champs
            depenses_patterns = {
                'taxes_municipales': r'Taxes?\s+municipales?\s*\([\d]+\)\s*([\d\s,]+)\s*\$',
                'taxe_scolaire': r'Taxe?\s+scolaires?\s*\([\d]+\)\s*([\d\s,]+)\s*\$',
                'taxes_secteur': r'Taxes?\s+secteur\s*([\d\s,]+)\s*\$',
                'taxes_affaires': r"Taxes?\s+d['']affaires?\s*([\d\s,]+)\s*\$",
                'taxes_eau': r"Taxes?\s+d['']eau\s*([\d\s,]+)\s*\$",
                'electricite': r'Énergie\s*-\s*Électricité\s*([\d\s,]+)\s*\$',
                'mazout': r'Énergie\s*-\s*Mazout\s*([\d\s,]+)\s*\$',
                'gaz': r'Énergie\s*-\s*Gaz\s*([\d\s,]+)\s*\$',
                'ascenseur': r'Ascenseur\(s\)\s*([\d\s,]+)\s*\$',
                'assurances': r'Assurances?\s*([\d\s,]+)\s*\$',
                'cable': r'Câble\s*\(télé\)\s*([\d\s,]+)\s*\$',
                'concierge': r'Concierge\s*([\d\s,]+)\s*\$',
                'contenant_sanitaire': r'Contenant\s+sanitaire\s*([\d\s,]+)\s*\$',
                'deneigement': r'Déneigement\s*([\d\s,]+)\s*\$',
                'entretien': r'Entretien\s*([\d\s,]+)\s*\$',
                'equipement_location': r'Équipement\s*\(location\)\s*([\d\s,]+)\s*\$',
                'frais_communs': r'Frais\s+communs?\s*([\d\s,]+)\s*\$',
                'gestion_administration': r'Gestion[/]Administration\s*([\d\s,]+)\s*\$',
                'ordures': r'Ordures?\s*([\d\s,]+)\s*\$',
                'pelouse': r'Pelouse\s*([\d\s,]+)\s*\$',
                'publicite': r'Publicité\s*([\d\s,]+)\s*\$',
                'securite': r'Sécurité\s*([\d\s,]+)\s*\$',
                'recuperation_depenses': r'Récupération\s+des\s+dépenses?\s*([\d\s,]+)\s*\$',
            }
            
            depenses_found = 0
            for key, pattern in depenses_patterns.items():
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    financial_data['depenses_exploitation'][key] = match.group(1).replace(' ', '').replace(',', '').strip()
                    depenses_found += 1
            
            # Total des dépenses
            match = re.search(r'Total\s*([\d\s,]+)\s*\$.*?Revenus\s+nets', page_text, re.IGNORECASE | re.DOTALL)
            if match:
                financial_data['depenses_exploitation']['total'] = match.group(1).replace(' ', '').replace(',', '').strip()
                depenses_found += 1
            
            if depenses_found > 0:
                print(f"[OK] Depenses d'exploitation: {depenses_found} elements remplis sur {len(financial_data['depenses_exploitation'])}")
            
        except Exception as e:
            print(f"Erreur extraction donnees financieres: {e}")
        
        return financial_data
    
    def extract_units_info(self, page_text):
        """Extrait le nombre d'unités résidentielles et commerciales"""
        units_data = {
            'residentielles': [],
            'commerciales': [],
            'total_residentiel': 0,
            'total_commercial': 0
        }
        
        try:
            # Unités résidentielles (format: "3 ½" "3", "4 ½" "2")
            unit_patterns = [
                r'(\d)\s*½\s*(\d+)',
                r'(\d)\s+½\s+(\d+)',
            ]
            
            for pattern in unit_patterns:
                matches = re.findall(pattern, page_text)
                for match in matches:
                    type_unit = f"{match[0]} 1/2"
                    nombre = match[1]
                    units_data['residentielles'].append({
                        'type': type_unit,
                        'nombre': nombre
                    })
                    units_data['total_residentiel'] += int(nombre)
            
            # Commercial
            match = re.search(r'Commercial\s*(\d+)', page_text)
            if match:
                nombre = match.group(1)
                units_data['commerciales'].append({
                    'type': 'Commercial',
                    'nombre': nombre
                })
                units_data['total_commercial'] = int(nombre)
            
            if units_data['residentielles'] or units_data['commerciales']:
                print(f"[OK] Unites: {units_data['total_residentiel']} resid., {units_data['total_commercial']} comm.")
            
        except Exception as e:
            print(f"Erreur extraction unites: {e}")
        
        return units_data
    
    def extract_caracteristiques(self, page_text):
        """Extrait les caractéristiques détaillées"""
        caracteristiques = {
            'systeme_egouts': None,
            'approv_eau': None,
            'stationnement_detail': None,
            'chauffage': None,
            'eau_acces': None,
            'commodites_propriete': None,
            'commodites_batiment': None,
            'renovations': None
        }
        
        try:
            # Système d'égouts
            match = re.search(r"Système\s+d['']égouts?\s*([A-Za-zÀ-ÿ\s]+?)(?:\n|Approv)", page_text, re.IGNORECASE)
            if match:
                caracteristiques['systeme_egouts'] = match.group(1).strip()
            
            # Approvisionnement eau
            match = re.search(r'Approv\.?\s+eau\s*([A-Za-zÀ-ÿ\s]+?)(?:\n|Stationnement)', page_text, re.IGNORECASE)
            if match:
                caracteristiques['approv_eau'] = match.group(1).strip()
            
            # Stationnement détaillé
            match = re.search(r'Stationnement\s*\(total\)\s*([^\\n]+)', page_text, re.IGNORECASE)
            if match:
                caracteristiques['stationnement_detail'] = match.group(1).strip()
                print(f"[OK] Stationnement: {caracteristiques['stationnement_detail']}")
            
            # Chauffage
            match = re.search(r'Chauffage\s*([A-Za-zÀ-ÿ\s]+?)(?:\n|Eau)', page_text, re.IGNORECASE)
            if match:
                caracteristiques['chauffage'] = match.group(1).strip()
            
        except Exception as e:
            print(f"Erreur extraction caracteristiques: {e}")
        
        return caracteristiques
    
    def extract_inclusions_exclusions(self, page_text):
        """Extrait les inclusions, exclusions, remarques et addenda"""
        data = {
            'inclusions': None,
            'exclusions': None,
            'remarques': None,
            'addenda': None,
            'source': None
        }
        
        try:
            # Inclusions - Pattern amélioré
            incl_match = re.search(r'Inclusions?\s*[:\-]?\s*([A-ZÀ-Ÿ][^\n]{5,200})', page_text, re.IGNORECASE)
            if incl_match:
                inclusions = incl_match.group(1).strip()
                inclusions = re.sub(r'\s+', ' ', inclusions)
                # Arrêter avant "Exclusions" si présent
                inclusions = re.split(r'\s*Exclusions?', inclusions)[0].strip()
                if len(inclusions) > 3:
                    data['inclusions'] = inclusions
                    print(f"[OK] Inclusions: {data['inclusions'][:80]}...")
            
            # Exclusions - Pattern amélioré
            excl_match = re.search(r'Exclusions?\s*[:\-]?\s*([A-ZÀ-Ÿ][^\n]{5,200})', page_text, re.IGNORECASE)
            if excl_match:
                exclusions = excl_match.group(1).strip()
                exclusions = re.sub(r'\s+', ' ', exclusions)
                # Arrêter avant "Remarques" si présent
                exclusions = re.split(r'\s*Remarques?', exclusions)[0].strip()
                if len(exclusions) > 3:
                    data['exclusions'] = exclusions
                    print(f"[OK] Exclusions: {data['exclusions'][:80]}...")
            
            # Remarques
            match = re.search(r'Remarques?\s*((?:.|\n)+?)(?:Addenda|Source|$)', page_text, re.IGNORECASE)
            if match:
                remarques = match.group(1).strip()
                # Nettoyer les remarques
                remarques = re.sub(r'\s+', ' ', remarques)
                data['remarques'] = remarques
                print(f"[OK] Remarques: {remarques[:100]}...")
            
            # Addenda
            match = re.search(r'Addenda\s*((?:.|\n)+?)(?:Source|$)', page_text, re.IGNORECASE)
            if match:
                addenda = match.group(1).strip()
                addenda = re.sub(r'\s+', ' ', addenda)
                data['addenda'] = addenda
                print(f"[OK] Addenda: {addenda[:100]}...")
            
            # Source - Utiliser le Pattern 3 qui fonctionne !
            source = None
            
            # Pattern principal: Cherche "Source" suivi d'un nom d'agence jusqu'à "Agence immobilière"
            # Pattern robuste qui s'arrête à "Agence immobilière"
            match = re.search(r'Source[^A-ZÀ-Ÿ]*([A-ZÀ-Ÿ][A-Za-zÀ-ÿ0-9\s&\-\',/\.]+?Agence immobilière)', page_text, re.IGNORECASE)
            if match:
                source = match.group(1).strip()
                source = re.sub(r'\s+', ' ', source)
            else:
                # Si pas trouvé avec "Agence immobilière", essayer sans (moins robuste)
                match = re.search(r'Source[^A-ZÀ-Ÿ]*([A-ZÀ-Ÿ][A-Za-zÀ-ÿ0-9\s&\-\',/\.]+)', page_text, re.IGNORECASE)
                if match:
                    source = match.group(1).strip()
                    source = re.sub(r'\s+', ' ', source)
                    # Arrêter avant des mots indésirables (texte de la page qui n'est pas la source)
                    stop_words = r'(?:La présente|Inscription|Dernière|Le présent|mguimo|Erreur|Téléchargement|Données|Contact|Avis|Note|Voir)'
                    source = re.split(stop_words, source, flags=re.IGNORECASE)[0].strip()
                    # Nettoyer les caractères de ponctuation en fin de texte
                    source = re.sub(r'[\.,;:\s]+$', '', source)
                
            # Si pas trouvé ou trop court, chercher directement "RAY HARVEY"
            if not source or len(source) < 10:
                match = re.search(r'(RAY HARVEY\s*&\s*ASSOCIÉS[^a-z]{0,30}Agence immobilière)', page_text, re.IGNORECASE)
                if match:
                    source = match.group(1).strip()
                    source = re.sub(r'\s+', ' ', source)
            
            # Nettoyer la source finale
            if source:
                source = re.sub(r'[\n\r\t]+', ' ', source)
                source = re.sub(r'\s+', ' ', source)
                source = source.strip()
                # Limiter à 150 caractères max
                if len(source) > 150:
                    source = source[:150].strip()
                data['source'] = source
                print(f"[OK] Source: {data['source']}")
            else:
                print(f"[WARNING] Source non trouvee")
            
        except Exception as e:
            print(f"Erreur extraction inclusions/exclusions: {e}")
        
        return data
    
    def extract_all_info_complete(self):
        """Extrait TOUTES les informations disponibles (version complète)"""
        print("\n=== EXTRACTION COMPLETE DES INFORMATIONS ===")
        
        # Faire défiler pour charger tout le contenu
        self.scroll_in_panel()
        
        # Obtenir le HTML complet
        html = self.driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        page_text = soup.get_text()
        
        # Structure de données complète
        property_data = {
            # Informations de base
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
            
            # Caractéristiques
            'chambres': None,
            'salles_bain': None,
            'superficie_habitable': None,
            'superficie_terrain': None,
            'nb_photos': 0,
            
            # Courtier
            'courtier_email': None,
            'courtier_telephone': None,
            
            # NOUVELLES SECTIONS
            'donnees_financieres': {},
            'unites': {},
            'caracteristiques_detaillees': {},
            'inclusions': None,
            'exclusions': None,
            'remarques': None,
            'addenda': None,
            'source': None,
            
            'url': self.driver.current_url
        }
        
        try:
            # === INFORMATIONS DE BASE (comme avant) ===
            prix_match = re.search(r'(\d[\d\s]+)\s*\$', page_text)
            if prix_match:
                property_data['prix'] = prix_match.group(1).replace(' ', '').strip()
                print(f"[OK] Prix: {property_data['prix']} $")
            
            quartier_match = re.search(r'(?:dans le quartier|quartier)\s+([A-Za-zÀ-ÿ\s\-\/]+?)(?:\s+construit|\s+\d{4}|$)', page_text, re.IGNORECASE)
            if quartier_match:
                property_data['quartier'] = quartier_match.group(1).strip()
                print(f"[OK] Quartier: {property_data['quartier']}")
            
            types = ['Quintuplex', 'Quadruplex', 'Triplex', 'Duplex', 'Maison', 'Condominium', 'Autre']
            for type_prop in types:
                if type_prop in page_text:
                    property_data['type_propriete'] = type_prop
                    print(f"[OK] Type: {type_prop}")
                    break
            
            year_match = re.search(r'construit\s+en\s+(\d{4})', page_text, re.IGNORECASE)
            if year_match:
                property_data['annee_construction'] = year_match.group(1)
                print(f"[OK] Annee: {property_data['annee_construction']}")
            
            centris_match = re.search(r'(?:No|Numéro)\s*Centris\s*[:\-]?\s*(\d+)', page_text, re.IGNORECASE)
            if centris_match:
                property_data['numero_centris'] = centris_match.group(1)
                print(f"[OK] Numero Centris: {property_data['numero_centris']}")
            
            date_match = re.search(r"Date\s*d['']envoi\s*[:\-]?\s*(\d{4}-\d{2}-\d{2})", page_text)
            if date_match:
                property_data['date_envoi'] = date_match.group(1)
                print(f"[OK] Date d'envoi: {property_data['date_envoi']}")
            
            if 'Nouvelle annonce' in page_text:
                property_data['statut'] = 'Nouvelle annonce'
                print(f"[OK] Statut: Nouvelle annonce")
            
            sup_match = re.search(r'([\d\s,]+)\s*pi²', page_text)
            if sup_match:
                property_data['superficie_terrain'] = sup_match.group(1).replace(' ', '').replace(',', '').strip()
                print(f"[OK] Superficie terrain: {property_data['superficie_terrain']} pi²")
            
            photo_match = re.search(r'photo[s]?\s*\((\d+)\)', page_text, re.IGNORECASE)
            if photo_match:
                property_data['nb_photos'] = int(photo_match.group(1))
                print(f"[OK] Photos: {property_data['nb_photos']}")
            
            email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', page_text)
            if email_match:
                property_data['courtier_email'] = email_match.group(1)
                print(f"[OK] Email: {property_data['courtier_email']}")
            
            tel_match = re.search(r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})', page_text)
            if tel_match:
                property_data['courtier_telephone'] = tel_match.group(1)
                print(f"[OK] Telephone: {property_data['courtier_telephone']}")
            
            # === NOUVELLES EXTRACTIONS COMPLÈTES ===
            print("\n--- Extraction des donnees financieres ---")
            property_data['donnees_financieres'] = self.extract_financial_data(soup, page_text)
            
            print("\n--- Extraction des unites ---")
            property_data['unites'] = self.extract_units_info(page_text)
            
            print("\n--- Extraction des caracteristiques detaillees ---")
            property_data['caracteristiques_detaillees'] = self.extract_caracteristiques(page_text)
            
            print("\n--- Extraction inclusions/exclusions/remarques ---")
            inclusions_data = self.extract_inclusions_exclusions(page_text)
            property_data['inclusions'] = inclusions_data['inclusions']
            property_data['exclusions'] = inclusions_data['exclusions']
            property_data['remarques'] = inclusions_data['remarques']
            property_data['addenda'] = inclusions_data['addenda']
            property_data['source'] = inclusions_data['source']
            
            print("\n=== FIN DE L'EXTRACTION COMPLETE ===")
            
        except Exception as e:
            print(f"[ERREUR] Erreur lors de l'extraction: {e}")
            import traceback
            traceback.print_exc()
        
        return property_data
    
    def scrape_property_complete(self, index=0):
        """Fonction principale: scrape complet d'une propriété"""
        if self.click_on_property_by_index(index):
            return self.extract_all_info_complete()
        return None
    
    def close_panel(self):
        """Ferme le panneau de détail"""
        try:
            current_url = self.driver.current_url.split('#')[0]
            self.driver.get(current_url)
            time.sleep(2)
            return True
        except:
            return False
    
    def close(self):
        """Ferme le navigateur"""
        if self.driver:
            self.driver.quit()


def test_complete_scraper():
    """Test du scraper complet"""
    url = "https://matrix.centris.ca/Matrix/Public/Portal.aspx?ID=0-3319143035-10&eml=Y2JlYXVkZXRAcmF5aGFydmV5LmNh&L=2"
    
    print("="*80)
    print("TEST DU SCRAPER COMPLET - EXTRACTION TOTALE")
    print("="*80)
    
    scraper = CentrisDetailScraperComplete()
    
    if not scraper.init_driver():
        print("[ERREUR] Impossible d'initialiser le driver Chrome")
        return
    
    try:
        print(f"\nChargement de la page: {url}")
        scraper.driver.get(url)
        time.sleep(5)
        
        # Scraper la première propriété avec toutes les données
        property_data = scraper.scrape_property_complete(index=0)
        
        if property_data:
            print("\n" + "="*80)
            print("RESULTAT DU SCRAPING COMPLET")
            print("="*80)
            
            # Sauvegarder en JSON
            output_file = 'property_complete.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(property_data, f, indent=2, ensure_ascii=False)
            
            print(f"\n[OK] Donnees completes sauvegardees dans '{output_file}'")
            print(f"\nResume:")
            print(f"  - Prix: {property_data.get('prix')}")
            print(f"  - Type: {property_data.get('type_propriete')}")
            print(f"  - Revenus nets: {property_data.get('donnees_financieres', {}).get('revenus_nets_exploitation')}")
            print(f"  - Unites resid.: {property_data.get('unites', {}).get('total_residentiel', 0)}")
            print(f"  - Unites comm.: {property_data.get('unites', {}).get('total_commercial', 0)}")
            print(f"  - Remarques: {'Oui' if property_data.get('remarques') else 'Non'}")
            print(f"  - Addenda: {'Oui' if property_data.get('addenda') else 'Non'}")
            
            return property_data
        else:
            print("[ERREUR] Echec du scraping")
            
    except Exception as e:
        print(f"[ERREUR] Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nFermeture du navigateur dans 5 secondes...")
        time.sleep(5)
        scraper.close()


if __name__ == "__main__":
    test_complete_scraper()

