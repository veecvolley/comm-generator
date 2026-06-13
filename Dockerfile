# Dockerfile multi-stage optimisé pour Comm'Generator
# Build: docker build -t veec-comm-generator:latest .
# Run: docker run -p 8000:8000 veec-comm-generator:latest

# ==========================================
# Stage 1: Builder - Install dependencies
# ==========================================
FROM python:3.13-slim AS builder

# Variables d'environnement pour Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Installer les dépendances système nécessaires pour la compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Créer un virtualenv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copier requirements et installer les dépendances Python
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# ==========================================
# Stage 2: Runtime - Application finale
# ==========================================
FROM python:3.13-slim

# Labels pour metadata
LABEL maintainer="VEEC Volley <contact@veec-volley.fr>"
LABEL description="Générateur d'images de communication pour le volley-ball"
LABEL version="1.0.0"

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    LOG_LEVEL=INFO \
    HOST=0.0.0.0 \
    PORT=8000

# Créer un utilisateur non-root pour la sécurité
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app /tmp/comm_generator_cache && \
    chown -R appuser:appuser /app /tmp/comm_generator_cache

# Copier le virtualenv depuis le builder
COPY --from=builder --chown=appuser:appuser /opt/venv /opt/venv

# Définir le répertoire de travail
WORKDIR /app

# Copier l'application
COPY --chown=appuser:appuser . .

# Passer à l'utilisateur non-root
USER appuser

# Exposer le port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Commande par défaut
CMD ["python", "run.py"]
