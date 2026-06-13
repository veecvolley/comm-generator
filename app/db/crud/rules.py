from sqlalchemy.orm import Session
from app.db.models import TeamDetectionPattern, TeamRule


def get_detection_pattern(db: Session) -> str:
    row = db.query(TeamDetectionPattern).first()
    return row.pattern if row else ""


def set_detection_pattern(db: Session, pattern: str):
    row = db.query(TeamDetectionPattern).first()
    if row:
        row.pattern = pattern
    else:
        db.add(TeamDetectionPattern(pattern=pattern))
    db.commit()


def get_rules(db: Session) -> list[TeamRule]:
    return db.query(TeamRule).filter_by(is_default=False).order_by(TeamRule.order_index).all()


def get_default_rule(db: Session) -> TeamRule | None:
    return db.query(TeamRule).filter_by(is_default=True).first()


def get_rule(db: Session, rule_id: int) -> TeamRule | None:
    return db.query(TeamRule).filter_by(id=rule_id).first()


def create_rule(db: Session, data: dict) -> TeamRule:
    max_idx = db.query(TeamRule).filter_by(is_default=False).count()
    rule = TeamRule(
        order_index=max_idx,
        match_label=data.get("match_label", ""),
        match_genre=data.get("match_genre", ""),
        match_type=data.get("match_type", ""),
        match_niveau=data.get("match_niveau", ""),
        match_titre=data.get("match_titre", ""),
        pseudo_template=data.get("pseudo_template", ""),
        pseudo=data.get("pseudo", ""),
        font_size=data.get("font_size", "bold_15"),
        auto_num=data.get("auto_num", False),
        is_default=False,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def update_rule(db: Session, rule_id: int, data: dict) -> TeamRule | None:
    rule = db.query(TeamRule).filter_by(id=rule_id).first()
    if not rule:
        return None
    for field in ["match_label", "match_genre", "match_type", "match_niveau", "match_titre",
                  "pseudo_template", "pseudo", "font_size", "auto_num"]:
        if field in data:
            setattr(rule, field, data[field])
    db.commit()
    db.refresh(rule)
    return rule


def delete_rule(db: Session, rule_id: int):
    rule = db.query(TeamRule).filter_by(id=rule_id).first()
    if rule:
        db.delete(rule)
        db.commit()


def reorder_rules(db: Session, rule_ids: list[int]):
    for idx, rule_id in enumerate(rule_ids):
        rule = db.query(TeamRule).filter_by(id=rule_id).first()
        if rule:
            rule.order_index = idx
    db.commit()


def update_default_rule(db: Session, pseudo_from: str, font_size: str):
    row = db.query(TeamRule).filter_by(is_default=True).first()
    if row:
        row.pseudo_template = pseudo_from
        row.font_size = font_size
    else:
        db.add(TeamRule(
            order_index=9999,
            pseudo_template=pseudo_from,
            font_size=font_size,
            is_default=True,
        ))
    db.commit()
