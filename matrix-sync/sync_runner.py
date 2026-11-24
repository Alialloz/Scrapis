"""Déroulement d'une synchronisation : les quatre étapes décrites dans le CRM."""
import logging
import time
from typing import Any, Dict, List, Optional

import config
import helpers
from api_client import ApiClient, ApiError
from matrix_browser import (
    Cancelled,
    LoginError,
    MatrixBrowser,
    MatrixError,
    SmsTimeout,
)

logger = logging.getLogger("matrix-sync.runner")

PHASE_TITLES = {
    "NEW": "nouvelles inscriptions",
    "MODIFIED": "inscriptions modifiées",
    "EXPIRED": "inscriptions expirées",
    "SOLD": "inscriptions vendues",
}


class SyncRunner:
    def __init__(self, api: ApiClient, job: Dict[str, Any]) -> None:
        self.api = api
        self.job = job
        self.run_id: int = job["id"]
        self.phases: List[str] = [p for p in helpers.PHASES if p in job.get("phases", [])]
        self.dates: Dict[str, str] = job.get("dates", {})
        self.dry_run: bool = bool(job.get("dryRun"))
        self.sms_wait: int = int(job.get("smsWaitMinutes", 15))
        self.browser = MatrixBrowser()
        self.phase_results: Dict[str, Dict[str, Any]] = {}
        self._last_control = 0.0

    # ---- Échanges avec le CRM ------------------------------------------------------------------

    def report(self, step: str, state: Optional[str] = None, login_ok: bool = False) -> None:
        try:
            result = self.api.status(self.run_id, step=step, state=state, login_ok=login_ok)
            if result.get("cancelRequested"):
                raise Cancelled("Annulée depuis le CRM.")
        except ApiError as error:
            logger.warning("Statut non transmis : %s", error)

    def check_cancel(self, force: bool = False) -> None:
        """Interroge le CRM au plus toutes les 5 secondes (annulation demandée ?)."""
        now = time.time()
        if not force and now - self._last_control < 5:
            return
        self._last_control = now
        try:
            if self.api.control(self.run_id).get("cancelRequested"):
                raise Cancelled("Annulée depuis le CRM.")
        except ApiError as error:
            logger.warning("Contrôle impossible : %s", error)

    def ask_sms(self, attempt: int) -> Optional[str]:
        """Prévient le CRM qu'un code SMS est attendu, puis l'attend (la personne le saisit dans le CRM)."""
        self.report("En attente du code SMS (à saisir dans le CRM)", state="WAITING_SMS")
        deadline = time.time() + self.sms_wait * 60
        last_ping = 0.0
        while time.time() < deadline:
            time.sleep(3)
            try:
                control = self.api.control(self.run_id)
            except ApiError as error:
                logger.warning("Contrôle impossible : %s", error)
                continue
            if control.get("cancelRequested"):
                raise Cancelled("Annulée depuis le CRM.")
            if control.get("status") not in ("WAITING_SMS", "RUNNING"):
                return None
            code = control.get("smsCode")
            if code:
                logger.info("Code SMS reçu du CRM (tentative %d).", attempt)
                self.report("Code SMS reçu", state="RUNNING")
                return code
            if time.time() - last_ping > 60:
                # Signe de vie : sans lui, l'API croirait le robot arrêté.
                self.report("En attente du code SMS (à saisir dans le CRM)", state="WAITING_SMS")
                last_ping = time.time()
        return None

    # ---- Déroulement ---------------------------------------------------------------------------

    def execute(self) -> None:
        logger.info(
            "Synchronisation %d : étapes %s%s", self.run_id, self.phases, " (mode rapport)" if self.dry_run else ""
        )
        try:
            self.browser.start()
            self.browser.login(self.ask_sms, lambda step: self.report(step))
            self.report("Connecté à Matrix", state="RUNNING", login_ok=True)

            for index, phase in enumerate(self.phases, start=1):
                self.check_cancel(force=True)
                try:
                    self.run_phase(phase, index, len(self.phases))
                except (Cancelled, LoginError, SmsTimeout):
                    raise
                except (MatrixError, ApiError) as error:
                    logger.error("Étape %s interrompue : %s", phase, error)
                    self.phase_results[phase] = {"complete": False, "found": self.phase_results.get(phase, {}).get("found", 0)}
                    self._safe_item_error(phase, "?", f"Étape interrompue : {error}")

            self.finish(True)
        except Cancelled as error:
            self.finish(False, str(error))
        except (LoginError, SmsTimeout) as error:
            self.finish(False, str(error))
        except Exception as error:  # noqa: BLE001 - toute panne imprévue doit être remontée au CRM
            logger.exception("Synchronisation %d en échec", self.run_id)
            self.browser.save_debug("echec")
            self.finish(False, f"Erreur inattendue : {error}")
        finally:
            self.browser.stop()

    def finish(self, success: bool, error: Optional[str] = None) -> None:
        try:
            self.api.finish(self.run_id, success, error, self.phase_results)
        except ApiError as api_error:
            logger.error("Fin de synchronisation non transmise : %s", api_error)

    def _safe_item_error(self, phase: str, number: str, message: str) -> None:
        try:
            self.api.item_error(self.run_id, phase, number, message)
        except ApiError as error:
            logger.warning("Erreur d'annonce non transmise : %s", error)

    def run_phase(self, phase: str, index: int, total: int) -> None:
        since = self.dates.get(phase)
        if not since:
            raise MatrixError(f"Pas de date de départ pour l'étape {phase}.")

        title = PHASE_TITLES[phase]
        prefix = f"Étape {index}/{total} : {title}"
        self.report(f"{prefix} — recherche depuis le {since}")

        self.browser.open_first_favorite()
        found = self.browser.run_search(phase, since)
        self.phase_results[phase] = {"complete": False, "found": found}
        logger.info("%s : %d résultat(s) depuis le %s", phase, found, since)

        if found == 0:
            self.phase_results[phase]["complete"] = True
            self.report(f"{prefix} — aucun résultat")
            return

        errors = 0
        seen = set()
        position = 0
        while True:
            self.check_cancel()
            header = self.browser.read_header()
            number = header["number"]
            if not number:
                raise MatrixError("Numéro Centris illisible sur la fiche.")
            if number in seen:
                break
            seen.add(number)
            position += 1
            if position > config.MAX_LISTINGS_PER_PHASE:
                raise MatrixError(f"Plus de {config.MAX_LISTINGS_PER_PHASE} résultats : arrêt de sécurité.")

            self.report(f"{prefix} — {position}/{found} (n° {number})")
            if not self.process_current(phase, header):
                errors += 1

            time.sleep(config.LISTING_PAUSE)
            if not self.browser.go_next(number):
                break

        # La date n'avance que si tout s'est bien passé : sinon la même période est relue la prochaine fois.
        self.phase_results[phase] = {"complete": errors == 0 and position > 0, "found": found}
        logger.info("%s terminée : %d fiche(s), %d erreur(s)", phase, position, errors)

    def process_current(self, phase: str, header: Dict[str, Any]) -> bool:
        """Traite la fiche affichée. Renvoie False en cas d'erreur sur cette fiche."""
        number = header["number"]
        try:
            if phase in ("NEW", "MODIFIED"):
                listing = self.browser.parse_listing()
                if (listing.get("centrisNo") or "") != number:
                    raise MatrixError(f"La fiche lue porte le n° {listing.get('centrisNo') or '?'} au lieu de {number}.")
                if not listing.get("address"):
                    raise MatrixError("Adresse illisible sur la fiche.")

                brokers_error: Optional[str] = None
                if phase == "NEW":
                    try:
                        brokers = self.browser.parse_brokers(header)
                        listing["brokers"] = brokers.get("brokers", [])
                        listing["collaborators"] = brokers.get("collaborators", [])
                        if not listing["brokers"]:
                            # Pas une panne : certaines annonces n'affichent aucun courtier (le CRM garde alors les siens).
                            logger.info("NEW n° %s : aucun courtier inscripteur lu.", number)
                    except MatrixError as error:
                        brokers_error = f"Courtiers non lus : {error}"
                else:
                    # Étape « modifiées » : jamais de courtiers.
                    listing.pop("brokers", None)
                    listing.pop("collaborators", None)

                result = self.api.listing(self.run_id, phase, number, listing)
                logger.info("%s n° %s : %s — %s", phase, number, result.get("outcome"), result.get("message"))
                if brokers_error:
                    self._safe_item_error(phase, number, f"{brokers_error} (le reste de la fiche a été traité)")
                    return False
                return result.get("outcome") != "ERROR"

            if not helpers.header_status_matches(phase, header.get("status")):
                logger.warning(
                    "%s n° %s ignoré : statut lu « %s » (attendu pour cette étape).", phase, number, header.get("status")
                )
                self._safe_item_error(phase, number, f"Statut lu sur la fiche : « {header.get('status')} » : ignorée.")
                return False

            result = self.api.status_change(self.run_id, phase, number)
            logger.info("%s n° %s : %s — %s", phase, number, result.get("outcome"), result.get("message"))
            return result.get("outcome") != "ERROR"
        except (MatrixError, ApiError) as error:
            logger.error("%s n° %s : %s", phase, number, error)
            self._safe_item_error(phase, number, str(error))
            return False
