import json
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, UniqueConstraint, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class AppSetting(Base):
    __tablename__ = "app_settings"
    key = Column(String, primary_key=True)
    value = Column(Text, default="")
    description = Column(Text, default="")


class Gymnase(Base):
    __tablename__ = "gymnases"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)


class ActiveSaison(Base):
    __tablename__ = "active_saisons"
    id = Column(Integer, primary_key=True, autoincrement=True)
    saison = Column(String, nullable=False, unique=True)


class CategoryConfig(Base):
    __tablename__ = "category_configs"
    __table_args__ = (UniqueConstraint("saison", "code"),)
    id = Column(Integer, primary_key=True, autoincrement=True)
    saison = Column(String, nullable=False)
    code = Column(String, nullable=False)
    titre = Column(Text, default="")
    type = Column(String, default="")
    genre = Column(String, default="")
    category = Column(String, default="")
    niveau = Column(String, default="")
    label = Column(String, default="")


class TeamDetectionPattern(Base):
    __tablename__ = "team_detection_pattern"
    pattern = Column(String, primary_key=True)


class TeamRule(Base):
    __tablename__ = "team_rules"
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_index = Column(Integer, nullable=False, default=0)
    match_label = Column(String, default="")
    match_genre = Column(String, default="")
    match_type = Column(String, default="")
    match_niveau = Column(String, default="")
    match_titre = Column(String, default="")
    pseudo_template = Column(String, default="")
    pseudo = Column(String, default="")
    font_size = Column(String, default="bold_15")
    auto_num = Column(Boolean, default=False)
    is_default = Column(Boolean, default=False)


class Template(Base):
    """
    Template config stored as JSON blobs for flexibility.
    offsets_x is heterogeneous (mix of int and dict), so JSON is the right fit.
    """
    __tablename__ = "templates"
    name = Column(String, primary_key=True)
    display_name = Column(String, default="")
    description = Column(Text, default="")
    inherit_from = Column(String, nullable=True)
    is_default = Column(Boolean, default=False)
    backgrounds = Column(Text, default="{}")
    banners = Column(Text, default="{}")
    fonts = Column(Text, default="{}")
    offsets_y = Column(Text, default="{}")
    offsets_x = Column(Text, default="{}")
    sizes = Column(Text, default="{}")

    def get_backgrounds(self) -> dict:
        return json.loads(self.backgrounds or "{}")

    def get_banners(self) -> dict:
        return json.loads(self.banners or "{}")

    def get_fonts(self) -> dict:
        return json.loads(self.fonts or "{}")

    def get_offsets_y(self) -> dict:
        return json.loads(self.offsets_y or "{}")

    def get_offsets_x(self) -> dict:
        return json.loads(self.offsets_x or "{}")

    def get_sizes(self) -> dict:
        return json.loads(self.sizes or "{}")


class RefValue(Base):
    __tablename__ = "ref_values"
    __table_args__ = (UniqueConstraint("category", "value"),)
    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String, nullable=False)
    value = Column(String, nullable=False)


class Club(Base):
    __tablename__ = "clubs"
    code = Column(String, primary_key=True)
    name = Column(String, default="")
    has_logo = Column(Boolean, default=False)


class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True, autoincrement=True)
    match_code = Column(String, unique=True, nullable=False)
    entity = Column(String, default="")
    cat_code = Column(String, default="")
    saison = Column(String, nullable=False, default="")
    division_code = Column(String, default="")
    date = Column(String, default="")
    time = Column(String, default="")
    logo_a = Column(String, default="")
    team_a = Column(String, default="")
    logo_b = Column(String, default="")
    team_b = Column(String, default="")
    sets = Column(String, default="")
    score = Column(String, default="")
    place = Column(String, default="")
    synced_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class GymnaSeAddress(Base):
    __tablename__ = "gymnase_addresses"
    id = Column(Integer, primary_key=True, autoincrement=True)
    match_code = Column(String, unique=True, nullable=False)
    entity = Column(String, default="")
    name = Column(String, default="")
    street = Column(String, default="")
    postal_code = Column(String, default="")
    city = Column(String, default="")
    cached_at = Column(DateTime, server_default=func.now())
