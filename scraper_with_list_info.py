"""
Scraper COMPLET avec extraction des informations depuis la LISTE + le PANNEAU DE DÉTAIL
"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json
import re
import requests
from scraper_detail_complete import CentrisDetailScraperComplete


class CentrisScraperWithListInfo(CentrisDetailScraperComplete):
    """Scraper qui extrait d'abord les infos de la liste, puis les détails"""
    
    def extract_info_from_list(self, index=0):
        """
        Extrait les informations visibles dans la liste AVANT de cliquer
        
        Args:
            index: Index de la propriété dans la liste
            
        Returns:
            dict: Informations de base extraites de la liste
        """
        print(f"\n=== Extraction des infos depuis la liste (propriete #{index+1}) ===")
        
        list_data = {
            'prix': None,
            'adresse': None,
            'ville': None,
            'arrondissement': None,
            'quartier': None,
            'type_propriete': None,
            'annee_construction': None,
            'numero_centris': None,
            'date_envoi': None,
            'statut': None
        }
        
        try:
            # Attendre que la page soit chargée
            time.sleep(2)
            
            # Faire défiler pour s'assurer que les éléments sont visibles
            self.driver.execute_script("window.scrollTo(0, 1000);")
            time.sleep(1)
            
            # Obtenir tous les conteneurs de propriétés
            # Essayer plusieurs sélecteurs possibles
            property_containers = []
            
            # Méthode 1: Chercher par structure (divs qui contiennent prix + adresse + Centris)
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # Trouver tous les blocs qui contiennent "No Centris"
            all_text_blocks = soup.find_all(string=re.compile(r'No Centris', re.IGNORECASE))
            
            for text_block in all_text_blocks:
                # Remonter pour trouver le conteneur parent
                parent = text_block.parent
                for _ in range(5):
                    if parent:
                        parent_text = parent.get_text()
                        # Vérifier si ce bloc contient prix, adresse et No Centris
                        if '$' in parent_text and 'Québec' in parent_text and 'No Centris' in parent_text:
                            property_containers.append(parent)
                            break
                        try:
                            parent = parent.parent
                        except:
                            break
            
            print(f"Conteneurs de proprietes trouves: {len(property_containers)}")
            
            if not property_containers or index >= len(property_containers):
                print(f"[ATTENTION] Conteneur {index} non trouve, extraction limitee")
                return list_data
            
            # Extraire les infos du conteneur ciblé
            target_container = property_containers[index]
            container_text = target_container.get_text()
            
            print(f"\nTexte du conteneur (premiers 300 chars):")
            print(container_text[:300])
            print()
            
            # Extraire le prix (toujours en premier)
            prix_match = re.search(r'([\d\s]+)\s*\$\s*(?:\+\s*(?:TPS|TVQ|taxes))?', container_text)
            if prix_match:
                list_data['prix'] = prix_match.group(1).replace(' ', '').strip()
                print(f"[OK] Prix (liste): {list_data['prix']} $")
            
            # Extraire l'adresse (format: numéro + type de rue + nom)
            # Format typique: "220Z-226BZ Boul. Pierre-Bertrand"
            adresse_patterns = [
                # Pattern 1: Numéro (avec lettres et tirets) + Boul./Av./Rue + Nom
                r'(\d+[A-Z]*(?:-\d+[A-Z]*)*\s+(?:Boul\.|Boulevard|Av\.|Avenue|Rue|Ch\.|Chemin|Route)\s+[A-Za-zÀ-ÿ\'\-\.\s]+?)(?=\n|Québec|$)',
                # Pattern 2: Chercher spécifiquement les adresses avec tirets
                r'(\d+[A-Z]+-\d+[A-Z]+\s+(?:Boul\.|Av\.|Rue|Ch\.)\s+[^\n]+?)(?=\n)',
                # Pattern 3: Format simple
                r'(\d+(?:-\d+)?\s+(?:Boul\.|Av\.|Rue|Ch\.)\s+[^\n]+?)(?=\n)',
            ]
            
            for i, pattern in enumerate(adresse_patterns):
                match = re.search(pattern, container_text, re.IGNORECASE | re.MULTILINE)
                if match:
                    adresse = match.group(1).strip()
                    # Nettoyer l'adresse (enlever espaces multiples, retours à la ligne)
                    adresse = re.sub(r'\s+', ' ', adresse)
                    adresse = adresse.strip()
                    
                    # Vérifier que l'adresse est valide (contient au moins un chiffre et un mot)
                    if len(adresse) > 5 and any(char.isdigit() for char in adresse):
                        list_data['adresse'] = adresse
                        print(f"[OK] Adresse (liste, pattern {i+1}): {list_data['adresse']}")
                        break
            
            # Extraire ville et arrondissement (format: Québec (Arrondissement))
            ville_match = re.search(r'Québec\s*\(([^)]+)\)', container_text)
            if ville_match:
                list_data['ville'] = 'Québec'
                list_data['arrondissement'] = ville_match.group(1).strip()
                print(f"[OK] Ville/Arrondissement (liste): {list_data['ville']} ({list_data['arrondissement']})")
            
            # Extraire le quartier (format: "dans le quartier XXX construit")
            quartier_match = re.search(r'(?:dans le quartier|quartier)\s+([A-Za-zÀ-ÿ\s\-\/]+?)\s+construit', container_text, re.IGNORECASE)
            if quartier_match:
                list_data['quartier'] = quartier_match.group(1).strip()
                print(f"[OK] Quartier (liste): {list_data['quartier']}")
            
            # Extraire le type de propriété
            types = ['Quintuplex', 'Quadruplex', 'Triplex', 'Duplex', 'Maison', 'Condominium', 'Autre']
            for type_prop in types:
                if type_prop in container_text:
                    list_data['type_propriete'] = type_prop
                    print(f"[OK] Type (liste): {type_prop}")
                    break
            
            # Extraire l'année de construction
            year_match = re.search(r'construit\s+en\s+(\d{4})', container_text, re.IGNORECASE)
            if year_match:
                list_data['annee_construction'] = year_match.group(1)
                print(f"[OK] Annee (liste): {list_data['annee_construction']}")
            
            # Extraire le numéro Centris
            centris_match = re.search(r'No\s*Centris\s*[:\-]?\s*(\d+)', container_text, re.IGNORECASE)
            if centris_match:
                list_data['numero_centris'] = centris_match.group(1)
                print(f"[OK] Numero Centris (liste): {list_data['numero_centris']}")
            
            # Extraire la date d'envoi
            date_match = re.search(r"Date\s*d['']envoi\s*[:\-]?\s*(\d{4}-\d{2}-\d{2})", container_text)
            if date_match:
                list_data['date_envoi'] = date_match.group(1)
                print(f"[OK] Date d'envoi (liste): {list_data['date_envoi']}")
            
            # Extraire le statut (badge)
            if 'Nouvelle annonce' in container_text:
                list_data['statut'] = 'Nouvelle annonce'
                print(f"[OK] Statut (liste): Nouvelle annonce")
            elif 'Nouveau prix' in container_text:
                list_data['statut'] = 'Nouveau prix'
                print(f"[OK] Statut (liste): Nouveau prix")
            
            print("\n=== Fin extraction liste ===")
            
        except Exception as e:
            print(f"[ERREUR] Erreur extraction liste: {e}")
            import traceback
            traceback.print_exc()
        
        return list_data
    
    def extract_photo_urls(self):
        """
        Extrait les URLs de toutes les photos de la propriété
        
        Returns:
            list: Liste des URLs des photos
        """
        print("\n=== Extraction des URLs des photos ===")
        
        photo_urls = []
        
        try:
            # AVANT de cliquer, extraire les IDs des photos depuis les vignettes visibles
            print("Extraction des IDs de photos depuis le panneau actuel...")
            html_before = self.driver.page_source
            
            # Chercher toutes les URLs d'images matrixmedia dans le panneau
            import re
            pattern = r'https?://matrixmedia\.centris\.ca/MediaServer/GetMedia\.ashx\?[^"\'<>\s]+'
            all_media_before = re.findall(pattern, html_before)
            
            photo_ids = []
            for url in all_media_before:
                # Extraire le Key (ID de la photo)
                key_match = re.search(r'Key=(\d+)', url)
                if key_match:
                    photo_id = key_match.group(1)
                    if photo_id not in photo_ids:
                        photo_ids.append(photo_id)
            
            print(f"[INFO] {len(photo_ids)} ID(s) de photos trouvés")
            
            # Chercher le lien/bouton "Voir toutes les photos"
            photo_button_selectors = [
                "//a[contains(text(), 'Voir toutes les photos')]",
                "//a[contains(text(), 'Voir toute')]",
                "//button[contains(text(), 'photo')]",
                "//*[contains(text(), 'photo') and contains(text(), '(')]",
            ]
            
            photo_button = None
            for selector in photo_button_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        photo_button = elements[0]
                        print(f"[OK] Bouton photos trouvé: {photo_button.text[:50]}")
                        break
                except:
                    continue
            
            if not photo_button:
                print("[INFO] Bouton photos non trouvé, utilisation des IDs trouvés")
                # Construire les URLs avec les IDs trouvés
                if photo_ids:
                    for i, photo_id in enumerate(photo_ids):
                        # Construire l'URL en haute résolution
                        # Size=2 pour taille moyenne, Size=4 pour grande taille
                        photo_url = f"https://matrixmedia.centris.ca/MediaServer/GetMedia.ashx?Key={photo_id}&TableID=1&Type=1&Number={i}&Size=4"
                        photo_urls.append(photo_url)
                
                print(f"[OK] {len(photo_urls)} URLs de photos générées")
                return photo_urls
            
            # Extraire le nombre total de photos depuis le bouton
            import re
            total_photos = 9  # Valeur par défaut
            if photo_button:
                match = re.search(r'\((\d+)\)', photo_button.text)
                if match:
                    total_photos = int(match.group(1))
                    print(f"[OK] Nombre total de photos annoncé: {total_photos}")
            
            # Cliquer sur le bouton pour ouvrir la galerie (nouvelle page)
            print("Clic sur le bouton photos...")
            current_window = self.driver.current_window_handle
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", photo_button)
            time.sleep(0.5)
            photo_button.click()
            
            # Attendre que la nouvelle page/onglet se charge
            print("Attente du chargement de la galerie...")
            time.sleep(5)  # Attendre plus longtemps
            
            # Vérifier si un nouvel onglet s'est ouvert
            all_windows = self.driver.window_handles
            if len(all_windows) > 1:
                # Basculer vers le nouvel onglet
                for window in all_windows:
                    if window != current_window:
                        self.driver.switch_to.window(window)
                        break
                print(f"[OK] Nouvelle page ouverte: {self.driver.current_url[:80]}...")
                time.sleep(2)
            else:
                # C'est la même fenêtre, peut-être un overlay/modal
                print("[INFO] Galerie ouverte dans la même fenêtre")
            
            # NOUVELLE MÉTHODE: Utiliser l'API directement
            print(f"Extraction des URLs via l'API Centris...")
            
            # Extraire le numéro Centris depuis l'URL
            current_url = self.driver.current_url
            centris_id_match = re.search(r'/propriete/(\d+)/', current_url)
            
            if not centris_id_match:
                # Essayer depuis les données déjà extraites
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(current_url)
                if 'etok' in current_url:
                    centris_id_match = re.search(r'A(\d+)', current_url)
            
            high_res_photos = []
            
            if centris_id_match:
                centris_id = centris_id_match.group(1) if centris_id_match.lastindex else centris_id_match.group(0).replace('A', '')
                print(f"[INFO] Numéro Centris extrait de l'URL: {centris_id}")
                
                # Faire une requête POST vers l'API de photos
                try:
                    api_url = "https://www.centris.ca/Property/PhotoViewerDataListing"
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                        'X-Requested-With': 'XMLHttpRequest',
                        'Referer': current_url
                    }
                    
                    data = {
                        'id': centris_id,
                        'imageSize': 'large'  # Demander les grandes images
                    }
                    
                    response = requests.post(api_url, headers=headers, data=data, timeout=10)
                    
                    if response.status_code == 200:
                        api_data = response.json()
                        print(f"[OK] Réponse API reçue")
                        
                        # Extraire les URLs des photos depuis la réponse
                        if isinstance(api_data, dict) and 'images' in api_data:
                            for img_data in api_data['images']:
                                if 'url' in img_data:
                                    high_res_photos.append(img_data['url'])
                        elif isinstance(api_data, dict):
                            # Chercher les URLs dans toutes les valeurs
                            for key, value in api_data.items():
                                if isinstance(value, str) and 'mspublic.centris.ca' in value:
                                    high_res_photos.append(value)
                                elif isinstance(value, list):
                                    for item in value:
                                        if isinstance(item, str) and 'mspublic.centris.ca' in item:
                                            high_res_photos.append(item)
                        
                        print(f"[OK] {len(high_res_photos)} URLs extraites de l'API")
                    else:
                        print(f"[WARNING] API request failed: {response.status_code}")
                
                except Exception as e:
                    print(f"[WARNING] Erreur API: {e}")
            
            # Si l'API n'a pas fonctionné, fallback: chercher dans le HTML
            if len(high_res_photos) == 0:
                print(f"[INFO] Fallback: recherche dans le HTML...")
                time.sleep(3)
                
                html = self.driver.page_source
                pattern = r'https?://mspublic\.centris\.ca/media\.ashx\?[^"\'<>\s]+'
                all_media_urls = re.findall(pattern, html)
                
                for url in all_media_urls:
                    cleaned_url = url.replace('&amp;', '&').rstrip('";,')
                    if 'w=100' not in cleaned_url and 'h=75' not in cleaned_url:
                        if 't=pi' in cleaned_url or 'sm=' in cleaned_url:
                            if cleaned_url not in high_res_photos:
                                high_res_photos.append(cleaned_url)
            
            photo_urls = high_res_photos[:total_photos] if len(high_res_photos) > total_photos else high_res_photos
            
            if len(photo_urls) < total_photos:
                print(f"[WARNING] Seulement {len(photo_urls)} photos trouvées sur {total_photos} annoncées")
            
            # Fermer l'onglet de la galerie et revenir à la fenêtre principale
            if len(self.driver.window_handles) > 1:
                self.driver.close()
                self.driver.switch_to.window(current_window)
                print(f"[OK] Retour à la fenêtre principale")
            else:
                # Si c'était un modal, essayer de le fermer
                try:
                    close_buttons = self.driver.find_elements(By.XPATH, "//button[contains(@class, 'close') or contains(@aria-label, 'close') or contains(text(), '×')]")
                    if close_buttons:
                        close_buttons[0].click()
                        time.sleep(0.5)
                except:
                    pass
            
            # Enlever les doublons
            photo_urls = list(set(photo_urls))
            
            # Filtrer pour ne garder QUE les vraies photos de propriété
            # Les vraies photos viennent de matrixmedia.centris.ca/MediaServer/GetMedia.ashx
            filtered_urls = []
            for url in photo_urls:
                # Garder UNIQUEMENT les URLs du MediaServer qui sont les vraies photos
                if 'matrixmedia.centris.ca/MediaServer/GetMedia.ashx' in url:
                    filtered_urls.append(url)
            
            # Si on n'a pas trouvé toutes les photos dans le HTML, chercher dans le JavaScript
            if filtered_urls:
                print(f"[INFO] {len(filtered_urls)} photos trouvées dans le HTML")
                
                # Vérifier si on a toutes les photos
                import re
                total_photos_expected = 9
                if photo_button:
                    match = re.search(r'\((\d+)\)', photo_button.text)
                    if match:
                        total_photos_expected = int(match.group(1))
                
                # Si on n'a pas toutes les photos, chercher dans le JavaScript/source
                if len(filtered_urls) < total_photos_expected:
                    print(f"[INFO] Recherche de {total_photos_expected - len(filtered_urls)} photos supplémentaires dans le code source...")
                    
                    # Chercher dans le code source toutes les URLs de photos avec le pattern
                    page_source = self.driver.page_source
                    
                    # Pattern pour trouver les URLs complètes (avec & ou &amp;)
                    # Chercher toutes les URLs qui contiennent GetMedia.ashx
                    pattern = r'https://matrixmedia\.centris\.ca/MediaServer/GetMedia\.ashx\?[^"\'<>\s]+'
                    all_media_urls = re.findall(pattern, page_source)
                    
                    # Nettoyer et dédupliquer
                    cleaned_urls = []
                    for url in all_media_urls:
                        # Remplacer &amp; par &
                        cleaned_url = url.replace('&amp;', '&')
                        # Enlever les caractères indésirables à la fin
                        cleaned_url = cleaned_url.rstrip('";,')
                        
                        # Filtrer pour ne garder que les photos (Type=1 généralement)
                        if 'Type=1' in cleaned_url and cleaned_url not in cleaned_urls:
                            cleaned_urls.append(cleaned_url)
                    
                    # Ajouter les nouvelles URLs
                    for url in cleaned_urls:
                        if url not in filtered_urls:
                            filtered_urls.append(url)
                    
                    print(f"[INFO] Total de photos trouvées: {len(filtered_urls)}")
                
                photo_urls = filtered_urls
            
            # Si toujours pas assez de photos, essayer un filtrage moins strict
            if not filtered_urls:
                for url in photo_urls:
                    # Exclure les images qui sont clairement des icônes, overlays, markers, etc.
                    exclude_keywords = [
                        'icon', 'logo', 'button', 'arrow', 'thumb', 'spinner',
                        'poi_', 'marker_', 'overlay', 'background', 'mapimages',
                        'anchor', 'pin', 'flag', 'badge', 'banner'
                    ]
                    if not any(keyword in url.lower() for keyword in exclude_keywords):
                        # Vérifier que l'URL contient 'photo' ou 'image' ou 'media'
                        if any(kw in url.lower() for kw in ['photo', 'image', 'media', 'listing', 'property']):
                            filtered_urls.append(url)
                
                photo_urls = filtered_urls
            
            print(f"[OK] {len(photo_urls)} URLs de photos extraites")
            
            # Afficher les premières URLs pour vérification
            if photo_urls:
                print("\nPremières photos:")
                for i, url in enumerate(photo_urls[:3], 1):
                    print(f"  {i}. {url[:80]}...")
            
            # Fermer la galerie si elle est ouverte (optionnel)
            try:
                close_buttons = self.driver.find_elements(By.XPATH, "//button[contains(@class, 'close') or contains(text(), '×')]")
                if close_buttons:
                    close_buttons[0].click()
                    time.sleep(0.5)
            except:
                pass
            
        except Exception as e:
            print(f"[ERREUR] Erreur extraction photos: {e}")
            import traceback
            traceback.print_exc()
        
        return photo_urls
    
    def scrape_property_with_list_info(self, index=0):
        """
        Scrape complet: d'abord les infos de la liste, puis les détails du panneau
        
        Args:
            index: Index de la propriété
            
        Returns:
            dict: Données complètes combinées
        """
        print("\n" + "="*80)
        print(f"SCRAPING COMPLET PROPRIETE #{index+1} (LISTE + DETAILS)")
        print("="*80)
        
        # Étape 1: Extraire les infos de la liste
        list_info = self.extract_info_from_list(index)
        
        # Étape 2: Cliquer et extraire les détails
        if not self.click_on_property_by_index(index):
            print("[ERREUR] Impossible de cliquer sur la propriete")
            return list_info  # Retourner au moins les infos de la liste
        
        # Étape 3: Extraire les détails du panneau
        detail_info = self.extract_all_info_complete()
        
        # Étape 3.5: Extraire les URLs des photos
        photo_urls = self.extract_photo_urls()
        detail_info['photo_urls'] = photo_urls
        detail_info['nb_photos'] = len(photo_urls)
        
        # Étape 4: Fusionner les données (priorité aux infos de la liste pour certains champs)
        combined_data = detail_info.copy()
        
        # Les champs de la liste ont priorité s'ils sont remplis
        priority_fields = ['adresse', 'ville', 'arrondissement', 'quartier', 'type_propriete', 
                          'annee_construction', 'numero_centris', 'date_envoi', 'statut']
        
        for field in priority_fields:
            if list_info.get(field) and not combined_data.get(field):
                combined_data[field] = list_info[field]
                print(f"[MERGE] {field}: utilise valeur de la liste")
            elif list_info.get(field) and combined_data.get(field):
                # Si les deux ont une valeur, garder celle de la liste (plus fiable)
                if list_info[field] != combined_data[field]:
                    print(f"[MERGE] {field}: liste='{list_info[field]}' vs detail='{combined_data[field]}' -> garde liste")
                    combined_data[field] = list_info[field]
        
        # Ajouter les données de la liste comme référence
        combined_data['_donnees_liste'] = list_info
        
        return combined_data


