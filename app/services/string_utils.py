import unicodedata
import re
from datetime import datetime
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
from app.core.constants import jours, mois
from app.core.logger import get_logger

logger = get_logger(__name__)


def _norm(s: str) -> str:
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().strip().upper()


def _load_team_rules_from_db() -> Dict[str, Any]:
    """Loads team rules from DB. Falls back to YAML if DB not ready."""
    try:
        from app.db.database import get_db_session
        from app.db.crud.rules import get_rules, get_default_rule, get_detection_pattern
        db = get_db_session()
        try:
            pattern = get_detection_pattern(db)
            if not pattern:
                raise ValueError("DB not seeded")
            rules_rows = get_rules(db)
            default_row = get_default_rule(db)
            rules = []
            for r in rules_rows:
                match = {}
                if r.match_label: match["label"] = r.match_label
                if r.match_genre: match["genre"] = r.match_genre
                if r.match_type: match["type"] = r.match_type
                if r.match_niveau: match["niveau"] = r.match_niveau
                if r.match_titre: match["titre"] = r.match_titre
                result = {"font_size": r.font_size}
                if r.pseudo_template: result["pseudo_template"] = r.pseudo_template
                if r.pseudo: result["pseudo"] = r.pseudo
                if r.auto_num: result["auto_num"] = r.auto_num
                rules.append({"match": match, "result": result})

            default = {"pseudo_from": "team", "font_size": "bold_15"}
            if default_row:
                default = {
                    "pseudo_from": default_row.pseudo_template or "team",
                    "font_size": default_row.font_size,
                }
            return {
                "team_detection_pattern": pattern,
                "rules": rules,
                "default": default,
            }
        finally:
            db.close()
    except Exception:
        return _load_team_rules_from_yaml()


def _load_team_rules_from_yaml() -> Dict[str, Any]:
    import yaml
    rules_path = Path(__file__).parents[2] / "team_rules.yaml"
    if not rules_path.exists():
        return {"team_detection_pattern": "", "rules": [], "default": {"pseudo_from": "team", "font_size": "bold_15"}}
    with open(rules_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# In-memory cache, refreshed on demand via reset_team_rules_cache()
_team_rules_cache: Optional[Dict[str, Any]] = None


def reset_team_rules_cache():
    global _team_rules_cache
    _team_rules_cache = None


def _load_team_rules() -> Dict[str, Any]:
    global _team_rules_cache
    if _team_rules_cache is None:
        _team_rules_cache = _load_team_rules_from_db()
    return _team_rules_cache


def _match_rule(rule_match: Dict[str, str], label: str, genre: str,
                type_volley: str, niveau: str, titre: str) -> bool:
    if "label" in rule_match and rule_match["label"] != label:
        return False
    if "genre" in rule_match and rule_match["genre"] != genre:
        return False
    if "type" in rule_match and rule_match["type"] != type_volley:
        return False
    if "niveau" in rule_match and rule_match["niveau"] != niveau:
        return False
    if "titre" in rule_match and rule_match["titre"] != titre:
        return False
    return True


def get_team_pseudo(label: str, genre: str, type: str, niveau: str,
                    team: str, titre: str) -> Tuple[str, str]:
    rules_config = _load_team_rules()

    res = re.search(r"\b(\d+)\s*$", team)
    num = int(res.group(1)) if res else None

    detection_pattern = rules_config.get("team_detection_pattern", "")
    detected = bool(re.search(detection_pattern, team, re.IGNORECASE))

    logger.debug("Team detection: %s => %s", team, detected)

    if not detected:
        default = rules_config.get("default", {})
        return team, default.get("font_size", "bold_15")

    for rule in rules_config.get("rules", []):
        rule_match = rule.get("match", {})
        rule_result = rule.get("result", {})

        if _match_rule(rule_match, label, genre, type, niveau, titre):
            if "pseudo" in rule_result:
                pseudo = rule_result["pseudo"]
            elif "pseudo_template" in rule_result:
                template = rule_result["pseudo_template"]
                pseudo = template.format(num=num if num is not None else 1, label=label)
            else:
                pseudo = team

            if rule_result.get("auto_num") and num is not None:
                pseudo = f"{pseudo}-{num}"

            font_size = rule_result.get("font_size", "bold_15")
            return pseudo, font_size

    default = rules_config.get("default", {})
    pseudo_from = default.get("pseudo_from", "team")
    font_size = default.get("font_size", "bold_15")

    if pseudo_from == "team":
        return team, font_size
    elif pseudo_from == "label":
        return label, font_size
    return team, font_size


def formater_periode(date_start_dt: datetime, date_end_dt: datetime) -> str:
    d1 = date_start_dt
    d2 = date_end_dt

    mois_d1 = mois[d1.strftime("%B")]
    mois_d2 = mois[d2.strftime("%B")]

    if d1.month == d2.month and d1.year == d2.year:
        return f"{d1.day} et {d2.day} {mois_d1} {d1.year}"
    return f"{d1.day} {mois_d1} {d1.year} au {d2.day} {mois_d2} {d2.year}"
