from datetime import datetime
from pathlib import Path
from typing import Optional, List
from PIL import Image, ImageFont
from app.core.constants import jours, mois
from app.core.colors import (
    TEXT_TITLE_GRAY, TEXT_DATE_YELLOW, TEXT_BLACK, STROKE_BLACK,
    VICTORY_GREEN, DEFEAT_RED, DRAW_YELLOW
)
from app.services.image_utils import paste_image_fit_box, draw_centered_text_overlay
from app.services.score_utils import did_team_a_win, format_sets, create_score_image
from app.services.string_utils import _norm, get_team_pseudo, formater_periode
from app.services.data_provider import parse_csv_rows, get_gymnase_address
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


# Note: LayoutOffsets dataclass pour future amélioration
# @dataclass
# class LayoutOffsets:
#     """Offsets verticaux pour le positionnement des éléments dans l'image."""
#     base: int
#     title: int
#     date_title: int
#     entity: int
#     category: int
#     team_name: int
#     delta: int
#     logo: int
#     team: int
#     date: int
#     place: int
#     place_type: int
#     sets: int
#     victory: int
#     score: int
#
#     def increment_all(self, delta: int) -> None:
#         """Incrémente tous les offsets d'un delta donné."""
#         self.base += delta
#         self.entity += delta
#         self.category += delta
#         self.team_name += delta
#         self.logo += delta
#         self.team += delta
#         self.date += delta
#         self.place += delta
#         self.place_type += delta
#         self.sets += delta
#         self.victory += delta
#         self.score += delta

BASE_PATH = Path(__file__).resolve().parent.parent  # == app/
ASSETS_DIR = BASE_PATH / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
CLUBS_DIR = ASSETS_DIR / "clubs"
ICONS_DIR = ASSETS_DIR / "icons"
BACKGROUNDS_DIR = ASSETS_DIR / "backgrounds"
BANNERS_DIR = ASSETS_DIR / "banners"
def _get_indoor_gyms():
    return {_norm(n) for n in settings.club_gymnases}

def setup_graphics(format="pub", multiplier=2, template_config=None):
    """
    Configuration des polices et du fond d'image.

    :param format: Format de l'image (pub ou story)
    :param multiplier: Multiplicateur pour les tailles
    :param template_config: Configuration du template à utiliser
    :return: (multiplier, fonts, background, template_config)
    """
    if template_config is None:
        from app.core.image_templates import template_manager
        template_config = template_manager.get_template()

    m = multiplier

    # Création des polices à partir de la config du template
    fonts = {}
    for font_key, size in template_config.fonts.items():
        if font_key == "main":
            fonts[font_key] = ImageFont.truetype(FONTS_DIR / "DejaVuSans.ttf", size=size*m)
        elif font_key.startswith("bold"):
            fonts[font_key] = ImageFont.truetype(FONTS_DIR / "OpenSans-ExtraBold.ttf", size=size*m)
        elif font_key == "title":
            fonts[font_key] = ImageFont.truetype(FONTS_DIR / "Gagalin-Regular.ttf", size=size*m)
        elif font_key in ["sets", "victory", "date_title"]:
            fonts[font_key] = ImageFont.truetype(FONTS_DIR / "Coiny-Regular.ttf", size=size*m)

    # Chargement du background depuis la config du template
    bg_filename = template_config.backgrounds.get(format, f"{format}.png")
    background = Image.open(BACKGROUNDS_DIR / bg_filename).convert("RGBA")

    return m, fonts, background, template_config

