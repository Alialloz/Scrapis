# Robot Matrix -> CRM (outil indépendant de Scrapis)

Ce robot fait à la place d'une personne ce qu'on faisait avec le plugin Chrome sur Matrix (Centris) :
il lit les annonces et met à jour les mandats du CRM avec « Importer depuis Centris ».

Il n'a **aucun lien** avec Scrapis : autre dossier (`/opt/matrix-sync`), autre service systemd
(`matrix-sync`), autre clé d'API (`MATRIX_SYNC_API_KEY`) et autres routes (`/robot/matrix/*`).

## Ce qu'il fait (étapes configurables dans le CRM, Outils > Synchronisation Matrix)

1. Connexion à Matrix (code d'usager + mot de passe, **code SMS saisi dans le CRM** si Matrix le demande).
2. Tableau de bord > « Mes recherches favorites » > première recherche > onglet Critères.
3. Pour chaque étape, il remplit le statut et la date (avec le « + ») puis lance la recherche, et lit les fiches une à une :

| Étape | Statut | Champ de date | Action sur le mandat |
|---|---|---|---|
| Nouvelles inscriptions | En vigueur | Nouvelles inscriptions | Importer depuis Centris, **avec courtiers** (fiche + page des courtiers) |
| Inscriptions modifiées | En vigueur | Inscriptions modifiées | Importer depuis Centris, sans courtiers |
| Expirées | Expiré | Date d'expiration | Statut de vente = Expiré |
| Vendues | Vendu | Changements de statut | Statut de vente = Vendu |

Les dates sont calculées par l'API (dernière synchronisation réussie moins 1 jour de recouvrement).
La lecture des fiches réutilise **le code du plugin** (`js/plugin_parsing.js`), donc le même format que « Copier ».

## Mode rapport

Réglage du CRM : le robot lit tout et dit ce qu'il ferait, sans modifier aucun mandat ni faire avancer les dates.

## Installation sur le serveur

```
scp -r matrix-sync root@SERVEUR:/tmp/
ssh root@SERVEUR "bash /tmp/matrix-sync/deploy/install.sh"
```

Puis, sur le serveur : renseigner `MATRIX_USER` et `MATRIX_PASSWORD` dans `/opt/matrix-sync/.env`
(la clé d'API y est déjà générée ; la même valeur doit être dans `MATRIX_SYNC_API_KEY` côté API).

```
systemctl restart matrix-sync
tail -f /var/log/matrix-sync.log
```

Test de connexion seul (le code SMS se tape dans la console) :

```
sudo -u matrixsync /opt/matrix-sync/venv/bin/python /opt/matrix-sync/matrix_robot.py --login-only
```

## Diagnostic

En cas de blocage (page de connexion inconnue, délai dépassé…), le robot garde une capture d'écran et le HTML de la
page dans `/opt/matrix-sync/data/debug/` (jamais de mot de passe).

## Sécurité

- Identifiants uniquement dans `/opt/matrix-sync/.env` (droits 600), jamais dans git ni dans le CRM.
- Le code SMS transite chiffré par l'API, n'est lu qu'une fois par le robot, puis effacé ; il n'est jamais journalisé.
- Après un refus de mot de passe ou 3 codes SMS refusés, le robot s'arrête (pas d'insistance, pas de verrouillage du compte).
- Une courte pause sépare les annonces ; Chrome ne démarre que pendant une synchronisation et seulement si la mémoire libre suffit.
- Idéalement, utiliser un code d'usager Matrix réservé au robot (la page de connexion interdit de partager son propre accès).

## Tests

```
python -m unittest discover -s tests
```
