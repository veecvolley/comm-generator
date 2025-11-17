from datetime import datetime
from pathlib import Path
from PIL import Image, ImageFont
from app.core.constants import jours, mois
from app.services.image_utils import paste_image_fit_box, draw_centered_text_overlay
from app.services.score_utils import did_team_a_win, format_sets, create_score_image
from app.services.string_utils import _norm, get_team_pseudo, formater_periode
from app.services.data_provider import parse_csv_rows, get_gymnase_address
from app.core.config import settings
import re

BASE_PATH = Path(__file__).resolve().parent.parent  # == app/
ASSETS_DIR = BASE_PATH / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
CLUBS_DIR = ASSETS_DIR / "clubs"
ICONS_DIR = ASSETS_DIR / "icons"
BACKGROUNDS_DIR = ASSETS_DIR / "backgrounds"
BANNERS_DIR = ASSETS_DIR / "banners"
INDOOR_GYMS = {_norm(n) for n in settings.club_gymnases}

def setup_graphics(format="pub", multiplier=2):
    m = multiplier
    fonts = {
        "main": ImageFont.truetype(FONTS_DIR / "DejaVuSans.ttf", size=50*m),
        "bold_10": ImageFont.truetype(FONTS_DIR / "OpenSans-ExtraBold.ttf", size=10*m),
        "bold_12": ImageFont.truetype(FONTS_DIR / "OpenSans-ExtraBold.ttf", size=12*m),
        "bold_13": ImageFont.truetype(FONTS_DIR / "OpenSans-ExtraBold.ttf", size=13*m),
        "bold_14": ImageFont.truetype(FONTS_DIR / "OpenSans-ExtraBold.ttf", size=14*m),
        "bold_15": ImageFont.truetype(FONTS_DIR / "OpenSans-ExtraBold.ttf", size=15*m),
        "bold_25": ImageFont.truetype(FONTS_DIR / "OpenSans-ExtraBold.ttf", size=25*m),
        "title": ImageFont.truetype(FONTS_DIR / "Gagalin-Regular.ttf", size=35*m),
        "sets": ImageFont.truetype(FONTS_DIR / "Coiny-Regular.ttf", size=30*m),
        "victory": ImageFont.truetype(FONTS_DIR / "Coiny-Regular.ttf", size=25*m),
        "date_title": ImageFont.truetype(FONTS_DIR / "Coiny-Regular.ttf", size=20*m),
    }
    background = Image.open(BACKGROUNDS_DIR / f"{format}.png").convert("RGBA")
    return m, fonts, background

