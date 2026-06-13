"""
Settings backed by SQLite DB with lazy loading.
Falls back to YAML if the DB is not yet seeded (first boot).
The existing API (from app.core.config import settings) is preserved.
"""
from pathlib import Path
from typing import Any, Dict


class Settings:
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._gymnases: list[str] = []
        self._saisons: list[str] = []
        self._loaded = False

    # ---- Internal loading ----

    def _load(self):
        if self._loaded:
            return
        try:
            from app.db.database import get_db_session
            from app.db.crud.config import get_all_settings, get_gymnases, get_active_saisons
            db = get_db_session()
            try:
                raw = get_all_settings(db)
                if raw.get("seed_done"):
                    self._data = raw
                    self._gymnases = get_gymnases(db)
                    self._saisons = get_active_saisons(db)
                    self._loaded = True
                    return
            finally:
                db.close()
        except Exception:
            pass
        # Fallback: load from YAML (before DB is seeded)
        self._load_from_yaml()
        self._loaded = True

    def _load_from_yaml(self):
        import yaml
        base = Path(__file__).parents[2]
        config_path = base / "config.yaml"
        saisons_path = base / "saisons.yaml"

        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
        else:
            cfg = {}

        ffvb = cfg.get("ffvb", {})
        club = cfg.get("club", {})
        tpl = cfg.get("templates", {})

        self._data = {
            "ffvb_csv_url": ffvb.get("csv_url", ""),
            "ffvb_csv_url_division": ffvb.get("csv_url_division", ""),
            "ffvb_address_pdf_url": ffvb.get("address_pdf_url", ""),
            "club_name": club.get("name", ""),
            "club_id": str(club.get("id", "")),
            "default_template": tpl.get("default", "template1"),
        }
        self._gymnases = club.get("gymnases", [])
        self._saisons = [str(s) for s in club.get("saisons", [])]

        # Load saisons data for get_season_config
        if saisons_path.exists():
            with open(saisons_path, "r", encoding="utf-8") as f:
                doc = yaml.safe_load(f) or {}
            saisons_raw = doc.get("saisons", doc)
            self._saisons_data = saisons_raw if isinstance(saisons_raw, dict) else {}
        else:
            self._saisons_data = {}

    def refresh(self):
        """Force reload from DB on next access."""
        self._loaded = False

    # ---- Public properties ----

    @property
    def ffvb_csv_url(self):
        self._load()
        return self._data.get("ffvb_csv_url", "")

    @property
    def ffvb_csv_url_division(self):
        self._load()
        return self._data.get("ffvb_csv_url_division", "")

    @property
    def ffvb_address_url(self):
        self._load()
        return self._data.get("ffvb_address_pdf_url", "")

    @property
    def club(self):
        self._load()
        return self._data.get("club_name", "")

    @property
    def club_id(self):
        self._load()
        return self._data.get("club_id", "")

    @property
    def club_gymnases(self):
        self._load()
        return self._gymnases

    @property
    def club_saisons(self):
        self._load()
        return self._saisons

    @property
    def default_template(self):
        self._load()
        return self._data.get("default_template", "template1")

    @property
    def saisons(self):
        """
        Returns all season category configs as a nested dict.
        Reads from DB; falls back to _saisons_data (YAML) when not yet seeded.
        """
        self._load()
        if self._loaded and self._data.get("seed_done"):
            try:
                from app.db.database import get_db_session
                from app.db.crud.seasons import get_categories_for_season, get_seasons
                db = get_db_session()
                try:
                    result = {}
                    for saison in get_seasons(db):
                        result[saison] = get_categories_for_season(db, saison)
                    return result
                finally:
                    db.close()
            except Exception:
                pass
        return getattr(self, "_saisons_data", {})

    def get_season_config(self, saison: str, code: str) -> dict:
        """Retrieves category config for a given season/code."""
        self._load()
        if self._data.get("seed_done"):
            try:
                from app.db.database import get_db_session
                from app.db.crud.seasons import get_category
                db = get_db_session()
                try:
                    return get_category(db, saison, code)
                finally:
                    db.close()
            except Exception:
                pass
        # Fallback to in-memory YAML data
        sd = getattr(self, "_saisons_data", {})
        s = saison.replace("/", "-")
        try:
            return sd.get(s, sd.get(saison, {})).get(code, {})
        except Exception:
            return {}

    # ---- Legacy compatibility (config.yaml dict access) ----

    @property
    def config(self):
        """Legacy compatibility: returns a dict mimicking config.yaml structure."""
        self._load()
        return {
            "ffvb": {
                "csv_url": self.ffvb_csv_url,
                "csv_url_division": self.ffvb_csv_url_division,
                "address_pdf_url": self.ffvb_address_url,
            },
            "club": {
                "name": self.club,
                "id": self.club_id,
                "gymnases": self._gymnases,
                "saisons": self._saisons,
            },
            "templates": {
                "default": self.default_template,
            },
        }


settings = Settings()
