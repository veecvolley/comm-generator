from fastapi import APIRouter, Request, Query, HTTPException, Depends
from fastapi.responses import StreamingResponse, JSONResponse, Response, HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional, List
import asyncio
from app.services.image_gen import generate_filtered_image
from app.services.seasons import generate_config_seasons
from app.core.logger import get_logger
from app.core.cache import image_cache
from app.db.database import get_db
from app.db.crud import seasons as crud_seasons
import io
import pathlib
from app.core.templates import templates
from app.core.config import settings

logger = get_logger(__name__)

VERSION = open(pathlib.Path(__file__).parents[2] / "VERSION.md", encoding="utf-8").readline().strip()

router = APIRouter()

_PARIS_TZ = None
def _fmt_sync(dt) -> str | None:
    """Convertit un datetime UTC naïf en heure de Paris, formate en dd/mm/yyyy HH:MM."""
    if dt is None:
        return None
    global _PARIS_TZ
    if _PARIS_TZ is None:
        from zoneinfo import ZoneInfo
        _PARIS_TZ = ZoneInfo("Europe/Paris")
    from datetime import timezone
    dt_utc = dt.replace(tzinfo=timezone.utc)
    return dt_utc.astimezone(_PARIS_TZ).strftime("%d/%m/%Y %H:%M")


@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "version": VERSION,
        "service": "comm-generator"
    }


@router.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    from app.db.crud.config import get_active_saisons, get_setting
    from app.db.crud.ffvb import get_last_sync
    saisons = sorted(get_active_saisons(db), reverse=True)
    club_name = get_setting(db, "club_name")
    last_sync = get_last_sync(db)
    last_sync_str = _fmt_sync(last_sync)
    return templates.TemplateResponse("index.html", {
        "request": request, "version": VERSION,
        "saisons": saisons, "club_name": club_name,
        "last_sync": last_sync_str,
    })


@router.post("/sync-ffvb")
async def sync_ffvb(
    saison: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Déclenche la synchronisation FFVB depuis l'app principale."""
    from app.db.crud.config import get_active_saisons
    from app.db.database import get_db_session
    from app.services.sync import sync_matches

    saisons_list = [saison] if saison else get_active_saisons(db)

    total_inserted = total_updated = 0
    errors = []

    for s in saisons_list:
        try:
            sync_db = get_db_session()
            try:
                result = await asyncio.to_thread(sync_matches, sync_db, s, "")
                total_inserted += result.inserted
                total_updated  += result.updated
            finally:
                sync_db.close()
        except Exception as e:
            errors.append(f"{s}: {e}")

    from app.db.crud.ffvb import get_last_sync
    last_sync = get_last_sync(db)
    last_sync_str = _fmt_sync(last_sync)

    return {
        "inserted": total_inserted,
        "updated":  total_updated,
        "errors":   errors,
        "last_sync": last_sync_str,
    }


@router.get("/categories")
def categories(
    saison: str = Query(..., description="Saison au format YYYY-YYYY (ou YYYY/YYYY)"),
    db: Session = Depends(get_db)
):
    s = saison.strip().replace("/", "-")
    cats = crud_seasons.get_categories_for_season(db, s)
    if not cats:
        # Fallback: try with "/" separator
        cats = crud_seasons.get_categories_for_season(db, s.replace("-", "/"))
    if not cats:
        return JSONResponse(status_code=404, content={"error": f"Saison '{saison}' non trouvée"})
    return cats


@router.get("/image")
async def image(
    saison: Optional[str] = "2025/2026",
    mode: Optional[str] = "planning",
    title: Optional[str] = "Matchs",
    format: Optional[str] = "pub",
    template: Optional[str] = None,
    categories: Optional[List[str]] = Query(None),
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    use_cache: bool = Query(True, description="Utiliser le cache des images"),
):
    logger.info("Image generation request - Mode: %s, Saison: %s, Template: %s, Categories: %s",
                mode, saison, template, categories)

    cache_params = {
        "saison": saison,
        "mode": mode,
        "title": title,
        "format": format,
        "template": template,
        "categories": categories or [],
        "date_start": date_start,
        "date_end": date_end,
    }

    if use_cache:
        cached_image = image_cache.get(**cache_params)
        if cached_image:
            logger.info("Serving image from cache")
            return Response(content=cached_image, media_type="image/png")

    logger.info("Generating new image asynchronously")
    try:
        from app.db.database import get_db_session
        def _gen():
            db = get_db_session()
            try:
                return generate_filtered_image(
                    categories, date_start, date_end, title, format, mode, saison, template, db=db
                )
            finally:
                db.close()

        img = await asyncio.to_thread(_gen)
    except ValueError as e:
        logger.error("Template error: %s", e)
        raise HTTPException(status_code=400, detail=str(e))

    if use_cache:
        await asyncio.to_thread(image_cache.set, img, **cache_params)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    logger.info("Image generated successfully")
    return StreamingResponse(buf, media_type="image/png")


@router.get("/templates")
def list_templates():
    from app.core.image_templates import template_manager
    return {
        "default": template_manager.default_template,
        "templates": template_manager.list_templates()
    }


@router.post("/update-config")
def update_config(db: Session = Depends(get_db)):
    """Met à jour la configuration des saisons depuis la FFVB."""
    from app.db.crud.config import get_setting, get_active_saisons
    club_id = get_setting(db, "club_id") or settings.club_id
    saisons = get_active_saisons(db) or settings.club_saisons
    try:
        generate_config_seasons(club_id, saisons, "saisons.yaml")
        return {"message": "Configuration mise à jour avec succès."}
    except Exception as e:
        return {"message": f"Erreur : {e}"}


@router.post("/cache/clear")
def clear_cache(expired_only: bool = Query(False, description="Supprimer uniquement les fichiers expirés")):
    logger.info("Cache clear requested (expired_only=%s)", expired_only)
    if expired_only:
        deleted_count = image_cache.clear_expired()
    else:
        deleted_count = image_cache.clear_all()
    return {
        "message": "Cache nettoyé avec succès",
        "deleted_files": deleted_count
    }
