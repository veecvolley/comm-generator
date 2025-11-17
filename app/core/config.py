import yaml
from pathlib import Path
from typing import Any, Dict

def _safe_load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}

class Settings:
    """
    - config.yaml  : configuration générale (ffvb, club, championnat, etc.)
    - saisons.yaml : données de saisons (clé racine attendue: 'saisons')
    """
    def __init__(
        self,
        base_dir: Path | None = None,
        config_filename: str = "config.yaml",
        saisons_filename: str = "saisons.yaml",
    ):
        # Répertoire racine par défaut: <repo>/ (deux niveaux au-dessus de ce fichier)
        self.base_dir = base_dir or (Path(__file__).parents[2])

        self.config_path = self.base_dir / config_filename
        self.saisons_path = self.base_dir / saisons_filename

        # Chargements séparés
        self.config: Dict[str, Any] = _safe_load_yaml(self.config_path)
        self._saisons_doc: Dict[str, Any] = _safe_load_yaml(self.saisons_path)

        # Compat: accepte soit un fichier saisons.yaml avec racine 'saisons',
        # soit directement le mapping des saisons à la racine.
        if "saisons" in self._saisons_doc and isinstance(self._saisons_doc["saisons"], dict):
            self.saisons: Dict[str, Any] = self._saisons_doc["saisons"]
        else:
            # tolère un fichier où les saisons sont à la racine
            self.saisons = self._saisons_doc

    # ---- Accès config générale (config.yaml) ----
    @property
    def ffvb_csv_url(self):
        return self.config.get("ffvb", {}).get("csv_url")

    @property
    def ffvb_csv_url_division(self):
        return self.config.get("ffvb", {}).get("csv_url_division")

    @property
    def ffvb_address_url(self):
        return self.config.get("ffvb", {}).get("address_pdf_url")

    @property
    def club(self):
        return self.config.get("club", {}).get("name")

    @property
    def club_id(self):
        return self.config.get("club", {}).get("id")

    @property
    def club_gymnases(self):
        return self.config.get("club", {}).get("gymnases", [])

    @property
    def club_saisons(self):
        return self.config.get("club", {}).get("saisons", [])

    # ---- Accès saisons (saisons.yaml) ----
    def get_season_config(self, saison: str, code: str) -> dict:
        """
        Récupère la configuration d'une catégorie pour une saison donnée
        depuis saisons.yaml. Retourne un dict vide si non trouvée.
        """
        try:
            return self.saisons[saison][code]
        except Exception:
            return {}

# Instance par défaut
settings = Settings()
