
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

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

def did_team_a_win(sets):
    if not sets or '/' not in sets:
        return None
    parts = sets.strip().split('/')
    if len(parts) == 2 and all(part.strip().isdigit() for part in parts):
        a, b = int(parts[0]), int(parts[1])
        if a == b:
            return None  # Égalité
        return a > b
    return a < b

def create_score_image(score):
    FONT_SIZE = 40
    OFFSET_Y = -5
    COLOR_WIN_BG = (253, 197, 5)
    COLOR_WIN_FG = (87, 87, 87)
    COLOR_LOSE_BG = (38, 38, 38)
    COLOR_LOSE_FG = (255, 255, 255)

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

        bg_a, fg_a = (COLOR_WIN_BG, COLOR_WIN_FG) if a > b else (COLOR_LOSE_BG, COLOR_LOSE_FG)
        bg_b, fg_b = (COLOR_WIN_BG, COLOR_WIN_FG) if b > a else (COLOR_LOSE_BG, COLOR_LOSE_FG)

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
