#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de test pour extraire une annonce complète et voir ce qui est envoyé à l'API
"""

import time
import json
from datetime import datetime
from scraper_with_list_info import CentrisScraperWithListInfo

# Configuration
MATRIX_URL = "https://matrix.centris.ca/Matrix/Public/Portal.aspx?ID=0-3319143035-10&eml=Y2JlYXVkZXRAcmF5aGFydmV5LmNh&L=2"


def format_json_preview(data, max_length=100):
    """Formate un aperçu d'une valeur JSON"""
    if data is None:
        return "None"
    if isinstance(data, str):
        return f'"{data[:max_length]}..."' if len(data) > max_length else f'"{data}"'
    if isinstance(data, (int, float)):
        return str(data)
    if isinstance(data, list):
        return f"[{len(data)} éléments]"
    if isinstance(data, dict):
        return f"{{{len(data)} champs}}"
    return str(data)


def print_section(title):
    """Affiche un titre de section"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def display_property_data(property_data):
    """Affiche les données de la propriété de manière structurée"""
    
    print_section("📋 INFORMATIONS DE BASE")
    base_fields = ['prix', 'adresse', 'ville', 'arrondissement', 'quartier', 
                   'type_propriete', 'annee_construction', 'numero_centris', 
                   'date_envoi', 'statut']
    
    for field in base_fields:
        value = property_data.get(field)
        if value:
            print(f"  ✓ {field:25s}: {value}")
        else:
            print(f"  ✗ {field:25s}: Non disponible")
    
    print_section("💰 DONNÉES FINANCIÈRES")
    financieres = property_data.get('donnees_financieres', {})
    
    # Revenus bruts potentiels
    revenus_bruts = financieres.get('revenus_bruts_potentiels', {})
    if any(revenus_bruts.values()):
        print("  📊 Revenus bruts potentiels:")
        for key, value in revenus_bruts.items():
            if value:
                print(f"    - {key:20s}: {value:>10s} $")
    
    # Revenus bruts effectifs
    revenus_effectifs = financieres.get('revenus_bruts_effectifs')
    if revenus_effectifs:
        print(f"  📈 Revenus bruts effectifs : {revenus_effectifs:>10s} $")
    
    # Dépenses d'exploitation
    depenses = financieres.get('depenses_exploitation', {})
    depenses_remplies = {k: v for k, v in depenses.items() if v}
    if depenses_remplies:
        print(f"  📉 Dépenses d'exploitation ({len(depenses_remplies)} postes):")
        for key, value in list(depenses_remplies.items())[:5]:  # Afficher les 5 premiers
            print(f"    - {key:25s}: {value:>10s} $")
        if len(depenses_remplies) > 5:
            print(f"    ... et {len(depenses_remplies) - 5} autres postes")
    
    # Revenus nets
    revenus_nets = financieres.get('revenus_nets_exploitation')
    if revenus_nets:
        print(f"  💵 Revenus nets d'exploitation: {revenus_nets:>10s} $")
    
    print_section("🏠 UNITÉS")
    unites = property_data.get('unites', {})
    
    residentielles = unites.get('residentielles', [])
    if residentielles:
        print("  🏡 Unités résidentielles:")
        for unite in residentielles:
            print(f"    - {unite.get('type')}: {unite.get('nombre')} unité(s)")
        print(f"  📊 Total résidentiel: {unites.get('total_residentiel', 0)} unités")
    
    commerciales = unites.get('commerciales', [])
    if commerciales:
        print("  🏢 Unités commerciales:")
        for unite in commerciales:
            print(f"    - {unite.get('type')}: {unite.get('nombre')} unité(s)")
        print(f"  📊 Total commercial: {unites.get('total_commercial', 0)} unités")
    
    print_section("🔧 CARACTÉRISTIQUES DÉTAILLÉES")
    carac = property_data.get('caracteristiques_detaillees', {})
    carac_fields = {
        'systeme_egouts': 'Système d\'égouts',
        'approv_eau': 'Approvisionnement en eau',
        'stationnement_detail': 'Stationnement',
        'chauffage': 'Chauffage'
    }
    
    for key, label in carac_fields.items():
        value = carac.get(key)
        if value:
            print(f"  ✓ {label:30s}: {value}")
    
    print_section("📝 INCLUSIONS / EXCLUSIONS / REMARQUES")
    
    inclusions = property_data.get('inclusions')
    if inclusions:
        print(f"  ✅ Inclusions: {inclusions[:150]}...")
    else:
        print("  ✗ Inclusions: Non disponible")
    
    exclusions = property_data.get('exclusions')
    if exclusions:
        print(f"  ❌ Exclusions: {exclusions[:150]}...")
    else:
        print("  ✗ Exclusions: Non disponible")
    
    remarques = property_data.get('remarques')
    if remarques:
        print(f"  💬 Remarques: {remarques[:150]}...")
    else:
        print("  ✗ Remarques: Non disponible")
    
    addenda = property_data.get('addenda')
    if addenda:
        print(f"  📄 Addenda: {addenda[:150]}...")
    else:
        print("  ✗ Addenda: Non disponible")
    
    print_section("📸 PHOTOS")
    photo_urls = property_data.get('photo_urls', [])
    nb_photos = property_data.get('nb_photos', 0)
    
    print(f"  📊 Nombre de photos: {nb_photos}")
    if photo_urls:
        print(f"  🔗 URLs extraites: {len(photo_urls)}")
        print("\n  Aperçu des 3 premières photos:")
        for i, url in enumerate(photo_urls[:3], 1):
            print(f"    {i}. {url[:80]}...")
        if len(photo_urls) > 3:
            print(f"    ... et {len(photo_urls) - 3} autres photos")
    else:
        print("  ✗ Aucune URL de photo extraite")
    
    print_section("👤 COURTIER")
    courtier_fields = {
        'courtier_email': 'Email',
        'courtier_telephone': 'Téléphone',
        'courtier_nom': 'Nom',
        'courtier_agence': 'Agence'
    }
    
    for key, label in courtier_fields.items():
        value = property_data.get(key)
        if value:
            print(f"  ✓ {label:15s}: {value}")
    
    print_section("🔗 AUTRES INFORMATIONS")
    print(f"  🌐 URL: {property_data.get('url', 'Non disponible')}")
    
    # Données de la liste (pour comparaison)
    donnees_liste = property_data.get('_donnees_liste', {})
    if donnees_liste:
        print(f"  📋 Données de la liste disponibles: Oui ({len(donnees_liste)} champs)")


def simulate_api_send(property_data, api_endpoint):
    """Simule l'envoi à l'API sans vraiment envoyer"""
    print_section("📤 SIMULATION ENVOI À L'API")
    
    print(f"  🎯 Endpoint: {api_endpoint}")
    print(f"  📦 Content-Type: application/json")
    print(f"  📊 Taille du JSON: {len(json.dumps(property_data))} caractères")
    
    # Afficher la structure JSON qui serait envoyée
    print("\n  📋 Structure du JSON qui serait envoyé:")
    print("  {")
    for key, value in property_data.items():
        if key == '_donnees_liste':
            continue  # Ignorer les données internes
        preview = format_json_preview(value)
        print(f'    "{key}": {preview}')
    print("  }")
    
    print("\n  ℹ️  Note: L'envoi n'est PAS effectué (mode simulation)")
    print("  ℹ️  Pour envoyer réellement, configurez API_ENDPOINT dans config_api.py")


def test_extraction_complete():
    """
    Fonction principale de test
    """
    print("\n" + "="*80)
    print("  🧪 TEST D'EXTRACTION COMPLÈTE D'UNE ANNONCE")
    print("="*80)
    
    print("\n📍 Étape 1/5: Initialisation du scraper...")
    scraper = CentrisScraperWithListInfo()
    
    if not scraper.init_driver():
        print("❌ ERREUR: Impossible d'initialiser le driver Chrome")
        return None
    
    print("✅ Driver initialisé avec succès")
    
    try:
        print("\n📍 Étape 2/5: Chargement de la page Matrix...")
        print(f"   URL: {MATRIX_URL[:60]}...")
        scraper.driver.get(MATRIX_URL)
        time.sleep(5)
        print("✅ Page chargée")
        
        print("\n📍 Étape 3/5: Extraction de la première annonce (la plus récente)...")
        print("   ⏳ Cela peut prendre 30-60 secondes...")
        print("   - Extraction des infos de la liste")
        print("   - Clic sur l'annonce")
        print("   - Extraction des détails complets")
        print("   - Extraction des photos (9 URLs)")
        
        start_time = time.time()
        property_data = scraper.scrape_property_with_list_info(index=0)
        elapsed_time = time.time() - start_time
        
        if not property_data:
            print("❌ ERREUR: Impossible d'extraire les données")
            return None
        
        print(f"✅ Extraction réussie en {elapsed_time:.1f} secondes")
        
        print("\n📍 Étape 4/5: Affichage des données extraites...")
        display_property_data(property_data)
        
        print("\n📍 Étape 5/5: Sauvegarde et simulation d'envoi à l'API...")
        
        # Sauvegarder le JSON
        filename = f"test_extraction_{property_data.get('numero_centris', 'unknown')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(property_data, f, indent=2, ensure_ascii=False)
        print(f"  ✅ Données sauvegardées dans: {filename}")
        
        # Importer la config pour l'endpoint API
        try:
            from config_api import API_ENDPOINT
        except ImportError:
            API_ENDPOINT = "https://votre-api.com/api/properties"
        
        # Simuler l'envoi à l'API
        simulate_api_send(property_data, API_ENDPOINT)
        
        print_section("✅ TEST TERMINÉ AVEC SUCCÈS")
        print(f"  📁 Fichier généré: {filename}")
        print(f"  🔢 Numéro Centris: {property_data.get('numero_centris', 'N/A')}")
        print(f"  💰 Prix: {property_data.get('prix', 'N/A')} $")
        print(f"  📍 Adresse: {property_data.get('adresse', 'N/A')}")
        print(f"  📸 Photos: {len(property_data.get('photo_urls', []))} URLs")
        print(f"  ⏱️  Temps total: {elapsed_time:.1f} secondes")
        
        return property_data
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        print("\n🔄 Fermeture du navigateur...")
        time.sleep(2)
        scraper.close()
        print("✅ Navigateur fermé")


if __name__ == "__main__":
    print("\n" + "🚀"*40)
    print("  SCRAPIS - TEST D'EXTRACTION COMPLÈTE")
    print("  Test de l'extraction et simulation d'envoi à l'API")
    print("🚀"*40)
    
    result = test_extraction_complete()
    
    if result:
        print("\n" + "🎉"*40)
        print("  TEST RÉUSSI!")
        print("🎉"*40)
    else:
        print("\n" + "❌"*40)
        print("  TEST ÉCHOUÉ")
        print("❌"*40)
