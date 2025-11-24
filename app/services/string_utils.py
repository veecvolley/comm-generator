import unicodedata
import re
from datetime import datetime
from app.core.constants import jours, mois

def _norm(s: str) -> str:
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().strip().upper()


def get_team_pseudo(label, genre, type, niveau, team, titre):
    """
    Fonction qui retourne une valeur dépendant de la combinaison de cinq variables d'entrée.

    :param label: première variable
    :param genre: deuxième variable
    :param type: troisième variable
    :param niveau: quatrième variable
    :param team: cinquième variable
    :return: une valeur résultante selon la combinaison
    """

    res = re.search(r'\b(\d+)\s*$', team)
    num = int(res.group(1)) if res else 1

    detected = bool(re.search(r"fs val d'europe esbly coupvray", team, re.IGNORECASE))

    print(f"{team} ==================> {detected}")

    if detected:

        if label == "SVA" and type == "Volley-Assis":
           
            pseudo = "SVA"
            font_size = "bold_25"

        elif label == "SF" and genre == "Féminin" and type == "Volley-Ball" and niveau == "Championnat Régional":

            pseudo = f"SF{ num }"
            font_size = "bold_25"

        elif label == "SM" and genre == "Masculin" and type == "Volley-Ball" and niveau == "Championnat Régional":

            pseudo = f"SM{ num }"
            font_size = "bold_25"

        elif label == "SF" and genre == "Féminin" and type == "Volley-Ball" and niveau == "Championnat Départemental":

            pseudo = f"SF{ num }"
            font_size = "bold_25"

        elif label == "SM" and genre == "Masculin" and type == "Volley-Ball" and niveau == "Championnat Départemental":

            pseudo = f"SM{ num }"
            font_size = "bold_25"

        # elif label == "M15G" and genre == "Masculin" and type == "Volley-Ball" and niveau == "Championnat Régional":

        #     pseudo = "M15G-1"
        #     font_size = "bold_25"

        elif label == "M15G" and genre == "Masculin" and type == "Volley-Ball" and niveau == "Championnat Départemental":

            pseudo = "M15G"
            font_size = "bold_25"

        elif label == "M15F" and genre == "Féminin" and type == "Volley-Ball" and niveau == "Championnat Régional":

            pseudo = "M15F-1"
            font_size = "bold_25"

        elif label == "M15F" and genre == "Féminin" and type == "Volley-Ball" and niveau == "Championnat Départemental":

            pseudo = "M15F-2"
            font_size = "bold_25"

        elif label == "M18G" and genre == "Masculin" and type == "Volley-Ball" and niveau == "Championnat Régional":

            pseudo = "M18G-1"
            font_size = "bold_25"

        elif label == "M18G" and genre == "Masculin" and type == "Volley-Ball" and niveau == "Qualifications Régionales":

            pseudo = "M18G-1"
            font_size = "bold_25"

        elif label == "M18G" and genre == "Masculin" and type == "Volley-Ball" and niveau == "Championnat Départemental":

            pseudo = "M18G-2"
            font_size = "bold_25"

        elif label == "M18F" and genre == "Féminin" and type == "Volley-Ball" and titre == "[J] M18 FEMININ 6x6 - Ph1 - Poule B":

            pseudo = "M18F-1"
            font_size = "bold_25"

        elif label == "M18F" and genre == "Féminin" and type == "Volley-Ball" and titre == "[J] M18 FEMININ 6x6 - Ph1 - Poule C":

            pseudo = "M18F-2"
            font_size = "bold_25"

        elif label == "M13G" and genre == "Masculin" and type == "Volley-Ball" and niveau == "Championnat Départemental":

            pseudo = "M13G-2"
            font_size = "bold_25"

        elif label == "M13G" and genre == "Masculin" and type == "Volley-Ball" and niveau == "Championnat Régional":

            pseudo = "M13G-1"
            font_size = "bold_25"

        elif label == "M13F" and genre == "Féminin" and type == "Volley-Ball":

            pseudo = label
            font_size = "bold_25"

        else:
            pseudo = team
            font_size = "bold_15"

    else:
      pseudo = team
      font_size = "bold_15"

    return pseudo, font_size


def formater_periode(date_start_dt: str, date_end_dt: str) -> str:
    """
    Formate deux dates en texte français.
    Exemple : "2025-10-18 00:00:00" et "2025-10-19 00:00:00"
              -> "18 et 19 octobre 2025"
    """

    d1 = date_start_dt
    d2 = date_end_dt

    # Récupération des noms de mois en français via ta constante
    mois_d1 = mois[d1.strftime("%B")]
    mois_d2 = mois[d2.strftime("%B")]

    # Si même mois et même année
    if d1.month == d2.month and d1.year == d2.year:
        date_label = f"{d1.day} et {d2.day} {mois_d1} {d1.year}"

    # Si mois ou année différents
    else:
        date_label = f"{d1.day} {mois_d1} {d1.year} au {d2.day} {mois_d2} {d2.year}"

    return date_label