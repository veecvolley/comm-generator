# API Documentation - Comm'Generator

Documentation complète de l'API REST de Comm'Generator.

## Base URL

```
http://localhost:8000
```

En production, remplacer par votre domaine.

---

## Endpoints

### 1. Health Check

Vérifie que l'application fonctionne correctement.

**Endpoint:** `GET /health`

**Réponse (200 OK):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "service": "comm-generator"
}
```

**Exemples:**
```bash
# cURL
curl http://localhost:8000/health

# HTTPie
http GET localhost:8000/health

# Python requests
import requests
response = requests.get('http://localhost:8000/health')
print(response.json())
```

**Utilisations:**
- Monitoring (Kubernetes liveness probe)
- Load balancer health check
- CI/CD pipeline validation

---

### 2. Index / Web Interface

Interface web de l'application.

**Endpoint:** `GET /`

**Réponse:** Page HTML interactive

**Exemple:**
```bash
# Ouvrir dans le navigateur
open http://localhost:8000
```

---

### 3. Obtenir les catégories

Liste les catégories disponibles pour une saison donnée.

**Endpoint:** `GET /categories`

**Paramètres (Query):**
| Paramètre | Type | Requis | Description | Exemple |
|-----------|------|--------|-------------|---------|
| saison | string | ✅ Oui | Saison au format YYYY/YYYY ou YYYY-YYYY | 2025/2026 |

**Réponse (200 OK):**
```json
{
  "SF1": {
    "label": "SF1",
    "genre": "Féminin",
    "type": "Volley-Ball",
    "niveau": "Championnat Régional",
    "titre": "Sénior Féminin - Régional"
  },
  "SM1": {
    "label": "SM1",
    "genre": "Masculin",
    "type": "Volley-Ball",
    "niveau": "Championnat Régional",
    "titre": "Sénior Masculin - Régional"
  }
}
```

**Réponse (404 Not Found):**
```json
{
  "error": "Saison '1999/2000' non trouvée"
}
```

**Exemples:**
```bash
# cURL
curl "http://localhost:8000/categories?saison=2025/2026"

# Avec séparateur -
curl "http://localhost:8000/categories?saison=2025-2026"

# HTTPie
http GET localhost:8000/categories saison==2025/2026

# Python requests
import requests
response = requests.get(
    'http://localhost:8000/categories',
    params={'saison': '2025/2026'}
)
categories = response.json()
```

---

### 4. Générer une image

Génère une image PNG de communication pour les matchs.

**Endpoint:** `GET /image`

**Paramètres (Query):**
| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| saison | string | Non | 2025/2026 | Saison au format YYYY/YYYY |
| mode | string | Non | planning | Mode: `planning` ou `results` |
| title | string | Non | Matchs | Titre de l'image |
| format | string | Non | pub | Format: `pub` ou `story` |
| categories | array | Non | - | Liste des catégories à filtrer |
| date_start | string | Non | - | Date début (YYYY-MM-DD) |
| date_end | string | Non | - | Date fin (YYYY-MM-DD) |
| use_cache | boolean | Non | true | Utiliser le cache |

**Réponse (200 OK):**
- Content-Type: `image/png`
- Body: Image PNG binaire

**Exemples détaillés:**

#### a) Image de planning basique
```bash
curl "http://localhost:8000/image" --output planning.png
```

#### b) Résultats du week-end
```bash
curl "http://localhost:8000/image?mode=results&date_start=2025-01-10&date_end=2025-01-12&title=Résultats du week-end" --output results.png
```

#### c) Filtrage par catégories
```bash
# Une catégorie
curl "http://localhost:8000/image?categories=SF1" --output sf1.png

# Plusieurs catégories
curl "http://localhost:8000/image?categories=SF1&categories=SM1&categories=M18" --output seniors.png
```

#### d) Format story (vertical)
```bash
curl "http://localhost:8000/image?format=story&title=Story Instagram" --output story.png
```

#### e) Sans cache (force la régénération)
```bash
curl "http://localhost:8000/image?use_cache=false" --output fresh.png
```

#### f) Exemple complet avec Python
```python
import requests
from datetime import datetime, timedelta

# Calculer dates du week-end prochain
today = datetime.now()
days_ahead = 5 - today.weekday()  # Samedi
if days_ahead <= 0:
    days_ahead += 7
saturday = today + timedelta(days_ahead)
sunday = saturday + timedelta(1)

# Générer l'image
response = requests.get(
    'http://localhost:8000/image',
    params={
        'mode': 'planning',
        'title': 'Matchs du week-end',
        'date_start': saturday.strftime('%Y-%m-%d'),
        'date_end': sunday.strftime('%Y-%m-%d'),
        'categories': ['SF1', 'SM1'],
        'format': 'pub'
    }
)

# Sauvegarder
if response.status_code == 200:
    with open('weekend.png', 'wb') as f:
        f.write(response.content)
    print("✅ Image générée: weekend.png")
else:
    print(f"❌ Erreur: {response.status_code}")
```

#### g) Exemple JavaScript/TypeScript
```typescript
async function generateImage(params: {
  mode?: 'planning' | 'results',
  title?: string,
  dateStart?: string,
  dateEnd?: string,
  categories?: string[],
  format?: 'pub' | 'story'
}): Promise<Blob> {
  const url = new URL('http://localhost:8000/image');
  
  // Ajouter les paramètres
  if (params.mode) url.searchParams.append('mode', params.mode);
  if (params.title) url.searchParams.append('title', params.title);
  if (params.dateStart) url.searchParams.append('date_start', params.dateStart);
  if (params.dateEnd) url.searchParams.append('date_end', params.dateEnd);
  if (params.format) url.searchParams.append('format', params.format);
  params.categories?.forEach(cat => url.searchParams.append('categories', cat));
  
  const response = await fetch(url.toString());
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  
  return response.blob();
}

