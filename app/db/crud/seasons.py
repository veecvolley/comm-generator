from sqlalchemy.orm import Session
from app.db.models import CategoryConfig


def get_seasons(db: Session) -> list[str]:
    rows = db.query(CategoryConfig.saison).distinct().order_by(CategoryConfig.saison).all()
    return [r[0] for r in rows]


def get_categories_for_season(db: Session, saison: str) -> dict:
    """Returns {code: {titre, type, genre, category, niveau, label}} for a season."""
    # Normalize separator
    s = saison.replace("/", "-")
    rows = db.query(CategoryConfig).filter_by(saison=s).all()
    if not rows:
        # Try other separator form
        s = saison.replace("-", "/")
        rows = db.query(CategoryConfig).filter_by(saison=s).all()
    return {
        row.code: {
            "titre": row.titre,
            "type": row.type,
            "genre": row.genre,
            "category": row.category,
            "niveau": row.niveau,
            "label": row.label,
        }
        for row in rows
    }


def get_category(db: Session, saison: str, code: str) -> dict:
    s = saison.replace("/", "-")
    row = db.query(CategoryConfig).filter_by(saison=s, code=code).first()
    if not row:
        s = saison.replace("-", "/")
        row = db.query(CategoryConfig).filter_by(saison=s, code=code).first()
    if not row:
        return {}
    return {
        "titre": row.titre,
        "type": row.type,
        "genre": row.genre,
        "category": row.category,
        "niveau": row.niveau,
        "label": row.label,
    }


def upsert_category(db: Session, saison: str, code: str, data: dict):
    s = saison.replace("/", "-")
    row = db.query(CategoryConfig).filter_by(saison=s, code=code).first()
    if row:
        row.titre = data.get("titre", row.titre)
        row.type = data.get("type", row.type)
        row.genre = data.get("genre", row.genre)
        row.category = data.get("category", row.category)
        row.niveau = data.get("niveau", row.niveau)
        row.label = data.get("label", row.label)
    else:
        db.add(CategoryConfig(
            saison=s, code=code,
            titre=data.get("titre", ""),
            type=data.get("type", ""),
            genre=data.get("genre", ""),
            category=data.get("category", ""),
            niveau=data.get("niveau", ""),
            label=data.get("label", ""),
        ))
    db.commit()


def delete_category(db: Session, saison: str, code: str):
    s = saison.replace("/", "-")
    row = db.query(CategoryConfig).filter_by(saison=s, code=code).first()
    if row:
        db.delete(row)
        db.commit()
