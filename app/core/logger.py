"""Configuration du système de logging pour l'application."""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Configure et retourne un logger.

    :param name: Nom du logger (généralement __name__)
    :param level: Niveau de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    :param log_file: Chemin optionnel vers un fichier de log
    :param format_string: Format personnalisé des messages
    :return: Logger configuré
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Éviter d'ajouter plusieurs handlers si déjà configuré
    if logger.handlers:
        return logger

    # Format par défaut
    if format_string is None:
        format_string = "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] %(message)s"

    formatter = logging.Formatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")

    # Handler pour la console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler pour fichier (optionnel)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Récupère un logger avec la configuration par défaut de l'application.

    :param name: Nom du logger (généralement __name__)
    :return: Logger configuré
    """
    # Utiliser DEBUG en développement, INFO en production
    # Peut être configuré via variable d'environnement
    import os
    level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_str, logging.INFO)

    return setup_logger(name, level=level)
