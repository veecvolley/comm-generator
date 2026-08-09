"""Admin routes — /admin/"""
import json
from fastapi import APIRouter, Request, Depends, Form, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, List

from app.db.database import get_db
from app.db.crud import config as crud_config
from app.db.crud import seasons as crud_seasons
from app.db.crud import rules as crud_rules
from app.db.crud import templates_crud
from app.db.crud import ffvb as crud_ffvb
from app.core.templates import templates as jinja
from app.core.logger import get_logger

logger = get_logger(__name__)

admin_router = APIRouter(prefix="/admin", tags=["admin"])


def _ctx(request: Request, **kwargs) -> dict:
    return {"request": request, **kwargs}


# ──────────────────────────────────────────────────────────────
# Dashboard
# ──────────────────────────────────────────────────────────────

@admin_router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    active_saisons = crud_config.get_active_saisons(db)
    stats = {}
    for s in active_saisons:
        stats[s] = crud_ffvb.get_match_count(db, s.replace("/", "-"))
    last_sync = crud_ffvb.get_last_sync(db)
    total_matches = crud_ffvb.get_match_count(db)
    nb_categories = db.query(__import__("app.db.models", fromlist=["CategoryConfig"]).CategoryConfig).count()
    nb_rules = len(crud_rules.get_rules(db))
    return jinja.TemplateResponse("admin/dashboard.html", _ctx(
        request,
        active_saisons=active_saisons,
        stats=stats,
        last_sync=last_sync,
        total_matches=total_matches,
        nb_categories=nb_categories,
        nb_rules=nb_rules,
    ))


# ──────────────────────────────────────────────────────────────
# Configuration du club
# ──────────────────────────────────────────────────────────────

@admin_router.get("/config", response_class=HTMLResponse)
def config_page(request: Request, db: Session = Depends(get_db)):
    from app.db.models import Gymnase, ActiveSaison
    settings_data = crud_config.get_all_settings(db)
    gymnases = db.query(Gymnase).order_by(Gymnase.name).all()
    saisons = db.query(ActiveSaison).order_by(ActiveSaison.saison).all()
    ref_values = {
        cat: crud_config.get_ref_values(db, cat)
        for cat in ("label", "type", "genre", "niveau")
    }
    return jinja.TemplateResponse("admin/config.html", _ctx(
        request, settings=settings_data, gymnases=gymnases, saisons=saisons,
        ref_values=ref_values,
        success=request.query_params.get("success"),
    ))


@admin_router.post("/config")
def config_save(
    request: Request,
    db: Session = Depends(get_db),
    club_name: str = Form(""),
    club_id: str = Form(""),
    ffvb_csv_url: str = Form(""),
    ffvb_csv_url_division: str = Form(""),
    ffvb_address_pdf_url: str = Form(""),
    default_template: str = Form("template1"),
):
    fields = {
        "club_name": club_name,
        "club_id": club_id,
        "ffvb_csv_url": ffvb_csv_url,
        "ffvb_csv_url_division": ffvb_csv_url_division,
        "ffvb_address_pdf_url": ffvb_address_pdf_url,
        "default_template": default_template,
    }
    for key, value in fields.items():
        crud_config.set_setting(db, key, value)

    # Refresh in-memory settings
    from app.core.config import settings
    settings.refresh()
    from app.core.image_templates import template_manager
    template_manager.reload()

    return RedirectResponse("/admin/config?success=1", status_code=303)


@admin_router.post("/config/ref/{category}/add")
def ref_value_add(category: str, db: Session = Depends(get_db), value: str = Form(...)):
    allowed = {"label", "type", "genre", "niveau"}
    if category not in allowed:
        raise HTTPException(status_code=400, detail="Catégorie invalide")
    crud_config.add_ref_value(db, category, value.strip())
    return RedirectResponse("/admin/config?success=1", status_code=303)


@admin_router.post("/config/ref/{ref_id}/edit")
def ref_value_edit(ref_id: int, db: Session = Depends(get_db), value: str = Form(...)):
    from app.db.models import RefValue, CategoryConfig
    row = db.query(RefValue).filter_by(id=ref_id).first()
    if row:
        old_value = row.value
        new_value = value.strip()
        row.value = new_value
        # Cascade to CategoryConfig rows using the old value
        col_map = {"label": "label", "type": "type", "genre": "genre", "niveau": "niveau"}
        if row.category in col_map and old_value != new_value:
            col = getattr(CategoryConfig, col_map[row.category])
            db.query(CategoryConfig).filter(col == old_value).update(
                {col_map[row.category]: new_value}, synchronize_session="fetch"
            )
        db.commit()
    return RedirectResponse("/admin/config?success=1", status_code=303)


