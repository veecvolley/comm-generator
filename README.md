# VEEC Comm'Generator

[![Release](https://img.shields.io/github/v/release/veecvolley/FFVB-Parser)](https://github.com/veecvolley/FFVB-Parser)
[![Python Version](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/release/python-3130/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-35%2B%20passing-brightgreen.svg)](tests/)

Générateur d'images de communication pour les matchs de volley-ball, basé sur les données de la FFVB.

---

## Fonctionnalités

- **Génération PNG** — Création automatique d'images de communication (publication ou story)
- **Planning** — Affichage des matchs à venir avec détails équipes et gymnases
- **Résultats** — Visualisation des résultats avec scores et sets
- **Données FFVB** — Synchronisation directe avec la fédération (CSV + PDF)
- **Interface admin** — Gestion complète de la configuration via `/admin/`
- **Base de données SQLite** — Configuration et données persistantes, gérées sans YAML
- **Cache intelligent** — Réutilisation des images générées (50–500× plus rapide)
- **Génération asynchrone** — Plusieurs requêtes traitées en parallèle
- **Templates configurables** — Backgrounds, banners, fonts, offsets par template
- **Docker** — Déploiement containerisé prêt pour production

---

## Démarrage rapide

### Option 1 : Docker (recommandé)

```bash
# 1. Cloner le repository
git clone https://github.com/veecvolley/comm-generator.git
cd comm-generator

# 2. Lancer avec Docker Compose
docker-compose up -d

# 3. Accéder à l'application
open http://localhost:8000
```

### Option 2 : Installation locale

```bash
# 1. Prérequis : Python 3.13+
pip install -r requirements.txt

# 2. Configuration
cp .env.example .env
# Éditer .env si nécessaire

# 3. Démarrage
./scripts/start.sh
# Ou : python run.py
```

Au premier démarrage, la base SQLite est créée automatiquement et alimentée depuis les fichiers YAML (`config.yaml`, `saisons.yaml`, `team_rules.yaml`, `templates.yaml`).

---

## Configuration

### Variables d'environnement (`.env`)

```bash
# Logging
LOG_LEVEL=INFO          # DEBUG | INFO | WARNING | ERROR

# Cache images
CACHE_DIR=/tmp/comm_generator_cache
CACHE_EXPIRY_MINUTES=60

# Serveur
HOST=0.0.0.0
PORT=8000
RELOAD=false            # true pour hot-reload en dev
```

### Configuration applicative

Toute la configuration est gérée via l'interface `/admin/` et stockée en base SQLite :

- **Club** : nom, identifiant FFVB, URLs de sync
- **Saisons & Catégories** : avec éditeur inline et référentiel Label/Type/Genre/Niveau
- **Règles d'équipes** : ordre de priorité pour le rendu des noms
- **Templates** : backgrounds, banners, fonts, offsets — avec upload PNG intégré

Les fichiers YAML (`config.yaml`, `saisons.yaml`, `team_rules.yaml`, `templates.yaml`) servent uniquement de seed initial et ne sont plus relus après le premier démarrage.

---

## Interface admin

Accessible via `/admin/` :

| Section | Description |
|---|---|
| **Dashboard** | Vue d'ensemble : nb matchs, dernière sync, nb catégories |
| **Configuration** | Paramètres club, URLs FFVB, gymnases, saisons, référentiel |
| **Saisons & Catégories** | Édition inline avec dropdowns, filtre texte, sync FFVB |
| **Règles d'équipes** | Gestion des pseudonymes et tailles de police par équipe |
| **Templates** | Création, édition clé/valeur, upload PNG, aperçu miniature |
| **Données FFVB** | Tableau des matchs avec filtres, tri colonnes, sync manuelle |

---

## API

### Health check
```
GET /health
→ {"status": "healthy", "version": "...", "service": "comm-generator"}
```

### Génération d'image
```
GET /image
```

| Paramètre | Type | Défaut | Description |
|---|---|---|---|
| `saison` | string | `2025/2026` | Saison au format YYYY/YYYY |
| `mode` | string | `planning` | `planning` ou `results` |
| `title` | string | `Matchs` | Titre affiché sur l'image |
| `format` | string | `pub` | `pub` (carré) ou `story` (vertical) |
| `template` | string | — | Nom du template (défaut si absent) |
| `categories` | array | — | Codes de catégories à inclure |
| `date_start` | string | — | Date début `YYYY-MM-DD` |
| `date_end` | string | — | Date fin `YYYY-MM-DD` |
| `use_cache` | bool | `true` | Désactiver pour forcer la régénération |

```bash
# Planning du week-end
curl "http://localhost:8000/image?mode=planning&date_start=2025-01-10&date_end=2025-01-12" -o planning.png

# Résultats catégories spécifiques
curl "http://localhost:8000/image?mode=results&categories=SF1&categories=SM1" -o results.png
```

### Catégories disponibles
```
GET /categories?saison=2025/2026
```

### Gestion du cache
```
POST /cache/clear               → vide tout le cache
POST /cache/clear?expired_only=true  → supprime uniquement les fichiers expirés
```

### Sync FFVB (depuis l'app principale)
```
POST /sync-ffvb[?saison=2025/2026]
→ {"inserted": N, "updated": N, "errors": [], "last_sync": "dd/mm/yyyy HH:MM"}
```

### Mise à jour de la configuration
```
POST /update-config
```

La documentation OpenAPI interactive est disponible sur `/docs`.

---

## Docker

### Build

```bash
# Build simple
docker build -t veec-comm-generator:latest .

# Avec le script
./scripts/build-docker.sh v1.0.0
```

### Run

```bash
# Simple
docker run -p 8000:8000 veec-comm-generator:latest

# Avec volumes (persistance DB et config)
docker run -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  veec-comm-generator:latest
```

### Docker Compose

```bash
docker-compose up -d          # Production
docker-compose logs -f        # Logs en temps réel
docker-compose down           # Arrêt
docker-compose up -d --build  # Rebuild + redémarrage
```

Le fichier `docker-compose.yml` inclut un health check, la persistance du cache et de la base SQLite via volumes.

---

## Tests

```bash
# Tous les tests
pytest

# Avec coverage
pytest --cov=app --cov-report=html

# Script dédié
./scripts/test.sh

# Tests ciblés
pytest tests/test_string_utils.py -v
pytest tests/test_score_utils.py -v
pytest -m unit
pytest -m integration
```

**Couverture actuelle :** 35+ tests, 70%+ coverage.

---

## Architecture

```
comm-generator/
├── app/
│   ├── api/
│   │   ├── routes.py          # App principale (/, /image, /categories, /sync-ffvb)
│   │   └── admin.py           # Interface admin (/admin/*)
│   ├── core/
│   │   ├── cache.py           # Cache images PNG (MD5 des paramètres)
│   │   ├── colors.py          # Constantes de couleurs
│   │   ├── config.py          # Configuration (lit depuis DB)
│   │   ├── image_templates.py # Chargement des templates depuis DB
│   │   ├── logger.py          # Logging centralisé
│   │   └── templates.py       # Jinja2
│   ├── db/
│   │   ├── database.py        # Engine SQLAlchemy, session factory
│   │   ├── models.py          # Modèles ORM (templates, catégories, matchs, règles…)
│   │   ├── seed.py            # Migration initiale depuis les YAML
│   │   └── crud/              # CRUD par domaine (config, seasons, rules, templates, ffvb)
│   ├── models/
│   │   └── requests.py        # Modèles Pydantic pour la validation des entrées
│   ├── services/
│   │   ├── data_provider.py   # Fetch CSV/PDF FFVB + cache HTTP
│   │   ├── image_gen.py       # Composition des images (Pillow)
│   │   ├── score_utils.py     # Parsing et formatage des scores
│   │   ├── string_utils.py    # Règles de nommage des équipes
│   │   └── sync.py            # Synchronisation FFVB → DB
│   ├── assets/                # PNG : backgrounds, banners, clubs, fonts, icons
│   ├── static/                # CSS, JS, images statiques
│   ├── templates/             # Jinja2 : index.html + admin/
│   └── main.py                # Point d'entrée FastAPI, montage static/assets
├── data/                      # Base SQLite (gitignorée)
├── tests/                     # Tests unitaires et d'intégration
├── scripts/                   # start.sh, test.sh, build-docker.sh
├── config.yaml                # Seed initial (club, URLs FFVB)
├── saisons.yaml               # Seed initial (saisons, catégories)
├── team_rules.yaml            # Seed initial (règles équipes)
├── templates.yaml             # Seed initial (templates images)
├── Dockerfile
├── docker-compose.yml
├── pytest.ini
├── requirements.txt
└── run.py
```

---

## Développement

```bash
# Créer un virtualenv
python -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Configurer
cp .env.example .env
# LOG_LEVEL=DEBUG, RELOAD=true

# Lancer en mode dev
python run.py
```

### Ajouter une règle d'équipe

Via l'interface `/admin/team-rules/`, ou directement dans `team_rules.yaml` avant le premier démarrage :

```yaml
- match:
    label: "M20F"
    genre: "Féminin"
    type: "Volley-Ball"
  result:
    pseudo: "M20F"
    font_size: "bold_25"
```

### Ajouter un template

Via `/admin/templates/new` — l'interface permet de saisir backgrounds, banners, fonts et offsets en clé/valeur, avec upload PNG et aperçu intégré.

---

## Performance

| Scénario | Sans cache | Avec cache | Gain |
|---|---|---|---|
| 1re génération | 2–5 s | 2–5 s | — |
| 2e requête identique | 2–5 s | 10–50 ms | **50–500×** |
| 5 requêtes parallèles | 25 s | ~5–8 s | **3–5×** |

---

## Support

- Issues : [GitHub Issues](https://github.com/veecvolley/comm-generator/issues)
- Documentation API interactive : `http://localhost:8000/docs`

---

## License

MIT License — voir [LICENSE](LICENSE) pour plus de détails.

---

**Développé avec ❤️ par VEEC Volley**
