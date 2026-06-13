"""Système de cache pour les images générées."""

import hashlib
import io
import os
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
from PIL import Image
from app.core.logger import get_logger

logger = get_logger(__name__)

# Configuration du cache via variables d'environnement
CACHE_DIR = Path(os.getenv("CACHE_DIR", "/tmp/comm_generator_cache"))
CACHE_EXPIRY_MINUTES = int(os.getenv("CACHE_EXPIRY_MINUTES", "60"))


class ImageCache:
    """Gestionnaire de cache pour les images générées."""

    def __init__(self, cache_dir: Path = CACHE_DIR, expiry_minutes: int = CACHE_EXPIRY_MINUTES):
        self.cache_dir = cache_dir
        self.expiry_minutes = expiry_minutes
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Image cache initialized at %s (expiry: %d min)", cache_dir, expiry_minutes)

    def _generate_cache_key(self, **params) -> str:
        """
        Génère une clé de cache unique basée sur les paramètres.

        :param params: Paramètres de génération d'image
        :return: Clé de cache (hash MD5)
        """
        # Créer une chaîne représentant tous les paramètres
        key_parts = []
        for key in sorted(params.keys()):
            value = params[key]
            if isinstance(value, list):
                value = tuple(sorted(value))
            key_parts.append(f"{key}={value}")

        key_string = "|".join(key_parts)
        cache_key = hashlib.md5(key_string.encode()).hexdigest()
        return cache_key

    def _get_cache_path(self, cache_key: str) -> Path:
        """Retourne le chemin du fichier cache."""
        return self.cache_dir / f"{cache_key}.png"

    def _is_cache_valid(self, cache_path: Path) -> bool:
        """
        Vérifie si le fichier cache est encore valide (pas expiré).

        :param cache_path: Chemin du fichier cache
        :return: True si valide, False sinon
        """
        if not cache_path.exists():
            return False

        # Vérifier l'âge du fichier
        file_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
        age = datetime.now() - file_time
        max_age = timedelta(minutes=self.expiry_minutes)

        if age > max_age:
            logger.debug("Cache expired for %s (age: %s)", cache_path.name, age)
            return False

        return True

    def get(self, **params) -> Optional[bytes]:
        """
        Récupère une image du cache si elle existe et est valide.

        :param params: Paramètres de génération d'image
        :return: Données PNG de l'image ou None si pas en cache
        """
        cache_key = self._generate_cache_key(**params)
        cache_path = self._get_cache_path(cache_key)

        if self._is_cache_valid(cache_path):
            logger.info("Cache hit for key: %s", cache_key)
            with open(cache_path, "rb") as f:
                return f.read()

        logger.debug("Cache miss for key: %s", cache_key)
        return None

    def set(self, image: Image.Image, **params) -> None:
        """
        Sauvegarde une image dans le cache.

        :param image: Image PIL à sauvegarder
        :param params: Paramètres de génération d'image
        """
        cache_key = self._generate_cache_key(**params)
        cache_path = self._get_cache_path(cache_key)

        try:
            image.save(cache_path, format="PNG")
            logger.info("Image cached with key: %s", cache_key)
        except Exception as e:
            logger.error("Failed to cache image: %s", e)

    def clear_expired(self) -> int:
        """
        Nettoie les fichiers cache expirés.

        :return: Nombre de fichiers supprimés
        """
        deleted_count = 0
        for cache_file in self.cache_dir.glob("*.png"):
            if not self._is_cache_valid(cache_file):
                try:
                    cache_file.unlink()
                    deleted_count += 1
                    logger.debug("Deleted expired cache file: %s", cache_file.name)
                except Exception as e:
                    logger.error("Failed to delete cache file %s: %s", cache_file.name, e)

        logger.info("Cleared %d expired cache files", deleted_count)
        return deleted_count

    def clear_all(self) -> int:
        """
        Supprime tous les fichiers du cache.

        :return: Nombre de fichiers supprimés
        """
        deleted_count = 0
        for cache_file in self.cache_dir.glob("*.png"):
            try:
                cache_file.unlink()
                deleted_count += 1
            except Exception as e:
                logger.error("Failed to delete cache file %s: %s", cache_file.name, e)

        logger.info("Cleared all %d cache files", deleted_count)
        return deleted_count


# Instance globale du cache
image_cache = ImageCache()