@admin_router.post("/config/ref/{ref_id}/delete")
def ref_value_delete(ref_id: int, db: Session = Depends(get_db)):
    crud_config.delete_ref_value(db, ref_id)
    return RedirectResponse("/admin/config?success=1", status_code=303)


@admin_router.post("/config/gymnase/add")
def gymnase_add(request: Request, db: Session = Depends(get_db), name: str = Form(...)):
    crud_config.add_gymnase(db, name.strip())
    from app.core.config import settings
    settings.refresh()
    return RedirectResponse("/admin/config?success=1", status_code=303)


@admin_router.post("/config/gymnase/{gymnase_id}/delete")
def gymnase_delete(gymnase_id: int, db: Session = Depends(get_db)):
    crud_config.delete_gymnase(db, gymnase_id)
    from app.core.config import settings
    settings.refresh()
    return RedirectResponse("/admin/config?success=1", status_code=303)


@admin_router.post("/config/saison/add")
def saison_add(request: Request, db: Session = Depends(get_db), saison: str = Form(...)):
    crud_config.add_saison(db, saison.strip())
    from app.core.config import settings
    settings.refresh()
    return RedirectResponse("/admin/config?success=1", status_code=303)


@admin_router.post("/config/saison/{saison_id}/delete")
def saison_delete(saison_id: int, db: Session = Depends(get_db)):
    crud_config.delete_saison(db, saison_id)
    from app.core.config import settings
    settings.refresh()
    return RedirectResponse("/admin/config?success=1", status_code=303)


# ──────────────────────────────────────────────────────────────
# Saisons / Catégories
# ──────────────────────────────────────────────────────────────

@admin_router.get("/seasons", response_class=HTMLResponse)
def seasons_page(request: Request, db: Session = Depends(get_db)):
    from app.db.models import CategoryConfig
    saisons = sorted(crud_seasons.get_seasons(db), reverse=True)
    cats_by_season = {}
    for s in saisons:
        cats_by_season[s] = crud_seasons.get_categories_for_season(db, s)
    labels = [r.value for r in crud_config.get_ref_values(db, "label")]
    types = [r.value for r in crud_config.get_ref_values(db, "type")]
    genres = [r.value for r in crud_config.get_ref_values(db, "genre")]
    niveaux = [r.value for r in crud_config.get_ref_values(db, "niveau")]
    return jinja.TemplateResponse("admin/seasons.html", _ctx(
        request, saisons=saisons, cats_by_season=cats_by_season,
        labels=labels, types=types, genres=genres, niveaux=niveaux,
        success=request.query_params.get("success"),
        error=request.query_params.get("error"),
    ))


@admin_router.post("/seasons/new")
async def season_new(
    request: Request,
    db: Session = Depends(get_db),
    saison: str = Form(...),
    sync: bool = Form(False),
):
    """Ajoute une nouvelle saison (active_saisons) et optionnellement sync les catégories FFVB."""
    import re, asyncio
    from app.db.crud.config import add_saison, get_setting
    from app.db.crud.seasons import upsert_category
    from app.services.seasons import (
        fetch_lines, split_code_title, detect_type, detect_gender,
        detect_category, detect_level, build_label, normalize_season,
    )

    saison = saison.strip().replace("-", "/")
    if not re.match(r"^\d{4}/\d{4}$", saison):
        return RedirectResponse("/admin/seasons?error=Format+de+saison+invalide+(YYYY/YYYY)", status_code=303)

    saison_key = normalize_season(saison)   # → "2026-2027"
    add_saison(db, saison_key)
    from app.core.config import settings as app_settings
    app_settings.refresh()

    if not sync:
        return RedirectResponse("/admin/seasons?success=Saison+ajoutée", status_code=303)

    # Sync catégories FFVB pour cette saison uniquement
    club_id = get_setting(db, "club_id")

    def _do_sync():
        codes = {}
        lines = fetch_lines(club_id, saison)
        for line in lines:
            code, title = split_code_title(line)
            u = line.upper()
            codes[code] = {
                "titre": title,
                "type": detect_type(u),
                "genre": detect_gender(u),
                "category": detect_category(u),
                "niveau": detect_level(u),
                "label": build_label(detect_type(u), detect_gender(u), detect_category(u)),
            }
        return codes

    try:
        codes = await asyncio.to_thread(_do_sync)
        for code, info in codes.items():
            upsert_category(db, saison_key, code, info)
        n = len(codes)
        return RedirectResponse(
            f"/admin/seasons?success=Saison+{saison}+ajoutée+({n}+catégories+synchronisées)",
            status_code=303,
        )
    except Exception as e:
        logger.error("Season new sync failed: %s", e)
        return RedirectResponse(
            f"/admin/seasons?success=Saison+ajoutée&error=Sync+échouée+:+{e}",
            status_code=303,
        )


