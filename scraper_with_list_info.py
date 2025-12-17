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