def test_scraper_with_list():
    """Test du scraper avec extraction depuis la liste"""
    url = "https://matrix.centris.ca/Matrix/Public/Portal.aspx?ID=0-3319143035-10&eml=Y2JlYXVkZXRAcmF5aGFydmV5LmNh&L=2"
    
    print("="*80)
    print("TEST SCRAPER AVEC INFOS DE LA LISTE")
    print("="*80)
    
    scraper = CentrisScraperWithListInfo()
    
    if not scraper.init_driver():
        print("[ERREUR] Impossible d'initialiser le driver")
        return
    
    try:
        print(f"\nChargement de la page: {url}")
        scraper.driver.get(url)
        time.sleep(5)
        
        # Scraper la première propriété avec les infos de la liste
        property_data = scraper.scrape_property_with_list_info(index=0)
        
        if property_data:
            # Sauvegarder
            output_file = 'property_with_list_info.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(property_data, f, indent=2, ensure_ascii=False)
            
            print("\n" + "="*80)
            print("RESULTAT FINAL")
            print("="*80)
            print(f"\nDonnees sauvegardees dans '{output_file}'")
            
            print(f"\nInformations de base:")
            print(f"  Prix: {property_data.get('prix')}")
            print(f"  Adresse: {property_data.get('adresse')}")
            print(f"  Ville: {property_data.get('ville')}")
            print(f"  Arrondissement: {property_data.get('arrondissement')}")
            print(f"  Quartier: {property_data.get('quartier')}")
            print(f"  Type: {property_data.get('type_propriete')}")
            print(f"  Annee: {property_data.get('annee_construction')}")
            print(f"  No Centris: {property_data.get('numero_centris')}")
            print(f"  Date envoi: {property_data.get('date_envoi')}")
            print(f"  Statut: {property_data.get('statut')}")
            
            print(f"\nDonnees financieres:")
            print(f"  Revenus nets: {property_data.get('donnees_financieres', {}).get('revenus_nets_exploitation')}")
            print(f"  Depenses totales: {property_data.get('donnees_financieres', {}).get('depenses_exploitation', {}).get('total')}")
            
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
    test_scraper_with_list()

