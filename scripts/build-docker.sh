#!/bin/bash
# Script de build Docker pour Comm'Generator

set -e

VERSION=${1:-latest}
PLATFORM=${2:-linux/amd64}

echo "🐳 Build Docker de Comm'Generator"
echo "   Version: $VERSION"
echo "   Platform: $PLATFORM"
echo ""

# Build l'image
echo "🔨 Construction de l'image..."
docker build \
    --platform $PLATFORM \
    -t veec-comm-generator:$VERSION \
    -t veec-comm-generator:latest \
    .

echo ""
echo "✅ Image construite avec succès!"
echo ""
echo "📦 Images disponibles:"
docker images | grep veec-comm-generator

echo ""
echo "🚀 Pour lancer l'application:"
echo "   docker run -p 8000:8000 veec-comm-generator:$VERSION"
echo ""
echo "🐙 Ou avec docker-compose:"
echo "   docker-compose up -d"
