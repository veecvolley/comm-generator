from sqlalchemy.orm import Session
from app.db.models import AppSetting, Gymnase, ActiveSaison


def get_setting(db: Session, key: str) -> str:
    row = db.query(AppSetting).filter_by(key=key).first()
    return row.value if row else ""


def set_setting(db: Session, key: str, value: str, description: str = ""):
    row = db.query(AppSetting).filter_by(key=key).first()
    if row:
        row.value = value
        if description:
            row.description = description
    else:
        db.add(AppSetting(key=key, value=value, description=description))
    db.commit()


def get_all_settings(db: Session) -> dict:
    return {row.key: row.value for row in db.query(AppSetting).all()}


def get_gymnases(db: Session) -> list[str]:
    return [row.name for row in db.query(Gymnase).order_by(Gymnase.name).all()]


def add_gymnase(db: Session, name: str):
    if not db.query(Gymnase).filter_by(name=name).first():
        db.add(Gymnase(name=name))
        db.commit()


def delete_gymnase(db: Session, gymnase_id: int):
    row = db.query(Gymnase).filter_by(id=gymnase_id).first()
    if row:
        db.delete(row)
        db.commit()


def get_active_saisons(db: Session) -> list[str]:
    return [row.saison for row in db.query(ActiveSaison).order_by(ActiveSaison.saison).all()]


def add_saison(db: Session, saison: str):
    if not db.query(ActiveSaison).filter_by(saison=saison).first():
        db.add(ActiveSaison(saison=saison))
        db.commit()


def delete_saison(db: Session, saison_id: int):
    row = db.query(ActiveSaison).filter_by(id=saison_id).first()
    if row:
        db.delete(row)
        db.commit()


def get_ref_values(db: Session, category: str) -> list:
    from app.db.models import RefValue
    return db.query(RefValue).filter_by(category=category).order_by(RefValue.value).all()


def add_ref_value(db: Session, category: str, value: str):
    from app.db.models import RefValue
    from sqlalchemy import text
    db.execute(
        text("INSERT OR IGNORE INTO ref_values (category, value) VALUES (:cat, :val)"),
        {"cat": category, "val": value},
    )
    db.commit()


def delete_ref_value(db: Session, ref_id: int):
    from app.db.models import RefValue
    row = db.query(RefValue).filter_by(id=ref_id).first()
    if row:
        db.delete(row)
        db.commit()
