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
from logger_config import setup_logger, log_scraping_stats

# Configuration du logger (doit être fait en premier)
logger = setup_logger('production', level='INFO')
logger.info("="*80)
logger.info("SCRAPER CENTRIS - MODE PRODUCTION")
logger.info("="*80)

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
    logger.info("Configuration chargée depuis config_api.py")
except ImportError:
    logger.critical("Fichier config_api.py introuvable!")
    logger.critical("Veuillez configurer config_api.py avant de lancer le monitoring.")
    sys.exit(1)


class CentrisProductionMonitor(CentrisMonitor):
    """Version production du moniteur avec configuration personnalisée"""
    
    def __init__(self, min_date='2026-02-06', skip_photos=False):
        super().__init__(
            url=MATRIX_URL,
            api_endpoint=API_ENDPOINT,
            storage_file=STORAGE_FILE,
            min_date=min_date,
            skip_photos=skip_photos
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
        
    def _normalize_for_api(self, data):
        """
        L'API exige des chaînes pour quartier, annee_construction, statut.
        Convertit null en "" pour éviter les erreurs 400.
        """
        for key in ('quartier', 'annee_construction', 'statut'):
            if key in data and data[key] is None:
                data[key] = ""
            elif key in data and not isinstance(data[key], str):
                data[key] = str(data[key]) if data[key] is not None else ""
        if '_donnees_liste' in data and isinstance(data['_donnees_liste'], dict):
            for key in ('quartier', 'annee_construction', 'statut'):
                if key in data['_donnees_liste'] and data['_donnees_liste'][key] is None:
                    data['_donnees_liste'][key] = ""
                elif key in data['_donnees_liste'] and not isinstance(data['_donnees_liste'][key], str):
                    val = data['_donnees_liste'][key]
                    data['_donnees_liste'][key] = str(val) if val is not None else ""
        return data
    
    def send_to_api(self, property_data):
        """
        Envoie les données d'une propriété à l'API (version personnalisée)
        """
        if not self.api_endpoint or self.api_endpoint == "https://votre-api.com/api/properties":
            logger.warning("API non configurée! Configurez config_api.py")
            logger.info("Données sauvegardées localement uniquement")
            return True
        
        try:
            import requests
            
            # Copie pour ne pas modifier l'original, puis normalisation pour l'API
            payload = dict(property_data)
            if '_donnees_liste' in payload and isinstance(payload.get('_donnees_liste'), dict):
                payload['_donnees_liste'] = dict(payload['_donnees_liste'])
            payload = self._normalize_for_api(payload)
            
            centris_id = property_data.get('numero_centris', 'N/A')
            logger.info(f"Envoi des données à l'API - Centris #{centris_id}")
            logger.debug(f"Endpoint: {self.api_endpoint}")
            
            response = requests.post(
                self.api_endpoint,
                json=payload,
                headers=self.api_headers,
                timeout=self.api_timeout
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"✓ Données envoyées avec succès (Status: {response.status_code}) - Centris #{centris_id}")
                try:
                    response_data = response.json()
                    logger.debug(f"Réponse API: {response_data}")
                except:
                    pass
                return True
            else:
                logger.warning(f"API a retourné le status {response.status_code} - Centris #{centris_id}")
                logger.debug(f"Réponse: {response.text[:200]}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error(f"Timeout lors de l'envoi à l'API (>{self.api_timeout}s) - Centris #{centris_id}")
            return False
        except requests.exceptions.ConnectionError:
            logger.error(f"Impossible de se connecter à l'API: {self.api_endpoint}")
            return False
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi à l'API: {e}", exc_info=True)
            return False
    
    def run_monitoring_cycle(self):
        """
        Exécute un cycle de monitoring complet (version production)
        """
        cycle_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.info("="*80)
        logger.info(f"CYCLE DE MONITORING - {cycle_time}")
        logger.info("="*80)
        
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
                    logger.info(f"Limite à {self.max_listings_per_cycle} annonces pour ce cycle")
            
            # 3. Scraper chaque nouvelle annonce
            for idx, centris_id in enumerate(new_ids, 1):
                try:
                    logger.info(f"[{idx}/{len(new_ids)}] Traitement de l'annonce {centris_id}")
                    
                    # Scraper l'annonce
                    property_data = self.scrape_new_listing(centris_id)
                    
                    if property_data:
                        stats['scraped_successfully'] += 1
                        
                        # Vérifier si on a les détails (panneau ouvert) ou seulement la liste
                        has_detail = bool(
                            property_data.get('donnees_financieres') or
                            property_data.get('source') or
                            (not self.skip_photos and property_data.get('photo_urls') and len(property_data.get('photo_urls', [])) > 0)
                        )
                        if not has_detail:
                            logger.warning(
                                f"Données détail manquantes pour Centris #{centris_id} "
                                "(panneau non ouvert?) - non envoyé à l'API"
                            )
                        
                        # Sauvegarder localement si configuré
                        if self.save_json_locally:
                            filename = f"property_{centris_id}.json"
                            with open(filename, 'w', encoding='utf-8') as f:
                                json.dump(property_data, f, indent=2, ensure_ascii=False)
                            logger.info(f"✓ Données sauvegardées dans {filename}")
                        
                        # Envoyer à l'API seulement si on a les détails
                        if has_detail and self.send_to_api(property_data):
                            stats['sent_to_api'] += 1
                        
                        # Marquer comme scrapé
                        if isinstance(self.scraped_ids, list):
                            # Convertir la liste en dict si nécessaire
                            self.scraped_ids = {str(sid): "" for sid in self.scraped_ids}
                        self.scraped_ids[centris_id] = datetime.now().isoformat()
                        self.save_scraped_ids()
                        
                    else:
                        stats['errors'] += 1
                        logger.warning(f"Échec du scraping pour {centris_id}")
                    
                except Exception as e:
                    logger.error(f"Erreur lors du traitement de {centris_id}: {e}", exc_info=True)
                    stats['errors'] += 1
                
                # Pause entre chaque scraping
                if idx < len(new_ids):
                    logger.info(f"Pause de {self.delay_between_listings} secondes...")
                    time.sleep(self.delay_between_listings)
            
            # Résumé
            summary_stats = {
                'Total annonces sur la page': stats['total_listings'],
                'Nouvelles annonces': stats['new_listings'],
                'Scrapées avec succès': stats['scraped_successfully'],
                'Envoyées à l\'API': stats['sent_to_api'],
                'Erreurs': stats['errors'],
                'Total annonces en mémoire': len(self.scraped_ids)
            }
            log_scraping_stats(logger, summary_stats)
            
            # Sauvegarder les statistiques
            self.save_stats(stats)
            
            return stats
            
        except Exception as e:
            logger.critical(f"Erreur durant le cycle: {e}", exc_info=True)
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
            logger.warning(f"Impossible de sauvegarder les stats: {e}")
    
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
                
                logger.info(f"Backup: Sauvegarde créée: {backup_name}")
                
                # Garder seulement les 10 dernières sauvegardes
                backup_files = sorted(glob.glob("scraped_properties_backup_*.json"))
                if len(backup_files) > 10:
                    for old_backup in backup_files[:-10]:
                        try:
                            os.remove(old_backup)
                            logger.debug(f"Backup: Ancienne sauvegarde supprimée: {old_backup}")
                        except:
                            pass
                            
        except Exception as e:
            logger.warning(f"Impossible de créer la sauvegarde: {e}")
    
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
        
        logger.info("="*80)
        logger.info("NETTOYAGE AUTOMATIQUE DES FICHIERS JSON")
        logger.info("="*80)
        
        # Créer une sauvegarde du fichier scraped_properties.json AVANT le nettoyage
        self.backup_scraped_ids()
        
        try:
            # Trouver tous les fichiers property_*.json
            pattern = "property_*.json"
            json_files = glob.glob(pattern)
            
            if not json_files:
                logger.info("Aucun fichier JSON à nettoyer")
                return
            
            # Calculer la date limite (début de la semaine si KEEP_CURRENT_WEEK)
            if self.keep_current_week:
                # Début de la semaine (lundi)
                days_since_monday = now.weekday()
                week_start = now - timedelta(days=days_since_monday)
                week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
                logger.info(f"Conservation des fichiers depuis le {week_start.strftime('%Y-%m-%d')}")
            
            deleted_count = 0
            kept_count = 0
            
            for json_file in json_files:
                # ⚠️ PROTECTION ABSOLUE - Ne JAMAIS supprimer ces fichiers
                if json_file in self.protected_files:
                    kept_count += 1
                    logger.debug(f"PROTÉGÉ: {json_file} conservé (fichier protégé)")
                    continue
                
                # Double vérification pour scraped_properties.json
                if 'scraped_properties' in json_file:
                    kept_count += 1
                    logger.debug(f"PROTÉGÉ: {json_file} conservé (liste des IDs)")
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
                        logger.info(f"Supprimé: {json_file} (date: {file_time.strftime('%Y-%m-%d %H:%M')})")
                    else:
                        kept_count += 1
                        
                except Exception as e:
                    logger.warning(f"Impossible de supprimer {json_file}: {e}")
            
            logger.info(f"✓ Nettoyage terminé: {deleted_count} fichiers supprimés, {kept_count} fichiers conservés")
            
            # Marquer la date du dernier nettoyage
            self.last_cleanup_date = now
            
        except Exception as e:
            logger.error(f"Erreur durant le nettoyage: {e}", exc_info=True)
    
    def run_continuous_monitoring(self, interval_minutes=None):
        """
        Exécute le monitoring en continu
        """
        if interval_minutes is None:
            interval_minutes = MONITORING_INTERVAL
        
        logger.info("="*80)
        logger.info("DÉMARRAGE DU MONITORING CONTINU")
        logger.info(f"URL: {MATRIX_URL}")
        logger.info(f"API: {API_ENDPOINT}")
        logger.info(f"Intervalle: {interval_minutes} minutes")
        if self.auto_cleanup_enabled:
            days = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
            logger.info(f"Nettoyage auto: {days[self.cleanup_day]} à {self.cleanup_hour}h")
        logger.info("="*80)
        
        cycle_number = 0
        
        try:
            while True:
                cycle_number += 1
                logger.info(f">>> CYCLE #{cycle_number} <<<")
                
                # Vérifier si c'est l'heure du nettoyage
                if self.auto_cleanup_enabled:
                    self.cleanup_json_files()
                
                start_time = time.time()
                
                # Exécuter le cycle
                stats = self.run_monitoring_cycle()
                
                elapsed_time = time.time() - start_time
                
                logger.info(f"Cycle terminé en {elapsed_time:.0f} secondes")
                logger.info(f"Prochain cycle dans {interval_minutes} minutes...")
                logger.info(f"Appuyez sur Ctrl+C pour arrêter le monitoring")
                
                # Attendre avant le prochain cycle
                time.sleep(interval_minutes * 60)
                
        except KeyboardInterrupt:
            logger.info("Arrêt du monitoring demandé par l'utilisateur")
            logger.info(f"Total de {cycle_number} cycles exécutés")
            logger.info(f"{len(self.scraped_ids)} annonces en mémoire")
            logger.info("✓ Monitoring arrêté proprement")


def main():
    """
    Fonction principale - Mode Production
    """
    logger.info("="*80)
    logger.info("SCRAPER CENTRIS - VERSION PRODUCTION")
    logger.info("="*80)
    
    # Vérifier la configuration
    logger.info("Vérification de la configuration...")
    
    if API_ENDPOINT == "https://votre-api.com/api/properties":
        logger.warning("="*50)
        logger.warning("L'API N'EST PAS CONFIGURÉE !")
        logger.warning("Éditez config_api.py et configurez API_ENDPOINT")
        logger.warning("Les données seront sauvegardées localement uniquement")
        logger.warning("="*50)
        
        response = input("Continuer quand même ? (o/n) : ")
        if response.lower() != 'o':
            logger.info("Arrêt du programme")
            return
    else:
        logger.info(f"✓ API configurée: {API_ENDPOINT}")
    
    logger.info(f"✓ URL Matrix: {MATRIX_URL}")
    logger.info(f"✓ Intervalle: {MONITORING_INTERVAL} minutes")
    logger.info(f"✓ Fichier de stockage: {STORAGE_FILE}")
    logger.info(f"✓ Date minimale: 2026-01-26 (annonces antérieures ignorées)")
    
    # Créer le moniteur
    monitor = CentrisProductionMonitor(min_date='2026-02-06', skip_photos=False)
    
    # Lancer le monitoring continu
    logger.info("Lancement du monitoring continu...")
    logger.info("Le système va vérifier les nouvelles annonces toutes les heures")
    logger.info("Chaque nouvelle annonce sera automatiquement scrapée et envoyée à l'API")
    
    try:
        monitor.run_continuous_monitoring()
    except Exception as e:
        logger.critical(f"Erreur critique: {e}", exc_info=True)
        logger.info("Redémarrage du monitoring dans 60 secondes...")
        time.sleep(60)
        main()  # Redémarrer


if __name__ == "__main__":
    main()