@admin_router.post("/seasons/sync")
async def seasons_sync(db: Session = Depends(get_db)):
    """Sync season categories from FFVB website."""
    import asyncio
    from app.services.seasons import generate_config_seasons
    from app.db.crud.config import get_setting, get_active_saisons
    from app.db.crud.seasons import upsert_category

    club_id = get_setting(db, "club_id")
    saisons = get_active_saisons(db)

    try:
        def _do_sync():
            # We reuse existing seasons.py logic but insert to DB instead of YAML
            from app.services.seasons import fetch_lines, split_code_title, detect_type, detect_gender
            from app.services.seasons import detect_category, detect_level, build_label, normalize_season
            results = {}
            for saison in saisons:
                saison_key = normalize_season(saison)
                results[saison_key] = {}
                try:
                    lines = fetch_lines(club_id, saison)
                    for line in lines:
                        code, title = split_code_title(line)
                        u = line.upper()
                        type_ = detect_type(u)
                        gender = detect_gender(u)
                        category = detect_category(u)
                        level = detect_level(u)
                        label = build_label(type_, gender, category)
                        results[saison_key][code] = {
                            "titre": title, "type": type_, "genre": gender,
                            "category": category, "niveau": level, "label": label,
                        }
                except Exception as e:
                    results[saison_key]["_error"] = str(e)
            return results

        results = await asyncio.to_thread(_do_sync)

        for saison_key, codes in results.items():
            for code, info in codes.items():
                if code.startswith("_"):
                    continue
                upsert_category(db, saison_key, code, info)

        return RedirectResponse("/admin/seasons?success=1", status_code=303)
    except Exception as e:
        logger.error("Season sync failed: %s", e)
        return RedirectResponse(f"/admin/seasons?error={e}", status_code=303)


@admin_router.post("/seasons/{saison}/{code}/edit")
def season_category_edit(
    saison: str,
    code: str,
    db: Session = Depends(get_db),
    label: str = Form(""),
    type: str = Form(""),
    genre: str = Form(""),
    niveau: str = Form(""),
    titre: str = Form(""),
):
    cat = crud_seasons.get_category(db, saison, code)
    if not cat:
        raise HTTPException(status_code=404, detail="Catégorie non trouvée")
    crud_seasons.upsert_category(db, saison, code, {**cat, "label": label, "type": type, "genre": genre, "niveau": niveau, "titre": titre})
    return RedirectResponse("/admin/seasons?success=1", status_code=303)


@admin_router.post("/seasons/{saison}/{code}/delete")
def season_category_delete(saison: str, code: str, db: Session = Depends(get_db)):
    crud_seasons.delete_category(db, saison, code)
    return RedirectResponse("/admin/seasons?success=1", status_code=303)


@admin_router.post("/seasons/add")
def season_category_add(
    db: Session = Depends(get_db),
    saison: str = Form(...),
    code: str = Form(...),
    titre: str = Form(""),
    type: str = Form(""),
    genre: str = Form(""),
    category: str = Form(""),
    niveau: str = Form(""),
    label: str = Form(""),
):
    crud_seasons.upsert_category(db, saison, code.strip().upper(), {
        "titre": titre, "type": type, "genre": genre,
        "category": category, "niveau": niveau, "label": label,
    })
    return RedirectResponse("/admin/seasons?success=1", status_code=303)


# ──────────────────────────────────────────────────────────────
# Règles d'équipes
# ──────────────────────────────────────────────────────────────

