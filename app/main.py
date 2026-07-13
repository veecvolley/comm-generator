from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import pathlib

from app.api.routes import router
from app.api.admin import admin_router
from app.core.logger import get_logger

logger = get_logger(__name__)
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application...")

    # Initialize DB (create tables + seed from YAML if empty)
    from app.db.database import engine
    from app.db.models import Base
    from app.db.seed import seed
    from app.db.database import SessionLocal

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()

    logger.info("Database ready")
    yield
    logger.info("Shutting down application...")


app = FastAPI(
    title="VEEC Comm'Generator",
    description="Générateur d'images de communication pour le volley",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning("Validation error on %s: %s", request.url, exc.errors())
    return JSONResponse(status_code=422, content={"error": "Validation error", "details": exc.errors()})


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning("HTTP %s on %s: %s", exc.status_code, request.url, exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception on %s: %s", request.url, str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "message": "Une erreur inattendue s'est produite"},
    )


app.mount("/static",  StaticFiles(directory=BASE_DIR / "app" / "static"),  name="static")
app.mount("/assets",  StaticFiles(directory=BASE_DIR / "app" / "assets"),  name="assets")


@app.get("/admin")
def admin_redirect():
    return RedirectResponse("/admin/", status_code=301)


app.include_router(router)
app.include_router(admin_router)
