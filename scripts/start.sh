#!/bin/bash
# Script de démarrage de l'application Comm'Generator

set -e

echo "🚀 Démarrage de Comm'Generator..."

# Vérifier si .env existe
if [ ! -f ".env" ]; then
    echo "⚠️  Fichier .env non trouvé"
    echo "📝 Création depuis .env.example..."
    cp .env.example .env
    echo "✅ Fichier .env créé. Vous pouvez le modifier selon vos besoins."
fi

# Charger les variables d'environnement
export $(cat .env | grep -v '^#' | xargs)

# Démarrer l'application
echo "🎬 Lancement de l'application sur http://${HOST:-0.0.0.0}:${PORT:-8000}"
python run.py
