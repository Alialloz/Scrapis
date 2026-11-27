"""Pilotage de Matrix (Centris) avec Selenium : connexion, recherche favorite, parcours des fiches.

Le robot fait ce que la personne ferait à la main, sans contourner de protection :
connexion avec le code d'usager et le mot de passe, code SMS saisi par la personne
(via le CRM), recherche favorite, un résultat à la fois, avec une courte pause.
"""
import json
import logging
import re
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlparse

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

import config
import helpers

logger = logging.getLogger("matrix-sync.browser")

PARSING_JS = (Path(__file__).parent / "js" / "plugin_parsing.js").read_text(encoding="utf-8")


class MatrixError(Exception):
    """Problème côté Matrix (page inattendue, délai dépassé…)."""


class LoginError(MatrixError):
    """Connexion refusée ou impossible : on n'insiste pas, pour ne pas verrouiller le compte."""


class SessionLostError(LoginError):
    """Matrix a coupé la session (page « Autre session détectée »)."""


class SmsTimeout(MatrixError):
    """Le code SMS n'a pas été fourni à temps."""


class Cancelled(MatrixError):
    """La synchronisation a été annulée depuis le CRM."""


# --- Scripts exécutés dans les pages -------------------------------------------------------------

LOGIN_STATE_JS = """
const visible = el => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
const inputs = [...document.querySelectorAll('input')].filter(i => visible(i) &&
    !['hidden', 'submit', 'button', 'checkbox', 'radio', 'image'].includes(i.type));
const password = inputs.find(i => i.type === 'password') || null;
const others = inputs.filter(i => i.type !== 'password');
const errors = [...document.querySelectorAll(
    '.error, .errors, .alert, .alert-danger, [role=alert], .validation-summary-errors, .field-validation-error, .text-danger, .message-error')]
    .filter(visible).map(e => (e.textContent || '').replace(/\\s+/g, ' ').trim()).filter(Boolean);
const buttons = [...document.querySelectorAll('button, input[type=submit], input[type=button], a')]
    .filter(visible).map(b => (b.textContent || b.value || '').replace(/\\s+/g, ' ').trim()).filter(Boolean).slice(0, 25);
return { host: location.host, path: location.pathname, hasPassword: !!password,
         otherInputs: others.map(i => ({ type: i.type, name: i.name, id: i.id, ac: i.autocomplete })),
         errors: errors.slice(0, 3), buttons };
"""

# Remplit le champ de la recherche : vide toutes les dates, choisit le statut, écrit la date de l'étape.
SET_CRITERIA_JS = """
const [statusLabel, dateLabel, dateValue, allLabels] = arguments;
const norm = s => (s || '').replace(/\\s+/g, ' ').trim();
const field = label => {
  for (const tr of document.querySelectorAll('tr')) {
    if (norm(tr.textContent) === label) { const i = tr.querySelector('input[type=text]'); if (i) return i; }
  }
  return null;
};
const select = document.getElementById('Fm103_Ctrl3227_LB') ||
  [...document.querySelectorAll('select')].find(s => [...s.options].some(o => norm(o.text) === 'En vigueur'));
if (!select) return { ok: false, error: 'Liste des statuts introuvable.' };
const target = field(dateLabel);
if (!target) return { ok: false, error: 'Champ de date introuvable : ' + dateLabel };
allLabels.forEach(l => { const f = field(l); if (f) { f.value = ''; } });
let matched = false;
[...select.options].forEach(o => { o.selected = norm(o.text) === statusLabel; if (o.selected) matched = true; });
if (!matched) return { ok: false, error: 'Statut introuvable : ' + statusLabel };
select.dispatchEvent(new Event('change', { bubbles: true }));
target.value = dateValue;
target.dispatchEvent(new Event('change', { bubbles: true }));
return { ok: true, field: target.id, status: [...select.selectedOptions].map(o => norm(o.text)) };
"""

