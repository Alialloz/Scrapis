"""Robot de synchronisation Matrix -> CRM (outil indépendant de Scrapis).

Mode service (par défaut) : demande du travail à l'API toutes les quelques secondes ;
quand une synchronisation est en file (bouton du CRM ou planification), il ouvre Chrome,
se connecte à Matrix, parcourt les quatre étapes et envoie tout à l'API.

    python matrix_robot.py                 service
    python matrix_robot.py --login-only    teste seulement la connexion (code SMS saisi dans la console)
"""
import argparse
import logging
import signal
import sys
import time

import config
from api_client import ApiClient, ApiError
from matrix_browser import LoginError, MatrixBrowser, MatrixError, SmsTimeout
from sync_runner import SyncRunner

logger = logging.getLogger("matrix-sync")

_stop = False


def _handle_stop(signum, _frame) -> None:
    global _stop
    logger.info("Arrêt demandé (signal %s) : fin après la tâche en cours.", signum)
    _stop = True


def free_memory_mb() -> int:
    """Mémoire disponible (Mo) sous Linux ; très grande valeur ailleurs (le test ne s'applique pas)."""
    try:
        with open("/proc/meminfo", encoding="utf-8") as handle:
            for line in handle:
                if line.startswith("MemAvailable:"):
                    return int(line.split()[1]) // 1024
    except OSError:
        pass
    return 10**6


def serve() -> int:
    if not config.MATRIX_USER or not config.MATRIX_PASSWORD:
        logger.warning("MATRIX_USER / MATRIX_PASSWORD absents : la connexion échouera si Matrix la demande.")
    api = ApiClient()
    logger.info("Robot Matrix démarré (API : %s).", config.API_BASE)

    while not _stop:
        try:
            job = api.next_run()
        except ApiError as error:
            logger.warning("Impossible de joindre l'API : %s", error)
            time.sleep(config.POLL_SECONDS)
            continue

        if not job:
            time.sleep(config.POLL_SECONDS)
            continue

        available = free_memory_mb()
        if available < config.MIN_FREE_MB:
            # Le serveur est partagé avec Scrapis : on ne lance pas Chrome s'il manque de mémoire.
            logger.warning("Mémoire libre insuffisante (%d Mo) : synchronisation %d abandonnée.", available, job["id"])
            try:
                api.finish(job["id"], False, f"Mémoire insuffisante sur le serveur ({available} Mo libres).")
            except ApiError as error:
                logger.error("Abandon non transmis : %s", error)
            continue

        SyncRunner(api, job).execute()
        time.sleep(2)

    logger.info("Robot Matrix arrêté.")
    return 0


def login_only() -> int:
    """Test de connexion en local ou sur le serveur, sans API : le code SMS se tape dans la console."""
    browser = MatrixBrowser()
    try:
        browser.start()

        def ask_sms(attempt: int):
            return input(f"Code SMS reçu (tentative {attempt}), vide pour abandonner : ").strip() or None

        browser.login(ask_sms, lambda step: print(f"  - {step}"))
        print("Connexion réussie. La session est gardée pour les prochaines synchronisations.")
        browser.open_first_favorite()
        print("Recherche favorite ouverte :", browser.driver.current_url[:90])
        return 0
    except (LoginError, SmsTimeout, MatrixError) as error:
        print(f"Échec : {error}")
        browser.save_debug("login-only")
        return 1
    finally:
        browser.stop()


def main() -> int:
    parser = argparse.ArgumentParser(description="Robot de synchronisation Matrix")
    parser.add_argument("--login-only", action="store_true", help="teste seulement la connexion à Matrix")
    parser.add_argument("--visible", action="store_true", help="affiche la fenêtre de Chrome (test en local)")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s : %(message)s",
        stream=sys.stdout,
    )
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("selenium").setLevel(logging.WARNING)
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)

    if args.visible:
        config.HEADLESS = False

    signal.signal(signal.SIGTERM, _handle_stop)
    signal.signal(signal.SIGINT, _handle_stop)

    return login_only() if args.login_only else serve()


if __name__ == "__main__":
    sys.exit(main())
