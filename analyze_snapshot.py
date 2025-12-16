"""
Script pour analyser le snapshot de la page et identifier tous les éléments disponibles
"""
import json
import re
from collections import defaultdict

def extract_text_from_snapshot(snapshot_file):
    """Extrait tout le texte visible du snapshot"""
    try:
        with open(snapshot_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Le snapshot est en YAML, extraire les noms et textes
        texts = []
        names = []
        
        # Extraire les noms (name:)
        name_pattern = r'name:\s*(.+?)(?:\n|$)'
        names = re.findall(name_pattern, content)
        
        # Extraire les textes dans les rôles
        # Chercher les patterns comme "role: link" suivi de "name:"
        lines = content.split('\n')
        current_role = None
        current_name = None
        
        for i, line in enumerate(lines):
            if 'role:' in line:
                current_role = line.split('role:')[1].strip()
            if 'name:' in line:
                name_part = line.split('name:')[1].strip()
                if name_part and name_part not in ['', 'generic', 'form', 'textbox', 'link', 'button']:
                    names.append(name_part)
        
        return names, content
    except Exception as e:
        print(f"Erreur lors de la lecture du snapshot: {e}")
        return [], ""

def analyze_page_structure():
    """Analyse la structure de la page depuis les données web fournies"""
    
    print("="*80)
    print("ANALYSE COMPLÈTE DE LA PAGE CENTRIS MATRIX")
    print("="*80)
    
    # Données extraites du web search
    page_data = """
    Informations visibles sur la page:
    
    1. EN-TÊTE ET NAVIGATION:
    - Nom du courtier: Myriam Guimont
    - Agence: RAY HARVEY & ASSOCIÉS
    - Email: mguimont@rayharvey.ca
    - Téléphone: 418-849-7777
    - Menu de navigation: Trouver une maison, Recherches, Sauvegardés/Rejetés, Messages, Mon courtier, Plus, Aide
    
    2. FILTRES ET RECHERCHE:
    - Filtres disponibles (0 actifs)
    - Option pour enregistrer la recherche
    - Options de tri: Date d'envoi, Prix, Municipalité
    - Options d'affichage: Portal List, Sommaire
    
    3. COMPTEUR DE RÉSULTATS:
    - "64 inscriptions totales de la recherche Alerte - 5+ Qc"
    
    4. CARTE INTERACTIVE:
    - Carte avec outils: Recentrer, Dessiner, Drive Time
    - Options de zoom: Frontières, MLS Status, Parcel Characteristics, Tendances
    - Points d'intérêt: Arts et divertissement, Services bancaires, Éducation, etc.
    
    5. LISTE DES PROPRIÉTÉS (64 propriétés affichées):
    """
    
    print(page_data)
    
    # Exemples de propriétés avec toutes leurs données
    properties_example = """
    STRUCTURE D'UNE PROPRIÉTÉ (exemple complet):
    
    Propriété 1:
    - Prix: "750 000 $" (avec badge "Nouvelle annonce")
    - Adresse: "220Z-226BZ Boul. Pierre-Bertrand" (en gras)
    - Localisation: "Québec (Les Rivières)"
    - Description: "Autre dans le quartier Neufchâtel-Est/Lebourgneuf construit en 1949"
    - Numéro Centris: "23326443"
    - Date d'envoi: "2025-12-15"
    - Actions disponibles:
      * Retirer des favoris
      * Retirer des possibilités
      * Retirer des rejetés
      * Enregistrer comme favori
      * Enregistrer comme possibilité
      * Enregistrer comme rejeté
    
    Propriété 2:
    - Prix: "1 050 000 $" (avec badge "Nouvelle annonce")
    - Adresse: "164-174 Av. Ruel" (en gras)
    - Localisation: "Québec (Beauport)"
    - Description: "Autre dans le quartier Chutes-Montmorency construit en 1926"
    - Numéro Centris: "16311005"
    - Date d'envoi: "2025-12-10"
    
    Propriété 3:
    - Prix: "995 000 $ + TPS/TVQ" (avec badge "Nouvelle annonce")
    - Adresse: "11032-11040 Boul. Valcartier" (en gras)
    - Localisation: "Québec (La Haute-Saint-Charles)"
    - Description: "Autre dans le quartier Des Châtels construit en 1940"
    - Numéro Centris: "24772371"
    - Date d'envoi: "2025-12-05"
    """
    
    print(properties_example)
    
    # Analyser tous les champs disponibles
    print("\n" + "="*80)
    print("CHAMPS DE DONNÉES IDENTIFIÉS POUR CHAQUE PROPRIÉTÉ:")
    print("="*80)
    
    fields = {
        "Prix": {
            "description": "Prix de la propriété",
            "exemples": ["750 000 $", "1 050 000 $", "995 000 $ + TPS/TVQ", "1 389 000 $"],
            "badges": ["Nouvelle annonce", "Nouveau prix"],
            "format": "Montant avec ou sans taxes (TPS/TVQ)"
        },
        "Adresse": {
            "description": "Adresse complète de la propriété",
            "exemples": ["220Z-226BZ Boul. Pierre-Bertrand", "164-174 Av. Ruel", "19 Rue Ste-Angèle"],
            "format": "Numéro et nom de rue, parfois avec plage (ex: 220Z-226BZ)"
        },
        "Ville et Arrondissement": {
            "description": "Localisation géographique",
            "exemples": ["Québec (Les Rivières)", "Québec (Beauport)", "Québec (La Cité-Limoilou)"],
            "format": "Ville (Arrondissement)"
        },
        "Quartier": {
            "description": "Quartier spécifique dans l'arrondissement",
            "exemples": ["Neufchâtel-Est/Lebourgneuf", "Chutes-Montmorency", "Vieux-Québec/Cap-Blanc/Colline parlem."],
            "format": "Nom du quartier"
        },
        "Type de propriété": {
            "description": "Type de bâtiment",
            "exemples": ["Autre", "Quintuplex", "Duplex", "Triplex"],
            "format": "Catégorie de propriété"
        },
        "Année de construction": {
            "description": "Année de construction du bâtiment",
            "exemples": ["1949", "1926", "1940", "1834"],
            "format": "Année (4 chiffres)"
        },
        "Numéro Centris": {
            "description": "Identifiant unique Centris",
            "exemples": ["23326443", "16311005", "24772371"],
            "format": "Numéro à 8 chiffres"
        },
        "Date d'envoi": {
            "description": "Date de publication de l'annonce",
            "exemples": ["2025-12-15", "2025-12-10", "2025-12-05"],
            "format": "YYYY-MM-DD"
        },
        "Statut": {
            "description": "Statut de l'annonce",
            "exemples": ["Nouvelle annonce", "Nouveau prix", "Aucun badge"],
            "format": "Badge visuel ou absence de badge"
        },
        "Actions utilisateur": {
            "description": "Actions disponibles pour chaque propriété",
            "exemples": [
                "Enregistrer comme favori",
                "Enregistrer comme possibilité",
                "Enregistrer comme rejeté",
                "Retirer des favoris/possibilités/rejetés"
            ],
            "format": "Boutons d'action"
        },
        "Lien vers détail": {
            "description": "URL vers la page de détail de la propriété",
            "format": "Lien cliquable (probablement dans l'adresse ou le titre)"
        }
    }
    
    for field_name, field_info in fields.items():
        print(f"\n{field_name}:")
        print(f"  Description: {field_info['description']}")
        print(f"  Format: {field_info['format']}")
        if 'exemples' in field_info:
            print(f"  Exemples: {', '.join(field_info['exemples'][:3])}")
        if 'badges' in field_info:
            print(f"  Badges possibles: {', '.join(field_info['badges'])}")
    
    # Analyser les patterns de données
    print("\n" + "="*80)
    print("PATTERNS DE DONNÉES IDENTIFIÉS:")
    print("="*80)
    
    patterns = {
        "Prix": r"([\d\s]+)\s*\$\s*(?:\+\s*TPS/TVQ)?",
        "Adresse": r"(\d+[A-Z]?(?:-\d+[A-Z]?)?\s+[A-Za-zÀ-ÿ\s\-\.]+)",
        "Numéro Centris": r"No Centris\s*:\s*(\d+)",
        "Date d'envoi": r"Date d'envoi\s*:\s*(\d{4}-\d{2}-\d{2})",
        "Année construction": r"construit en (\d{4})",
        "Quartier": r"dans le quartier ([^c]+?)(?:construit|$)",
        "Ville/Arrondissement": r"Québec\s*\(([^)]+)\)",
        "Type": r"(Autre|Quintuplex|Duplex|Triplex|Maison|Condominium|etc\.)"
    }
    
    for pattern_name, pattern in patterns.items():
        print(f"  {pattern_name}: {pattern}")
    
    # Éléments de l'interface
    print("\n" + "="*80)
    print("ÉLÉMENTS DE L'INTERFACE UTILISATEUR:")
    print("="*80)
    
    ui_elements = {
        "Navigation principale": [
            "Trouver une maison",
            "Recherches",
            "Sauvegardés / Rejetés",
            "Messages",
            "Mon courtier",
            "Plus",
            "Aide"
        ],
        "Filtres et tri": [
            "Filtres (0 actifs)",
            "Enregistrer votre recherche",
            "Tri par: Date d'envoi, Prix, Municipalité",
            "Vue: Portal List, Sommaire"
        ],
        "Carte interactive": [
            "Outils: Recentrer, Dessiner, Drive Time",
            "Zoom: Frontières, MLS Status, Parcel Characteristics, Tendances",
            "Points d'intérêt: 13 catégories (Arts, Banques, Éducation, etc.)"
        ],
        "Actions sur propriétés": [
            "Enregistrer comme favori/possibilité/rejeté",
            "Retirer des favoris/possibilités/rejetés"
        ],
        "Pagination": [
            "Bouton 'Voir plus de résultats' en bas de page"
        ]
    }
    
    for element_type, items in ui_elements.items():
        print(f"\n{element_type}:")
        for item in items:
            print(f"  - {item}")
    
    # Informations supplémentaires possibles
    print("\n" + "="*80)
    print("INFORMATIONS POTENTIELLEMENT DISPONIBLES (non visibles dans l'exemple):")
    print("="*80)
    
    potential_fields = [
        "Nombre de chambres",
        "Nombre de salles de bain",
        "Superficie (pi² ou m²)",
        "Superficie du terrain",
        "Garage/Parking",
        "Photos (liens vers images)",
        "Description détaillée",
        "Caractéristiques supplémentaires",
        "Coordonnées du vendeur/courtier",
        "Historique des prix",
        "Évaluations municipales",
        "Taxes municipales",
        "Informations sur le quartier",
        "Proximité des services",
        "Transport en commun",
        "Écoles à proximité"
    ]
    
    for field in potential_fields:
        print(f"  - {field}")
    
    print("\n" + "="*80)
    print("RÉSUMÉ:")
    print("="*80)
    print(f"""
    La page affiche une liste de 64 propriétés immobilières avec les informations suivantes:
    
    DONNÉES PRINCIPALES PAR PROPRIÉTÉ:
    ✓ Prix (avec badges de statut)
    ✓ Adresse complète
    ✓ Ville et arrondissement
    ✓ Quartier
    ✓ Type de propriété
    ✓ Année de construction
    ✓ Numéro Centris (ID unique)
    ✓ Date d'envoi de l'annonce
    ✓ Actions utilisateur (favoris, etc.)
    
    ÉLÉMENTS DE L'INTERFACE:
    ✓ Navigation principale
    ✓ Filtres et options de tri
    ✓ Carte interactive avec outils
    ✓ Liste des propriétés avec pagination
    
    FORMAT DES DONNÉES:
    - Les prix sont en dollars canadiens
    - Les dates sont au format YYYY-MM-DD
    - Les adresses incluent parfois des plages (ex: 220Z-226BZ)
    - Les types de propriétés sont catégorisés (Autre, Quintuplex, etc.)
    """)
    
    print("\n" + "="*80)

if __name__ == "__main__":
    analyze_page_structure()

