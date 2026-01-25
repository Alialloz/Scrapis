#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de migration des print() vers le système de logging
"""

import re

# Mappings de remplacement
REPLACEMENTS = [
    # Erreurs critiques
    (r'print\("\[ERREUR CRITIQUE\]([^"]+)"\)', r'logger.critical("\1")'),
    (r"print\('\[ERREUR CRITIQUE\]([^']+)'\)", r"logger.critical('\1')"),
    (r'print\(f"\[ERREUR CRITIQUE\]([^"]+)"\)', r'logger.critical(f"\1")'),
    
    # Erreurs
    (r'print\("\[ERREUR\]([^"]+)"\)', r'logger.error("\1")'),
    (r"print\('\[ERREUR\]([^']+)'\)", r"logger.error('\1')"),
    (r'print\(f"\[ERREUR\]([^"]+)"\)', r'logger.error(f"\1")'),
    
    # Warnings
    (r'print\("\[WARNING\]([^"]+)"\)', r'logger.warning("\1")'),
    (r"print\('\[WARNING\]([^']+)'\)", r"logger.warning('\1')"),
    (r'print\(f"\[WARNING\]([^"]+)"\)', r'logger.warning(f"\1")'),
    
    # OK/Succès
    (r'print\("\[OK\]([^"]+)"\)', r'logger.info("✓\1")'),
    (r"print\('\[OK\]([^']+)'\)", r"logger.info('✓\1')"),
    (r'print\(f"\[OK\]([^"]+)"\)', r'logger.info(f"✓\1")'),
    
    # Info
    (r'print\("\[INFO\]([^"]+)"\)', r'logger.info("\1")'),
    (r"print\('\[INFO\]([^']+)'\)", r"logger.info('\1')"),
    (r'print\(f"\[INFO\]([^"]+)"\)', r'logger.info(f"\1")'),
    
    # API
    (r'print\("\[API\]([^"]+)"\)', r'logger.info("API:\1")'),
    (r"print\('\[API\]([^']+)'\)", r"logger.info('API:\1')"),
    (r'print\(f"\[API\]([^"]+)"\)', r'logger.info(f"API:\1")'),
    
    # PROTEGE
    (r'print\(f"\[PROTEGE\]([^"]+)"\)', r'logger.debug(f"PROTÉGÉ:\1")'),
    
    # SUPPRIME
    (r'print\(f"\[SUPPRIME\]([^"]+)"\)', r'logger.info(f"Supprimé:\1")'),
    
    # BACKUP
    (r'print\(f"\[BACKUP\]([^"]+)"\)', r'logger.info(f"Backup:\1")'),
]

def migrate_file(filepath):
    """Migre un fichier vers le système de logging"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Appliquer tous les remplacements
    for pattern, replacement in REPLACEMENTS:
        content = re.sub(pattern, replacement, content)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ {filepath} migré")
        return True
    else:
        print(f"  {filepath} - aucun changement")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python migrate_to_logging.py <fichier.py>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    migrate_file(filepath)
