"""Tests unitaires pour string_utils."""

import pytest
from app.services.string_utils import _norm, get_team_pseudo, formater_periode
from datetime import datetime


class TestNorm:
    """Tests pour la fonction _norm."""

    @pytest.mark.unit
    def test_norm_basic(self):
        """Test normalisation basique."""
        assert _norm("hello") == "HELLO"
        assert _norm("Hello World") == "HELLO WORLD"

    @pytest.mark.unit
    def test_norm_accents(self):
        """Test normalisation avec accents."""
        assert _norm("Été") == "ETE"
        assert _norm("Café") == "CAFE"
        assert _norm("Noël") == "NOEL"

    @pytest.mark.unit
    def test_norm_special_chars(self):
        """Test normalisation avec caractères spéciaux."""
        assert _norm("Val d'Europe") == "VAL D'EUROPE"
        assert _norm("Saint-Étienne") == "SAINT-ETIENNE"

    @pytest.mark.unit
    def test_norm_empty(self):
        """Test normalisation avec chaîne vide."""
        assert _norm("") == ""
        assert _norm(None) == ""

    @pytest.mark.unit
    def test_norm_whitespace(self):
        """Test normalisation avec espaces."""
        assert _norm("  hello  ") == "HELLO"
        assert _norm("\t\n hello \t\n") == "HELLO"


class TestGetTeamPseudo:
    """Tests pour la fonction get_team_pseudo."""

    @pytest.mark.unit
    def test_sva_volley_assis(self):
        """Test pour SVA Volley-Assis."""
        pseudo, font = get_team_pseudo(
            "SVA", "Mixte", "Volley-Assis", "",
            "FS VAL D'EUROPE ESBLY COUPVRAY", ""
        )
        assert pseudo == "SVA"
        assert font == "bold_25"

    @pytest.mark.unit
    def test_sf_regional_with_number(self):
        """Test pour SF avec numéro d'équipe."""
        pseudo, font = get_team_pseudo(
            "SF", "Féminin", "Volley-Ball", "Championnat Régional",
            "FS VAL D'EUROPE ESBLY COUPVRAY 2", ""
        )
        assert "SF" in pseudo
        assert "2" in pseudo
        assert font == "bold_25"

    @pytest.mark.unit
    def test_m15f_regional(self):
        """Test pour M15F Championnat Régional."""
        pseudo, font = get_team_pseudo(
            "M15F", "Féminin", "Volley-Ball", "Championnat Régional",
            "FS VAL D'EUROPE ESBLY COUPVRAY", ""
        )
        assert pseudo == "M15F-1"
        assert font == "bold_25"

    @pytest.mark.unit
    def test_m15f_departemental(self):
        """Test pour M15F Championnat Départemental."""
        pseudo, font = get_team_pseudo(
            "M15F", "Féminin", "Volley-Ball", "Championnat Départemental",
            "FS VAL D'EUROPE ESBLY COUPVRAY", ""
        )
        assert pseudo == "M15F-2"
        assert font == "bold_25"

    @pytest.mark.unit
    def test_m18f_with_titre(self):
        """Test pour M18F avec titre spécifique."""
        pseudo, font = get_team_pseudo(
            "M18F", "Féminin", "Volley-Ball", "",
            "FS VAL D'EUROPE ESBLY COUPVRAY",
            "[J] M18 FEMININ 6x6 - Ph1 - Poule B"
        )
        assert pseudo == "M18F-2"
        assert font == "bold_25"

    @pytest.mark.unit
    def test_undetected_team(self):
        """Test pour équipe non détectée."""
        pseudo, font = get_team_pseudo(
            "SF", "Féminin", "Volley-Ball", "Championnat Régional",
            "Autre Club Volley", ""
        )
        assert pseudo == "Autre Club Volley"
        assert font == "bold_15"

    @pytest.mark.unit
    def test_cache_loading(self):
        """Test que le cache YAML fonctionne."""
        # Premier appel charge le cache
        pseudo1, _ = get_team_pseudo(
            "SVA", "Mixte", "Volley-Assis", "",
            "FS VAL D'EUROPE ESBLY COUPVRAY", ""
        )
        # Deuxième appel utilise le cache
        pseudo2, _ = get_team_pseudo(
            "SVA", "Mixte", "Volley-Assis", "",
            "FS VAL D'EUROPE ESBLY COUPVRAY", ""
        )
        assert pseudo1 == pseudo2 == "SVA"


class TestFormaterPeriode:
    """Tests pour la fonction formater_periode."""

    @pytest.mark.unit
    def test_same_month_same_year(self):
        """Test période dans le même mois."""
        d1 = datetime(2025, 1, 18)
        d2 = datetime(2025, 1, 19)
        result = formater_periode(d1, d2)
        assert "18 et 19" in result
        assert "janvier" in result
        assert "2025" in result

    @pytest.mark.unit
    def test_different_months_same_year(self):
        """Test période sur des mois différents."""
        d1 = datetime(2025, 1, 30)
        d2 = datetime(2025, 2, 2)
        result = formater_periode(d1, d2)
        assert "30 janvier" in result
        assert "2 février" in result
        assert "2025" in result

    @pytest.mark.unit
    def test_different_years(self):
        """Test période sur des années différentes."""
        d1 = datetime(2024, 12, 30)
        d2 = datetime(2025, 1, 2)
        result = formater_periode(d1, d2)
        assert "30 décembre 2024" in result
        assert "2 janvier 2025" in result
