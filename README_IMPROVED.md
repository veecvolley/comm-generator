# VEEC Comm'Generator 🏐

[![Release](https://img.shields.io/github/v/release/veecvolley/FFVB-Parser)](https://github.com/veecvolley/FFVB-Parser)
[![Python Version](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/release/python-3130/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-35%2B%20passing-brightgreen.svg)](tests/)

Générateur d'images de communication professionnelles pour les matchs de volley-ball, basé sur les données de la FFVB.

![Comm'Generator Screenshot](screenshot.png)

---

## ✨ Fonctionnalités

- 📱 **Génération PNG** - Création automatique d'images de communication
- 📅 **Planning** - Affichage des matchs à venir avec détails
- 🏆 **Résultats** - Visualisation des résultats avec scores
- 🗄️ **Données live** - Synchronisation directe avec la FFVB
- ⚡ **Performance** - Cache intelligent (50-500x plus rapide)
- 🔄 **Async** - Génération asynchrone pour haute disponibilité
- 🧪 **Tests** - 35+ tests automatisés avec 70%+ coverage
- 📊 **Monitoring** - Health check et logs structurés
- 🐳 **Docker** - Déploiement containerisé prêt pour production

---

## 🚀 Démarrage rapide

### Option 1: Docker (Recommandé)

```bash
# 1. Cloner le repository
git clone https://github.com/veecvolley/comm-generator.git
cd comm-generator

# 2. Lancer avec Docker Compose
docker-compose up -d

# 3. Accéder à l'application
open http://localhost:8000
```

### Option 2: Installation locale

```bash
# 1. Prérequis
python >= 3.13
pip

# 2. Installation
pip install -r requirements.txt

# 3. Configuration
cp .env.example .env
# Éditer .env selon vos besoins

# 4. Démarrage
./scripts/start.sh
# Ou: python run.py
```

---

## 📖 Documentation

### Configuration

Toute la configuration se fait via le fichier `.env`:

```bash
# Logging
LOG_LEVEL=INFO                  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Cache
CACHE_DIR=/tmp/comm_generator_cache
CACHE_EXPIRY_MINUTES=60        # Durée de vie du cache en minutes

# Serveur
HOST=0.0.0.0
PORT=8000
RELOAD=false                    # true pour hot-reload en dev
```

### Fichiers de configuration

- `config.yaml` - Configuration générale (club, FFVB URLs)
- `saisons.yaml` - Données des saisons et catégories
- `team_rules.yaml` - Règles de pseudonymes des équipes

---

## 🔌 API Endpoints

### Health Check
```bash
GET /health
```
Retourne l'état de santé de l'application.

**Réponse:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "service": "comm-generator"
}
```

### Génération d'image
```bash
GET /image
```

**Paramètres:**
- `saison` (string): Saison au format YYYY/YYYY (défaut: 2025/2026)
- `mode` (string): planning ou results (défaut: planning)
- `title` (string): Titre de l'image (défaut: "Matchs")
- `format` (string): pub ou story (défaut: pub)
- `categories` (array): Filtrage par catégories (optionnel)
- `date_start` (string): Date de début YYYY-MM-DD (optionnel)
- `date_end` (string): Date de fin YYYY-MM-DD (optionnel)
- `use_cache` (boolean): Utiliser le cache (défaut: true)

**Exemples:**
```bash
# Image de planning pour le week-end
curl "http://localhost:8000/image?saison=2025/2026&mode=planning&date_start=2025-01-10&date_end=2025-01-12" --output planning.png

# Résultats avec catégories spécifiques
curl "http://localhost:8000/image?mode=results&categories=SF1&categories=SM1" --output results.png

# Sans cache (force la régénération)
curl "http://localhost:8000/image?use_cache=false" --output fresh.png
```

### Catégories
```bash
GET /categories?saison=2025/2026
```
Liste les catégories disponibles pour une saison.

### Gestion du cache
```bash
# Nettoyer les fichiers expirés
POST /cache/clear?expired_only=true

# Nettoyer tout le cache
POST /cache/clear
```

**Réponse:**
```json
{
  "message": "Cache nettoyé avec succès",
  "deleted_files": 15
}
```

---

## 🐳 Docker

### Build

```bash
# Build simple
docker build -t veec-comm-generator:latest .

# Ou avec le script
./scripts/build-docker.sh v1.0.0
```

### Run

```bash
# Run simple
docker run -p 8000:8000 veec-comm-generator:latest

# Avec volumes pour configuration
docker run -p 8000:8000 \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  -v $(pwd)/saisons.yaml:/app/saisons.yaml:ro \
  veec-comm-generator:latest
```

### Docker Compose

```bash
# Production
docker-compose up -d

# Development (avec hot-reload)
docker-compose --profile dev up -d

# Voir les logs
docker-compose logs -f

# Arrêter
docker-compose down
```

---

## 🧪 Tests

```bash
# Lancer tous les tests
pytest

# Tests avec coverage
pytest --cov=app --cov-report=html

# Ou avec le script
./scripts/test.sh

# Tests spécifiques
pytest tests/test_string_utils.py -v
pytest -k "test_cache" -v

# Tests par marker
pytest -m unit          # Tests unitaires uniquement
pytest -m integration   # Tests d'intégration uniquement
```

**Statistiques des tests:**
- ✅ 35+ tests
- ✅ 70%+ coverage
- ✅ Tests unitaires + intégration
- ✅ CI/CD ready

---

## 📊 Performance

### Cache

Le système de cache améliore drastiquement les performances:

| Scénario | Sans cache | Avec cache | Gain |
|----------|------------|------------|------|
| 1ère requête | 2-5 sec | 2-5 sec | - |
| 2ème requête identique | 2-5 sec | 10-50 ms | **50-500x** |
| 10 requêtes | 20-50 sec | 2-5 sec | **4-10x** |

### Async

La génération asynchrone permet de traiter plusieurs requêtes simultanément:

| Scénario | Synchrone | Asynchrone | Gain |
|----------|-----------|------------|------|
| 1 requête | 5 sec | 5 sec | - |
| 5 requêtes parallèles | 25 sec | ~5-8 sec | **3-5x** |

---

## 🛠️ Architecture

```
comm-generator/
├── app/
│   ├── api/              # Routes FastAPI
│   │   └── routes.py
│   ├── core/             # Configuration et utilitaires
│   │   ├── cache.py      # Système de cache
│   │   ├── colors.py     # Constantes de couleurs
│   │   ├── config.py     # Configuration
│   │   ├── logger.py     # Logging
│   │   └── templates.py
│   ├── models/           # Modèles Pydantic
│   │   └── requests.py
│   ├── services/         # Logique métier
│   │   ├── data_provider.py
│   │   ├── image_gen.py
│   │   ├── score_utils.py
│   │   └── string_utils.py
│   ├── assets/           # Ressources (logos, fonts)
│   └── main.py           # Point d'entrée FastAPI
├── tests/                # Tests automatisés
├── scripts/              # Scripts utilitaires
├── config.yaml           # Configuration club
├── saisons.yaml          # Données saisons
├── team_rules.yaml       # Règles équipes
├── Dockerfile            # Image Docker optimisée
├── docker-compose.yml    # Orchestration
├── pytest.ini            # Configuration tests
├── requirements.txt      # Dépendances Python
└── run.py               # Point d'entrée application
```

---

## 🔧 Développement

### Prérequis
- Python 3.13+
- pip
- Docker (optionnel)

### Setup environnement de dev

```bash
# 1. Créer un virtualenv
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Configurer
cp .env.example .env
# Éditer .env: LOG_LEVEL=DEBUG, RELOAD=true

# 4. Lancer en mode dev
python run.py
# Ou: uvicorn run:app --reload
```

### Ajouter une nouvelle équipe

Éditer `team_rules.yaml`:

```yaml
- match:
    label: "M20F"
    genre: "Féminin"
    type: "Volley-Ball"
  result:
    pseudo: "M20F"
    font_size: "bold_25"
```

Redémarrer → fonctionne immédiatement!

### Contribuer

1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

**Guidelines:**
- ✅ Écrire des tests pour toute nouvelle fonctionnalité
- ✅ Suivre PEP 8
- ✅ Ajouter des types hints
- ✅ Documenter les fonctions publiques
- ✅ Coverage > 70%

---

## 📝 Changelog

Voir [CHANGELOG_IMPROVEMENTS.md](CHANGELOG_IMPROVEMENTS.md) et [CHANGELOG_IMPROVEMENTS_PHASE2.md](CHANGELOG_IMPROVEMENTS_PHASE2.md) pour l'historique détaillé.

### Dernières améliorations

**Phase 2 (2026-01-09):**
- ✅ Tests automatisés (35+ tests, 70%+ coverage)
- ✅ Health check endpoint
- ✅ Cache des images (50-500x gain)
- ✅ Génération asynchrone (2-5x gain)
- ✅ Configuration environnement (.env)
- ✅ Docker optimisé (multi-stage)
- ✅ Scripts utilitaires

**Phase 1:**
- ✅ Refactoring get_team_pseudo → YAML
- ✅ Logging professionnel
- ✅ Types hints complets
- ✅ Validation Pydantic
- ✅ Gestion d'erreurs centralisée

---

## 🤝 Support

- 📧 Email: contact@veec-volley.fr
- 🐛 Issues: [GitHub Issues](https://github.com/veecvolley/comm-generator/issues)
- 📖 Documentation complète: [Wiki](https://github.com/veecvolley/comm-generator/wiki)

---

## 📄 License

MIT License - Voir [LICENSE](LICENSE) pour plus de détails.

---

## 🙏 Remerciements

- FFVB pour les données
- Claude AI pour l'assistance au développement
- La communauté Python et FastAPI

---

**Développé avec ❤️ par VEEC Volley**
