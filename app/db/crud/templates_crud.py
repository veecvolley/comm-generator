import json
from sqlalchemy.orm import Session
from app.db.models import Template


def get_all_templates(db: Session) -> list[Template]:
    return db.query(Template).order_by(Template.name).all()


def get_template(db: Session, name: str) -> Template | None:
    return db.query(Template).filter_by(name=name).first()


def get_default_template_name(db: Session) -> str:
    row = db.query(Template).filter_by(is_default=True).first()
    if row:
        return row.name
    first = db.query(Template).first()
    return first.name if first else "template1"


def upsert_template(db: Session, name: str, data: dict) -> Template:
    tpl = db.query(Template).filter_by(name=name).first()
    if tpl:
        tpl.display_name = data.get("display_name", tpl.display_name)
        tpl.description = data.get("description", tpl.description)
        tpl.inherit_from = data.get("inherit_from", tpl.inherit_from)
        tpl.backgrounds = json.dumps(data.get("backgrounds", tpl.get_backgrounds()))
        tpl.banners = json.dumps(data.get("banners", tpl.get_banners()))
        tpl.fonts = json.dumps(data.get("fonts", tpl.get_fonts()))
        tpl.offsets_y = json.dumps(data.get("offsets_y", tpl.get_offsets_y()))
        tpl.offsets_x = json.dumps(data.get("offsets_x", tpl.get_offsets_x()))
        tpl.sizes = json.dumps(data.get("sizes", tpl.get_sizes()))
    else:
        tpl = Template(
            name=name,
            display_name=data.get("display_name", name),
            description=data.get("description", ""),
            inherit_from=data.get("inherit_from"),
            is_default=data.get("is_default", False),
            backgrounds=json.dumps(data.get("backgrounds", {})),
            banners=json.dumps(data.get("banners", {})),
            fonts=json.dumps(data.get("fonts", {})),
            offsets_y=json.dumps(data.get("offsets_y", {})),
            offsets_x=json.dumps(data.get("offsets_x", {})),
            sizes=json.dumps(data.get("sizes", {})),
        )
        db.add(tpl)
    db.commit()
    db.refresh(tpl)
    return tpl


def set_default_template(db: Session, name: str):
    db.query(Template).update({"is_default": False})
    tpl = db.query(Template).filter_by(name=name).first()
    if tpl:
        tpl.is_default = True
    db.commit()


def rename_template(db: Session, old_name: str, new_name: str) -> bool:
    """Rename a template ID: copy to new name, fix references, delete old."""
    if old_name == new_name:
        return True
    if db.query(Template).filter_by(name=new_name).first():
        return False  # name already taken

    src = db.query(Template).filter_by(name=old_name).first()
    if not src:
        return False

    db.add(Template(
        name=new_name,
        display_name=src.display_name,
        description=src.description,
        inherit_from=src.inherit_from,
        is_default=src.is_default,
        backgrounds=src.backgrounds,
        banners=src.banners,
        fonts=src.fonts,
        offsets_y=src.offsets_y,
        offsets_x=src.offsets_x,
        sizes=src.sizes,
    ))
    # Fix inherit_from references
    db.query(Template).filter(Template.inherit_from == old_name).update(
        {"inherit_from": new_name}, synchronize_session="fetch"
    )
    db.delete(src)
    db.commit()
    return True
