"""Fonctions pures (sans navigateur ni réseau), faciles à tester."""
import re
from typing import Dict, Optional, Tuple
from urllib.parse import quote

PHASES = ("NEW", "MODIFIED", "EXPIRED", "SOLD")

# Pour chaque étape : statut à choisir dans Matrix et champ de date à remplir (libellés visibles à l'écran).
PHASE_CRITERIA: Dict[str, Dict[str, str]] = {
    "NEW": {"status": "En vigueur", "date_field": "Nouvelles inscriptions"},
    "MODIFIED": {"status": "En vigueur", "date_field": "Inscriptions modifiées"},
    "EXPIRED": {"status": "Expiré", "date_field": "Date d'expiration"},
    "SOLD": {"status": "Vendu", "date_field": "Changements de statut"},
}

# Tous les champs de date du formulaire : on les vide avant de remplir celui de l'étape,
# pour qu'un critère oublié dans la recherche favorite ne fausse pas les résultats.
ALL_DATE_FIELDS = [
    "Nouvelles inscriptions",
    "Modifications de prix",
    "Inscriptions modifiées",
    "Demandé/Vendu",
    "Changements de statut",
    "Date d'expiration",
]

# Statut attendu dans l'en-tête de la fiche, pour les étapes qui changent le statut du mandat.
EXPECTED_HEADER_STATUS = {"EXPIRED": "expire", "SOLD": "vendu"}

_STATUS_WORDS = ("en vigueur", "expiré", "vendu", "hors marché", "annulé", "retiré", "suspendu")


def matrix_date(iso_date: str) -> str:
    """'2026-11-20' -> '20261120+' (le « + » veut dire « à cette date ou plus tard »)."""
    match = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", (iso_date or "").strip())
    if not match:
        raise ValueError(f"Date invalide : {iso_date!r}")
    return "".join(match.groups()) + "+"


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").replace("\u00a0", " ")).strip()


def strip_accents(text: str) -> str:
    import unicodedata

    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def parse_header(text: str) -> Dict[str, Optional[str]]:
    """'19356747 (Expiré 2026-11-20)' -> numéro, statut et date.

    Le statut est lu dans la première parenthèse : « (Vendu 2026-11-19, 200 jours) (PA acceptée ... ) ».
    """
    text = normalize(text)
    number_match = re.search(r"\d{5,}", text)
    number = number_match.group(0) if number_match else None

    status = None
    date = None
    paren = re.search(r"\(([^)]*)\)", text)
    if paren:
        inside = normalize(paren.group(1))
        lowered = inside.lower()
        for word in _STATUS_WORDS:
            if lowered.startswith(word):
                status = inside[: len(word)]
                break
        date_match = re.search(r"\d{4}-\d{2}-\d{2}", inside)
        date = date_match.group(0) if date_match else None

    return {"number": number, "status": status, "date": date}


def header_status_matches(phase: str, status: Optional[str]) -> bool:
    """Vrai si le statut lu sur la fiche correspond à l'étape (toujours vrai pour NEW/MODIFIED)."""
    expected = EXPECTED_HEADER_STATUS.get(phase)
    if not expected:
        return True
    return expected in strip_accents((status or "").lower())


def parse_counter(text: str) -> Optional[Tuple[int, int]]:
    """'1 de 7' -> (1, 7)."""
    match = re.search(r"(\d+)\s+de\s+(\d+)", text or "")
    return (int(match.group(1)), int(match.group(2))) if match else None


def itq_popup_url(origin: str, href: str) -> Optional[str]:
    """Adresse de la page « courtier inscripteur, propriétaire, prêt » d'une fiche.

    Le lien de la fiche est de la forme
    javascript:Dpy.ITQPopup('74',160,'','11 Mzc4NzAwNjk0','8fdf...',400,400)
    et ouvre /Matrix/Public/DisplayITQPopup.aspx?iid=..&did=..&strtabid=..&params=..&exk=..
    """
    match = re.search(r"ITQPopup\('([^']*)',\s*(\d+),\s*'([^']*)',\s*'([^']*)',\s*'([^']*)'", href or "")
    if not match:
        return None
    iid, did, tab, params, exk = match.groups()
    return (
        f"{origin.rstrip('/')}/Matrix/Public/DisplayITQPopup.aspx"
        f"?iid={iid}&did={did}&strtabid={tab}&params={quote(params)}&exk={exk}"
    )


DOORS_BY_TYPE = {"duplex": 2, "triplex": 3, "quadruplex": 4, "quintuplex": 5}


def doors_from_property_type(text: Optional[str]) -> Optional[int]:
    """Le plugin ne lit que des chiffres : « Quadruplex » donnait null. On le déduit du nom."""
    lowered = strip_accents((text or "").lower())
    for word, doors in DOORS_BY_TYPE.items():
        if word in lowered:
            return doors
    return None
