import csv
import io
import ssl
import re
import pdfplumber
from typing import Optional, Dict, Any
from app.core.config import settings
from app.core.logger import get_logger
from pathlib import Path

logger = get_logger(__name__)

CACHE_DIR = Path("/tmp/ffvb_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)


from requests.adapters import HTTPAdapter

class LegacySSLAdapter(HTTPAdapter):
    """Adaptateur SSL pour les serveurs utilisant des configurations SSL anciennes (TLS 1.2 forcé)."""

    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.options |= ssl.OP_LEGACY_SERVER_CONNECT
        ctx.maximum_version = ssl.TLSVersion.TLSv1_2
        ctx.set_ciphers("RSA:@SECLEVEL=0")
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        kwargs["ssl_context"] = ctx
        super().init_poolmanager(*args, **kwargs)


def _get_session():
    import requests_cache
    session = requests_cache.CachedSession(str(CACHE_DIR / "http_cache"), expire_after=600)
    session.mount("https://", LegacySSLAdapter())
    return session


def _fetch_gymnase_from_ffvb(codmatch: str, codent: str) -> Optional[Dict[str, str]]:
    """Fetches gymnasium address from FFVB PDF (raw network call)."""
    url = settings.ffvb_address_url
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"codmatch": codmatch, "codent": codent}
    response = _get_session().post(url, headers=headers, data=data, verify=False)

    if getattr(response, "from_cache", False):
        logger.debug("Cache hit for gymnase PDF: %s/%s", codmatch, codent)

    if response.status_code != 200 or response.headers.get("Content-Type") != "application/pdf":
        logger.warning("Failed to download gymnase PDF for %s/%s - Status: %s",
                       codmatch, codent, response.status_code)
        return None

    with pdfplumber.open(io.BytesIO(response.content)) as pdf:
        text = ""
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"

        logger.debug("PDF text extracted for %s/%s:\n%s", codmatch, codent, repr(text))

        match = re.search(r"Salle\s*\n(.*?)(Sol\s*:|Arbitre\.s|$)", text, re.DOTALL)
        if match:
            salle_block = match.group(1)
            lines = [line.strip() for line in salle_block.split("\n") if line.strip()]
            if lines:
                nom = lines[0]
                for i in range(1, len(lines)):
                    match_cp = re.search(r"^(\d{5})\s+(.+)", lines[i])
                    if match_cp and i > 0:
                        code_postal = match_cp.group(1)
                        ville = match_cp.group(2).strip()
                        ville = re.sub(r"\s*T[ée]l\.?:.*", "", ville.replace("\\'", "'"), flags=re.I)
                        rue = lines[i - 1].lower()
                        return {"nom": nom, "rue": rue, "code_postal": code_postal, "ville": ville}

        match_new = re.search(r"^SALLE\s+(.+)\n(.+)\n(\d{5})\s+(.+)", text, re.MULTILINE)
        if match_new:
            nom = match_new.group(1).strip()
            rue = match_new.group(2).strip().lower()
            code_postal = match_new.group(3)
            ville = match_new.group(4).strip()
            ville = re.sub(r"\s*T[ée]l\.?:.*", "", ville.replace("\\'", "'"), flags=re.I)
            return {"nom": nom, "rue": rue, "code_postal": code_postal, "ville": ville}

    return None


def get_gymnase_address(codmatch: str, codent: str, db=None) -> Optional[Dict[str, str]]:
    """
    Returns gymnasium address. Checks DB cache first, falls back to FFVB.
    Stores result in DB when a session is provided.
    """
    if db is not None:
        from app.db.crud.ffvb import get_gymnase_address as db_get, upsert_gymnase_address
        row = db_get(db, codmatch)
        if row:
            return {"nom": row.name, "rue": row.street, "code_postal": row.postal_code, "ville": row.city}

    result = _fetch_gymnase_from_ffvb(codmatch, codent)

    if db is not None and result:
        from app.db.crud.ffvb import upsert_gymnase_address
        upsert_gymnase_address(db, codmatch, codent, result)
        db.commit()

    return result


def _fetch_csv_rows_from_ffvb(saison: str, division: str):
    """Raw FFVB CSV fetch (used by sync service)."""
    url = settings.ffvb_csv_url if not division else settings.ffvb_csv_url_division
    saison = saison.replace("-", "/")

    payload = {
        "cnclub": settings.club_id,
        "cal_saison": saison,
        "cal_codent": "LIIDF",
        "cal_coddiv": division,
        "typ_edition": "E",
        "type": "RES",
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    logger.debug("Fetching CSV from FFVB: %s - Payload: %s", url, payload)
    response = _get_session().post(url, data=payload, headers=headers, verify=False)

    if getattr(response, "from_cache", False):
        logger.debug("Cache hit for CSV FFVB")

    response.raise_for_status()
    csv_utf8_str = response.content.decode("latin1").encode("utf-8").decode("utf-8")
    return csv.reader(io.StringIO(csv_utf8_str), delimiter=";", quotechar='"')


def parse_csv_rows(saison: str, division: str, db=None):
    """
    Returns match rows for the given season.
    Reads from DB if data is fresh; otherwise fetches from FFVB and stores in DB.
    Always falls back to live FFVB if DB is unavailable.
    """
    if db is not None:
        from app.db.crud.ffvb import get_matches, are_matches_fresh
        if are_matches_fresh(db, saison.replace("/", "-")):
            matches = get_matches(db, saison.replace("/", "-"), division)
            logger.debug("Serving %d matches from DB cache for %s", len(matches), saison)
            return [
                [m.entity, "", m.match_code, m.date, m.time,
                 m.logo_a, m.team_a, m.logo_b, m.team_b,
                 m.sets, m.score, "", m.place]
                for m in matches
            ]
        # DB stale — sync first
        from app.services.sync import sync_matches
        logger.info("Match cache stale for %s — syncing from FFVB", saison)
        sync_matches(db, saison, division)
        matches = get_matches(db, saison.replace("/", "-"), division)
        return [
            [m.entity, "", m.match_code, m.date, m.time,
             m.logo_a, m.team_a, m.logo_b, m.team_b,
             m.sets, m.score, "", m.place]
            for m in matches
        ]

    # No DB session — fetch live from FFVB
    return _fetch_csv_rows_from_ffvb(saison, division)


def parse_local_csv_rows():
    with open("export20242025_utf8.csv", newline="", encoding="utf-8") as csvfile:
        return csv.reader(csvfile, delimiter=";", quotechar='"')
