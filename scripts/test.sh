#!/bin/bash
# Script de tests pour Comm'Generator

set -e

echo "🧪 Lancement des tests..."

# Vérifier que pytest est installé
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest n'est pas installé"
    echo "📦 Installation de pytest..."
    pip install -r requirements.txt
fi

# Lancer les tests
echo "▶️  Tests unitaires..."
pytest tests/ -v --tb=short

# Tests avec coverage
echo ""
echo "📊 Tests avec coverage..."
pytest --cov=app --cov-report=term-missing --cov-report=html

echo ""
echo "✅ Tests terminés!"
echo "📄 Rapport de coverage disponible dans htmlcov/index.html"
