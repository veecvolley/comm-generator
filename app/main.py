from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import pathlib
import asyncio

from app.api.routes import router
from app.services.seasons import generate_config_seasons
from app.core.config import settings

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent

app = FastAPI()
app.mount("/static", StaticFiles(directory=BASE_DIR / "app" / "static"), name="static")
app.include_router(router)

@app.on_event("startup")
async def on_startup():
    club_id = settings.config["club"]["id"]
    club_saisons = settings.config["club"]["saisons"]
    # # hors thread pour éviter de bloquer la boucle
    # await asyncio.to_thread(generate_config_seasons, club_id, club_saisons, "saisons.yaml")