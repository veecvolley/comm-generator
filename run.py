"""Point d'entrée principal de l'application."""

import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

from app.main import app

# Pour lancer avec uvicorn:
# uvicorn run:app --reload
#
# Ou avec configuration depuis .env:
# uvicorn run:app --host $HOST --port $PORT --reload=$RELOAD

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "false").lower() == "true"

    uvicorn.run(
        "run:app",
        host=host,
        port=port,
        reload=reload,
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )
