#!/bin/bash
################################################################################
# Script d'installation automatique du Scraper Centris sur Ubuntu
# Pour DigitalOcean Droplet
################################################################################

set -e  # Arrêt si erreur
export DEBIAN_FRONTEND=noninteractive
sudo dpkg --configure -a -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold"
export NEEDRESTART_MODE=a

echo "========================================================================"
echo "    INSTALLATION AUTOMATIQUE DU SCRAPER CENTRIS"
echo "========================================================================"
echo ""

# Couleurs pour les messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERREUR]${NC} $1"
}

# Vérifier qu'on est root
if [ "$EUID" -ne 0 ]; then 
    print_error "Ce script doit etre execute en tant que root (sudo)"
    exit 1
fi

print_warning "Debut de l'installation..."
echo ""

# 1. Mise à jour du système
print_warning "Etape 1/8: Mise a jour du systeme..."
apt-get update -qq
apt-get upgrade -y -qq
print_success "Systeme a jour"
echo ""

# 2. Installation de Python 3.12
print_warning "Etape 2/8: Installation de Python 3.12..."
apt-get install -y -qq software-properties-common
add-apt-repository -y ppa:deadsnakes/ppa
apt-get update -qq
apt-get install -y -qq python3.12 python3.12-venv python3.12-dev python3-pip
print_success "Python 3.12 installe"
python3.12 --version
echo ""

# 3. Installation de Chrome
print_warning "Etape 3/8: Installation de Google Chrome..."
wget -q -O /tmp/google-chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
apt-get install -y -qq /tmp/google-chrome.deb
rm /tmp/google-chrome.deb
print_success "Chrome installe"
google-chrome --version
echo ""

# 4. Installation de ChromeDriver
print_warning "Etape 4/8: Installation de ChromeDriver..."
apt-get install -y -qq unzip wget
CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+')
CHROME_MAJOR_VERSION=$(echo $CHROME_VERSION | cut -d. -f1)
print_warning "Chrome version: $CHROME_VERSION (Major: $CHROME_MAJOR_VERSION)"

# Télécharger ChromeDriver compatible
wget -q "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/${CHROME_VERSION}/linux64/chromedriver-linux64.zip" -O /tmp/chromedriver.zip || {
    print_warning "Version exacte non trouvee, tentative avec version majeure..."
    wget -q "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_MAJOR_VERSION}" -O /tmp/chromedriver_version
    DRIVER_VERSION=$(cat /tmp/chromedriver_version)
    wget -q "https://chromedriver.storage.googleapis.com/${DRIVER_VERSION}/chromedriver_linux64.zip" -O /tmp/chromedriver.zip
}

unzip -qq /tmp/chromedriver.zip -d /tmp/
if [ -f /tmp/chromedriver-linux64/chromedriver ]; then
    mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/
else
    mv /tmp/chromedriver /usr/local/bin/
fi
chmod +x /usr/local/bin/chromedriver
rm -rf /tmp/chromedriver* /tmp/chromedriver_version
print_success "ChromeDriver installe"
chromedriver --version
echo ""

# 5. Installation des dépendances système pour Selenium
print_warning "Etape 5/8: Installation des dependances pour Selenium..."
apt-get install -y -qq \
    xvfb \
    libxi6 \
    libgconf-2-4 \
    libnss3 \
    libxss1 \
    libappindicator3-1 \
    fonts-liberation \
    libgbm-dev
print_success "Dependances installees"
echo ""

# 6. Création du répertoire de travail
print_warning "Etape 6/8: Creation du repertoire de travail..."
APP_DIR="/opt/scraper-centris"
mkdir -p $APP_DIR
print_success "Repertoire cree: $APP_DIR"
echo ""

# 7. Installation de Git
print_warning "Etape 7/8: Installation de Git..."
apt-get install -y -qq git
print_success "Git installe"
echo ""

# 8. Configuration du service systemd
print_warning "Etape 8/8: Creation du service systemd..."
cat > /etc/systemd/system/scraper-centris.service << 'EOF'
[Unit]
Description=Scraper Centris - Monitoring automatique
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/scraper-centris
ExecStart=/usr/bin/python3.12 /opt/scraper-centris/scraper_production.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/scraper-centris.log
StandardError=append:/var/log/scraper-centris-error.log

# Variables d'environnement
Environment="DISPLAY=:99"
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
print_success "Service systemd cree"
echo ""

print_success "========================================================================"
print_success "    INSTALLATION TERMINEE AVEC SUCCES!"
print_success "========================================================================"
echo ""
echo "Prochaines etapes:"
echo ""
echo "1. Cloner votre code dans $APP_DIR:"
echo "   cd $APP_DIR"
echo "   git clone https://github.com/VOTRE-REPO/Scrapis.git ."
echo ""
echo "2. Installer les dependances Python:"
echo "   pip3.12 install -r requirements.txt"
echo ""
echo "3. Configurer config_api.py (verifier l'API endpoint)"
echo ""
echo "4. Demarrer le service:"
echo "   systemctl start scraper-centris"
echo "   systemctl enable scraper-centris  # Auto-start au demarrage"
echo ""
echo "5. Verifier les logs:"
echo "   tail -f /var/log/scraper-centris.log"
echo ""
print_warning "Note: Le service redemarrera automatiquement en cas d'erreur"

