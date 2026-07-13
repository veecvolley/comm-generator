# Changelog

Toutes les modifications notables du projet sont documentées dans ce fichier.

---

## [Unreleased] — 2026-07

### Ajouts
- Tableau des catégories dans l'app principale : colonnes Label, Type, Genre, Niveau, Titre avec filtre texte libre et sélection par case à cocher
- Bouton tout sélectionner / désélectionner sur le tableau des catégories
- Réagencement du layout principal : paramètres à gauche, catégories à droite (plus large), image en bas pleine largeur
- Bouton "Générer l'image" repositionné en haut, centré au-dessus des colonnes
- Champ "Type" (Planning / Résultats) converti en deux boutons radio visuels (btn-check)
- Bouton de synchronisation FFVB dans la navbar de l'app principale avec date/heure de dernière sync (heure Paris, `Europe/Paris`)
- Upload de fichiers PNG dans l'éditeur de templates (backgrounds, banners) avec toast de confirmation
- Aperçu miniature des images dans l'éditeur de templates, clic → lightbox plein écran
- Mount statique `/assets` pour servir les fichiers PNG uploadés
- Module de création de template dans l'admin (`/admin/templates/new`) basé sur le formulaire d'édition
- Filtre texte libre dans la section "Saisons & Catégories" de l'admin

### Corrections
- `NameError: pdfplumber not defined` dans `data_provider.py` : import manquant ajouté
- Heure de synchronisation affichée en UTC au lieu de l'heure de Paris : conversion `Europe/Paris` via `zoneinfo`

---

## [Phase 4] — 2026-06-13

### Migration SQLite + Interface Admin

#### Base de données
- Remplacement de l'ensemble de la configuration YAML par SQLite (SQLAlchemy 2.x ORM)
- Modèles : `AppSetting`, `Gymnase`, `ActiveSaison`, `CategoryConfig`, `TeamRule`, `TeamDetectionPattern`, `Template`, `TemplateFont`, `TemplateOffsetY`, `TemplateOffsetX`, `TemplateSize`, `Match`, `Club`, `GymnaseAddress`, `RefValue`
- Seed automatique au premier démarrage depuis les YAML existants
- Sync des catégories FFVB → DB avec upsert idempotent (`ON CONFLICT DO UPDATE`)

#### Interface admin (`/admin/`)
- **Dashboard** : stats matchs, dernière sync, nb catégories par saison
- **Configuration** : paramètres club, URLs FFVB, gymnases, saisons actives
- **Référentiel** : gestion des valeurs Label / Type / Genre / Niveau avec cascade vers CategoryConfig
- **Saisons & Catégories** : tri saisons desc, édition inline avec dropdowns alimentés par le référentiel
- **Règles d'équipes** : liste, création, suppression, réordonnancement
- **Templates** : liste avec édition inline du titre et de l'ID, édition clé/valeur (remplace JSON brut), sections Assets / Fonts / Offsets
- **Données FFVB** : tableau des matchs avec filtres saison/type/genre, tri colonnes, pagination

#### App principale
- Refactoring complet en Bootstrap 5 (remplacement de FontAwesome par Bootstrap Icons)
- Saisons pre-rendues côté serveur depuis la DB
- Nom du club lu depuis la DB (navbar)
- Templates avec display_name depuis la DB
- Catégories groupées par type dans le sélecteur
- Boutons Télécharger / Partager (Web Share API avec fallback download)
- Lightbox avec zoom et drag

#### Services
- `app/services/sync.py` : synchronisation FFVB → DB (matchs, clubs, adresses gymnases)
- `app/core/image_templates.py` : chargement des templates depuis DB avec héritage
- `app/core/config.py` : lecture de la configuration depuis DB
- Suppression de la dépendance aux YAML en runtime

#### Corrections
- `UNIQUE constraint failed: matches.match_code` lors de la sync FFVB : résolu avec `ON CONFLICT(match_code) DO UPDATE SET`
- Redirect `/admin` → `/admin/` : ajout d'une route explicite dans `main.py`
- Valeurs de référentiel non propagées aux CategoryConfig : cascade lors de l'édition d'un RefValue

---

## [Phase 3] — 2026-01-09

### Déploiement & Documentation

- **`app/core/colors.py`** : constantes de couleurs centralisées (`TEXT_TITLE_GRAY`, `VICTORY_GREEN`, `DEFEAT_RED`…)
- **Dockerfile** multi-stage optimisé : builder + runtime slim, utilisateur non-root, health check intégré
- **`docker-compose.yml`** : profils production et développement, volumes pour cache et config
- **`.dockerignore`** : exclusion tests, docs, virtualenvs — contexte Docker réduit de 90 %
- **`scripts/`** : `start.sh` (démarrage local), `test.sh` (tests + coverage), `build-docker.sh` (build Docker versionné)
- **`API.md`** : documentation exhaustive de l'API avec exemples cURL, Python, JavaScript, PHP

---

## [Phase 2] — 2026-01-09

### Tests & Performance

- **Tests automatisés** : 35+ tests avec pytest (`test_string_utils.py`, `test_score_utils.py`, `test_routes.py`), coverage 70%+
- **`GET /health`** : endpoint de health check pour orchestrateurs (Docker, Kubernetes)
- **`app/core/cache.py`** : cache des images basé sur MD5 des paramètres, expiration configurable, endpoint `POST /cache/clear`
- **Génération asynchrone** : route `/image` convertie en `async def` avec `asyncio.to_thread()` — 2–5× plus rapide en parallèle
- **Configuration via `.env`** : `LOG_LEVEL`, `CACHE_DIR`, `CACHE_EXPIRY_MINUTES`, `HOST`, `PORT`, `RELOAD`
- **`.env.example`** : template de configuration

---

## [Phase 1] — 2026-01-09

### Qualité du code

- **`team_rules.yaml`** : externalisation des règles de pseudonymes d'équipes (155 lignes de if/elif → fichier YAML)
- **`app/core/logger.py`** : logging centralisé, remplacement de tous les `print()`, niveau configurable via `LOG_LEVEL`
- **Types hints** : ajout complet sur toutes les fonctions publiques des services
- **`app/models/requests.py`** : validation Pydantic des entrées (`date_start`, `date_end`, `mode`, `format`, cohérence des dates)
- **Gestion d'erreurs globale** dans `main.py` : handlers `RequestValidationError`, `HTTPException`, `Exception`
- **Migration `lifespan`** : remplacement de l'API dépréciée `@app.on_event("startup")`
- **Versioning des dépendances** : versions épinglées dans `requirements.txt`
- **Corrections** : `did_team_a_win()` retournait `None` au lieu d'une valeur inatteignable ; `score_utils.py` nettoyé
