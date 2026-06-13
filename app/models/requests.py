"""Modèles Pydantic pour la validation des requêtes."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


class ImageGenerationRequest(BaseModel):
    """Modèle pour la génération d'images."""

    saison: str = Field(
        default="2025/2026",
        pattern=r"^\d{4}[-/]\d{4}$",
        description="Saison au format YYYY/YYYY ou YYYY-YYYY"
    )
    mode: str = Field(
        default="planning",
        pattern="^(planning|results)$",
        description="Mode de génération: planning ou results"
    )
    title: str = Field(
        default="Matchs",
        min_length=1,
        max_length=100,
        description="Titre de l'image"
    )
    format: str = Field(
        default="pub",
        pattern="^(pub|story)$",
        description="Format de l'image: pub ou story"
    )
    template: Optional[str] = Field(
        default=None,
        description="Nom du template à utiliser (si non spécifié, utilise le défaut)"
    )
    categories: Optional[List[str]] = Field(
        default=None,
        description="Liste des codes de catégories à filtrer"
    )
    date_start: Optional[str] = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Date de début au format YYYY-MM-DD"
    )
    date_end: Optional[str] = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Date de fin au format YYYY-MM-DD"
    )

    @field_validator('date_end')
    @classmethod
    def validate_date_range(cls, v: Optional[str], info) -> Optional[str]:
        """Valide que date_end est après date_start."""
        if v and info.data.get('date_start'):
            date_start = datetime.strptime(info.data['date_start'], "%Y-%m-%d")
            date_end = datetime.strptime(v, "%Y-%m-%d")
            if date_end < date_start:
                raise ValueError("date_end doit être après date_start")
        return v

    @field_validator('categories')
    @classmethod
    def validate_categories(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Valide que les catégories sont des codes valides."""
        if v:
            # Vérifier que chaque catégorie est bien un code de 3 caractères
            for cat in v:
                if not cat or len(cat) != 3:
                    raise ValueError(f"Code de catégorie invalide: {cat}")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "saison": "2025/2026",
                    "mode": "planning",
                    "title": "Matchs du week-end",
                    "format": "pub",
                    "template": "template1",
                    "categories": ["SF1", "SM1", "M18"],
                    "date_start": "2025-01-10",
                    "date_end": "2025-01-12"
                }
            ]
        }
    }