@admin_router.get("/team-rules", response_class=HTMLResponse)
def team_rules_page(request: Request, db: Session = Depends(get_db)):
    rules = crud_rules.get_rules(db)
    default_rule = crud_rules.get_default_rule(db)
    detection_pattern = crud_rules.get_detection_pattern(db)
    font_sizes = ["bold_10", "bold_12", "bold_13", "bold_14", "bold_15", "bold_25"]
    return jinja.TemplateResponse("admin/team_rules.html", _ctx(
        request, rules=rules, default_rule=default_rule,
        detection_pattern=detection_pattern, font_sizes=font_sizes,
        success=request.query_params.get("success"),
    ))


@admin_router.post("/team-rules/pattern")
def team_rules_pattern_save(db: Session = Depends(get_db), pattern: str = Form("")):
    crud_rules.set_detection_pattern(db, pattern.strip())
    from app.services.string_utils import reset_team_rules_cache
    reset_team_rules_cache()
    return RedirectResponse("/admin/team-rules?success=1", status_code=303)


@admin_router.post("/team-rules/default")
def team_rules_default_save(
    db: Session = Depends(get_db),
    pseudo_from: str = Form("team"),
    font_size: str = Form("bold_15"),
):
    crud_rules.update_default_rule(db, pseudo_from, font_size)
    from app.services.string_utils import reset_team_rules_cache
    reset_team_rules_cache()
    return RedirectResponse("/admin/team-rules?success=1", status_code=303)


@admin_router.post("/team-rules/add")
def team_rules_add(
    db: Session = Depends(get_db),
    match_label: str = Form(""),
    match_genre: str = Form(""),
    match_type: str = Form(""),
    match_niveau: str = Form(""),
    match_titre: str = Form(""),
    pseudo: str = Form(""),
    pseudo_template: str = Form(""),
    font_size: str = Form("bold_25"),
    auto_num: bool = Form(False),
):
    crud_rules.create_rule(db, {
        "match_label": match_label, "match_genre": match_genre,
        "match_type": match_type, "match_niveau": match_niveau, "match_titre": match_titre,
        "pseudo": pseudo, "pseudo_template": pseudo_template,
        "font_size": font_size, "auto_num": auto_num,
    })
    from app.services.string_utils import reset_team_rules_cache
    reset_team_rules_cache()
    return RedirectResponse("/admin/team-rules?success=1", status_code=303)


@admin_router.post("/team-rules/{rule_id}/delete")
def team_rules_delete(rule_id: int, db: Session = Depends(get_db)):
    crud_rules.delete_rule(db, rule_id)
    from app.services.string_utils import reset_team_rules_cache
    reset_team_rules_cache()
    return RedirectResponse("/admin/team-rules?success=1", status_code=303)


@admin_router.post("/team-rules/{rule_id}/edit")
def team_rules_edit(
    rule_id: int,
    db: Session = Depends(get_db),
    match_label: str = Form(""),
    match_genre: str = Form(""),
    match_type: str = Form(""),
    match_niveau: str = Form(""),
    match_titre: str = Form(""),
    pseudo: str = Form(""),
    pseudo_template: str = Form(""),
    font_size: str = Form("bold_25"),
    auto_num: bool = Form(False),
):
    crud_rules.update_rule(db, rule_id, {
        "match_label": match_label, "match_genre": match_genre,
        "match_type": match_type, "match_niveau": match_niveau, "match_titre": match_titre,
        "pseudo": pseudo, "pseudo_template": pseudo_template,
        "font_size": font_size, "auto_num": auto_num,
    })
    from app.services.string_utils import reset_team_rules_cache
    reset_team_rules_cache()
    return RedirectResponse("/admin/team-rules?success=1", status_code=303)


