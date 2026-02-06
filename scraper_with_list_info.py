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
    
    def _find_property_containers(self):
        """
        Trouve tous les conteneurs de propriétés sur la page.
        Supporte Québec, Lévis et autres villes.
        
        Returns:
            list: Liste de tuples (container, centris_id)
        """
        html = self.driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        all_text_blocks = soup.find_all(string=re.compile(r'No\s*Centris', re.IGNORECASE))
        
        results = []
        seen_ids = set()
        
        for text_block in all_text_blocks:
            parent = text_block.parent
            for _ in range(8):
                if parent:
                    parent_text = parent.get_text()
                    # Vérifier : contient un prix ($) ET un numéro Centris
                    # Ne PAS filtrer par ville pour supporter Lévis, etc.
                    if '$' in parent_text and 'No Centris' in parent_text:
                        centris_match = re.search(r'No\s*Centris\s*[:\-]?\s*(\d+)', parent_text, re.IGNORECASE)
                        if centris_match:
                            cid = centris_match.group(1)
                            if cid not in seen_ids:
                                seen_ids.add(cid)
                                results.append((parent, cid))
                        break
                    try:
                        parent = parent.parent
                    except:
                        break
        
        return results
    
    def find_container_by_centris_id(self, centris_id):
        """
        Trouve le conteneur d'une propriété par son numéro Centris.
        
        Args:
            centris_id: Numéro Centris à trouver
            
        Returns:
            tuple: (container, index) ou (None, -1) si non trouvé
        """
        containers = self._find_property_containers()
        for idx, (container, cid) in enumerate(containers):
            if cid == centris_id:
                return container, idx
        return None, -1
    
    def click_on_property_by_centris_id(self, centris_id):
        """
        Trouve et clique sur une propriété par son numéro Centris.
        
        Args:
            centris_id: Numéro Centris de la propriété
            
        Returns:
            bool: True si le panneau s'est ouvert, False sinon
        """
        try:
            print(f"\n=== Clic sur la propriete Centris #{centris_id} ===")
            time.sleep(2)
            
            container, idx = self.find_container_by_centris_id(centris_id)
            
            if container is None:
                print(f"[ERREUR] Annonce Centris #{centris_id} non trouvée sur la page")
                return False
            
            container_text = container.get_text()
            print(f"[OK] Conteneur trouvé (index {idx}) pour Centris #{centris_id}")
            
            # Extraire l'adresse du conteneur
            adresse_patterns = [
                # Pattern pour "2020 27e Rue" (numero civique + ordinal + type de rue)
                r'(\d+(?:-\d+[A-Z]*)?\s+\d+(?:e|er|re|ère)\s+(?:Boul\.|Boulevard|Av\.|Avenue|Rue|Ch\.|Chemin|Route)[A-Za-zÀ-ÿ\'\-\.\s]*)(?=\n|Québec|Lévis|$)',
                r'(\d+(?:-\d+[A-Z]*)*\s+(?:(?:1re|2e|1er)\s+)?(?:Boul\.|Boulevard|Av\.|Avenue|Rue|Ch\.|Chemin|Route)\s+[A-Za-zÀ-ÿ\'\-\.\s]*?)(?=\n|Québec|Lévis|$)',
                r'(\d+[A-Z]*(?:-\d+[A-Z]*)*\s+(?:Boul\.|Boulevard|Av\.|Avenue|Rue|Ch\.|Chemin|Route)\s+[A-Za-zÀ-ÿ\'\-\.\s]+?)(?=\n|Québec|Lévis|$)',
            ]
            adresse_match = None
            for pattern in adresse_patterns:
                adresse_match = re.search(pattern, container_text, re.IGNORECASE | re.MULTILINE)
                if adresse_match:
                    break
            
            if not adresse_match:
                print("[ERREUR] Impossible d'extraire l'adresse du conteneur")
                return False
            
            adresse_cible = adresse_match.group(1).strip()
            adresse_cible = re.sub(r'\s+', ' ', adresse_cible)
            print(f"Adresse cible: {adresse_cible}")
            
            # Chercher les liens de propriété cliquables
            self.driver.execute_script("window.scrollTo(0, 1000);")
            time.sleep(1)
            
            property_links = self.driver.find_elements(
                By.XPATH, 
                "//a[contains(text(), 'Boul.') or contains(text(), 'Rue') or contains(text(), 'Av.') or contains(text(), 'Ch.') or contains(text(), 'Avenue')]"
            )
            
            if not property_links:
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                property_links = [link for link in all_links 
                                if link.text and len(link.text) > 10 
                                and any(char.isdigit() for char in link.text)
                                and ('Boul' in link.text or 'Rue' in link.text or 'Av.' in link.text or 'Avenue' in link.text)]
            
            print(f"Liens de proprietes trouves: {len(property_links)}")
            
            # Chercher le lien qui correspond à l'adresse cible
            target_link = None
            for link in property_links:
                link_text = link.text.strip()
                link_text_clean = re.sub(r'\s+', ' ', link_text)
                adresse_clean = re.sub(r'\s+', ' ', adresse_cible)
                
                if adresse_clean in link_text_clean or link_text_clean in adresse_clean:
                    target_link = link
                    print(f"Lien correspondant trouve: {link_text[:60]}")
                    break
            
            if not target_link:
                print(f"[ERREUR] Aucun lien ne correspond a l'adresse: {adresse_cible}")
                print("Liens disponibles:")
                for i, link in enumerate(property_links[:10]):
                    print(f"  {i}: {link.text[:60]}")
                return False
            
            # Cliquer sur le lien et attendre le panneau
            return self._click_and_wait_panel(target_link)
                
        except Exception as e:
            print(f"Erreur lors du clic par Centris ID: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def extract_info_from_list_by_centris_id(self, centris_id):
        """
        Extrait les informations de la liste pour une propriété identifiée par son numéro Centris.
        
        Args:
            centris_id: Numéro Centris de la propriété
            
        Returns:
            dict: Informations de base extraites de la liste
        """
        print(f"\n=== Extraction des infos depuis la liste (Centris #{centris_id}) ===")
        
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
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, 1000);")
            time.sleep(1)
            
            container, idx = self.find_container_by_centris_id(centris_id)
            
            if container is None:
                print(f"[ATTENTION] Conteneur pour Centris #{centris_id} non trouvé")
                return list_data
            
            container_text = container.get_text()
            
            print(f"\nTexte du conteneur (premiers 300 chars):")
            print(container_text[:300])
            print()
            
            # Extraire le prix
            prix_match = re.search(r'([\d\s]+)\s*\$\s*(?:\+\s*(?:TPS|TVQ|taxes))?', container_text)
            if prix_match:
                list_data['prix'] = prix_match.group(1).replace(' ', '').strip()
                print(f"[OK] Prix (liste): {list_data['prix']} $")
            
            # Extraire l'adresse
            adresse_patterns = [
                # Pattern pour "2020 27e Rue" (numero civique + ordinal + type de rue)
                r'(\d+(?:-\d+[A-Z]*)?\s+\d+(?:e|er|re|ère)\s+(?:Boul\.|Boulevard|Av\.|Avenue|Rue|Ch\.|Chemin|Route)[A-Za-zÀ-ÿ\'\-\.\s]*)(?=\n|Québec|Lévis|$)',
                r'(\d+(?:-\d+[A-Z]*)*\s+(?:(?:1re|2e|1er)\s+)?(?:Boul\.|Boulevard|Av\.|Avenue|Rue|Ch\.|Chemin|Route)\s+[A-Za-zÀ-ÿ\'\-\.\s]*?)(?=\n|Québec|Lévis|$)',
                r'(\d+[A-Z]*(?:-\d+[A-Z]*)*\s+(?:Boul\.|Boulevard|Av\.|Avenue|Rue|Ch\.|Chemin|Route)\s+[A-Za-zÀ-ÿ\'\-\.\s]+?)(?=\n|Québec|Lévis|$)',
                r'(\d+[A-Z]+-\d+[A-Z]+\s+(?:Boul\.|Av\.|Rue|Ch\.)\s+[^\n]+?)(?=\n)',
                r'(\d+(?:-\d+)?\s+(?:Boul\.|Av\.|Rue|Ch\.)\s+[^\n]+?)(?=\n)',
            ]
            
            for i, pattern in enumerate(adresse_patterns):
                match = re.search(pattern, container_text, re.IGNORECASE | re.MULTILINE)
                if match:
                    adresse = match.group(1).strip()
                    adresse = re.sub(r'\s+', ' ', adresse)
                    adresse = adresse.strip()
                    if len(adresse) > 5 and any(char.isdigit() for char in adresse):
                        list_data['adresse'] = adresse
                        print(f"[OK] Adresse (liste, pattern {i+1}): {list_data['adresse']}")
                        break
            
            # Extraire ville et arrondissement - supporter Québec ET Lévis
            ville_match = re.search(r'(Québec|Lévis)\s*\(([^)]+)\)', container_text)
            if ville_match:
                list_data['ville'] = ville_match.group(1).strip()
                list_data['arrondissement'] = ville_match.group(2).strip()
                print(f"[OK] Ville/Arrondissement (liste): {list_data['ville']} ({list_data['arrondissement']})")
            
            # Extraire le quartier
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
            
            # Extraire le statut
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
    
    def scrape_property_by_centris_id(self, centris_id, skip_photos=False):
        """
        Scrape complet d'une propriété identifiée par son numéro Centris.
        
        Args:
            centris_id: Numéro Centris de la propriété
            skip_photos: Si True, ne pas extraire les URLs des photos
            
        Returns:
            dict: Données complètes combinées
        """
        print("\n" + "="*80)
        print(f"SCRAPING COMPLET PROPRIETE CENTRIS #{centris_id}" + (" [sans photos]" if skip_photos else ""))
        print("="*80)
        
        # Étape 1: Extraire les infos de la liste par Centris ID
        list_info = self.extract_info_from_list_by_centris_id(centris_id)
        
        # Étape 2: Cliquer sur la propriété par Centris ID
        if not self.click_on_property_by_centris_id(centris_id):
            print("[ERREUR] Impossible de cliquer sur la propriete")
            return list_info  # Retourner au moins les infos de la liste
        
        # Étape 3: Extraire les détails du panneau
        detail_info = self.extract_all_info_complete()
        
        # Étape 3.5: Photos
        if skip_photos:
            detail_info['photo_urls'] = []
            detail_info['nb_photos'] = 0
        else:
            photo_urls = self.extract_photo_urls()
            detail_info['photo_urls'] = photo_urls
            detail_info['nb_photos'] = len(photo_urls)
        
        # Étape 4: Fusionner les données (priorité aux infos de la liste)
        combined_data = detail_info.copy()
        
        priority_fields = ['adresse', 'ville', 'arrondissement', 'quartier', 'type_propriete', 
                          'annee_construction', 'numero_centris', 'date_envoi', 'statut']
        
        for field in priority_fields:
            if list_info.get(field) and not combined_data.get(field):
                combined_data[field] = list_info[field]
                print(f"[MERGE] {field}: utilise valeur de la liste")
            elif list_info.get(field) and combined_data.get(field):
                if list_info[field] != combined_data[field]:
                    print(f"[MERGE] {field}: liste='{list_info[field]}' vs detail='{combined_data[field]}' -> garde liste")
                    combined_data[field] = list_info[field]
        
        combined_data['_donnees_liste'] = list_info
        
        # Fermer le panneau de détail
        print("\n=== Fermeture du panneau ===")
        if self.close_panel():
            print("[OK] Panneau ferme, retour a la liste")
        else:
            print("[WARNING] Echec fermeture panneau")
        
        return combined_data
    
    def _click_and_wait_panel(self, target_link):
        """
        Clique sur un lien et attend que le panneau de détail s'ouvre.
        
        Args:
            target_link: Élément Selenium du lien à cliquer
            
        Returns:
            bool: True si le panneau s'est ouvert
        """
        try:
            url_before = self.driver.current_url
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target_link)
            time.sleep(0.5)
            
            target_link.click()
            print("[INFO] Clic effectue, attente de l'ouverture du panneau...")
            
            panel_opened = False
            for i in range(15):
                time.sleep(0.5)
                url_changed = '#' in self.driver.current_url and self.driver.current_url != url_before
                try:
                    html = self.driver.page_source
                    panel_indicators = [
                        'Caractéristiques du bâtiment',
                        'Dimensions des pièces',
                        'Revenus et dépenses',
                        'Addenda',
                        'Inclusions',
                    ]
                    panel_present = any(indicator in html for indicator in panel_indicators)
                except:
                    panel_present = False
                
                if url_changed or panel_present:
                    print(f"[OK] Panneau detecte! (tentative {i+1})")
                    if url_changed:
                        print(f"     URL: {self.driver.current_url}")
                    if panel_present:
                        print(f"     Elements de detail detectes dans le DOM")
                    time.sleep(3)
                    panel_opened = True
                    break
            
            if panel_opened:
                return True
            
            # Fallback JavaScript
            print("[INFO] Tentative avec clic JavaScript...")
            self.driver.execute_script("arguments[0].click();", target_link)
            
            for i in range(15):
                time.sleep(0.5)
                url_changed = '#' in self.driver.current_url and self.driver.current_url != url_before
                try:
                    html = self.driver.page_source
                    panel_indicators = ['Caractéristiques du bâtiment', 'Dimensions des pièces', 'Revenus et dépenses', 'Addenda', 'Inclusions']
                    panel_present = any(indicator in html for indicator in panel_indicators)
                except:
                    panel_present = False
                
                if url_changed or panel_present:
                    print(f"[OK] Panneau detecte (JS)! (tentative {i+1})")
                    time.sleep(3)
                    return True
            
            print("[ERREUR] Le panneau ne s'est pas ouvert apres toutes les tentatives")
            return False
            
        except Exception as e:
            print(f"[ERREUR] Echec du clic: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def click_on_property_by_index(self, index=0):
        """
        Version synchronisée avec extract_info_from_list()
        Utilise la MÊME logique pour trouver les conteneurs
        """
        try:
            print(f"\n=== Clic sur la propriete #{index+1} ===")
            time.sleep(2)
            
            # Utiliser la méthode centralisée pour trouver les conteneurs
            containers = self._find_property_containers()
            property_containers = [c[0] for c in containers]
            
            print(f"Conteneurs de proprietes trouves: {len(property_containers)}")
            
            if not property_containers or index >= len(property_containers):
                print("Index invalide ou aucun conteneur trouve")
                return False
            
            # Extraire l'adresse du conteneur à l'index voulu
            target_container = property_containers[index]
            container_text = target_container.get_text()
            
            # Patterns d'extraction d'adresse (priorité: adresse complète type "1209-1213 1re Avenue")
            adresse_patterns = [
                # Pattern pour "2020 27e Rue" (numero civique + ordinal + type de rue)
                r'(\d+(?:-\d+[A-Z]*)?\s+\d+(?:e|er|re|ère)\s+(?:Boul\.|Boulevard|Av\.|Avenue|Rue|Ch\.|Chemin|Route)[A-Za-zÀ-ÿ\'\-\.\s]*)(?=\n|Québec|Lévis|$)',
                # Pattern avec "1re"/"2e"/"1er" avant Avenue/Rue (ex: 1209-1213 1re Avenue)
                r'(\d+(?:-\d+[A-Z]*)*\s+(?:(?:1re|2e|1er)\s+)?(?:Boul\.|Boulevard|Av\.|Avenue|Rue|Ch\.|Chemin|Route)\s+[A-Za-zÀ-ÿ\'\-\.\s]*?)(?=\n|Québec|Lévis|$)',
                # Pattern standard (ex: 420 Boul. Pierre-Bertrand)
                r'(\d+[A-Z]*(?:-\d+[A-Z]*)*\s+(?:Boul\.|Boulevard|Av\.|Avenue|Rue|Ch\.|Chemin|Route)\s+[A-Za-zÀ-ÿ\'\-\.\s]+?)(?=\n|Québec|Lévis|$)',
            ]
            adresse_match = None
            for pattern in adresse_patterns:
                adresse_match = re.search(pattern, container_text, re.IGNORECASE | re.MULTILINE)
                if adresse_match:
                    break
            
            if not adresse_match:
                print("[ERREUR] Impossible d'extraire l'adresse du conteneur")
                return False
            
            adresse_cible = adresse_match.group(1).strip()
            adresse_cible = re.sub(r'\s+', ' ', adresse_cible)
            print(f"Adresse cible: {adresse_cible}")
            
            # Chercher TOUS les liens de propriété (inclure "Avenue" en entier pour 1re Avenue, etc.)
            self.driver.execute_script("window.scrollTo(0, 1000);")
            time.sleep(1)
            
            property_links = self.driver.find_elements(
                By.XPATH, 
                "//a[contains(text(), 'Boul.') or contains(text(), 'Rue') or contains(text(), 'Av.') or contains(text(), 'Ch.') or contains(text(), 'Avenue')]"
            )
            
            if not property_links:
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                property_links = [link for link in all_links 
                                if link.text and len(link.text) > 10 
                                and any(char.isdigit() for char in link.text)
                                and ('Boul' in link.text or 'Rue' in link.text or 'Av.' in link.text or 'Avenue' in link.text)]
            
            print(f"Liens de proprietes trouves: {len(property_links)}")
            
            # Chercher le lien qui correspond à l'adresse cible
            target_link = None
            for link in property_links:
                link_text = link.text.strip()
                # Nettoyer et normaliser
                link_text_clean = re.sub(r'\s+', ' ', link_text)
                adresse_clean = re.sub(r'\s+', ' ', adresse_cible)
                
                # Vérifier si c'est le bon lien
                if adresse_clean in link_text_clean or link_text_clean in adresse_clean:
                    target_link = link
                    print(f"Lien correspondant trouve: {link_text[:60]}")
                    break
            
            if not target_link:
                print(f"[ERREUR] Aucun lien ne correspond a l'adresse: {adresse_cible}")
                # Debug : afficher tous les liens trouvés
                print("Liens disponibles:")
                for i, link in enumerate(property_links[:10]):
                    print(f"  {i}: {link.text[:60]}")
                return False
            
            # Cliquer sur le lien et attendre le panneau
            return self._click_and_wait_panel(target_link)
                
        except Exception as e:
            print(f"Erreur lors du clic: {e}")
            import traceback
            traceback.print_exc()
            return False
    
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
            
            # Utiliser la méthode centralisée pour trouver les conteneurs
            containers = self._find_property_containers()
            property_containers = [c[0] for c in containers]
            
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
            adresse_patterns = [
                # Pattern pour "2020 27e Rue" (numero civique + ordinal + type de rue)
                r'(\d+(?:-\d+[A-Z]*)?\s+\d+(?:e|er|re|ère)\s+(?:Boul\.|Boulevard|Av\.|Avenue|Rue|Ch\.|Chemin|Route)[A-Za-zÀ-ÿ\'\-\.\s]*)(?=\n|Québec|Lévis|$)',
                r'(\d+(?:-\d+[A-Z]*)*\s+(?:(?:1re|2e|1er)\s+)?(?:Boul\.|Boulevard|Av\.|Avenue|Rue|Ch\.|Chemin|Route)\s+[A-Za-zÀ-ÿ\'\-\.\s]*?)(?=\n|Québec|Lévis|$)',
                r'(\d+[A-Z]*(?:-\d+[A-Z]*)*\s+(?:Boul\.|Boulevard|Av\.|Avenue|Rue|Ch\.|Chemin|Route)\s+[A-Za-zÀ-ÿ\'\-\.\s]+?)(?=\n|Québec|Lévis|$)',
                r'(\d+[A-Z]+-\d+[A-Z]+\s+(?:Boul\.|Av\.|Rue|Ch\.)\s+[^\n]+?)(?=\n)',
                r'(\d+(?:-\d+)?\s+(?:Boul\.|Av\.|Rue|Ch\.)\s+[^\n]+?)(?=\n)',
            ]
            
            for i, pattern in enumerate(adresse_patterns):
                match = re.search(pattern, container_text, re.IGNORECASE | re.MULTILINE)
                if match:
                    adresse = match.group(1).strip()
                    adresse = re.sub(r'\s+', ' ', adresse)
                    adresse = adresse.strip()
                    if len(adresse) > 5 and any(char.isdigit() for char in adresse):
                        list_data['adresse'] = adresse
                        print(f"[OK] Adresse (liste, pattern {i+1}): {list_data['adresse']}")
                        break
            
            # Extraire ville et arrondissement - supporter Québec ET Lévis
            ville_match = re.search(r'(Québec|Lévis)\s*\(([^)]+)\)', container_text)
            if ville_match:
                list_data['ville'] = ville_match.group(1).strip()
                list_data['arrondissement'] = ville_match.group(2).strip()
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
            
            # MÉTHODE: Naviguer manuellement dans le carrousel photo par photo
            print(f"Navigation dans le carrousel pour extraire les {total_photos} photos...")
            high_res_photos = []
            
            # Attendre que la première photo se charge
            time.sleep(4)
            
            for photo_num in range(total_photos):
                print(f"  Extraction photo {photo_num + 1}/{total_photos}...")
                
                try:
                    # Attendre un peu pour être sûr que la photo est chargée
                    time.sleep(2)
                    
                    # Extraire l'URL de la photo actuellement affichée
                    html = self.driver.page_source
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Chercher l'image principale affichée (plusieurs patterns)
                    # La photo active est généralement dans un élément avec une classe spécifique
                    all_imgs = soup.find_all('img')
                    
                    for img in all_imgs:
                        src = img.get('src') or img.get('data-src')
                        if src and 'mspublic.centris.ca/media.ashx' in src:
                            # Vérifier que c'est une grande image (pas une vignette)
                            if 'w=100' not in src and 'h=75' not in src:
                                if 't=pi' in src or 'sm=' in src:
                                    if src not in high_res_photos:
                                        high_res_photos.append(src)
                                        print(f"    [OK] Photo {photo_num + 1}: {src[:80]}...")
                                        break
                    
                    # Après avoir extrait la photo, cliquer sur "Suivant" pour la prochaine
                    if photo_num < total_photos - 1:
                        # Essayer plusieurs méthodes pour passer à la photo suivante
                        next_clicked = False
                        
                        # Méthode 1: Touche flèche droite
                        try:
                            from selenium.webdriver.common.keys import Keys
                            from selenium.webdriver.common.action_chains import ActionChains
                            
                            actions = ActionChains(self.driver)
                            actions.send_keys(Keys.ARROW_RIGHT).perform()
                            next_clicked = True
                            print(f"    [NEXT] Fleche droite appuyee")
                            time.sleep(1.5)
                        except Exception as e:
                            print(f"    [WARNING] Flèche droite échouée: {e}")
                        
                        # Méthode 2: Cliquer sur un bouton suivant
                        if not next_clicked:
                            next_button_selectors = [
                                "//button[contains(@class, 'next')]",
                                "//button[contains(@class, 'right')]",
                                "//a[contains(@class, 'next')]",
                                "//a[contains(@class, 'right')]",
                                "//*[@role='button' and contains(@aria-label, 'next')]",
                                "//*[@role='button' and contains(@aria-label, 'Next')]",
                                "//button[contains(text(), '›')]",
                                "//button[contains(text(), '→')]",
                            ]
                            
                            for selector in next_button_selectors:
                                try:
                                    buttons = self.driver.find_elements(By.XPATH, selector)
                                    for btn in buttons:
                                        if btn.is_displayed() and btn.is_enabled():
                                            btn.click()
                                            next_clicked = True
                                            print(f"    [NEXT] Bouton suivant clique")
                                            time.sleep(1.5)
                                            break
                                    if next_clicked:
                                        break
                                except:
                                    continue
                        
                        if not next_clicked:
                            print(f"    [WARNING] Impossible de passer à la photo suivante")
                            # Essayer quand même de continuer
                
                except Exception as e:
                    print(f"    [ERREUR] Photo {photo_num + 1}: {e}")
                    continue
            
            photo_urls = high_res_photos
            
            if len(photo_urls) < total_photos:
                print(f"[WARNING] Seulement {len(photo_urls)} photos extraites sur {total_photos} annoncées")
            else:
                print(f"[OK] {len(photo_urls)} photos extraites avec succès!")
            
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
            
            # Enlever les doublons TOUT EN PRÉSERVANT L'ORDRE
            seen = set()
            unique_photo_urls = []
            for url in photo_urls:
                if url not in seen:
                    seen.add(url)
                    unique_photo_urls.append(url)
            photo_urls = unique_photo_urls
            
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
    
    def scrape_property_with_list_info(self, index=0, skip_photos=False):
        """
        Scrape complet: d'abord les infos de la liste, puis les détails du panneau
        
        Args:
            index: Index de la propriété
            skip_photos: Si True, ne pas extraire les URLs des photos (plus rapide)
            
        Returns:
            dict: Données complètes combinées
        """
        print("\n" + "="*80)
        print(f"SCRAPING COMPLET PROPRIETE #{index+1} (LISTE + DETAILS)" + (" [sans photos]" if skip_photos else ""))
        print("="*80)
        
        # Étape 1: Extraire les infos de la liste
        list_info = self.extract_info_from_list(index)
        
        # Étape 2: Cliquer et extraire les détails
        if not self.click_on_property_by_index(index):
            print("[ERREUR] Impossible de cliquer sur la propriete")
            return list_info  # Retourner au moins les infos de la liste
        
        # Étape 3: Extraire les détails du panneau
        detail_info = self.extract_all_info_complete()
        
        # Étape 3.5: Extraire les URLs des photos (sauf si skip_photos=True pour gagner du temps)
        if skip_photos:
            detail_info['photo_urls'] = []
            detail_info['nb_photos'] = 0
        else:
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
        
        # Fermer le panneau de détail pour revenir à la liste
        print("\n=== Fermeture du panneau ===")
        if self.close_panel():
            print("[OK] Panneau ferme, retour a la liste")
        else:
            print("[WARNING] Echec fermeture panneau")
        
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

