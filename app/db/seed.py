"""Initial seed of the database from YAML config files."""
import json
import yaml
from pathlib import Path
from sqlalchemy.orm import Session
from app.db.models import (
    AppSetting, Gymnase, ActiveSaison, CategoryConfig,
    TeamDetectionPattern, TeamRule, Template, Base
)

BASE_DIR = Path(__file__).resolve().parents[2]


def _load_yaml(filename: str) -> dict:
    path = BASE_DIR / filename
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def is_seeded(db: Session) -> bool:
    return db.query(AppSetting).filter_by(key="seed_done").first() is not None


_REF_DEFAULTS = {
    "type": ["Volley-Ball", "Beach-Volley", "Volley-Assis"],
    "genre": ["Masculin", "Féminin", "Mixte"],
    "niveau": [
        "Challenge de France",
        "Championnat Départemental",
        "Championnat Interdépartemental",
        "Championnat Loisir Compet'Lib",
        "Championnat Régional",
        "Championnat de France",
        "Coupe Ile-de-France",
        "Coupe de France",
        "Coupe de France 4e tour",
        "Coupe de Ile-de-France",
        "Coupe de Seine & Marne",
        "Plateau de Match",
        "Qualifications Régionales",
    ],
    "label": ["LX", "M11", "M11F", "M11G", "M13F", "M13G", "M15F", "M15G", "M15X",
              "M18", "M18F", "M18G", "M21", "M21G", "SF", "SM", "SMB", "SVA"],
}


def seed(db: Session):
    if not is_seeded(db):
        _seed_config(db)
        _seed_saisons(db)
        _seed_team_rules(db)
        _seed_templates(db)
        db.add(AppSetting(key="seed_done", value="1", description="Seed initial depuis YAML complété"))
        db.commit()

    # Seed ref_values independently so existing installs also get it
    if not db.query(AppSetting).filter_by(key="ref_done").first():
        _seed_ref_values(db)
        db.add(AppSetting(key="ref_done", value="1", description="Référentiel valeurs initialisé"))
        db.commit()

    # Always sync: add any label/niveau values from CategoryConfig not yet in RefValue
    _sync_ref_from_categories(db)


def _seed_config(db: Session):
    config = _load_yaml("config.yaml")
    ffvb = config.get("ffvb", {})
    club = config.get("club", {})
    templates_cfg = config.get("templates", {})

    settings = [
        AppSetting(key="ffvb_csv_url", value=ffvb.get("csv_url", ""), description="URL CSV calendrier FFVB"),
        AppSetting(key="ffvb_csv_url_division", value=ffvb.get("csv_url_division", ""), description="URL CSV par division FFVB"),
        AppSetting(key="ffvb_address_pdf_url", value=ffvb.get("address_pdf_url", ""), description="URL PDF adresse gymnase FFVB"),
        AppSetting(key="club_name", value=club.get("name", ""), description="Nom du club"),
        AppSetting(key="club_id", value=str(club.get("id", "")), description="Identifiant FFVB du club"),
        AppSetting(key="default_template", value=templates_cfg.get("default", "template1"), description="Template d'image par défaut"),
    ]
    db.add_all(settings)

    for gym_name in club.get("gymnases", []):
        db.merge(Gymnase(name=gym_name))

    for saison in club.get("saisons", []):
        db.merge(ActiveSaison(saison=str(saison)))


def _seed_saisons(db: Session):
    doc = _load_yaml("saisons.yaml")
    saisons_data = doc.get("saisons", doc)

    for saison_key, codes in saisons_data.items():
        if not isinstance(codes, dict):
            continue
        for code, info in codes.items():
            if not isinstance(info, dict):
                continue
            db.add(CategoryConfig(
                saison=str(saison_key),
                code=str(code),
                titre=info.get("titre", ""),
                type=info.get("type", ""),
                genre=info.get("genre", ""),
                category=info.get("category", ""),
                niveau=info.get("niveau", ""),
                label=info.get("label", ""),
            ))


def _seed_team_rules(db: Session):
    doc = _load_yaml("team_rules.yaml")

    pattern = doc.get("team_detection_pattern", "")
    if pattern:
        db.merge(TeamDetectionPattern(pattern=pattern))

    for idx, rule in enumerate(doc.get("rules", [])):
        match = rule.get("match", {})
        result = rule.get("result", {})
        db.add(TeamRule(
            order_index=idx,
            match_label=match.get("label", ""),
            match_genre=match.get("genre", ""),
            match_type=match.get("type", ""),
            match_niveau=match.get("niveau", ""),
            match_titre=match.get("titre", ""),
            pseudo_template=result.get("pseudo_template", ""),
            pseudo=result.get("pseudo", ""),
            font_size=result.get("font_size", "bold_15"),
            auto_num=result.get("auto_num", False),
            is_default=False,
        ))

    default = doc.get("default", {})
    if default:
        db.add(TeamRule(
            order_index=9999,
            match_label="",
            match_genre="",
            match_type="",
            match_niveau="",
            match_titre="",
            pseudo_template=default.get("pseudo_from", "team"),
            pseudo="",
            font_size=default.get("font_size", "bold_15"),
            auto_num=False,
            is_default=True,
        ))


def _sync_ref_from_categories(db: Session):
    """Insert any label/niveau values used in CategoryConfig that are missing from RefValue."""
    from app.db.models import CategoryConfig
    from sqlalchemy import text
    for field in ("label", "niveau"):
        col = getattr(CategoryConfig, field)
        values = [r[0] for r in db.query(col).filter(col != "").distinct().all()]
        for v in values:
            db.execute(
                text("INSERT OR IGNORE INTO ref_values (category, value) VALUES (:cat, :val)"),
                {"cat": field, "val": v},
            )
    db.commit()


def _seed_ref_values(db: Session):
    from app.db.models import RefValue
    from sqlalchemy import text
    for category, values in _REF_DEFAULTS.items():
        for v in values:
            db.execute(
                text("INSERT OR IGNORE INTO ref_values (category, value) VALUES (:cat, :val)"),
                {"cat": category, "val": v},
            )


def _seed_templates(db: Session):
    doc = _load_yaml("templates.yaml")
    default_tpl = doc.get("default_template", "template1")
    templates = doc.get("templates", {})

    for name, tpl in templates.items():
        db.merge(Template(
            name=name,
            display_name=tpl.get("name", name),
            description=tpl.get("description", ""),
            inherit_from=tpl.get("inherit_from"),
            is_default=(name == default_tpl),
            backgrounds=json.dumps(tpl.get("backgrounds", {})),
            banners=json.dumps(tpl.get("banners", {})),
            fonts=json.dumps(tpl.get("fonts", {})),
            offsets_y=json.dumps(tpl.get("offsets_y", {})),
            offsets_x=json.dumps(tpl.get("offsets_x", {})),
            sizes=json.dumps(tpl.get("sizes", {})),
        ))
