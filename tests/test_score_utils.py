"""Tests unitaires pour score_utils."""

import pytest
from app.services.score_utils import format_sets, did_team_a_win


class TestFormatSets:
    """Tests pour la fonction format_sets."""

    @pytest.mark.unit
    def test_format_sets_valid(self):
        """Test formatage valide des sets."""
        assert format_sets("3/1") == "3 - 1"
        assert format_sets("2/3") == "2 - 3"
        assert format_sets("0/3") == "0 - 3"

    @pytest.mark.unit
    def test_format_sets_with_spaces(self):
        """Test formatage avec espaces."""
        assert format_sets(" 3 / 1 ") == "3 - 1"
        assert format_sets("  2  /  3  ") == "2 - 3"

    @pytest.mark.unit
    def test_format_sets_invalid(self):
        """Test formatage invalide."""
        assert format_sets("invalid") == "invalid"
        assert format_sets("3-1") == "3-1"
        assert format_sets("") == ""
        assert format_sets(None) is None

    @pytest.mark.unit
    def test_format_sets_non_numeric(self):
        """Test formatage avec caractères non numériques."""
        assert format_sets("a/b") == "a/b"
        assert format_sets("3/x") == "3/x"


class TestDidTeamAWin:
    """Tests pour la fonction did_team_a_win."""

    @pytest.mark.unit
    def test_team_a_wins(self):
        """Test quand l'équipe A gagne."""
        assert did_team_a_win("3/1") is True
        assert did_team_a_win("3/0") is True
        assert did_team_a_win("3/2") is True

    @pytest.mark.unit
    def test_team_a_loses(self):
        """Test quand l'équipe A perd."""
        assert did_team_a_win("1/3") is False
        assert did_team_a_win("0/3") is False
        assert did_team_a_win("2/3") is False

    @pytest.mark.unit
    def test_draw(self):
        """Test en cas d'égalité."""
        assert did_team_a_win("2/2") is None
        assert did_team_a_win("1/1") is None
        assert did_team_a_win("0/0") is None

    @pytest.mark.unit
    def test_invalid_format(self):
        """Test avec format invalide."""
        assert did_team_a_win("") is None
        assert did_team_a_win("invalid") is None
        assert did_team_a_win("3-1") is None
        assert did_team_a_win("a/b") is None

    @pytest.mark.unit
    def test_with_spaces(self):
        """Test avec espaces."""
        assert did_team_a_win(" 3 / 1 ") is True
        assert did_team_a_win("  1  /  3  ") is False
        assert did_team_a_win(" 2 / 2 ") is None