def generate_filtered_image(categories_filter=None, date_start=None, date_end=None, title=None, format="pub", mode="planning", saison=None):
    m, fonts, background = setup_graphics(format)

    # Offsets
    v = 200*m
    v_title = 68*m
    v_date_title = 130*m
    v_entity = 215*m
    v_category = 240*m
    v_team_name = 260*m
    v_delta = 80*m
    v_logo = 205*m
    v_team = 235*m
    v_date = 235*m
    v_place = 217*m
    v_place_type = 220*m
    v_sets = 238*m
    v_victory = 238*m
    v_score = 202*m

    draw_centered_text_overlay(background, title, 1030*m, 660*m, v_title, fonts["title"],
                                fill=(66,66,66,255), stroke_width=0, stroke_fill=(0,0,0,255))

    date_start_dt = datetime.strptime(date_start, "%Y-%m-%d") if date_start else None
    date_end_dt = datetime.strptime(date_end, "%Y-%m-%d") if date_end else None
    date_title = formater_periode(date_start_dt, date_end_dt)

    draw_centered_text_overlay(background, date_title, 1030*m, 860*m, v_date_title, fonts["date_title"],
                                fill=(253,197,5,255), stroke_width=0, stroke_fill=(0,0,0,255))

    print(f"{date_start_dt}  -  {date_end_dt} ==> {date_title}")

    reader = list(parse_csv_rows(saison,""))
    # reader1 = list(parse_csv_rows(saison,""))
    # reader2 = list(parse_csv_rows(saison,"QCM"))
    # reader = reader1 + reader2


    for row in reader:
        entity, match, date = row[0], row[2], row[3]
        hour = "" if row[4] == "00:00" else row[4]
        logo_a, team_a, logo_b, team_b = row[5], row[6], row[7], row[8]
        sets, score = row[9], row[10]
        place = row[12]
        cat_code = match[:3]

        if team_a == 'xxxxx':
            continue

        if date == 'Date':
            continue

        dt = datetime.strptime(date, "%Y-%m-%d")
        if date_start_dt and dt < date_start_dt: continue
        if date_end_dt and dt > date_end_dt: continue
        if categories_filter and cat_code not in categories_filter: continue
        # entities_str = list(settings.entities.keys())
        # if entity not in entities_str: continue
        print(f"{saison} | {cat_code}")
        cat_info = settings.get_season_config(saison, cat_code)
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

            if score:
                victory_color = "green" if result else "red" if result is False else "yellow"
                victory_text = "VICTOIRE" if result else "DÉFAITE" if result is False else "ÉGALITÉ"
            else:
                victory_text = "INCONNU"
                victory_color = "yellow"

            overlay = Image.open(BANNERS_DIR / f"result_{victory_color}.png").convert("RGBA")
            background.paste(overlay, (20*m, v), overlay)
        else:
            overlay = Image.open(BANNERS_DIR / "planning.png").convert("RGBA")
            background.paste(overlay, (20*m, v), overlay)

        # Debug console
        print(f"{format} | {cat_code} | {date_full} - {entity} - {match} - {category} - ({logo_a}) {team_a} - ({logo_b}) {team_b} - {sets} - {score} - {place}")
        print(f"==> {cat_info['label']} - {cat_info['genre']} - {cat_info['type']} - {cat_info['niveau']}")


        draw_centered_text_overlay(background, title_entity, 115*m, 95*m, v_entity, fonts["bold_15"], stroke_width=1, stroke_fill=(0,0,0,255))
        draw_centered_text_overlay(background, category, 115*m, 95*m, v_category, fonts["bold_15"], stroke_width=1, stroke_fill=(0,0,0,255))
        draw_centered_text_overlay(background, team_name, 115*m, 95*m, v_team_name, fonts["bold_15"], stroke_width=1, stroke_fill=(0,0,0,255))

        try:
            background = paste_image_fit_box(background, CLUBS_DIR / f"{logo_a}.png", 170*m, v_logo, 65*m, 65*m)
        except FileNotFoundError:
            background = paste_image_fit_box(background, CLUBS_DIR / "no_logo.png", 170*m, v_logo, 65*m, 65*m)

        team_a, team_font_size = get_team_pseudo(cat_info['label'], cat_info['genre'], cat_info['type'], cat_info['niveau'], team_a)
        draw_centered_text_overlay(background, team_a.replace("-", " "), 120*m, 310*m, v_team, fonts[team_font_size], fill=(0,0,0,255))

        try:
            background = paste_image_fit_box(background, CLUBS_DIR / f"{logo_b}.png", 425*m, v_logo, 65*m, 65*m)
        except FileNotFoundError:
            background = paste_image_fit_box(background, CLUBS_DIR / "no_logo.png", 425*m, v_logo, 65*m, 65*m)

        team_b, team_font_size = get_team_pseudo(cat_info['label'], cat_info['genre'], cat_info['type'], cat_info['niveau'], team_b)
        draw_centered_text_overlay(background, team_b.replace("-", " "), 120*m, 560*m, v_team, fonts[team_font_size], fill=(0,0,0,255))

        print(f"==> {team_a} - {team_b}")


        if mode == "results" and score:
            color = (0,109,57,255) if result else (167,46,59,255) if result is False else (245,159,10,255) 
            draw_centered_text_overlay(background, victory_text, 200*m, 705*m, v_victory, fonts["victory"], fill=color)

            sets_formatted = format_sets(sets)
            draw_centered_text_overlay(background, sets_formatted, 100*m, 828*m, v_sets, fonts["sets"], fill=(10,58,128,255))

            score_img = create_score_image(score)
            background.paste(score_img, (876*m, v_score))
        elif mode == "planning":
            draw_centered_text_overlay(background, date_full, 100*m, 705*m, v_date, fonts["bold_15"])
            result = get_gymnase_address(match, entity)
            place_nom = result["nom"] if result else ""
            place_adr = result["rue"] if result else "Adresse non trouvée"
            place_ville = result["ville"] if result else ""

            draw_centered_text_overlay(background, place_nom, 210*m, 882*m, v_place, fonts["bold_14"], stroke_width=1, stroke_fill=(0,0,0,255))
            draw_centered_text_overlay(background, place_adr, 210*m, 882*m, v_place + 40, fonts["bold_12"], stroke_width=1, stroke_fill=(0,0,0,255))
            draw_centered_text_overlay(background, place_ville, 210*m, 882*m, v_place + 80, fonts["bold_15"], stroke_width=1, stroke_fill=(0,0,0,255))

            place_type = "int" if _norm(place) in INDOOR_GYMS else "ext"
            overlay = Image.open(ICONS_DIR / f"{place_type}.png").convert("RGBA").resize((40*m, 40*m))
            background.paste(overlay, (995*m, v_place_type), overlay)

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
