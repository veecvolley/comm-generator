"""Constantes de couleurs utilisées dans l'application."""

from typing import Tuple

# Type alias pour les couleurs RGBA
Color = Tuple[int, int, int, int]

# Couleurs de texte
TEXT_TITLE_GRAY: Color = (66, 66, 66, 255)
TEXT_DATE_YELLOW: Color = (253, 197, 5, 255)
TEXT_BLACK: Color = (0, 0, 0, 255)
TEXT_WHITE: Color = (255, 255, 255)

# Couleurs de victoire/défaite
VICTORY_GREEN: Color = (0, 109, 57, 255)
DEFEAT_RED: Color = (167, 46, 59, 255)
DRAW_YELLOW: Color = (245, 159, 10, 255)

# Couleurs pour les scores
SCORE_WIN_BG: Color = (253, 197, 5)  # RGB seulement (sans alpha)
SCORE_WIN_FG: Color = (87, 87, 87)
SCORE_LOSE_BG: Color = (38, 38, 38)
SCORE_LOSE_FG: Color = (255, 255, 255)

# Couleurs de fond/bordure
STROKE_BLACK: Color = (0, 0, 0, 255)
BACKGROUND_WHITE: Color = (255, 255, 255, 255)

# Mapping des couleurs de bannières de résultat
RESULT_BANNER_COLORS = {
    "victory": "green",
    "defeat": "red",
    "draw": "yellow",
    "unknown": "yellow"
}
