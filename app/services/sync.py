"""Service de synchronisation FFVB → SQLite."""
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
from app.db.crud import ffvb as crud_ffvb
from app.db.crud import seasons as crud_seasons
from app.db.models import Match
from app.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SyncResult:
    inserted: int = 0
    updated: int = 0
    skipped: int = 0
    addresses_synced: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def total(self):
        return self.inserted + self.updated


def sync_matches(db: Session, saison: str, division_code: str = "") -> SyncResult:
    """
    Fetches matches from FFVB CSV and upserts them in the DB.
    Also discovers club codes encountered in the data.
    """
    from app.services.data_provider import _fetch_csv_rows_from_ffvb
    from app.db.crud import seasons as crud_seasons

    result = SyncResult()

    try:
        rows = list(_fetch_csv_rows_from_ffvb(saison, division_code))
    except Exception as e:
        logger.error("Failed to fetch CSV from FFVB: %s", e)
        result.errors.append(str(e))
        return result

    # Pré-charger les codes de la saison pour la résolution du cat_code
    s_norm = saison.replace("/", "-")
    season_cats = crud_seasons.get_categories_for_season(db, s_norm)
    season_codes_sorted = sorted(season_cats.keys(), key=len, reverse=True)

    seen_clubs: set[str] = set()  # évite les doublons dans la même transaction

    for row in rows:
        try:
            if len(row) < 13:
                continue
            entity, match_code, date = row[0], row[2], row[3]
            hour = "" if row[4] == "00:00" else row[4]
            logo_a, team_a, logo_b, team_b = row[5], row[6], row[7], row[8]
            sets, score = row[9], row[10]
            place = row[12]

            if team_a == "xxxxx" or team_b == "xxxxx":
                result.skipped += 1
                continue
            if date == "Date":
                result.skipped += 1
                continue

            cat_code = next(
                (code for code in season_codes_sorted if match_code.startswith(code)),
                ""
            )

            existing = db.query(Match).filter_by(match_code=match_code).first()

            crud_ffvb.upsert_match(db, {
                "match_code": match_code,
                "entity": entity,
                "cat_code": cat_code,
                "saison": saison.replace("/", "-"),
                "division_code": division_code,
                "date": date,
                "time": hour,
                "logo_a": logo_a,
                "team_a": team_a,
                "logo_b": logo_b,
                "team_b": team_b,
                "sets": sets,
                "score": score,
                "place": place,
            })

            for code in [logo_a, logo_b]:
                if code and code not in seen_clubs:
                    crud_ffvb.upsert_club(db, code)
                    seen_clubs.add(code)

            if existing:
                result.updated += 1
            else:
                result.inserted += 1

        except Exception as e:
            logger.warning("Error processing row: %s - %s", row, e)
            result.errors.append(str(e))

    db.commit()
    logger.info("Sync complete: %d inserted, %d updated, %d skipped", result.inserted, result.updated, result.skipped)
    return result


def sync_gymnase_addresses(db: Session, saison: str, club_name: str) -> SyncResult:
    """Fetches gymnasium addresses for home matches (where team_a belongs to club)."""
    from app.services.data_provider import _fetch_gymnase_from_ffvb

    result = SyncResult()
    from app.db.models import Match
    matches = db.query(Match).filter(
        Match.saison == saison.replace("/", "-"),
        Match.team_a.ilike(f"%{club_name}%"),
    ).all()

    for match in matches:
        try:
            if crud_ffvb.get_gymnase_address(db, match.match_code):
                result.skipped += 1
                continue

            addr = _fetch_gymnase_from_ffvb(match.match_code, match.entity)
            if addr:
                crud_ffvb.upsert_gymnase_address(db, match.match_code, match.entity, addr)
                result.addresses_synced += 1
            else:
                result.skipped += 1
        except Exception as e:
            logger.warning("Error fetching address for %s: %s", match.match_code, e)
            result.errors.append(str(e))

    db.commit()
    return result