READ_HEADER_JS = """
const norm = s => (s || '').replace(/\\s+/g, ' ').trim();
const spans = [...document.querySelectorAll('span.heading2, span.heading1, span.label')]
  .filter(s => norm(s.textContent).includes('No Centris'));
let header = '';
for (const s of spans) {
  const td = s.closest('td'); const next = td && td.nextElementSibling;
  if (next && /\\d{5,}/.test(next.textContent || '')) { header = norm(next.textContent); break; }
}
const counter = (document.body.innerText.match(/\\d+\\s+de\\s+\\d+/) || [''])[0];
const nextLink = [...document.querySelectorAll('a')].find(a => norm(a.textContent) === 'Suivant' && a.getAttribute('href'));
const itq = [...document.querySelectorAll('a')].map(a => a.getAttribute('href') || '')
  .find(h => h.startsWith('javascript:Dpy.ITQPopup')) || '';
return { header, counter, hasNext: !!nextLink, itq, origin: location.origin };
"""

CLICK_NEXT_JS = """
const norm = s => (s || '').replace(/\\s+/g, ' ').trim();
const a = [...document.querySelectorAll('a')].find(a => norm(a.textContent) === 'Suivant' && a.getAttribute('href'));
if (!a) return false; a.click(); return true;
"""

# Après parse() : « Quadruplex » donne null avec le plugin (aucun chiffre), on le déduit du nom du type.
PROPERTY_TYPE_JS = """
const norm = s => (s || '').replace(/\\s+/g, ' ').trim();
for (const s of document.querySelectorAll('span.label, span.field')) {
  if (norm(s.textContent) !== 'Genre de propriété') continue;
  const td = s.closest('td'); const next = td && td.nextElementSibling;
  if (next) return norm(next.textContent);
}
return '';
"""


OTHER_SESSION_RE = re.compile(r"(autre session d[ée]tect|une autre personne a ouvert une session|another session)", re.IGNORECASE)