def generate_filtered_image(
    categories_filter: Optional[List[str]] = None,
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    title: Optional[str] = None,
    format: str = "pub",
    mode: str = "planning",
    saison: Optional[str] = None,
    template: Optional[str] = None,
    db=None,
) -> Image.Image:
    # Charger la configuration du template
    from app.core.image_templates import template_manager
    template_config = template_manager.get_template(template)

    m, fonts, background, template_config = setup_graphics(format, template_config=template_config)

    # Offsets verticaux depuis le template
    v = template_config.offsets_y['base'] * m
    v_title = template_config.offsets_y['title'] * m
    v_date_title = template_config.offsets_y['date_title'] * m
    v_entity = template_config.offsets_y['entity'] * m
    v_category = template_config.offsets_y['category'] * m
    v_team_name = template_config.offsets_y['team_name'] * m
    v_delta = template_config.offsets_y['delta'] * m
    v_logo = template_config.offsets_y['logo'] * m
    v_team = template_config.offsets_y['team'] * m
    v_date = template_config.offsets_y['date'] * m
    v_place = template_config.offsets_y['place'] * m
    v_place_type = template_config.offsets_y['place_type'] * m
    v_sets = template_config.offsets_y['sets'] * m
    v_victory = template_config.offsets_y['victory'] * m
    v_score = template_config.offsets_y['score'] * m

    draw_centered_text_overlay(background, title,
                                template_config.offsets_x['title']['center']*m,
                                template_config.offsets_x['title']['width']*m,
                                v_title, fonts["title"],
                                fill=TEXT_TITLE_GRAY, stroke_width=0, stroke_fill=STROKE_BLACK)

    date_start_dt = datetime.strptime(date_start, "%Y-%m-%d") if date_start else None
    date_end_dt = datetime.strptime(date_end, "%Y-%m-%d") if date_end else None
    date_title = formater_periode(date_start_dt, date_end_dt)

    draw_centered_text_overlay(background, date_title,
                                template_config.offsets_x['date_title']['center']*m,
                                template_config.offsets_x['date_title']['width']*m,
                                v_date_title, fonts["date_title"],
                                fill=TEXT_DATE_YELLOW, stroke_width=0, stroke_fill=STROKE_BLACK)

    logger.info("Generating image for period: %s - %s => %s", date_start_dt, date_end_dt, date_title)

    reader = list(parse_csv_rows(saison, "", db=db))
    # reader1 = list(parse_csv_rows(saison,""))
    # reader2 = list(parse_csv_rows(saison,"QCM"))
    # reader = reader1 + reader2

    # Pré-charger les codes de la saison, triés par longueur décroissante
    # pour matcher le code le plus long en premier (ex: DMBA avant DMA)
    season_cats = (
        settings.saisons.get(saison) or
        settings.saisons.get(saison.replace("-", "/")) or
        settings.saisons.get(saison.replace("/", "-")) or
        {}
    )
    season_codes_sorted = sorted(season_cats.keys(), key=len, reverse=True)

    for row in reader:
        entity, match, date = row[0], row[2], row[3]
        hour = "" if row[4] == "00:00" else row[4]
        logo_a, team_a, logo_b, team_b = row[5], row[6], row[7], row[8]
        sets, score = row[9], row[10]
        place = row[12]
        cat_code = next(
            (code for code in season_codes_sorted if match.startswith(code)),
            None
        )

        if team_a == 'xxxxx' or team_b == 'xxxxx':
            continue

        if date == 'Date':
            continue

        if cat_code is None:
            logger.debug("Aucun code saison trouvé pour le match '%s' — ignoré", match)
            continue

        dt = datetime.strptime(date, "%Y-%m-%d")
        if date_start_dt and dt < date_start_dt: continue
        if date_end_dt and dt > date_end_dt: continue
        if categories_filter and cat_code not in categories_filter:
            logger.debug("Match '%s' (cat_code='%s') ignoré — pas dans le filtre %s", match, cat_code, categories_filter)
            continue
        # entities_str = list(settings.entities.keys())
        # if entity not in entities_str: continue
        logger.debug("Processing match: %s | %s", saison, cat_code)
        cat_info = settings.get_season_config(saison, cat_code)
        if not cat_info:
            logger.warning("Code '%s' non trouvé dans saisons.yaml pour la saison %s — match ignoré", cat_code, saison)
            continue
        title_entity = cat_info['niveau']
        category = cat_info['type']
        team_name = cat_info['label']

        date_full = f"{jours[dt.strftime('%A')]} {dt.day} {mois[dt.strftime('%B')]} {hour}"

        if mode == "results":
            result = did_team_a_win(sets)
            club_a = settings.club.lower() in team_a.lower()
            club_b = settings.club.lower() in team_b.lower()
        
            if result is not None:  # Seulement si ce n'est pas une égalité
                if (result and club_a) or (not result and club_b):
                    result = True
                elif (not result and club_a) or (result and club_b):
                    result = False
            # Si result est None (égalité), on le laisse None

            if result == None:
               
                # Cas de forfait - détecté quand le score ne contient que des 25-0 ou 0-25
                if score:
                    score_sets = score.strip().split(',')
                    all_25_0 = all(s == "25-0" for s in score_sets)
                    all_0_25 = all(s == "0-25" for s in score_sets)
                    print(f"DEBUG: {result} - {score} - {score_sets} - {all_25_0} - {all_0_25}")
                    if all_25_0:
                        # Équipe A gagne par forfait de B
                        victory_text = "VICTOIRE" if club_a else "FORFAIT"
                        victory_color = "green" if club_a else "red"
                    elif all_0_25:
                        # Équipe B gagne par forfait de A
                        victory_text = "VICTOIRE" if club_b else "FORFAIT"
                        victory_color = "green" if club_b else "red"
                    else:
                        victory_text = "ÉGALITÉ"
                        victory_color = "yellow"
                else:
                    victory_text = "ÉGALITÉ"
                    victory_color = "yellow"
            elif score:
                victory_color = "green" if result else "red" if result is False else "yellow"
                victory_text = "VICTOIRE" if result else "DÉFAITE" if result is False else "ÉGALITÉ"
            else:
                victory_text = "INCONNU"
                victory_color = "yellow"

            banner_file = template_config.banners[f"result_{victory_color}"]
            overlay = Image.open(BANNERS_DIR / banner_file).convert("RGBA")
            background.paste(overlay, (20*m, v), overlay)
        else:
            banner_file = template_config.banners["planning"]
            overlay = Image.open(BANNERS_DIR / banner_file).convert("RGBA")
            background.paste(overlay, (20*m, v), overlay)

        # Log match details
        logger.debug(
            "Match details: %s | %s | %s - %s - %s - %s - (%s) %s - (%s) %s - %s - %s - %s",
            format, cat_code, date_full, entity, match, category, logo_a, team_a, logo_b, team_b, sets, score, place
        )
        logger.debug(
            "Category info: %s - %s - %s - %s - %s",
            cat_info['label'], cat_info['genre'], cat_info['type'], cat_info['niveau'], cat_info['titre']
        )


        draw_centered_text_overlay(background, title_entity,
                                    template_config.offsets_x['entity']['center']*m,
                                    template_config.offsets_x['entity']['width']*m,
                                    v_entity, fonts["bold_15"], stroke_width=1, stroke_fill=(0,0,0,255))
        draw_centered_text_overlay(background, category,
                                    template_config.offsets_x['category']['center']*m,
                                    template_config.offsets_x['category']['width']*m,
                                    v_category, fonts["bold_15"], stroke_width=1, stroke_fill=(0,0,0,255))
        draw_centered_text_overlay(background, team_name,
                                    template_config.offsets_x['team_name']['center']*m,
                                    template_config.offsets_x['team_name']['width']*m,
                                    v_team_name, fonts["bold_15"], stroke_width=1, stroke_fill=(0,0,0,255))

        logo_width = template_config.sizes['logo_width'] * m
        logo_height = template_config.sizes['logo_height'] * m

        try:
            background = paste_image_fit_box(background, CLUBS_DIR / f"{logo_a}.png",
                                            template_config.offsets_x['logo_a']*m, v_logo,
                                            logo_width, logo_height)
        except FileNotFoundError:
            background = paste_image_fit_box(background, CLUBS_DIR / "no_logo.png",
                                            template_config.offsets_x['logo_a']*m, v_logo,
                                            logo_width, logo_height)

        team_a, team_font_size = get_team_pseudo(cat_info['label'], cat_info['genre'], cat_info['type'], cat_info['niveau'], team_a, cat_info['titre'])
        draw_centered_text_overlay(background, team_a.replace("-", " "),
                                    template_config.offsets_x['team_a']['center']*m,
                                    template_config.offsets_x['team_a']['width']*m,
                                    v_team, fonts[team_font_size], fill=(0,0,0,255))

        try:
            background = paste_image_fit_box(background, CLUBS_DIR / f"{logo_b}.png",
                                            template_config.offsets_x['logo_b']*m, v_logo,
                                            logo_width, logo_height)
        except FileNotFoundError:
            background = paste_image_fit_box(background, CLUBS_DIR / "no_logo.png",
                                            template_config.offsets_x['logo_b']*m, v_logo,
                                            logo_width, logo_height)

        team_b, team_font_size = get_team_pseudo(cat_info['label'], cat_info['genre'], cat_info['type'], cat_info['niveau'], team_b, cat_info['titre'])
        draw_centered_text_overlay(background, team_b.replace("-", " "),
                                    template_config.offsets_x['team_b']['center']*m,
                                    template_config.offsets_x['team_b']['width']*m,
                                    v_team, fonts[team_font_size], fill=(0,0,0,255))

        logger.debug("Teams displayed: %s vs %s", team_a, team_b)


        if mode == "results" and score:
            color = (0,109,57,255) if victory_color == "green" else (167,46,59,255) if victory_color == "red" else (245,159,10,255)
            draw_centered_text_overlay(background, victory_text,
                                        template_config.offsets_x['victory']['center']*m,
                                        template_config.offsets_x['victory']['width']*m,
                                        v_victory, fonts["victory"], fill=color)

            sets_formatted = format_sets(sets)
            draw_centered_text_overlay(background, sets_formatted,
                                        template_config.offsets_x['sets']['center']*m,
                                        template_config.offsets_x['sets']['width']*m,
                                        v_sets, fonts["sets"], fill=(10,58,128,255))

            score_img = create_score_image(score)
            background.paste(score_img, (template_config.offsets_x['score']*m, v_score))
        elif mode == "planning":
            draw_centered_text_overlay(background, date_full,
                                        template_config.offsets_x['date']['center']*m,
                                        template_config.offsets_x['date']['width']*m,
                                        v_date, fonts["bold_15"])
            try:
                result = get_gymnase_address(match, entity, db=db)
            except Exception as e:
                logger.warning("Impossible de récupérer l'adresse du gymnase (%s): %s", match, e)
                result = None
            place_nom = result["nom"] if result else ""
            place_adr = result["rue"] if result else "Adresse non disponible"
            place_ville = result["ville"] if result else ""

            draw_centered_text_overlay(background, place_nom,
                                        template_config.offsets_x['place_nom']['center']*m,
                                        template_config.offsets_x['place_nom']['width']*m,
                                        v_place, fonts["bold_14"], stroke_width=1, stroke_fill=(0,0,0,255))
            draw_centered_text_overlay(background, place_adr,
                                        template_config.offsets_x['place_adr']['center']*m,
                                        template_config.offsets_x['place_adr']['width']*m,
                                        v_place + template_config.offsets_x['place_adr']['offset']*m,
                                        fonts["bold_12"], stroke_width=1, stroke_fill=(0,0,0,255))
            draw_centered_text_overlay(background, place_ville,
                                        template_config.offsets_x['place_ville']['center']*m,
                                        template_config.offsets_x['place_ville']['width']*m,
                                        v_place + template_config.offsets_x['place_ville']['offset']*m,
                                        fonts["bold_15"], stroke_width=1, stroke_fill=(0,0,0,255))

            place_type = "int" if _norm(place) in _get_indoor_gyms() else "ext"
            place_icon_size = template_config.sizes['place_icon'] * m
            overlay = Image.open(ICONS_DIR / f"{place_type}.png").convert("RGBA").resize((place_icon_size, place_icon_size))
            background.paste(overlay, (template_config.offsets_x['place_icon']*m, v_place_type), overlay)

        # Décalage vertical
        v += v_delta
        v_entity += v_delta
        v_category += v_delta
        v_team_name += v_delta
        v_logo += v_delta
        v_team += v_delta
        v_date += v_delta
        v_place += v_delta
        v_place_type += v_delta
        v_sets += v_delta
        v_victory += v_delta
        v_score += v_delta

    return background
