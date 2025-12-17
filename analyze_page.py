"""
Script pour analyser la structure de la page Centris et identifier tous les éléments disponibles
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json
import time

def analyze_page(url):
    """Analyse la structure de la page Centris"""
    
    # Configuration du driver
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        print(f"Chargement de la page: {url}")
        driver.get(url)
        time.sleep(5)  # Attendre le chargement
        
        # Faire défiler pour charger toutes les propriétés
        print("Défilement de la page...")
        last_height = driver.execute_script("return document.body.scrollHeight")
        for i in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        # Obtenir le HTML
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        print("\n" + "="*80)
        print("ANALYSE DE LA STRUCTURE DE LA PAGE")
        print("="*80)
        
        # 1. Analyser les titres et en-têtes
        print("\n1. TITRES ET EN-TÊTES:")
        print("-" * 80)
        title = driver.title
        print(f"Titre de la page: {title}")
        
        h1_tags = soup.find_all('h1')
        h2_tags = soup.find_all('h2')
        h3_tags = soup.find_all('h3')
        print(f"\nH1 tags: {len(h1_tags)}")
        for h1 in h1_tags[:3]:
            print(f"  - {h1.get_text().strip()}")
        print(f"\nH2 tags: {len(h2_tags)}")
        for h2 in h2_tags[:5]:
            print(f"  - {h2.get_text().strip()}")
        
        # 2. Analyser les classes CSS utilisées
        print("\n2. CLASSES CSS PRINCIPALES:")
        print("-" * 80)
        all_classes = set()
        for element in soup.find_all(class_=True):
            classes = element.get('class', [])
            if isinstance(classes, list):
                all_classes.update(classes)
            else:
                all_classes.add(classes)
        
        relevant_classes = [c for c in all_classes if any(keyword in c.lower() for keyword in 
                          ['property', 'listing', 'result', 'item', 'card', 'price', 'prix', 
                           'address', 'adresse', 'centris', 'date', 'envoi'])]
        
        print(f"Classes totales trouvées: {len(all_classes)}")
        print(f"Classes pertinentes: {len(relevant_classes)}")
        print("\nClasses pertinentes:")
        for cls in sorted(relevant_classes)[:20]:
            print(f"  - {cls}")
        
        # 3. Analyser les IDs
        print("\n3. IDs PRINCIPAUX:")
        print("-" * 80)
        all_ids = [elem.get('id') for elem in soup.find_all(id=True)]
        relevant_ids = [id for id in all_ids if id and any(keyword in id.lower() for keyword in 
                      ['property', 'listing', 'result', 'item', 'card'])]
        print(f"IDs pertinents trouvés: {len(relevant_ids)}")
        for id in relevant_ids[:10]:
            print(f"  - {id}")
        
        # 4. Analyser les éléments contenant des prix
        print("\n4. ÉLÉMENTS CONTENANT DES PRIX:")
        print("-" * 80)
        price_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '$')]")
        print(f"Éléments avec '$' trouvés: {len(price_elements)}")
        
        if price_elements:
            print("\nExemples de prix trouvés:")
            seen_prices = set()
            for elem in price_elements[:10]:
                try:
                    text = elem.text.strip()
                    if text and '$' in text and text not in seen_prices:
                        print(f"  - {text[:100]}")
                        seen_prices.add(text)
                except:
                    pass
        
        # 5. Analyser les éléments contenant "Centris"
        print("\n5. ÉLÉMENTS CONTENANT 'CENTRIS':")
        print("-" * 80)
        centris_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Centris')]")
        print(f"Éléments avec 'Centris' trouvés: {len(centris_elements)}")
        
        if centris_elements:
            print("\nExemples:")
            seen_texts = set()
            for elem in centris_elements[:5]:
                try:
                    text = elem.text.strip()
                    if text and text not in seen_texts:
                        print(f"  - {text[:150]}")
                        seen_texts.add(text)
                except:
                    pass
        
        # 6. Analyser la structure des propriétés individuelles
        print("\n6. STRUCTURE DES PROPRIÉTÉS:")
        print("-" * 80)
        
        # Chercher les conteneurs de propriétés
        property_containers = []
        
        # Stratégie 1: Chercher par "No Centris"
        centris_elems = driver.find_elements(By.XPATH, "//*[contains(text(), 'No Centris')]")
        for elem in centris_elems[:3]:
            try:
                # Remonter pour trouver le conteneur parent
                parent = elem
                for _ in range(5):
                    try:
                        parent = parent.find_element(By.XPATH, "./..")
                        text = parent.text.strip()
                        if text and '$' in text and len(text) > 100:
                            property_containers.append({
                                'element': parent,
                                'text': text[:500]
                            })
                            break
                    except:
                        break
            except:
                continue
        
        if property_containers:
            print(f"Conteneurs de propriétés trouvés: {len(property_containers)}")
            print("\nStructure d'une propriété (premier exemple):")
            print("-" * 80)
            first_prop = property_containers[0]['text']
            print(first_prop)
            
            # Analyser les balises HTML de cette propriété
            print("\nBalises HTML dans cette propriété:")
            try:
                parent_html = property_containers[0]['element'].get_attribute('outerHTML')
                prop_soup = BeautifulSoup(parent_html, 'html.parser')
                
                print(f"  - Divs: {len(prop_soup.find_all('div'))}")
                print(f"  - Spans: {len(prop_soup.find_all('span'))}")
                print(f"  - Liens (a): {len(prop_soup.find_all('a'))}")
                print(f"  - Strong/Bold: {len(prop_soup.find_all(['strong', 'b']))}")
                print(f"  - Listes (li): {len(prop_soup.find_all('li'))}")
                
                # Afficher les classes utilisées dans cette propriété
                classes_in_prop = set()
                for elem in prop_soup.find_all(class_=True):
                    cls = elem.get('class', [])
                    if isinstance(cls, list):
                        classes_in_prop.update(cls)
                    else:
                        classes_in_prop.add(cls)
                
                print(f"\nClasses CSS dans cette propriété ({len(classes_in_prop)}):")
                for cls in sorted(classes_in_prop)[:15]:
                    print(f"  - {cls}")
                
            except Exception as e:
                print(f"Erreur lors de l'analyse HTML: {e}")
        
        # 7. Analyser les liens
        print("\n7. LIENS SUR LA PAGE:")
        print("-" * 80)
        links = soup.find_all('a', href=True)
        property_links = [link for link in links if any(keyword in link.get('href', '').lower() 
                       for keyword in ['property', 'listing', 'detail', 'centris'])]
        print(f"Liens totaux: {len(links)}")
        print(f"Liens de propriétés potentiels: {len(property_links)}")
        if property_links:
            print("\nExemples de liens:")
            for link in property_links[:5]:
                href = link.get('href', '')
                text = link.get_text().strip()
                print(f"  - {text[:50]} -> {href[:80]}")
        
        # 8. Analyser les images
        print("\n8. IMAGES SUR LA PAGE:")
        print("-" * 80)
        images = soup.find_all('img')
        print(f"Images trouvées: {len(images)}")
        property_images = [img for img in images if any(keyword in img.get('src', '').lower() 
                       or keyword in img.get('alt', '').lower() 
                       for keyword in ['property', 'listing', 'photo', 'image'])]
        print(f"Images de propriétés potentielles: {len(property_images)}")
        
        # 9. Analyser les données structurées (JSON-LD, microdata)
        print("\n9. DONNÉES STRUCTURÉES:")
        print("-" * 80)
        json_ld = soup.find_all('script', type='application/ld+json')
        print(f"Scripts JSON-LD: {len(json_ld)}")
        
        # 10. Analyser les scripts JavaScript pour les données
        print("\n10. SCRIPTS JAVASCRIPT:")
        print("-" * 80)
        scripts = soup.find_all('script')
        print(f"Scripts totaux: {len(scripts)}")
        
        # Chercher des données dans les scripts
        data_scripts = []
        for script in scripts:
            script_text = script.string
            if script_text and any(keyword in script_text.lower() for keyword in 
                                  ['property', 'listing', 'centris', 'data', 'json']):
                data_scripts.append(script_text[:200])
        
        print(f"Scripts contenant des données potentielles: {len(data_scripts)}")
        
        # 11. Compter les propriétés visibles
        print("\n11. COMPTAGE DES PROPRIÉTÉS:")
        print("-" * 80)
        
        # Compter par différents critères
        count_by_price = len([e for e in price_elements if e.text.strip() and '$' in e.text])
        count_by_centris = len(centris_elements)
        
        # Chercher le texte "inscriptions" ou "résultats"
        results_text = soup.find_all(string=lambda x: x and ('inscription' in x.lower() or 'résultat' in x.lower() or 'result' in x.lower()))
        print(f"Éléments avec 'inscription/résultat': {len(results_text)}")
        for text in results_text[:3]:
            print(f"  - {text.strip()[:100]}")
        
        print(f"\nEstimation du nombre de propriétés:")
        print(f"  - Par éléments avec prix: {count_by_price}")
        print(f"  - Par éléments avec 'Centris': {count_by_centris}")
        
        # 12. Sauvegarder le HTML pour analyse ultérieure
        print("\n12. SAUVEGARDE:")
        print("-" * 80)
        with open('page_structure.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("HTML sauvegardé dans 'page_structure.html'")
        
        print("\n" + "="*80)
        print("ANALYSE TERMINÉE")
        print("="*80)
        
    except Exception as e:
        print(f"Erreur lors de l'analyse: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nFermeture du navigateur dans 10 secondes...")
        time.sleep(10)
        driver.quit()

if __name__ == "__main__":
    url = "https://matrix.centris.ca/Matrix/Public/Portal.aspx?ID=0-3319143035-10&eml=Y2JlYXVkZXRAcmF5aGFydmV5LmNh&L=2"
    analyze_page(url)


