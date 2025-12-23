#!/bin/bash
################################################################################
# Script de déploiement rapide du code sur le serveur
# À exécuter LOCALEMENT pour envoyer le code sur le serveur
################################################################################

# Configuration
SERVER_IP="VOTRE_IP_SERVEUR"  # ← MODIFIEZ ICI
SERVER_USER="root"
SERVER_PATH="/opt/scraper-centris"

echo "========================================================================"
echo "    DEPLOIEMENT DU SCRAPER CENTRIS"
echo "========================================================================"
echo ""

# Vérifier que l'IP est configurée
if [ "$SERVER_IP" = "VOTRE_IP_SERVEUR" ]; then
    echo "[ERREUR] Veuillez configurer SERVER_IP dans deploy.sh"
    exit 1
fi

echo "[INFO] Connexion au serveur: $SERVER_USER@$SERVER_IP"
echo ""

# 1. Créer une archive du code (exclure certains fichiers)
echo "[1/4] Creation de l'archive du code..."
tar -czf scraper-centris.tar.gz \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='property_*.json' \
    --exclude='*.log' \
    --exclude='backup_*' \
    --exclude='monitoring_stats.json' \
    *.py *.sh *.md *.txt 2>/dev/null
echo "[OK] Archive creee"

# 2. Envoyer l'archive sur le serveur
echo ""
echo "[2/4] Envoi de l'archive sur le serveur..."
scp scraper-centris.tar.gz $SERVER_USER@$SERVER_IP:/tmp/
echo "[OK] Archive envoyee"

# 3. Décompresser sur le serveur
echo ""
echo "[3/4] Decompression sur le serveur..."
ssh $SERVER_USER@$SERVER_IP << 'EOF'
cd /opt/scraper-centris
tar -xzf /tmp/scraper-centris.tar.gz
rm /tmp/scraper-centris.tar.gz
echo "[OK] Code decompresse"
EOF

# 4. Redémarrer le service
echo ""
echo "[4/4] Redemarrage du service..."
ssh $SERVER_USER@$SERVER_IP "systemctl restart scraper-centris"
echo "[OK] Service redémarre"

# Nettoyage local
rm scraper-centris.tar.gz

echo ""
echo "========================================================================"
echo "    DEPLOIEMENT TERMINE!"
echo "========================================================================"
echo ""
echo "Commandes utiles:"
echo "  - Voir les logs:        ssh $SERVER_USER@$SERVER_IP 'tail -f /var/log/scraper-centris.log'"
echo "  - Statut du service:    ssh $SERVER_USER@$SERVER_IP 'systemctl status scraper-centris'"
echo "  - Arreter le service:   ssh $SERVER_USER@$SERVER_IP 'systemctl stop scraper-centris'"
echo ""

