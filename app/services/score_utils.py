
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from app.core.colors import SCORE_WIN_BG, SCORE_WIN_FG, SCORE_LOSE_BG, SCORE_LOSE_FG

BASE_PATH = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_PATH / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"

def format_sets(sets):
    if not sets or '/' not in sets:
        return sets
    parts = sets.strip().split('/')
    if len(parts) == 2 and all(part.strip().isdigit() for part in parts):
        a, b = int(parts[0]), int(parts[1])
        return f"{a} - {b}"
    return sets

def did_team_a_win(sets: str) -> bool | None:
    """
    Détermine si l'équipe A a gagné basé sur le score des sets.

    :param sets: Score au format "X/Y" (ex: "3/1")
    :return: True si équipe A gagne, False si elle perd, None si égalité ou format invalide
    """
    if not sets or '/' not in sets:
        return None
    parts = sets.strip().split('/')
    if len(parts) == 2 and all(part.strip().isdigit() for part in parts):
        a, b = int(parts[0]), int(parts[1])
        if a == b:
            return None  # Égalité
        return a > b
    # Format invalide
    return None

def create_score_image(score):
    FONT_SIZE = 40
    OFFSET_Y = -5

    sets = []
    for s in score.split(','):
        try:
            a, b = map(int, s.strip().split('-'))
            sets.append([a, b])
        except ValueError:
            continue

    set_count = len(sets)
    box_width, box_height = 61, 61
    padding, spacing = 6, 6
    width = set_count * (box_width + spacing) + padding * 2 - spacing
    height = box_height * 2 + padding * 3

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(FONTS_DIR / "OpenSans-ExtraBold.ttf", FONT_SIZE)
    ascent, descent = font.getmetrics()

    for i, (a, b) in enumerate(sets):
        x = padding + i * (box_width + spacing)
        y_top = padding
        y_bottom = y_top + box_height + padding

        bg_a, fg_a = (SCORE_WIN_BG, SCORE_WIN_FG) if a > b else (SCORE_LOSE_BG, SCORE_LOSE_FG)
        bg_b, fg_b = (SCORE_WIN_BG, SCORE_WIN_FG) if b > a else (SCORE_LOSE_BG, SCORE_LOSE_FG)

        a_text = str(a)
        a_width = draw.textlength(a_text, font=font)
        a_x = x + (box_width - a_width) / 2
        a_y = y_top + (box_height - ascent) / 2 + OFFSET_Y
        draw.rectangle([x, y_top, x + box_width, y_top + box_height], fill=bg_a)
        draw.text((a_x, a_y), a_text, fill=fg_a, font=font)

        b_text = str(b)
        b_width = draw.textlength(b_text, font=font)
        b_x = x + (box_width - b_width) / 2
        b_y = y_bottom + (box_height - ascent) / 2 + OFFSET_Y
        draw.rectangle([x, y_bottom, x + box_width, y_bottom + box_height], fill=bg_b)
        draw.text((b_x, b_y), b_text, fill=fg_b, font=font)

    return image