@admin_router.post("/team-rules/reorder")
async def team_rules_reorder(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    rule_ids = body.get("order", [])
    crud_rules.reorder_rules(db, rule_ids)
    from app.services.string_utils import reset_team_rules_cache
    reset_team_rules_cache()
    return {"ok": True}


# ──────────────────────────────────────────────────────────────
# Templates d'images
# ──────────────────────────────────────────────────────────────

@admin_router.get("/templates", response_class=HTMLResponse)
def templates_page(request: Request, db: Session = Depends(get_db)):
    tpls = templates_crud.get_all_templates(db)
    default_name = templates_crud.get_default_template_name(db)
    return jinja.TemplateResponse("admin/templates.html", _ctx(
        request, templates=tpls, default_name=default_name,
        success=request.query_params.get("success"),
    ))


@admin_router.get("/templates/new", response_class=HTMLResponse)
def template_new_page(request: Request, db: Session = Depends(get_db)):
    from types import SimpleNamespace
    tpl = SimpleNamespace(
        name="", display_name="", description="", inherit_from=None,
        get_backgrounds=lambda: {}, get_banners=lambda: {},
        get_fonts=lambda: {}, get_sizes=lambda: {},
        get_offsets_y=lambda: {}, get_offsets_x=lambda: {},
    )
    all_templates = [t.name for t in templates_crud.get_all_templates(db)]
    return jinja.TemplateResponse("admin/template_edit.html", _ctx(
        request, tpl=tpl, is_new=True,
        all_templates=all_templates,
        backgrounds={}, banners={}, fonts={}, sizes={}, offsets_y={}, offsets_x={},
        error=request.query_params.get("error"),
    ))


@admin_router.post("/templates/new")
async def template_create(request: Request, db: Session = Depends(get_db)):
    import re
    form = await request.form()

    name = form.get("name", "").strip()
    if not name:
        return RedirectResponse("/admin/templates/new?error=L'ID+est+obligatoire", status_code=303)
    if not re.match(r'^[\w\-]+$', name):
        return RedirectResponse("/admin/templates/new?error=ID+invalide+(lettres,+chiffres,+tirets+uniquement)", status_code=303)
    if templates_crud.get_template(db, name):
        return RedirectResponse(f"/admin/templates/new?error=L'ID+'{name}'+est+déjà+utilisé", status_code=303)

    def _parse_json(field: str) -> dict:
        raw = form.get(field, "")
        try:
            return json.loads(raw) if raw.strip() else {}
        except Exception:
            return {}

    templates_crud.upsert_template(db, name, {
        "display_name": form.get("display_name", name),
        "description":  form.get("description", ""),
        "inherit_from": form.get("inherit_from") or None,
        "backgrounds":  _parse_json("backgrounds"),
        "banners":      _parse_json("banners"),
        "fonts":        _parse_json("fonts"),
        "offsets_y":    _parse_json("offsets_y"),
        "offsets_x":    _parse_json("offsets_x"),
        "sizes":        _parse_json("sizes"),
    })

    from app.core.image_templates import template_manager
    template_manager.reload()

    return RedirectResponse(f"/admin/templates/{name}?success=1", status_code=303)


@admin_router.get("/templates/{name}", response_class=HTMLResponse)
def template_edit_page(name: str, request: Request, db: Session = Depends(get_db)):
    tpl = templates_crud.get_template(db, name)
    if not tpl:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    all_templates = [t.name for t in templates_crud.get_all_templates(db) if t.name != name]
    return jinja.TemplateResponse("admin/template_edit.html", _ctx(
        request, tpl=tpl,
        all_templates=all_templates,
        backgrounds=tpl.get_backgrounds(),
        banners=tpl.get_banners(),
        fonts=tpl.get_fonts(),
        sizes=tpl.get_sizes(),
        offsets_y=tpl.get_offsets_y(),
        offsets_x=tpl.get_offsets_x(),
        success=request.query_params.get("success"),
    ))


@admin_router.post("/templates/{name}")
async def template_save(name: str, request: Request, db: Session = Depends(get_db)):
    form = await request.form()

    def _parse_json(field: str, fallback: dict) -> dict:
        raw = form.get(field, "")
        try:
            return json.loads(raw) if raw.strip() else fallback
        except Exception:
            return fallback

    tpl = templates_crud.get_template(db, name)
    templates_crud.upsert_template(db, name, {
        "display_name": form.get("display_name", name),
        "description": form.get("description", ""),
        "inherit_from": form.get("inherit_from") or None,
        "backgrounds": _parse_json("backgrounds", tpl.get_backgrounds() if tpl else {}),
        "banners": _parse_json("banners", tpl.get_banners() if tpl else {}),
        "fonts": _parse_json("fonts", tpl.get_fonts() if tpl else {}),
        "offsets_y": _parse_json("offsets_y", tpl.get_offsets_y() if tpl else {}),
        "offsets_x": _parse_json("offsets_x", tpl.get_offsets_x() if tpl else {}),
        "sizes": _parse_json("sizes", tpl.get_sizes() if tpl else {}),
    })

    from app.core.image_templates import template_manager
    template_manager.reload()

    return RedirectResponse(f"/admin/templates/{name}?success=1", status_code=303)


@admin_router.post("/templates/{name}/rename-id")
def template_rename_id(name: str, db: Session = Depends(get_db), new_name: str = Form(...)):
    new_name = new_name.strip()
    if not new_name:
        return RedirectResponse(f"/admin/templates?error=ID+invalide", status_code=303)
    ok = templates_crud.rename_template(db, name, new_name)
    if not ok:
        return RedirectResponse(f"/admin/templates?error=ID+déjà+utilisé", status_code=303)
    # Update default_template setting if needed
    from app.db.crud.config import get_setting, set_setting
    if get_setting(db, "default_template") == name:
        set_setting(db, "default_template", new_name)
    from app.core.config import settings
    settings.refresh()
    from app.core.image_templates import template_manager
    template_manager.reload()
    return RedirectResponse("/admin/templates?success=1", status_code=303)


@admin_router.post("/templates/{name}/rename")
def template_rename(name: str, db: Session = Depends(get_db), display_name: str = Form(...)):
    tpl = templates_crud.get_template(db, name)
    if not tpl:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    templates_crud.upsert_template(db, name, {
        "display_name": display_name.strip(),
        "description": tpl.description,
        "inherit_from": tpl.inherit_from,
        "backgrounds": tpl.get_backgrounds(),
        "banners": tpl.get_banners(),
        "fonts": tpl.get_fonts(),
        "offsets_y": tpl.get_offsets_y(),
        "offsets_x": tpl.get_offsets_x(),
        "sizes": tpl.get_sizes(),
    })
    from app.core.image_templates import template_manager
    template_manager.reload()
    return RedirectResponse("/admin/templates?success=1", status_code=303)


@admin_router.post("/templates/{name}/set-default")
def template_set_default(name: str, db: Session = Depends(get_db)):
    templates_crud.set_default_template(db, name)
    from app.core.config import settings
    settings.refresh()
    from app.core.image_templates import template_manager
    template_manager.reload()
    return RedirectResponse("/admin/templates?success=1", status_code=303)


# ──────────────────────────────────────────────────────────────
# Données FFVB
# ──────────────────────────────────────────────────────────────

_SORT_COLUMNS = {
    "date": ("date", "time"),
    "time": ("time", "date"),
    "cat_code": ("cat_code", "date"),
    "team_a": ("team_a", "date"),
    "team_b": ("team_b", "date"),
    "sets": ("sets", "date"),
    "score": ("score", "date"),
    "place": ("place", "date"),
}


@admin_router.get("/data", response_class=HTMLResponse)
def data_page(
    request: Request,
    db: Session = Depends(get_db),
    saison: Optional[str] = None,
    cat_code: Optional[str] = None,
    type_filter: Optional[str] = None,
    genre_filter: Optional[str] = None,
    sort: str = "date",
    order: str = "desc",
    page: int = 1,
):
    from app.db.models import Match, CategoryConfig
    from sqlalchemy import asc, desc

    active_saisons = sorted(crud_config.get_active_saisons(db), reverse=True)
    saison_filter = saison or (active_saisons[0] if active_saisons else "")

    q = db.query(Match).outerjoin(
        CategoryConfig,
        (Match.cat_code == CategoryConfig.code) & (Match.saison == CategoryConfig.saison),
    )
    if saison_filter:
        q = q.filter(Match.saison == saison_filter.replace("/", "-"))
    if cat_code:
        q = q.filter(Match.cat_code == cat_code)
    if type_filter:
        q = q.filter(CategoryConfig.type == type_filter)
    if genre_filter:
        q = q.filter(CategoryConfig.genre == genre_filter)

    total = q.count()
    per_page = 50

    _JOINED_SORT = {"type": CategoryConfig.type, "genre": CategoryConfig.genre}
    sort_key = sort if (sort in _SORT_COLUMNS or sort in _JOINED_SORT) else "date"
    dir_fn = desc if order == "desc" else asc

    if sort_key in _JOINED_SORT:
        q = q.order_by(dir_fn(_JOINED_SORT[sort_key]), asc(Match.date))
    else:
        primary, secondary = _SORT_COLUMNS[sort_key]
        q = q.order_by(dir_fn(getattr(Match, primary)), asc(getattr(Match, secondary)))

    matches = q.offset((page - 1) * per_page).limit(per_page).all()

    cat_codes = db.query(Match.cat_code).filter(
        Match.saison == saison_filter.replace("/", "-")
    ).distinct().order_by(Match.cat_code).all()
    cat_codes = [r[0] for r in cat_codes if r[0]]

    s_norm = saison_filter.replace("/", "-")
    types = [r[0] for r in db.query(CategoryConfig.type).filter(
        CategoryConfig.saison == s_norm, CategoryConfig.type != ""
    ).distinct().order_by(CategoryConfig.type).all()]

    genres = [r[0] for r in db.query(CategoryConfig.genre).filter(
        CategoryConfig.saison == s_norm, CategoryConfig.genre != ""
    ).distinct().order_by(CategoryConfig.genre).all()]

    cats_map = {
        code: {"type": info["type"], "genre": info["genre"]}
        for code, info in crud_seasons.get_categories_for_season(db, saison_filter).items()
    }

    last_sync = crud_ffvb.get_last_sync(db)
    total_pages = (total + per_page - 1) // per_page

    return jinja.TemplateResponse("admin/data.html", _ctx(
        request,
        matches=matches,
        active_saisons=active_saisons,
        saison_filter=saison_filter,
        cat_code_filter=cat_code or "",
        type_filter=type_filter or "",
        genre_filter=genre_filter or "",
        cat_codes=cat_codes,
        types=types,
        genres=genres,
        cats_map=cats_map,
        sort=sort_key,
        order=order,
        page=page,
        total=total,
        total_pages=total_pages,
        last_sync=last_sync,
        success=request.query_params.get("success"),
        error=request.query_params.get("error"),
    ))


@admin_router.post("/data/sync")
async def data_sync(
    request: Request,
    db: Session = Depends(get_db),
):
    """Sync matches from FFVB for all active seasons."""
    import asyncio
    from app.services.sync import sync_matches
    from app.db.crud.config import get_active_saisons

    saisons = get_active_saisons(db)
    total_inserted = 0
    total_updated = 0
    errors = []

    for saison in saisons:
        # Fresh session per saison: a failure on one won't block the others
        from app.db.database import get_db_session
        sync_db = get_db_session()
        try:
            result = await asyncio.to_thread(sync_matches, sync_db, saison, "")
            total_inserted += result.inserted
            total_updated += result.updated
            errors.extend([f"{saison}: {e}" for e in result.errors])
        except Exception as e:
            sync_db.rollback()
            errors.append(f"{saison}: {e}")
        finally:
            sync_db.close()

    if errors:
        msg = f"Sync partielle — {total_inserted} insérés, {total_updated} mis à jour. Erreurs: {'; '.join(errors[:3])}"
        return RedirectResponse(f"/admin/data?error={msg}", status_code=303)

    return RedirectResponse(
        f"/admin/data?success=Sync terminée — {total_inserted} insérés, {total_updated} mis à jour",
        status_code=303
    )


@admin_router.post("/assets/upload")
async def upload_asset(
    file: UploadFile = File(...),
    directory: str = Form(...),
):
    """Upload a PNG asset (background or banner) and save it to app/assets/{directory}/."""
    import re
    import shutil
    from pathlib import Path

    allowed = {"backgrounds", "banners", "clubs"}
    if directory not in allowed:
        raise HTTPException(400, f"Répertoire non autorisé : {directory}")

    if not file.filename.lower().endswith(".png"):
        raise HTTPException(400, "Seuls les fichiers PNG sont acceptés")

    safe_name = re.sub(r"[^\w\-.]", "_", file.filename)
    if not safe_name.lower().endswith(".png"):
        safe_name += ".png"

    assets_dir = Path(__file__).parents[1] / "assets" / directory
    assets_dir.mkdir(parents=True, exist_ok=True)
    dest = assets_dir / safe_name

    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    return {"filename": safe_name}


@admin_router.post("/data/sync-addresses")
async def data_sync_addresses(
    request: Request,
    db: Session = Depends(get_db),
    saison: str = Form(...),
):
    """Sync gymnasium addresses for home matches."""
    import asyncio
    from app.services.sync import sync_gymnase_addresses
    from app.db.crud.config import get_setting

    club_name = get_setting(db, "club_name")

    from app.db.database import get_db_session
    sync_db = get_db_session()
    try:
        result = await asyncio.to_thread(sync_gymnase_addresses, sync_db, saison, club_name)
        msg = f"Adresses synchronisées : {result.addresses_synced} nouvelles, {result.skipped} ignorées"
        return RedirectResponse(f"/admin/data?success={msg}", status_code=303)
    except Exception as e:
        sync_db.rollback()
        return RedirectResponse(f"/admin/data?error={e}", status_code=303)
    finally:
        sync_db.close()
