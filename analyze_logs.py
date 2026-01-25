#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script d'analyse des logs du scraper Centris
Permet d'identifier rapidement les problèmes et statistiques
"""

import re
import os
from datetime import datetime, timedelta
from collections import defaultdict, Counter

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "scraper.log")
ERROR_FILE = os.path.join(LOG_DIR, "errors.log")


def parse_log_line(line):
    """Parse une ligne de log et retourne les composants"""
    pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| (\w+)\s*\| ([^|]+) \| (.+)'
    match = re.match(pattern, line)
    
    if match:
        return {
            'timestamp': datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S'),
            'level': match.group(2).strip(),
            'logger': match.group(3).strip(),
            'message': match.group(4).strip()
        }
    return None


def analyze_logs(log_file, last_hours=24):
    """
    Analyse les logs et retourne des statistiques
    
    Args:
        log_file: Chemin vers le fichier de log
        last_hours: Analyser les X dernières heures
    """
    if not os.path.exists(log_file):
        print(f"[ERREUR] Fichier de log introuvable: {log_file}")
        return None
    
    cutoff_time = datetime.now() - timedelta(hours=last_hours)
    
    stats = {
        'total_lines': 0,
        'by_level': Counter(),
        'by_hour': defaultdict(int),
        'errors': [],
        'extractions_reussies': 0,
        'extractions_echouees': 0,
        'sources_extraites': Counter(),
        'photos_count': []
    }
    
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            stats['total_lines'] += 1
            parsed = parse_log_line(line)
            
            if not parsed:
                continue
            
            # Filtrer par temps
            if parsed['timestamp'] < cutoff_time:
                continue
            
            # Stats par niveau
            stats['by_level'][parsed['level']] += 1
            
            # Stats par heure
            hour_key = parsed['timestamp'].strftime('%Y-%m-%d %H:00')
            stats['by_hour'][hour_key] += 1
            
            # Extractions réussies/échouées
            if '✓ Extraction réussie' in parsed['message']:
                stats['extractions_reussies'] += 1
                
                # Extraire le numéro Centris
                centris_match = re.search(r'Centris #(\d+)', parsed['message'])
                if centris_match:
                    stats['sources_extraites'][centris_match.group(1)] += 1
            
            elif '✗ Échec extraction' in parsed['message']:
                stats['extractions_echouees'] += 1
            
            # Capturer les erreurs
            if parsed['level'] in ['ERROR', 'CRITICAL']:
                stats['errors'].append({
                    'timestamp': parsed['timestamp'],
                    'message': parsed['message']
                })
            
            # Extraire le nombre de photos
            photo_match = re.search(r'Photos: (\d+)', parsed['message'])
            if photo_match:
                stats['photos_count'].append(int(photo_match.group(1)))
    
    return stats


def print_stats_report(stats, hours=24):
    """Affiche un rapport détaillé des statistiques"""
    print("\n" + "="*80)
    print(f"RAPPORT D'ANALYSE DES LOGS - Dernières {hours}h")
    print("="*80)
    print()
    
    # Résumé général
    print("📊 RÉSUMÉ GÉNÉRAL")
    print("-" * 80)
    print(f"  Lignes de log: {stats['total_lines']}")
    print(f"  Extractions réussies: {stats['extractions_reussies']}")
    print(f"  Extractions échouées: {stats['extractions_echouees']}")
    
    if stats['extractions_reussies'] + stats['extractions_echouees'] > 0:
        success_rate = (stats['extractions_reussies'] / 
                       (stats['extractions_reussies'] + stats['extractions_echouees'])) * 100
        print(f"  Taux de réussite: {success_rate:.1f}%")
    print()
    
    # Stats par niveau
    print("📈 MESSAGES PAR NIVEAU")
    print("-" * 80)
    for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
        count = stats['by_level'].get(level, 0)
        if count > 0:
            bar = '█' * min(50, count // 10)
            print(f"  {level:10s}: {count:5d} {bar}")
    print()
    
    # Photos
    if stats['photos_count']:
        avg_photos = sum(stats['photos_count']) / len(stats['photos_count'])
        print("📸 STATISTIQUES PHOTOS")
        print("-" * 80)
        print(f"  Moyenne: {avg_photos:.1f} photos/annonce")
        print(f"  Min: {min(stats['photos_count'])}")
        print(f"  Max: {max(stats['photos_count'])}")
        print()
    
    # Erreurs récentes
    if stats['errors']:
        print("❌ DERNIÈRES ERREURS")
        print("-" * 80)
        for error in stats['errors'][-10:]:  # 10 dernières
            timestamp_str = error['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            msg = error['message'][:100]  # Tronquer si trop long
            print(f"  [{timestamp_str}] {msg}")
        print()
    
    # Activité par heure
    if stats['by_hour']:
        print("⏰ ACTIVITÉ PAR HEURE")
        print("-" * 80)
        sorted_hours = sorted(stats['by_hour'].items())[-24:]  # 24 dernières heures
        for hour, count in sorted_hours:
            bar = '█' * min(40, count // 5)
            print(f"  {hour}: {count:4d} {bar}")
    
    print()
    print("="*80)


def check_for_issues(stats):
    """Détecte les problèmes potentiels dans les logs"""
    issues = []
    
    # Taux d'échec élevé
    if stats['extractions_echouees'] > 0:
        total = stats['extractions_reussies'] + stats['extractions_echouees']
        failure_rate = (stats['extractions_echouees'] / total) * 100
        if failure_rate > 10:
            issues.append(f"⚠️  Taux d'échec élevé: {failure_rate:.1f}%")
    
    # Beaucoup d'erreurs
    if stats['by_level']['ERROR'] > 10:
        issues.append(f"⚠️  Nombre élevé d'erreurs: {stats['by_level']['ERROR']}")
    
    # Pas d'activité récente
    if stats['by_hour']:
        last_hour = max(stats['by_hour'].keys())
        last_activity = datetime.strptime(last_hour, '%Y-%m-%d %H:00')
        hours_since = (datetime.now() - last_activity).total_seconds() / 3600
        if hours_since > 2:
            issues.append(f"⚠️  Pas d'activité depuis {hours_since:.1f}h")
    
    # Moyenne de photos trop basse
    if stats['photos_count']:
        avg_photos = sum(stats['photos_count']) / len(stats['photos_count'])
        if avg_photos < 10:
            issues.append(f"⚠️  Moyenne de photos faible: {avg_photos:.1f}")
    
    return issues


def main():
    """Fonction principale"""
    import sys
    
    # Paramètre: nombre d'heures à analyser
    hours = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    
    print(f"Analyse des logs du scraper Centris...")
    print(f"Période: Dernières {hours} heures")
    
    # Analyser les logs
    stats = analyze_logs(LOG_FILE, hours)
    
    if not stats:
        return
    
    # Afficher le rapport
    print_stats_report(stats, hours)
    
    # Vérifier les problèmes
    issues = check_for_issues(stats)
    if issues:
        print("\n" + "="*80)
        print("🔍 PROBLÈMES DÉTECTÉS")
        print("="*80)
        for issue in issues:
            print(f"  {issue}")
        print()
    else:
        print("\n✅ Aucun problème détecté\n")


if __name__ == "__main__":
    main()
