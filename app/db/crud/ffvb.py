from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.models import Match, Club, GymnaSeAddress

MATCH_STALE_MINUTES = 60


def get_matches(db: Session, saison: str, division_code: str = "") -> list[Match]:
    q = db.query(Match).filter_by(saison=saison)
    if division_code:
        q = q.filter_by(division_code=division_code)
    return q.order_by(Match.date, Match.time).all()


def are_matches_fresh(db: Session, saison: str) -> bool:
    """Returns True if matches for this season exist and were synced recently."""
    cutoff = datetime.utcnow() - timedelta(minutes=MATCH_STALE_MINUTES)
    return db.query(Match).filter(
        Match.saison == saison,
        Match.synced_at >= cutoff
    ).first() is not None


def upsert_match(db: Session, data: dict):
    from sqlalchemy import text
    db.execute(
        text("""
            INSERT INTO matches (match_code, entity, cat_code, saison, division_code, date, time,
                                 logo_a, team_a, logo_b, team_b, sets, score, place, synced_at)
            VALUES (:match_code, :entity, :cat_code, :saison, :division_code, :date, :time,
                    :logo_a, :team_a, :logo_b, :team_b, :sets, :score, :place, :synced_at)
            ON CONFLICT(match_code) DO UPDATE SET
                entity=excluded.entity, cat_code=excluded.cat_code, saison=excluded.saison,
                division_code=excluded.division_code, date=excluded.date, time=excluded.time,
                logo_a=excluded.logo_a, team_a=excluded.team_a, logo_b=excluded.logo_b,
                team_b=excluded.team_b, sets=excluded.sets, score=excluded.score,
                place=excluded.place, synced_at=excluded.synced_at
        """),
        {**data, "synced_at": datetime.utcnow()},
    )


def upsert_club(db: Session, code: str, name: str = "", has_logo: bool = False):
    from sqlalchemy import text
    db.execute(
        text("INSERT OR IGNORE INTO clubs (code, name, has_logo) VALUES (:code, :name, :logo)"),
        {"code": code, "name": name, "logo": 1 if has_logo else 0},
    )


def get_gymnase_address(db: Session, match_code: str) -> GymnaSeAddress | None:
    return db.query(GymnaSeAddress).filter_by(match_code=match_code).first()


def upsert_gymnase_address(db: Session, match_code: str, entity: str, addr: dict):
    row = db.query(GymnaSeAddress).filter_by(match_code=match_code).first()
    if row:
        row.entity = entity
        row.name = addr.get("nom", "")
        row.street = addr.get("rue", "")
        row.postal_code = addr.get("code_postal", "")
        row.city = addr.get("ville", "")
        row.cached_at = datetime.utcnow()
    else:
        db.add(GymnaSeAddress(
            match_code=match_code,
            entity=entity,
            name=addr.get("nom", ""),
            street=addr.get("rue", ""),
            postal_code=addr.get("code_postal", ""),
            city=addr.get("ville", ""),
        ))


def get_match_count(db: Session, saison: str | None = None) -> int:
    q = db.query(Match)
    if saison:
        q = q.filter_by(saison=saison)
    return q.count()


def get_last_sync(db: Session) -> datetime | None:
    row = db.query(Match).order_by(Match.synced_at.desc()).first()
    return row.synced_at if row else None
