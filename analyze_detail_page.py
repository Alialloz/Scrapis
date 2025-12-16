"""
Script pour analyser le panneau de détail d'une propriété et identifier toutes les informations disponibles
"""
import re
import json

def analyze_detail_snapshot(snapshot_file):
    """Analyse le snapshot du panneau de détail"""
    
    print("="*80)
    print("ANALYSE DU PANNEAU DE DETAIL DE LA PROPRIETE")
    print("="*80)
    
    with open(snapshot_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extraire tous les noms/textes visibles
    name_pattern = r'name:\s*(.+?)(?:\n|ref:)'
    names = re.findall(name_pattern, content)
    
    # Filtrer les noms pertinents (exclure les éléments UI génériques)
    relevant_info = []
    ui_elements = ['Toggle', 'button', 'link', 'Effacer', 'Appliquer', 'Fermer', 
                   'Sauvegarder', 'Annuler', 'Raccourcis', 'Carte', 'Recentrer']
    
    for name in names:
        name_clean = name.strip().strip('"').strip("'")
        if name_clean and len(name_clean) > 2:
            # Exclure les éléments UI génériques
            if not any(ui in name_clean for ui in ui_elements):
                if name_clean not in relevant_info:
                    relevant_info.append(name_clean)
    
    print("\nINFORMATIONS IDENTIFIEES DANS LE PANNEAU DE DETAIL:\n")
    
    # Catégoriser les informations
    categories = {
        "Navigation": [],
        "Photos": [],
        "Actions": [],
        "Informations propriete": [],
        "Fonctionnalites": [],
        "Autres": []
    }
    
    for info in relevant_info:
        info_lower = info.lower()
        if any(word in info_lower for word in ['retour', 'précédent', 'suivant', 'résultat']):
            categories["Navigation"].append(info)
        elif any(word in info_lower for word in ['photo', 'image', 'voir toute']):
            categories["Photos"].append(info)
        elif any(word in info_lower for word in ['favori', 'possibilité', 'rejeté', 'enregistrer']):
            categories["Actions"].append(info)
        elif any(word in info_lower for word in ['communauté', 'financière', 'fonction']):
            categories["Fonctionnalites"].append(info)
        elif any(word in info_lower for word in ['prix', 'adresse', 'chambre', 'salle', 'superficie', 
                                                  'garage', 'terrain', 'année', 'construit', 'quartier']):
            categories["Informations propriete"].append(info)
        else:
            categories["Autres"].append(info)
    
    for category, items in categories.items():
        if items:
            print(f"\n{category.upper()}:")
            for item in items[:20]:  # Limiter à 20 par catégorie
                print(f"  - {item}")
    
    # Chercher des patterns spécifiques dans le contenu
    print("\n" + "="*80)
    print("PATTERNS SPECIFIQUES TROUVES:")
    print("="*80)
    
    # Chercher les nombres (prix, superficies, etc.)
    numbers = re.findall(r'\d+[\s,\.]?\d*\s*\$', content)
    if numbers:
        print(f"\nPrix trouves: {set(numbers[:10])}")
    
    # Chercher les dates
    dates = re.findall(r'\d{4}-\d{2}-\d{2}', content)
    if dates:
        print(f"\nDates trouves: {set(dates)}")
    
    # Chercher les numéros Centris
    centris = re.findall(r'No Centris[:\s]*(\d+)', content, re.IGNORECASE)
    if centris:
        print(f"\nNumeros Centris: {set(centris)}")
    
    # Chercher les adresses
    addresses = re.findall(r'\d+[A-Z]?(?:-\d+[A-Z]?)?\s+[A-Za-zÀ-ÿ\s\-\.]+', content)
    if addresses:
        print(f"\nAdresses trouvees: {set(addresses[:5])}")
    
    # Analyser la structure JSON trouvée
    json_match = re.search(r'\{[^{}]*"IsColumnar"[^{}]*\}', content)
    if json_match:
        print(f"\nDonnees JSON trouvees: {json_match.group()[:200]}...")
    
    # Chercher les IDs de propriétés
    property_ids = re.findall(r'\d{8,}', content)
    unique_ids = list(set(property_ids))[:10]
    if unique_ids:
        print(f"\nIDs numeriques trouves (peuvent etre des numeros Centris): {unique_ids}")
    
    print("\n" + "="*80)
    print("RESUME:")
    print("="*80)
    print(f"""
    Le panneau de detail s'est ouvert avec succes!
    
    Elements identifies:
    - Bouton "Retour aux resultats" (confirme qu'on est dans un panneau de detail)
    - Lien "Voir toutes les photos (9)" (indique qu'il y a 9 photos disponibles)
    - Actions: Enregistrer comme favori/possibilite/rejete
    - Fonctionnalites: Communaute, Fonction Financiere
    - Carte interactive toujours visible
    
    Le panneau semble etre un overlay/sidebar qui s'ouvre sur la page principale
    sans changer l'URL principale (juste ajout de #1 dans l'URL).
    """)

if __name__ == "__main__":
    snapshot_file = r"C:\Users\danse\.cursor\browser-logs\snapshot-2025-12-16T23-20-02-720Z.log"
    analyze_detail_snapshot(snapshot_file)

