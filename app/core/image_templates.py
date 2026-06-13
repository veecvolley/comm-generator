"""Template manager — loaded from DB with YAML fallback."""
import json
from dataclasses import dataclass
from typing import Optional, Dict, Any
from pathlib import Path
from app.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TemplateConfig:
    name: str
    description: str
    backgrounds: Dict[str, str]
    banners: Dict[str, str]
    fonts: Dict[str, int]
    offsets_y: Dict[str, int]
    offsets_x: Dict[str, Any]
    sizes: Dict[str, int]


class TemplateManager:
    def __init__(self):
        self._templates: Dict[str, TemplateConfig] = {}
        self._default_template: str = "template1"
        self._loaded = False

    @property
    def templates(self) -> Dict[str, TemplateConfig]:
        self._load()
        return self._templates

    @property
    def default_template(self) -> str:
        self._load()
        return self._default_template

    def _load(self):
        if self._loaded:
            return
        try:
            from app.db.database import get_db_session
            from app.db.crud.templates_crud import get_all_templates, get_default_template_name
            db = get_db_session()
            try:
                rows = get_all_templates(db)
                if rows:
                    self._default_template = get_default_template_name(db)
                    raw_map = {r.name: r for r in rows}
                    self._templates = {}
                    for name in raw_map:
                        self._templates[name] = self._build_from_db(name, raw_map)
                    self._loaded = True
                    logger.info("Templates loaded from DB: %s", list(self._templates.keys()))
                    return
            finally:
                db.close()
        except Exception as e:
            logger.warning("Could not load templates from DB (%s), falling back to YAML", e)
        self._load_from_yaml()
        self._loaded = True

    def _build_from_db(self, name: str, raw_map: dict) -> TemplateConfig:
        row = raw_map[name]
        data = {
            "name": row.display_name or name,
            "description": row.description or "",
            "backgrounds": row.get_backgrounds(),
            "banners": row.get_banners(),
            "fonts": row.get_fonts(),
            "offsets_y": row.get_offsets_y(),
            "offsets_x": row.get_offsets_x(),
            "sizes": row.get_sizes(),
        }
        if row.inherit_from and row.inherit_from in raw_map:
            parent = self._build_from_db(row.inherit_from, raw_map)
            parent_data = {
                "name": parent.name, "description": parent.description,
                "backgrounds": parent.backgrounds, "banners": parent.banners,
                "fonts": parent.fonts, "offsets_y": parent.offsets_y,
                "offsets_x": parent.offsets_x, "sizes": parent.sizes,
            }
            data = self._deep_merge(parent_data, data)
        return TemplateConfig(
            name=data["name"], description=data["description"],
            backgrounds=data["backgrounds"], banners=data["banners"],
            fonts=data["fonts"], offsets_y=data["offsets_y"],
            offsets_x=data["offsets_x"], sizes=data["sizes"],
        )

    def _load_from_yaml(self):
        import yaml
        config_path = Path(__file__).parent.parent.parent / "templates.yaml"
        if not config_path.exists():
            logger.error("templates.yaml not found")
            return
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        if not config or "templates" not in config:
            return
        self._default_template = config.get("default_template", "template1")
        all_templates = config["templates"]
        for name in all_templates:
            self._templates[name] = self._build_from_yaml(name, all_templates)
        logger.info("Templates loaded from YAML: %s", list(self._templates.keys()))

    def _build_from_yaml(self, name: str, all_templates: dict) -> TemplateConfig:
        data = all_templates[name]
        if "inherit_from" in data:
            parent_name = data["inherit_from"]
            parent_config = self._build_from_yaml(parent_name, all_templates)
            parent_data = {
                "name": parent_config.name, "description": parent_config.description,
                "backgrounds": parent_config.backgrounds, "banners": parent_config.banners,
                "fonts": parent_config.fonts, "offsets_y": parent_config.offsets_y,
                "offsets_x": parent_config.offsets_x, "sizes": parent_config.sizes,
            }
            data = self._deep_merge(parent_data, data)
        return TemplateConfig(
            name=data.get("name", name), description=data.get("description", ""),
            backgrounds=data.get("backgrounds", {}), banners=data.get("banners", {}),
            fonts=data.get("fonts", {}), offsets_y=data.get("offsets_y", {}),
            offsets_x=data.get("offsets_x", {}), sizes=data.get("sizes", {}),
        )

    def _deep_merge(self, base: Dict, overlay: Dict) -> Dict:
        result = base.copy()
        for key, value in overlay.items():
            if key == "inherit_from":
                continue
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def reload(self):
        self._loaded = False
        self._templates = {}
        self._load()

    def get_template(self, name: Optional[str] = None) -> TemplateConfig:
        self._load()
        template_name = name or self._default_template
        if template_name not in self._templates:
            available = list(self._templates.keys())
            raise ValueError(f"Template '{template_name}' not found. Available: {available}")
        logger.debug("Using template: %s", template_name)
        return self._templates[template_name]

    def list_templates(self) -> Dict[str, str]:
        self._load()
        return {name: tmpl.name for name, tmpl in self._templates.items()}


template_manager = TemplateManager()
