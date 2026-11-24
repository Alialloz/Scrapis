"""Configuration du robot Matrix, lue dans les variables d'environnement.

Sur le serveur, elles viennent du fichier /opt/matrix-sync/.env (lu par systemd).
En local, un fichier .env à côté du code est lu s'il existe. Aucun secret n'est écrit dans le code.
"""
import os
from pathlib import Path


def _load_dotenv() -> None:
    path = Path(__file__).with_name(".env")
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()


def _flag(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "oui")


# --- API du CRM (routes /robot/matrix, clé distincte de celle de Scrapis) ---
API_BASE = os.environ.get("MATRIX_API_BASE", "https://api.rayharvey.ca").rstrip("/")
API_KEY = os.environ.get("MATRIX_SYNC_API_KEY", "")

# --- Compte Matrix (idéalement un code d'usager réservé au robot) ---
MATRIX_URL = os.environ.get("MATRIX_URL", "https://matrix.centris.ca/Matrix/")
MATRIX_USER = os.environ.get("MATRIX_USER", "")
MATRIX_PASSWORD = os.environ.get("MATRIX_PASSWORD", "")

# --- Fichiers du robot ---
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("MATRIX_DATA_DIR", str(BASE_DIR / "data")))
PROFILE_DIR = DATA_DIR / "chrome-profile"
COOKIES_FILE = DATA_DIR / "session-cookies.json"
DEBUG_DIR = DATA_DIR / "debug"
KEEP_DEBUG_FILES = 30

# --- Navigateur ---
HEADLESS = _flag("MATRIX_HEADLESS", True)
CHROME_BIN = os.environ.get("CHROME_BIN", "/usr/bin/google-chrome" if os.name != "nt" else "")
CHROMEDRIVER_PATH = os.environ.get("CHROMEDRIVER_PATH", "")

# --- Rythme ---
POLL_SECONDS = int(os.environ.get("MATRIX_POLL_SECONDS", "20"))
PAGE_TIMEOUT = int(os.environ.get("MATRIX_PAGE_TIMEOUT", "45"))
# Pause entre deux annonces : on reste poli avec Matrix.
LISTING_PAUSE = float(os.environ.get("MATRIX_LISTING_PAUSE", "1.0"))
# Mémoire libre minimale (Mo) pour lancer Chrome sur le petit serveur partagé avec Scrapis.
MIN_FREE_MB = int(os.environ.get("MATRIX_MIN_FREE_MB", "500"))
MAX_LISTINGS_PER_PHASE = int(os.environ.get("MATRIX_MAX_LISTINGS", "600"))
