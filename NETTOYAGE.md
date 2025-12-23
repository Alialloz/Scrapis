# 🧹 SYSTÈME DE NETTOYAGE AUTOMATIQUE

## ⚠️ FICHIER CRITIQUE PROTÉGÉ

Le fichier **`scraped_properties.json`** contient la liste de tous les numéros Centris déjà scrapés. 

**CE FICHIER NE SERA JAMAIS SUPPRIMÉ !**

### Protection Multi-Niveaux

1. ✅ **Liste des fichiers protégés** dans `config_api.py`
2. ✅ **Vérification par nom** (double protection)
3. ✅ **Sauvegarde automatique** avant chaque nettoyage
4. ✅ **10 sauvegardes conservées** dans `scraped_properties_backup_YYYYMMDD_HHMMSS.json`

---

## 📋 Configuration du Nettoyage

### Dans `config_api.py`

```python
# Activer la suppression automatique des JSON locaux
AUTO_CLEANUP_ENABLED = True  # True = supprimer automatiquement les JSON

# Jour de la semaine pour le nettoyage (0=Lundi, 6=Dimanche)
CLEANUP_DAY = 6  # Dimanche

# Heure du nettoyage (0-23)
CLEANUP_HOUR = 23  # 23h00 (11 PM)

# Garder les fichiers de cette semaine (True) ou tout supprimer (False)
KEEP_CURRENT_WEEK = True  # True = garder les JSON de la semaine en cours

# Créer une sauvegarde du fichier scraped_properties.json
AUTO_BACKUP_SCRAPED_IDS = True  # Sauvegarde automatique avant nettoyage
```

---

## 🔄 Fonctionnement Automatique

### Quand le nettoyage se déclenche

Le système vérifie à chaque cycle (toutes les heures) :

1. Est-ce le bon **jour de la semaine** ? (CLEANUP_DAY)
2. Est-ce la bonne **heure** ? (CLEANUP_HOUR)
3. A-t-on déjà fait le nettoyage **aujourd'hui** ?

Si OUI aux 3 questions → Nettoyage automatique

### Processus de nettoyage

```
1. Création d'une sauvegarde de scraped_properties.json
   └─> scraped_properties_backup_20251219_230000.json

2. Scan de tous les fichiers property_*.json

3. Pour chaque fichier :
   ├─ Est-il dans la liste protégée ? → CONSERVER
   ├─ Contient-il "scraped_properties" ? → CONSERVER
   ├─ Est-il de cette semaine ? (si KEEP_CURRENT_WEEK=True) → CONSERVER
   └─ Sinon → SUPPRIMER

4. Affichage du résumé :
   ├─ X fichiers supprimés
   └─ Y fichiers conservés
```

---

## 📊 Exemples de Configuration

### Exemple 1 : Nettoyage léger (par défaut)

```python
AUTO_CLEANUP_ENABLED = True
CLEANUP_DAY = 6  # Dimanche
CLEANUP_HOUR = 23  # 23h
KEEP_CURRENT_WEEK = True  # Garder la semaine en cours
```

**Résultat :** Chaque dimanche à 23h, supprime les fichiers de plus d'une semaine.

### Exemple 2 : Nettoyage agressif

```python
AUTO_CLEANUP_ENABLED = True
CLEANUP_DAY = 6  # Dimanche
CLEANUP_HOUR = 23  # 23h
KEEP_CURRENT_WEEK = False  # Supprimer TOUS les fichiers
```

**Résultat :** Chaque dimanche à 23h, supprime TOUS les fichiers JSON (sauf protégés).

### Exemple 3 : Nettoyage quotidien

```python
AUTO_CLEANUP_ENABLED = True
CLEANUP_DAY = 0  # Lundi
CLEANUP_HOUR = 2  # 2h du matin
KEEP_CURRENT_WEEK = True
```

**Résultat :** Chaque lundi à 2h du matin, supprime les fichiers de plus d'une semaine.

### Exemple 4 : Désactiver le nettoyage

```python
AUTO_CLEANUP_ENABLED = False
```

**Résultat :** Aucun nettoyage automatique, les fichiers s'accumulent.

---

## 🛠️ Nettoyage Manuel

### Script de nettoyage immédiat

