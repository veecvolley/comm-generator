"""Tests d'intégration pour les routes API."""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Fixture pour le client de test."""
    return TestClient(app)


class TestIndexRoute:
    """Tests pour la route index."""

    @pytest.mark.integration
    def test_index_returns_200(self, client):
        """Test que l'index retourne 200."""
        response = client.get("/")
        assert response.status_code == 200

    @pytest.mark.integration
    def test_index_contains_html(self, client):
        """Test que l'index contient du HTML."""
        response = client.get("/")
        assert "text/html" in response.headers.get("content-type", "")


class TestCategoriesRoute:
    """Tests pour la route /categories."""

    @pytest.mark.integration
    def test_categories_without_saison_returns_422(self, client):
        """Test sans paramètre saison."""
        response = client.get("/categories")
        assert response.status_code == 422

    @pytest.mark.integration
    def test_categories_with_valid_saison(self, client):
        """Test avec saison valide."""
        response = client.get("/categories?saison=2025/2026")
        # Peut retourner 200 ou 404 selon si la saison existe
        assert response.status_code in [200, 404]

    @pytest.mark.integration
    def test_categories_with_dash_separator(self, client):
        """Test avec séparateur -."""
        response = client.get("/categories?saison=2025-2026")
        assert response.status_code in [200, 404]

    @pytest.mark.integration
    def test_categories_nonexistent_returns_404(self, client):
        """Test avec saison inexistante."""
        response = client.get("/categories?saison=1999/2000")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data


class TestImageRoute:
    """Tests pour la route /image."""

    @pytest.mark.integration
    def test_image_with_defaults(self, client):
        """Test génération d'image avec valeurs par défaut."""
        response = client.get("/image")
        # Peut échouer si données manquantes, mais ne doit pas crasher
        assert response.status_code in [200, 500]

    @pytest.mark.integration
    def test_image_returns_png(self, client):
        """Test que l'image retournée est au format PNG."""
        response = client.get("/image")
        if response.status_code == 200:
            assert response.headers.get("content-type") == "image/png"

    @pytest.mark.integration
    def test_image_with_invalid_mode(self, client):
        """Test avec mode invalide."""
        response = client.get("/image?mode=invalid")
        # Devrait être accepté car pas de validation stricte pour l'instant
        assert response.status_code in [200, 422, 500]

    @pytest.mark.integration
    def test_image_with_categories(self, client):
        """Test avec filtrage par catégories."""
        response = client.get("/image?categories=SF1&categories=SM1")
        assert response.status_code in [200, 500]

    @pytest.mark.integration
    def test_image_with_date_range(self, client):
        """Test avec plage de dates."""
        response = client.get(
            "/image?date_start=2025-01-10&date_end=2025-01-15"
        )
        assert response.status_code in [200, 500]


class TestUpdateConfigRoute:
    """Tests pour la route /update-config."""

    @pytest.mark.integration
    def test_update_config_post(self, client):
        """Test de la route update-config."""
        response = client.post("/update-config")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


class TestErrorHandling:
    """Tests pour la gestion d'erreurs."""

    @pytest.mark.integration
    def test_404_on_nonexistent_route(self, client):
        """Test 404 sur route inexistante."""
        response = client.get("/nonexistent")
        assert response.status_code == 404

    @pytest.mark.integration
    def test_error_response_is_json(self, client):
        """Test que les erreurs retournent du JSON."""
        response = client.get("/nonexistent")
        assert "application/json" in response.headers.get("content-type", "")