// Utilisation
const imageBlob = await generateImage({
  mode: 'planning',
  title: 'Matchs du 10-12 janvier',
  dateStart: '2025-01-10',
  dateEnd: '2025-01-12',
  categories: ['SF1', 'SM1']
});

// Afficher dans le navigateur
const imageUrl = URL.createObjectURL(imageBlob);
document.getElementById('preview').src = imageUrl;
```

---

### 5. Mettre à jour la configuration

Met à jour la configuration des saisons depuis la FFVB.

**Endpoint:** `POST /update-config`

**Réponse (200 OK):**
```json
{
  "message": "Configuration mise à jour avec succès."
}
```

**Réponse (erreur):**
```json
{
  "message": "Erreur : [détails de l'erreur]"
}
```

**Exemples:**
```bash
# cURL
curl -X POST http://localhost:8000/update-config

# HTTPie
http POST localhost:8000/update-config

# Python requests
import requests
response = requests.post('http://localhost:8000/update-config')
print(response.json())
```

---

### 6. Nettoyer le cache

Supprime les images en cache.

**Endpoint:** `POST /cache/clear`

**Paramètres (Query):**
| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| expired_only | boolean | Non | false | Si true, supprime uniquement les fichiers expirés |

**Réponse (200 OK):**
```json
{
  "message": "Cache nettoyé avec succès",
  "deleted_files": 15
}
```

**Exemples:**
```bash
# Nettoyer uniquement les fichiers expirés
curl -X POST "http://localhost:8000/cache/clear?expired_only=true"

# Nettoyer tout le cache
curl -X POST http://localhost:8000/cache/clear

# Python requests
import requests

# Expirés seulement
response = requests.post(
    'http://localhost:8000/cache/clear',
    params={'expired_only': True}
)

# Tout le cache
response = requests.post('http://localhost:8000/cache/clear')
print(f"Fichiers supprimés: {response.json()['deleted_files']}")
```

---

## Codes d'erreur

| Code | Description | Exemple |
|------|-------------|---------|
| 200 | OK | Succès |
| 404 | Not Found | Saison inexistante, route invalide |
| 422 | Validation Error | Paramètres invalides |
| 500 | Internal Server Error | Erreur serveur |

### Exemple d'erreur de validation (422)

```json
{
  "error": "Validation error",
  "details": [
    {
      "loc": ["query", "date_end"],
      "msg": "date_end doit être après date_start",
      "type": "value_error"
    }
  ]
}
```

---

## Rate Limiting

Actuellement, aucun rate limiting n'est implémenté. En production, il est recommandé d'ajouter:

```python
# Exemple avec slowapi
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/image")
@limiter.limit("10/minute")
async def image(...):
    ...
```

---

## CORS

En production, configurez CORS pour limiter les origines autorisées:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://votre-domaine.fr"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

---

## Monitoring & Logging

### Logs

Tous les appels API sont loggés avec:
- Timestamp
- Niveau (INFO, WARNING, ERROR)
- Module
- Message détaillé

Configuration via `.env`:
```bash
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Métriques

Pour Prometheus (future implémentation):
```python
from prometheus_client import Counter, Histogram

http_requests_total = Counter('http_requests_total', 'Total HTTP requests')
http_request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')
```

---

## Performance

### Cache

Le cache améliore drastiquement les performances:

| Scénario | Temps | Cache hit |
|----------|-------|-----------|
| Première génération | 2-5 sec | ❌ |
| Même requête (dans les 60 min) | 10-50 ms | ✅ |

**Gain:** 50-500x plus rapide!

### Async

Génération asynchrone = serveur non bloquant:

```
Requête 1 → [Génération 5s async]
Requête 2 → [Génération 5s async]  ← Traité en parallèle!
Requête 3 → [Génération 5s async]  ← Traité en parallèle!
```

---

## Exemples d'intégration

### Intégration dans un CMS WordPress

```php
<?php
// Récupérer l'image depuis l'API
function get_match_image($mode = 'planning', $title = 'Matchs') {
    $url = 'http://localhost:8000/image';
    $params = http_build_query([
        'mode' => $mode,
        'title' => $title,
        'saison' => '2025/2026'
    ]);
    
    $response = file_get_contents($url . '?' . $params);
    return $response;
}

// Utilisation dans un shortcode
add_shortcode('matchs_image', function($atts) {
    $atts = shortcode_atts([
        'mode' => 'planning',
        'title' => 'Matchs'
    ], $atts);
    
    $image_data = get_match_image($atts['mode'], $atts['title']);
    $base64 = base64_encode($image_data);
    
    return '<img src="data:image/png;base64,' . $base64 . '" />';
});
?>
```

### Automation avec cron

```bash
#!/bin/bash
# Script cron pour générer automatiquement les images

# Chaque vendredi à 18h, générer l'image du week-end
0 18 * * 5 /path/to/generate_weekend.sh

# generate_weekend.sh
SATURDAY=$(date -d "next saturday" +%Y-%m-%d)
SUNDAY=$(date -d "next sunday" +%Y-%m-%d)

curl "http://localhost:8000/image?mode=planning&date_start=$SATURDAY&date_end=$SUNDAY&title=Week-end" \
  --output /var/www/html/images/weekend.png

echo "✅ Image générée pour le $SATURDAY-$SUNDAY"
```

---

## Support

Questions? Problèmes?

- 📧 Email: contact@veec-volley.fr
- 🐛 Issues: [GitHub](https://github.com/veecvolley/comm-generator/issues)
- 📖 Documentation: [Wiki](https://github.com/veecvolley/comm-generator/wiki)

---

**Dernière mise à jour:** 2026-01-09
