#!/bin/bash
################################################################################
# Installation du robot Matrix sur le serveur (idempotent).
# A lancer en root, depuis le dossier qui contient le code (ex. /tmp/matrix-sync).
# Ne touche pas a Scrapis (/opt/scraper-centris, service scraper-centris).
################################################################################
set -euo pipefail

APP_DIR=/opt/matrix-sync
SRC_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "== Utilisateur et dossiers"
id matrixsync >/dev/null 2>&1 || useradd --system --home "$APP_DIR" --shell /usr/sbin/nologin matrixsync
mkdir -p "$APP_DIR" "$APP_DIR/data" "$APP_DIR/js" "$APP_DIR/deploy"

echo "== Code"
cp "$SRC_DIR"/*.py "$SRC_DIR"/requirements.txt "$APP_DIR"/
cp "$SRC_DIR"/js/*.js "$APP_DIR"/js/
cp "$SRC_DIR"/deploy/* "$APP_DIR"/deploy/

echo "== Python"
if [ ! -d "$APP_DIR/venv" ]; then
    python3.12 -m venv "$APP_DIR/venv"
fi
"$APP_DIR/venv/bin/pip" install --quiet --upgrade pip
"$APP_DIR/venv/bin/pip" install --quiet -r "$APP_DIR/requirements.txt"

echo "== Fichier .env"
if [ ! -f "$APP_DIR/.env" ]; then
    cp "$SRC_DIR/deploy/env.example" "$APP_DIR/.env"
    KEY=$(python3.12 -c "import secrets; print(secrets.token_urlsafe(48))")
    sed -i "s|^MATRIX_SYNC_API_KEY=.*|MATRIX_SYNC_API_KEY=$KEY|" "$APP_DIR/.env"
    echo "   .env cree avec une nouvelle cle d'API (a copier dans MATRIX_SYNC_API_KEY de l'API)."
else
    echo "   .env deja present : conserve tel quel."
fi

echo "== ChromeDriver"
if ! grep -q '^CHROMEDRIVER_PATH=.\+' "$APP_DIR/.env"; then
    # Le chromedriver du PATH est une coquille snap inutilisable ici : on reprend celui que Selenium a deja telecharge pour Scrapis.
    CHROME_VER=$(google-chrome --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | head -n 1 || true)
    DRIVER=$(find /root/.cache/selenium/chromedriver -path "*/${CHROME_VER}/chromedriver" -type f 2>/dev/null | head -n 1 || true)
    if [ -z "$DRIVER" ]; then
        DRIVER=$(find /root/.cache/selenium/chromedriver -name chromedriver -type f 2>/dev/null | sort | tail -n 1 || true)
    fi
    if [ -n "$DRIVER" ]; then
        mkdir -p "$APP_DIR/bin"
        cp "$DRIVER" "$APP_DIR/bin/chromedriver"
        chmod 755 "$APP_DIR/bin/chromedriver"
        sed -i "s|^CHROMEDRIVER_PATH=.*|CHROMEDRIVER_PATH=$APP_DIR/bin/chromedriver|" "$APP_DIR/.env"
        echo "   chromedriver copie depuis $DRIVER"
    else
        echo "   ATTENTION : aucun chromedriver trouve. Installez-en un correspondant a Chrome et renseignez CHROMEDRIVER_PATH."
    fi
fi

echo "== Droits"
chown -R matrixsync:matrixsync "$APP_DIR"
chmod 600 "$APP_DIR/.env"
chmod 700 "$APP_DIR/data"
touch /var/log/matrix-sync.log
chown matrixsync:matrixsync /var/log/matrix-sync.log

echo "== Service systemd"
cp "$APP_DIR/deploy/matrix-sync.service" /etc/systemd/system/matrix-sync.service
cat > /etc/logrotate.d/matrix-sync << 'EOF'
/var/log/matrix-sync.log {
    weekly
    rotate 4
    compress
    missingok
    notifempty
    copytruncate
}
EOF
systemctl daemon-reload
systemctl enable matrix-sync

echo
echo "Installation terminee. Etapes suivantes :"
echo "  1. nano $APP_DIR/.env   (renseigner MATRIX_USER et MATRIX_PASSWORD)"
echo "  2. systemctl restart matrix-sync && tail -f /var/log/matrix-sync.log"