class MatrixBrowser:
    def __init__(self) -> None:
        self.driver: Optional[webdriver.Chrome] = None

    # ---- Cycle de vie du navigateur ----------------------------------------------------------

    def start(self) -> None:
        config.PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        options = Options()
        if config.HEADLESS:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1440,900")
        options.add_argument(f"--user-data-dir={config.PROFILE_DIR}")
        options.add_argument("--lang=fr-CA")
        # Économie de mémoire : le serveur est petit et partagé.
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-background-networking")
        options.add_argument("--blink-settings=imagesEnabled=false")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        if config.CHROME_BIN:
            options.binary_location = config.CHROME_BIN

        if config.CHROMEDRIVER_PATH:
            self.driver = webdriver.Chrome(service=Service(config.CHROMEDRIVER_PATH), options=options)
        else:
            self.driver = webdriver.Chrome(options=options)
        self.driver.set_page_load_timeout(config.PAGE_TIMEOUT * 2)
        self._load_session_cookies()

    def stop(self) -> None:
        if not self.driver:
            return
        try:
            self._save_session_cookies()
        finally:
            try:
                self.driver.quit()
            except WebDriverException:
                pass
            self.driver = None

    def _cdp(self, command: str, params: Optional[dict] = None) -> Any:
        assert self.driver
        return self.driver.execute_cdp_cmd(command, params or {})

    def _save_session_cookies(self) -> None:
        """Garde aussi les cookies de session (qui disparaissent à la fermeture de Chrome) : l'équivalent de
        « se souvenir de cet appareil », pour ne redemander le code SMS que lorsque Matrix l'exige."""
        try:
            cookies = self._cdp("Network.getAllCookies").get("cookies", [])
            wanted = [c for c in cookies if "centris.ca" in c.get("domain", "")]
            config.DATA_DIR.mkdir(parents=True, exist_ok=True)
            config.COOKIES_FILE.write_text(json.dumps(wanted), encoding="utf-8")
            try:
                config.COOKIES_FILE.chmod(0o600)
            except OSError:
                pass
        except Exception as error:  # noqa: BLE001 - la sauvegarde ne doit jamais faire échouer la synchronisation
            logger.warning("Cookies non sauvegardés : %s", error)

    def _load_session_cookies(self) -> None:
        if not config.COOKIES_FILE.exists():
            return
        try:
            cookies = json.loads(config.COOKIES_FILE.read_text(encoding="utf-8"))
            self._cdp("Network.enable")
            for cookie in cookies:
                params = {k: cookie[k] for k in ("name", "value", "domain", "path", "secure", "httpOnly", "sameSite") if k in cookie}
                if cookie.get("expires", -1) and cookie["expires"] > 0:
                    params["expires"] = cookie["expires"]
                try:
                    self._cdp("Network.setCookie", params)
                except WebDriverException:
                    continue
        except Exception as error:  # noqa: BLE001
            logger.warning("Cookies non rechargés : %s", error)

    # ---- Utilitaires -------------------------------------------------------------------------

    def _js(self, script: str, *args: Any) -> Any:
        assert self.driver
        return self.driver.execute_script(script, *args)

    def save_debug(self, label: str) -> None:
        """Capture d'écran et HTML de la page, pour comprendre un blocage. Aucun mot de passe : il n'est jamais dans le HTML."""
        if not self.driver:
            return
        try:
            config.DEBUG_DIR.mkdir(parents=True, exist_ok=True)
            stamp = time.strftime("%Y%m%d-%H%M%S")
            safe = re.sub(r"[^a-z0-9_-]+", "-", label.lower())[:40]
            base = config.DEBUG_DIR / f"{stamp}-{safe}"
            self.driver.save_screenshot(str(base) + ".png")
            Path(str(base) + ".html").write_text(self.driver.page_source, encoding="utf-8")
            files = sorted(config.DEBUG_DIR.glob("*"), key=lambda p: p.stat().st_mtime)
            for old in files[: max(0, len(files) - config.KEEP_DEBUG_FILES * 2)]:
                old.unlink(missing_ok=True)
        except Exception as error:  # noqa: BLE001
            logger.warning("Capture de diagnostic impossible : %s", error)

    # ---- Connexion ---------------------------------------------------------------------------

    def _login_state(self) -> Dict[str, Any]:
        info = self._js(LOGIN_STATE_JS)
        host = info.get("host", "")
        on_matrix = host.endswith("matrix.centris.ca")
        path = (info.get("path") or "").lower()
        if on_matrix and not info.get("hasPassword") and "login" not in path and "signin" not in path:
            info["state"] = "matrix"
        elif info.get("hasPassword"):
            info["state"] = "login"
        elif info.get("otherInputs"):
            info["state"] = "sms"
        else:
            info["state"] = "unknown"
        return info

    def _wait_state(self, accepted: List[str], timeout: float) -> Dict[str, Any]:
        deadline = time.time() + timeout
        info: Dict[str, Any] = {"state": "unknown"}
        while time.time() < deadline:
            try:
                info = self._login_state()
            except WebDriverException:
                info = {"state": "unknown"}
            if info["state"] in accepted:
                return info
            time.sleep(1)
        return info

    def login(self, ask_sms: Callable[[int], Optional[str]], report: Callable[[str], None]) -> None:
        """Se connecte. `ask_sms(tentative)` doit renvoyer le code reçu par SMS, ou None si personne ne répond."""
        assert self.driver
        report("Ouverture de Matrix")
        self.driver.get(config.MATRIX_URL)
        info = self._wait_state(["matrix", "login", "sms"], 40)

        if info["state"] == "matrix" and self._other_session_detected():
            # Matrix n'autorise qu'une session par code d'usager : quelqu'un s'est connecté avec le même
            # code et a coupé celle du robot. On repart de la page de connexion.
            logger.warning("Matrix signale qu'une autre session a pris la place : reconnexion.")
            report("Session Matrix interrompue : reconnexion")
            self._click_first_button(r"(poursuivre|authentification|continue|sign in)")
            info = self._wait_state(["login", "sms", "matrix"], 40)
            if info["state"] == "matrix" and self._other_session_detected():
                raise LoginError("Matrix indique toujours qu'une autre session est ouverte avec ce code d'usager.")

        if info["state"] == "matrix":
            logger.info("Session Matrix encore valide : aucune connexion nécessaire.")
            return
        if info["state"] == "unknown":
            self.save_debug("login-page-inconnue")
            raise LoginError("La page de connexion de Matrix n'a pas été reconnue (voir le dossier de diagnostic).")
        if not config.MATRIX_USER or not config.MATRIX_PASSWORD:
            raise LoginError("MATRIX_USER / MATRIX_PASSWORD ne sont pas configurés sur le serveur.")

        if info["state"] == "login":
            report("Connexion à Matrix")
            self._submit_credentials()
            info = self._wait_state(["matrix", "sms", "login"], 45)
            if info["state"] == "login":
                self.save_debug("identifiants-refuses")
                detail = info["errors"][0] if info.get("errors") else "message non lisible"
                raise LoginError(f"Matrix a refusé la connexion ({detail}). Aucune autre tentative pour ne pas verrouiller le compte.")

        attempt = 0
        while info["state"] == "sms":
            attempt += 1
            if attempt > 3:
                raise LoginError("Code SMS refusé 3 fois : arrêt pour ne pas verrouiller le compte.")
            self._request_sms_if_needed(info)
            report("En attente du code SMS")
            code = ask_sms(attempt)
            if not code:
                raise SmsTimeout("Le code SMS n'a pas été saisi à temps.")
            report("Vérification du code SMS")
            self._submit_sms(code)
            info = self._wait_state(["matrix", "sms", "login"], 45)
            if info["state"] == "sms" and info.get("errors"):
                logger.warning("Code SMS refusé : %s", info["errors"][0])

        if info["state"] != "matrix":
            self.save_debug("connexion-incomplete")
            raise LoginError(f"Connexion incomplète (état : {info['state']}).")
        logger.info("Connecté à Matrix.")

    def _visible_inputs(self) -> List[Any]:
        assert self.driver
        result = []
        for element in self.driver.find_elements(By.CSS_SELECTOR, "input"):
            try:
                if element.is_displayed() and element.get_attribute("type") not in (
                    "hidden", "submit", "button", "checkbox", "radio", "image"
                ):
                    result.append(element)
            except WebDriverException:
                continue
        return result

    def _click_first_button(self, patterns: str) -> bool:
        assert self.driver
        regex = re.compile(patterns, re.IGNORECASE)
        for element in self.driver.find_elements(By.CSS_SELECTOR, "button, input[type=submit], input[type=button], a"):
            try:
                text = (element.text or element.get_attribute("value") or "").strip()
                if text and regex.search(helpers.strip_accents(text)) and element.is_displayed():
                    element.click()
                    return True
            except WebDriverException:
                continue
        return False

    def _submit_credentials(self) -> None:
        inputs = self._visible_inputs()
        password = next((i for i in inputs if i.get_attribute("type") == "password"), None)
        user = next((i for i in inputs if i.get_attribute("type") != "password"), None)
        if not user or not password:
            raise LoginError("Champs « code d'usager » et « mot de passe » introuvables.")
        user.clear()
        user.send_keys(config.MATRIX_USER)
        password.clear()
        password.send_keys(config.MATRIX_PASSWORD)
        self._tick_remember_device()
        if not self._click_first_button(r"(connexion|connect|sign in|log ?in|se connecter|soumettre|submit)"):
            password.send_keys(Keys.ENTER)

    def _tick_remember_device(self) -> None:
        """Si Matrix propose « se souvenir de cet appareil », on coche : moins de SMS à saisir."""
        assert self.driver
        pattern = re.compile(r"(souvenir|retenir|remember|trust|confiance|stay signed)", re.IGNORECASE)
        for box in self.driver.find_elements(By.CSS_SELECTOR, "input[type=checkbox]"):
            try:
                label_text = self._js(
                    "const e = arguments[0]; const l = e.labels && e.labels[0]; "
                    "return (l ? l.textContent : (e.closest('label') || e.parentElement || {}).textContent) || '';",
                    box,
                )
                if pattern.search(helpers.strip_accents(label_text)) and not box.is_selected():
                    self._js("arguments[0].click()", box)
            except WebDriverException:
                continue

    def _request_sms_if_needed(self, info: Dict[str, Any]) -> None:
        """Certains écrans demandent d'abord d'envoyer le SMS. S'il n'y a pas de champ à remplir, on clique sur « envoyer »."""
        if info.get("otherInputs"):
            return
        self._click_first_button(r"(envoyer|send|texto|sms|text message)")
        time.sleep(2)

    def _submit_sms(self, code: str) -> None:
        inputs = self._visible_inputs()
        if not inputs:
            raise LoginError("Champ du code SMS introuvable.")
        field = next((i for i in inputs if (i.get_attribute("autocomplete") or "") == "one-time-code"), inputs[0])
        field.clear()
        field.send_keys(code)
        self._tick_remember_device()
        if not self._click_first_button(r"(verif|valid|continu|confirm|soumettre|submit|suivant|next)"):
            field.send_keys(Keys.ENTER)

    # ---- Recherche favorite ------------------------------------------------------------------

    def open_first_favorite(self) -> None:
        """Tableau de bord > « Mes recherches favorites » > première recherche > onglet Critères."""
        assert self.driver
        self.driver.get(config.MATRIX_URL)
        link = None
        deadline = time.time() + config.PAGE_TIMEOUT
        while time.time() < deadline and link is None:
            links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='HotSearches/Run']")
            link = next((l for l in links if l.is_displayed()), None) or (links[0] if links else None)
            if link is None:
                time.sleep(1)
        if link is None:
            self.save_debug("favorites-introuvables")
            if self._other_session_detected():
                raise SessionLostError(
                    "Matrix a coupé la session du robot (page « Autre session détectée »)."
                )
            raise MatrixError("Aucune recherche favorite trouvée sur le tableau de bord de Matrix.")
        name = (link.get_attribute("textContent") or "").strip()
        logger.info("Recherche favorite : %s", name)
        self._js("arguments[0].click()", link)
        try:
            self._wait_for(lambda: "Results.aspx" in self.driver.current_url, "ouverture de la recherche favorite")
        except MatrixError:
            if self._other_session_detected():
                raise SessionLostError(
                    "Matrix a coupé la session du robot (page « Autre session détectée »)."
                ) from None
            raise

    def logout(self) -> None:
        """Ferme la session Matrix (« Fermer la session »). Sans cela, la session reste ouverte côté
        Matrix après la synchronisation et gêne la connexion suivante (autre session détectée)."""
        if not self.driver:
            return
        try:
            self.driver.get(config.MATRIX_URL.rstrip("/") + "/Logout.aspx")
            time.sleep(3)
            logger.info("Session Matrix fermée.")
        except WebDriverException as error:
            logger.warning("Fermeture de la session Matrix impossible : %s", error)

    def reset_session(self) -> None:
        """Oublie la session : cookies du navigateur et fichier de cookies. La prochaine connexion repart de zéro."""
        assert self.driver
        try:
            self._cdp("Network.enable")
            self._cdp("Network.clearBrowserCookies")
        except WebDriverException as error:
            logger.warning("Cookies du navigateur non effacés : %s", error)
        try:
            config.COOKIES_FILE.unlink(missing_ok=True)
        except OSError as error:
            logger.warning("Fichier de cookies non supprimé : %s", error)
        try:
            self.driver.get("about:blank")
        except WebDriverException:
            pass

    def _other_session_detected(self) -> bool:
        """Vrai si Matrix affiche « Autre session détectée » (un autre appareil s'est connecté avec le même code)."""
        try:
            text = self._js("return document.body ? document.body.innerText : ''") or ""
        except WebDriverException:
            return False
        return bool(OTHER_SESSION_RE.search(text))

    def _wait_for(self, condition: Callable[[], Any], what: str, timeout: Optional[float] = None) -> Any:
        try:
            return WebDriverWait(self.driver, timeout or config.PAGE_TIMEOUT, poll_frequency=0.5).until(
                lambda _d: condition()
            )
        except TimeoutException:
            self.save_debug(f"delai-{what}")
            raise MatrixError(f"Délai dépassé : {what}.") from None

    def _open_criteria_tab(self) -> None:
        self._js(
            "const a = document.getElementById('m_ucResultsPageTabs_m_lbSearchTab'); if (a) a.click();"
        )
        self._wait_for(
            lambda: self._js("return !!document.getElementById('Fm103_Ctrl3227_LB')"),
            "affichage de l'onglet Critères",
        )

    def run_search(self, phase: str, since_iso: str) -> int:
        """Remplit les critères de l'étape, lance la recherche et affiche la première fiche.

        Renvoie le nombre de résultats (0 si la recherche ne trouve rien)."""
        criteria = helpers.PHASE_CRITERIA[phase]
        self._open_criteria_tab()
        result = self._js(
            SET_CRITERIA_JS,
            criteria["status"],
            criteria["date_field"],
            helpers.matrix_date(since_iso),
            helpers.ALL_DATE_FIELDS,
        )
        if not result.get("ok"):
            self.save_debug(f"criteres-{phase}")
            raise MatrixError(result.get("error") or "Critères non remplis.")
        logger.info("%s : %s, %s = %s", phase, criteria["status"], criteria["date_field"], helpers.matrix_date(since_iso))

        # Matrix recompte les résultats en arrière-plan dès qu'un critère change. Un clic sur
        # « Résultats » pendant ce recalcul est ignoré : on attend la fin avant de cliquer.
        self._wait_no_async_postback()
        self._click_search()
        return self._wait_for_results()

    def _wait_no_async_postback(self, timeout: float = 20) -> None:
        """Attend que la page n'ait plus de mise à jour partielle en cours (ASP.NET)."""
        deadline = time.time() + timeout
        calm_since: Optional[float] = None
        while time.time() < deadline:
            try:
                busy = bool(self._js(
                    "const s = window.Sys && Sys.WebForms && Sys.WebForms.PageRequestManager;"
                    "const m = s ? s.getInstance() : null;"
                    "return m ? !!m.get_isInAsyncPostBack() : false;"
                ))
            except WebDriverException:
                busy = False
            if busy:
                calm_since = None
            elif calm_since is None:
                calm_since = time.time()
            elif time.time() - calm_since >= 1.5:
                return
            time.sleep(0.4)

    def _click_search(self, retry: bool = False) -> None:
        """Clique sur « Résultats ». Au deuxième essai, déclenche directement l'envoi du formulaire."""
        self._js(
            """
            const retry = arguments[0];
            const a = document.getElementById('m_ucSearchButtons_m_lbSearch');
            if (retry && typeof __doPostBack === 'function') {
                __doPostBack('m_ucSearchButtons$m_lbSearch', '');
            } else if (a) {
                a.click();
            }
            """,
            retry,
        )

    def _on_criteria_tab(self) -> bool:
        """Vrai tant que le formulaire de critères est affiché (et non les résultats)."""
        return bool(self._js(
            "const e = document.getElementById('Fm103_Ctrl3227_LB'); return !!(e && e.offsetParent !== null);"
        ))

    def _wait_for_results(self) -> int:
        """Attend soit la première fiche, soit le message « aucun résultat »."""
        deadline = time.time() + config.PAGE_TIMEOUT
        last_click = time.time()
        clicks = 1
        while time.time() < deadline:
            try:
                # Le clic n'a pas pris : on réessaie quelques fois avant d'abandonner.
                if clicks < 3 and time.time() - last_click > 12 and self._on_criteria_tab():
                    logger.info("Le formulaire de critères est toujours affiché : nouveau clic sur « Résultats ».")
                    self._wait_no_async_postback(10)
                    self._click_search(retry=True)
                    last_click = time.time()
                    clicks += 1
                    continue
                if self._ensure_detailed_display():
                    # L'affichage vient de changer : la page se recharge.
                    time.sleep(2)
                    continue
                header = self.read_header()
                if header["number"]:
                    counter = helpers.parse_counter(header["counter_text"])
                    return counter[1] if counter else 1
                text = self._js("return document.body ? document.body.innerText : ''") or ""
                if re.search(r"aucun(e)?\s+(r[eé]sultat|inscription|propri[eé]t[eé]|correspond)", text, re.IGNORECASE):
                    return 0
            except WebDriverException:
                pass
            time.sleep(1)
        self.save_debug("resultats-inconnus")
        raise MatrixError("La page de résultats n'a ni fiche ni message « aucun résultat ».")

    def _ensure_detailed_display(self) -> bool:
        """Les fiches se lisent une à une en affichage « Détaillé » (1 par page).

        Renvoie True si l'affichage vient d'être changé (la page se recharge)."""
        return bool(self._js(
            """
            const sel = document.getElementById('m_ucDisplayPicker_m_ddlDisplayFormats');
            if (!sel) return false;
            const norm = s => (s || '').replace(/\\s+/g, ' ').trim();
            const opt = [...sel.options].find(o => norm(o.text) === 'Détaillé');
            if (!opt || sel.value === opt.value) return false;
            sel.value = opt.value;
            sel.dispatchEvent(new Event('change', { bubbles: true }));
            return true;
            """
        ))

    # ---- Lecture des fiches ------------------------------------------------------------------

    def read_header(self) -> Dict[str, Any]:
        info = self._js(READ_HEADER_JS)
        parsed = helpers.parse_header(info.get("header", ""))
        return {
            **parsed,
            "counter_text": info.get("counter", ""),
            "has_next": bool(info.get("hasNext")),
            "itq": info.get("itq", ""),
            "origin": info.get("origin", "https://matrix.centris.ca"),
        }

    def go_next(self, current_number: str) -> bool:
        """Passe à la fiche suivante. Renvoie False s'il n'y en a plus."""
        if not self._js(CLICK_NEXT_JS):
            return False
        deadline = time.time() + config.PAGE_TIMEOUT
        while time.time() < deadline:
            time.sleep(0.7)
            try:
                number = self.read_header()["number"]
            except WebDriverException:
                continue
            if number and number != current_number:
                return True
        self.save_debug("suivant-bloque")
        raise MatrixError("Le bouton « Suivant » n'a pas changé de fiche.")

    def parse_listing(self) -> Dict[str, Any]:
        """Lit la fiche affichée avec le code du plugin (même format que le bouton « Copier »)."""
        raw = self._js(PARSING_JS + "\nreturn parse();")
        listing = json.loads(raw)
        if not listing.get("numberOfDoors"):
            doors = helpers.doors_from_property_type(self._js(PROPERTY_TYPE_JS))
            if doors:
                listing["numberOfDoors"] = doors
        return listing

    def parse_brokers(self, header: Dict[str, Any]) -> Dict[str, Any]:
        """Ouvre la page « courtier inscripteur, propriétaire et prêt hypothécaire » dans un onglet à part."""
        assert self.driver
        url = helpers.itq_popup_url(header["origin"], header["itq"])
        if not url:
            raise MatrixError("Lien vers les courtiers introuvable sur la fiche.")

        main = self.driver.current_window_handle
        self.driver.switch_to.new_window("tab")
        try:
            self.driver.get(url)
            self._wait_for(
                lambda: self._js("return document.querySelectorAll('span.heading2').length > 0"),
                "chargement de la page des courtiers",
                timeout=30,
            )
            raw = self._js(PARSING_JS + "\nreturn parseBrokerPage();")
            return json.loads(raw)
        finally:
            try:
                self.driver.close()
            except WebDriverException:
                pass
            self.driver.switch_to.window(main)

    def listing_address(self) -> str:
        try:
            return self.parse_listing().get("address", "")
        except Exception:  # noqa: BLE001
            return ""

    @staticmethod
    def origin_of(url: str) -> str:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"
