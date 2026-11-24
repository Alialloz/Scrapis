"""Appels du robot vers l'API du CRM (routes /robot/matrix)."""
import logging
import time
from typing import Any, Dict, Optional

import requests

import config

logger = logging.getLogger("matrix-sync.api")


class ApiError(Exception):
    pass


class ApiClient:
    def __init__(self) -> None:
        if not config.API_KEY:
            raise ApiError("MATRIX_SYNC_API_KEY n'est pas défini.")
        self.base = f"{config.API_BASE}/robot/matrix"
        self.session = requests.Session()
        self.session.headers.update({"X-Matrix-Key": config.API_KEY, "Content-Type": "application/json"})

    def _request(self, method: str, path: str, payload: Optional[dict] = None, timeout: int = 90) -> Any:
        url = f"{self.base}{path}"
        last_error: Optional[Exception] = None
        for attempt in range(1, 4):
            try:
                response = self.session.request(method, url, json=payload, timeout=timeout)
            except requests.RequestException as error:
                last_error = error
                logger.warning("API injoignable (%s, essai %d/3) : %s", path, attempt, error)
                time.sleep(2 * attempt)
                continue

            if response.status_code >= 500 and attempt < 3:
                logger.warning("API en erreur %d (%s, essai %d/3)", response.status_code, path, attempt)
                time.sleep(2 * attempt)
                continue
            if response.status_code >= 400:
                detail = response.text[:300]
                raise ApiError(f"{method} {path} -> {response.status_code} : {detail}")
            return response.json() if response.content else {}

        raise ApiError(f"{method} {path} : {last_error}")

    def next_run(self) -> Optional[Dict[str, Any]]:
        return self._request("GET", "/next", timeout=30).get("run")

    def status(self, run_id: int, step: Optional[str] = None, state: Optional[str] = None,
               login_ok: bool = False) -> Dict[str, Any]:
        body: Dict[str, Any] = {}
        if step:
            body["step"] = step[:300]
        if state:
            body["state"] = state
        if login_ok:
            body["loginOk"] = True
        return self._request("POST", f"/runs/{run_id}/status", body, timeout=30)

    def control(self, run_id: int) -> Dict[str, Any]:
        return self._request("GET", f"/runs/{run_id}/control", timeout=30)

    def listing(self, run_id: int, phase: str, centris_no: str, listing: Dict[str, Any]) -> Dict[str, Any]:
        return self._request(
            "POST",
            f"/runs/{run_id}/listing",
            {"phase": phase, "centrisNo": centris_no, "listing": listing},
            timeout=120,
        )

    def status_change(self, run_id: int, phase: str, centris_no: str, address: Optional[str] = None) -> Dict[str, Any]:
        body: Dict[str, Any] = {"phase": phase, "centrisNo": centris_no}
        if address:
            body["address"] = address[:300]
        return self._request("POST", f"/runs/{run_id}/status-change", body, timeout=60)

    def item_error(self, run_id: int, phase: str, centris_no: str, message: str) -> None:
        self._request(
            "POST",
            f"/runs/{run_id}/item-error",
            {"phase": phase, "centrisNo": centris_no or "?", "message": message[:500]},
            timeout=30,
        )

    def finish(self, run_id: int, success: bool, error: Optional[str] = None,
               phase_results: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
        body: Dict[str, Any] = {"success": success}
        if error:
            body["error"] = error[:1000]
        if phase_results:
            body["phaseResults"] = phase_results
        return self._request("POST", f"/runs/{run_id}/finish", body, timeout=60)
