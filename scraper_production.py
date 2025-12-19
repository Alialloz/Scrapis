#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Scraper Centris - Version Production
Monitoring continu avec envoi automatique à l'API
"""

import sys
import time
import json
import os
import glob
from datetime import datetime, timedelta
from scraper_monitor import CentrisMonitor

# Importer la configuration
try:
    from config_api import (
        API_ENDPOINT,
        API_HEADERS,
        API_TIMEOUT,
        MATRIX_URL,
        MONITORING_INTERVAL,
        STORAGE_FILE,
        DELAY_BETWEEN_LISTINGS,
        SAVE_JSON_LOCALLY,
        MAX_LISTINGS_PER_CYCLE,
        AUTO_CLEANUP_ENABLED,
        CLEANUP_DAY,
        CLEANUP_HOUR,
        KEEP_CURRENT_WEEK,
        PROTECTED_FILES,
        AUTO_BACKUP_SCRAPED_IDS
    )
except ImportError:
    print("[ERREUR] Fichier config_api.py introuvable!")
    print("Veuillez configurer config_api.py avant de lancer le monitoring.")
    sys.exit(1)


class CentrisProductionMonitor(CentrisMonitor):
    """Version production du moniteur avec configuration personnalisée"""
    
    def __init__(self):
        super().__init__(
            url=MATRIX_URL,
            api_endpoint=API_ENDPOINT,
            storage_file=STORAGE_FILE
        )
        self.api_headers = API_HEADERS
        self.api_timeout = API_TIMEOUT
        self.delay_between_listings = DELAY_BETWEEN_LISTINGS
        self.save_json_locally = SAVE_JSON_LOCALLY
        self.max_listings_per_cycle = MAX_LISTINGS_PER_CYCLE
        self.auto_cleanup_enabled = AUTO_CLEANUP_ENABLED
        self.cleanup_day = CLEANUP_DAY
        self.cleanup_hour = CLEANUP_HOUR
        self.keep_current_week = KEEP_CURRENT_WEEK
        self.protected_files = PROTECTED_FILES
        self.auto_backup_scraped_ids = AUTO_BACKUP_SCRAPED_IDS
        self.last_cleanup_date = None
        
    def send_to_api(self, property_data):
        """
        Envoie les données d'une propriété à l'API (version personnalisée)
        """
        if not self.api_endpoint or self.api_endpoint == "https://votre-api.com/api/properties":
            print("[WARNING] API non configuree! Configurez config_api.py")
            print("[INFO] Donnees sauvegardees localement uniquement")
            return True
        
        try:
            import requests
            
            print(f"[API] Envoi des donnees a {self.api_endpoint}...")
            
            response = requests.post(
                self.api_endpoint,
                json=property_data,
                headers=self.api_headers,
                timeout=self.api_timeout
            )
            
            if response.status_code in [200, 201]:
                print(f"[OK] Donnees envoyees avec succes (Status: {response.status_code})")
                try:
                    response_data = response.json()
                    print(f"[API] Reponse: {response_data}")
                except:
                    pass
                return True
            else:
                print(f"[WARNING] API a retourne le status {response.status_code}")
                print(f"  Reponse: {response.text[:200]}")
                return False
                
        except requests.exceptions.Timeout:
            print(f"[ERREUR] Timeout lors de l'envoi a l'API (>{self.api_timeout}s)")
            return False
        except requests.exceptions.ConnectionError:
            print(f"[ERREUR] Impossible de se connecter a l'API: {self.api_endpoint}")
            return False
        except Exception as e:
            print(f"[ERREUR] Erreur lors de l'envoi a l'API: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_monitoring_cycle(self):
        """
        Exécute un cycle de monitoring complet (version production)
        """
        print(f"\n{'='*80}")
        print(f"CYCLE DE MONITORING - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}")
        
        stats = {
            'timestamp': datetime.now().isoformat(),
            'total_listings': 0,
            'new_listings': 0,
            'scraped_successfully': 0,
            'sent_to_api': 0,
            'errors': 0
        }
        
        try:
            # 1. Récupérer tous les IDs actuels
            current_ids = self.get_all_listing_ids()
            stats['total_listings'] = len(current_ids)
            
            # 2. Identifier les nouvelles annonces
            new_ids = self.identify_new_listings(current_ids)
            stats['new_listings'] = len(new_ids)
            
            # Limiter le nombre d'annonces si configuré
            if self.max_listings_per_cycle > 0:
                new_ids = new_ids[:self.max_listings_per_cycle]
                if len(new_ids) < stats['new_listings']:
                    print(f"[INFO] Limite a {self.max_listings_per_cycle} annonces pour ce cycle")
            
            # 3. Scraper chaque nouvelle annonce
            for idx, centris_id in enumerate(new_ids, 1):
                try:
                    print(f"\n[{idx}/{len(new_ids)}] Traitement de l'annonce {centris_id}")
                    
                    # Scraper l'annonce
                    property_data = self.scrape_new_listing(centris_id)
                    
                    if property_data:
                        stats['scraped_successfully'] += 1
                        
                        # Sauvegarder localement si configuré
                        if self.save_json_locally:
                            filename = f"property_{centris_id}.json"
                            with open(filename, 'w', encoding='utf-8') as f:
                                json.dump(property_data, f, indent=2, ensure_ascii=False)
                            print(f"[OK] Donnees sauvegardees dans {filename}")
                        
                        # Envoyer à l'API
                        if self.send_to_api(property_data):
                            stats['sent_to_api'] += 1
                        
                        # Marquer comme scrapé
                        self.scraped_ids[centris_id] = datetime.now().isoformat()
                        self.save_scraped_ids()
                        
                    else:
                        stats['errors'] += 1
                        print(f"[WARNING] Echec du scraping pour {centris_id}")
                    
                except Exception as e:
                    print(f"[ERREUR] Erreur lors du traitement de {centris_id}: {e}")
                    stats['errors'] += 1
                    import traceback
                    traceback.print_exc()
                
                # Pause entre chaque scraping
                if idx < len(new_ids):
                    print(f"[INFO] Pause de {self.delay_between_listings} secondes...")
                    time.sleep(self.delay_between_listings)
            
            # Résumé
            print(f"\n{'='*80}")
            print(f"RESUME DU CYCLE")
            print(f"{'='*80}")
            print(f"Total annonces sur la page: {stats['total_listings']}")
            print(f"Nouvelles annonces: {stats['new_listings']}")
            print(f"Scrapees avec succes: {stats['scraped_successfully']}")
            print(f"Envoyees a l'API: {stats['sent_to_api']}")
            print(f"Erreurs: {stats['errors']}")
            print(f"Total annonces en memoire: {len(self.scraped_ids)}")
            
            # Sauvegarder les statistiques
            self.save_stats(stats)
            
            return stats
            
        except Exception as e:
            print(f"\n[ERREUR CRITIQUE] Erreur durant le cycle: {e}")
            import traceback
            traceback.print_exc()
            stats['errors'] += 1
            return stats
    
    def save_stats(self, stats):
        """Sauvegarde les statistiques du cycle"""
        try:
            stats_file = 'monitoring_stats.json'
            
            # Charger les stats existantes
            if os.path.exists(stats_file):
                with open(stats_file, 'r', encoding='utf-8') as f:
                    all_stats = json.load(f)
            else:
                all_stats = []
            
            # Ajouter les nouvelles stats
            all_stats.append(stats)
            
            # Garder seulement les 100 derniers cycles
            all_stats = all_stats[-100:]
            
            # Sauvegarder
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(all_stats, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"[WARNING] Impossible de sauvegarder les stats: {e}")
    
    def backup_scraped_ids(self):
        """
        Crée une sauvegarde du fichier scraped_properties.json
        """
        if not self.auto_backup_scraped_ids:
            return
        
        try:
            if os.path.exists(self.storage_file):
                # Créer un nom de fichier avec la date
                backup_name = f"scraped_properties_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                
                # Copier le fichier
                import shutil
                shutil.copy2(self.storage_file, backup_name)
                
                print(f"[BACKUP] Sauvegarde creee: {backup_name}")
                
                # Garder seulement les 10 dernières sauvegardes
                backup_files = sorted(glob.glob("scraped_properties_backup_*.json"))
                if len(backup_files) > 10:
                    for old_backup in backup_files[:-10]:
                        try:
                            os.remove(old_backup)
                            print(f"[BACKUP] Ancienne sauvegarde supprimee: {old_backup}")
                        except:
                            pass
                            
        except Exception as e:
            print(f"[WARNING] Impossible de creer la sauvegarde: {e}")
    
    def cleanup_json_files(self):
        """
        Supprime les fichiers JSON des propriétés selon la configuration
        ⚠️ NE SUPPRIME JAMAIS scraped_properties.json
        """
        if not self.auto_cleanup_enabled:
            return
        
        now = datetime.now()
        
        # Vérifier si c'est le bon jour et la bonne heure
        if now.weekday() != self.cleanup_day:
            return
        
        if now.hour != self.cleanup_hour:
            return
        
        # Vérifier si on a déjà fait le nettoyage aujourd'hui
        if self.last_cleanup_date and self.last_cleanup_date.date() == now.date():
            return
        
        print(f"\n{'='*80}")
        print(f"NETTOYAGE AUTOMATIQUE DES FICHIERS JSON")
        print(f"{'='*80}")
        
        # Créer une sauvegarde du fichier scraped_properties.json AVANT le nettoyage
        self.backup_scraped_ids()
        
        try:
            # Trouver tous les fichiers property_*.json
            pattern = "property_*.json"
            json_files = glob.glob(pattern)
            
            if not json_files:
                print("[INFO] Aucun fichier JSON a nettoyer")
                return
            
            # Calculer la date limite (début de la semaine si KEEP_CURRENT_WEEK)
            if self.keep_current_week:
                # Début de la semaine (lundi)
                days_since_monday = now.weekday()
                week_start = now - timedelta(days=days_since_monday)
                week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
                print(f"[INFO] Conservation des fichiers depuis le {week_start.strftime('%Y-%m-%d')}")
            
            deleted_count = 0
            kept_count = 0
            
            for json_file in json_files:
                # ⚠️ PROTECTION ABSOLUE - Ne JAMAIS supprimer ces fichiers
                if json_file in self.protected_files:
                    kept_count += 1
                    print(f"[PROTEGE] {json_file} conserve (fichier protege)")
                    continue
                
                # Double vérification pour scraped_properties.json
                if 'scraped_properties' in json_file:
                    kept_count += 1
                    print(f"[PROTEGE] {json_file} conserve (liste des IDs)")
                    continue
                
                try:
                    # Vérifier la date de modification du fichier
                    file_time = datetime.fromtimestamp(os.path.getmtime(json_file))
                    
                    # Décider si on supprime
                    should_delete = False
                    
                    if self.keep_current_week:
                        # Supprimer seulement les fichiers d'avant la semaine en cours
                        if file_time < week_start:
                            should_delete = True
                    else:
                        # Supprimer tous les fichiers
                        should_delete = True
                    
                    if should_delete:
                        os.remove(json_file)
                        deleted_count += 1
                        print(f"[SUPPRIME] {json_file} (date: {file_time.strftime('%Y-%m-%d %H:%M')})")
                    else:
                        kept_count += 1
                        
                except Exception as e:
                    print(f"[WARNING] Impossible de supprimer {json_file}: {e}")
            
            print(f"\n[OK] Nettoyage termine:")
            print(f"  - {deleted_count} fichiers supprimes")
            print(f"  - {kept_count} fichiers conserves")
            
            # Marquer la date du dernier nettoyage
            self.last_cleanup_date = now
            
        except Exception as e:
            print(f"[ERREUR] Erreur durant le nettoyage: {e}")
            import traceback
            traceback.print_exc()
    
    def run_continuous_monitoring(self, interval_minutes=None):
        """
        Exécute le monitoring en continu
        """
        if interval_minutes is None:
            interval_minutes = MONITORING_INTERVAL
        
        print(f"\n{'='*80}")
        print(f"DEMARRAGE DU MONITORING CONTINU")
        print(f"URL: {MATRIX_URL}")
        print(f"API: {API_ENDPOINT}")
        print(f"Intervalle: {interval_minutes} minutes")
        if self.auto_cleanup_enabled:
            days = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
            print(f"Nettoyage auto: {days[self.cleanup_day]} a {self.cleanup_hour}h")
        print(f"{'='*80}")
        
        cycle_number = 0
        
        try:
            while True:
                cycle_number += 1
                print(f"\n>>> CYCLE #{cycle_number} <<<")
                
                # Vérifier si c'est l'heure du nettoyage
                if self.auto_cleanup_enabled:
                    self.cleanup_json_files()
                
                start_time = time.time()
                
                # Exécuter le cycle
                stats = self.run_monitoring_cycle()
                
                elapsed_time = time.time() - start_time
                
                print(f"\n[INFO] Cycle termine en {elapsed_time:.0f} secondes")
                print(f"[INFO] Prochain cycle dans {interval_minutes} minutes...")
                print(f"[INFO] Appuyez sur Ctrl+C pour arreter le monitoring")
                
                # Attendre avant le prochain cycle
                time.sleep(interval_minutes * 60)
                
        except KeyboardInterrupt:
            print(f"\n\n[INFO] Arret du monitoring demande par l'utilisateur")
            print(f"[INFO] Total de {cycle_number} cycles executes")
            print(f"[INFO] {len(self.scraped_ids)} annonces en memoire")
            print(f"\n[OK] Monitoring arrete proprement")


def main():
    """
    Fonction principale - Mode Production
    """
    print("="*80)
    print("SCRAPER CENTRIS - VERSION PRODUCTION")
    print("="*80)
    
    # Vérifier la configuration
    print("\n[INFO] Verification de la configuration...")
    
    if API_ENDPOINT == "https://votre-api.com/api/properties":
        print("\n[WARNING] ==========================================")
        print("[WARNING] L'API N'EST PAS CONFIGUREE !")
        print("[WARNING] Editez config_api.py et configurez API_ENDPOINT")
        print("[WARNING] Les donnees seront sauvegardees localement uniquement")
        print("[WARNING] ==========================================\n")
        
        response = input("Continuer quand meme ? (o/n) : ")
        if response.lower() != 'o':
            print("[INFO] Arret du programme")
            return
    else:
        print(f"[OK] API configuree: {API_ENDPOINT}")
    
    print(f"[OK] URL Matrix: {MATRIX_URL}")
    print(f"[OK] Intervalle: {MONITORING_INTERVAL} minutes")
    print(f"[OK] Fichier de stockage: {STORAGE_FILE}")
    
    # Créer le moniteur
    monitor = CentrisProductionMonitor()
    
    # Lancer le monitoring continu
    print("\n[INFO] Lancement du monitoring continu...")
    print("[INFO] Le systeme va verifier les nouvelles annonces toutes les heures")
    print("[INFO] Chaque nouvelle annonce sera automatiquement scrapee et envoyee a l'API\n")
    
    try:
        monitor.run_continuous_monitoring()
    except Exception as e:
        print(f"\n[ERREUR CRITIQUE] {e}")
        import traceback
        traceback.print_exc()
        print("\n[INFO] Redemarrage du monitoring dans 60 secondes...")
        time.sleep(60)
        main()  # Redémarrer


if __name__ == "__main__":
    main()