```bash
python cleanup_manual.py
```

Ce script :
1. Liste tous les fichiers à supprimer
2. Demande confirmation
3. Supprime les fichiers (sauf protégés)

**⚠️ scraped_properties.json est TOUJOURS protégé, même en mode manuel !**

---

## 📁 Fichiers Protégés

Ces fichiers ne seront **JAMAIS** supprimés :

| Fichier | Raison |
|---------|--------|
| `scraped_properties.json` | ⚠️ **CRITIQUE** - Liste des IDs scrapés |
| `monitoring_stats.json` | Statistiques de monitoring |
| `property_with_list_info.json` | Fichier de test |
| `scraped_properties_backup_*.json` | Sauvegardes (10 dernières conservées) |

---

## 🔍 Logs du Nettoyage

Lors du nettoyage, vous verrez :

```
================================================================================
NETTOYAGE AUTOMATIQUE DES FICHIERS JSON
================================================================================
[BACKUP] Sauvegarde creee: scraped_properties_backup_20251219_230000.json
[INFO] Conservation des fichiers depuis le 2025-12-16
[PROTEGE] scraped_properties.json conserve (fichier protege)
[SUPPRIME] property_12053552.json (date: 2025-12-10 09:08)
[SUPPRIME] property_21008469.json (date: 2025-12-11 09:09)
...

[OK] Nettoyage termine:
  - 15 fichiers supprimes
  - 8 fichiers conserves
```

---

## 💾 Sauvegardes Automatiques

### Localisation

Les sauvegardes sont créées dans le même dossier :
- `scraped_properties_backup_20251219_230000.json`
- `scraped_properties_backup_20251226_230000.json`
- etc.

### Rotation

Seules les **10 dernières sauvegardes** sont conservées. Les plus anciennes sont automatiquement supprimées.

### Restauration

Pour restaurer une sauvegarde :

```bash
# Arrêter le monitoring
Ctrl+C

# Restaurer
copy scraped_properties_backup_20251219_230000.json scraped_properties.json

# Relancer le monitoring
python scraper_production.py
```

---

## ⚠️ IMPORTANT

### Si vous supprimez scraped_properties.json par erreur :

1. **Arrêter le monitoring immédiatement** (Ctrl+C)
2. **Restaurer depuis une sauvegarde** :
   ```bash
   copy scraped_properties_backup_XXXXXXXX_XXXXXX.json scraped_properties.json
   ```
3. **Relancer le monitoring**

### Si vous n'avez pas de sauvegarde :

Le système va re-scraper toutes les annonces comme si c'était la première fois.

⚠️ **Cela peut envoyer des doublons à votre API !**

**Solution :** Configurez votre API pour ignorer les doublons basés sur `numero_centris`.

---

## 📊 Estimation de l'Espace Disque

### Sans nettoyage

- 1 annonce = ~10 KB
- 100 nouvelles annonces/mois = 1 MB/mois
- 1 an = ~12 MB

### Avec nettoyage hebdomadaire (KEEP_CURRENT_WEEK=True)

- Maximum ~7 jours de données
- Si 10 annonces/jour = 70 fichiers max = ~700 KB

### Avec nettoyage hebdomadaire (KEEP_CURRENT_WEEK=False)

- Tous les fichiers supprimés chaque dimanche
- ~0 KB (sauf fichiers de la journée)

---

## ✅ Recommandations

1. ✅ **Laisser AUTO_CLEANUP_ENABLED = True**
2. ✅ **Laisser AUTO_BACKUP_SCRAPED_IDS = True**
3. ✅ **Garder KEEP_CURRENT_WEEK = True** (pour conserver une semaine de données)
4. ✅ **Faire une sauvegarde manuelle de scraped_properties.json régulièrement**
5. ✅ **Ne JAMAIS modifier manuellement scraped_properties.json**

---

## 🎯 Résumé

Le système de nettoyage :
- ✅ Libère automatiquement de l'espace disque
- ✅ Protège absolument scraped_properties.json
- ✅ Crée des sauvegardes automatiques
- ✅ Est entièrement configurable
- ✅ Fonctionne silencieusement en arrière-plan

**scraped_properties.json est protégé à 100% ! Aucun risque de perte ! 🛡️**




