"""
Exemple d'utilisation du scraper Centris
"""
from scraper_centris import CentrisScraper

def main():
    # URL de la page Centris à scraper
    url = "https://matrix.centris.ca/Matrix/Public/Portal.aspx?ID=0-3319143035-10&eml=Y2JlYXVkZXRAcmF5aGFydmV5LmNh&L=2"
    
    # Créer une instance du scraper
    # headless=False pour voir le navigateur, headless=True pour mode invisible
    scraper = CentrisScraper(url, headless=False)
    
    try:
        # Scraper la page
        properties = scraper.scrape()
        
        # Afficher le résumé
        scraper.print_summary()
        
        # Sauvegarder les données
        scraper.save_to_csv("mes_proprietes.csv")
        scraper.save_to_json("mes_proprietes.json")
        
        print(f"\n✅ Scraping terminé avec succès!")
        print(f"📊 {len(properties)} propriétés extraites")
        
    except Exception as e:
        print(f"❌ Erreur lors du scraping: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Toujours fermer le navigateur
        scraper.close()

if __name__ == "__main__":
    main()


