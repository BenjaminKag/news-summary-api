
# News Summary API

A Django + DRF service that **fetches news articles**, **tags** them, and **summarizes** their content.
The app runs in Docker with **PostgreSQL** for storage and **Redis** for caching. A background **fetcher** container refreshes data every 6 hours.

## Stack
- **Django** + **Django REST Framework**
- **PostgreSQL** (articles, sources, summaries, tags)
- **Redis** via `django-redis` (response + data caching)
- **Docker Compose** (multi-service dev stack)
- Optional LLM provider (e.g., OpenAI) for full summaries

---

## Architecture (dev)
- `app` — Django API (`runserver`), migrations, admin
- `db` — PostgreSQL (persistent volume `dev-db-data`)
- `redis` — Cache backend for Django/DRF
- `fetcher` — Sidecar that runs:
  - `fetch_articles --q <topic> --page-size <n>`
  - `tag_articles`
  - `summarize_articles --limit <n>` (in small batches to avoid long runs)

> The fetcher loops every **6 hours**. Each command uses `|| true` to avoid crashing the loop.

---

## Environment Variables

| Variable | Purpose | Example |
|---|---|---|
| `DB_HOST` | DB hostname | `db` |
| `DB_NAME` | DB name | `devdb` |
| `DB_USER` | DB user | `devuser` |
| `DB_PASS` | DB password | `changeme` |
| `NEWS_API_KEY` | API key for article ingestion | `...` |
| `OPENAI_API_KEY` | (Optional) LLM key for full summaries | `...` |
| `OPENAI_MODEL` | (Optional) LLM model id | `gpt-4o-mini` |

> In dev, these are injected from `docker-compose.yml`.

---

## Quickstart (Dev)

1) **Build & start**
```bash
docker compose up -d --build
docker compose ps
```

2) **Confirm services**
```bash
# App should be on http://localhost:8000
# Redis
docker compose exec redis redis-cli PING
# Django ↔ Redis
docker compose exec app python manage.py shell -c "from django.core.cache import cache; cache.set('hello','world',60); print(cache.get('hello'))"
```

3) **Run management commands (ad-hoc)**
```bash
docker compose exec app python manage.py fetch_articles --q technology --page-size 20
docker compose exec app python manage.py tag_articles
docker compose exec app python manage.py summarize_articles --limit 5   # small batches recommended
```

4) **Run tests**
```bash
docker compose exec app pytest -q
```

---

## API Endpoints (examples)

Base URL: `http://localhost:8000`
API prefix: `/api`

- `GET {{base_url}}{{api_prefix}}/articles/` — list articles (supports filters like `?tag=AI`, pagination)
- `GET {{base_url}}{{api_prefix}}/articles/{id}/` — retrieve an article
- `GET {{base_url}}{{api_prefix}}/sources/` — list sources
- `GET {{base_url}}{{api_prefix}}/tags/` — list tags (if exposed)
- (Read-only) `GET {{base_url}}{{api_prefix}}/summaries/{article_id}/` or nested in article serializer (depending on your serializers)

### Curl examples
```bash
curl "http://localhost:8000/api/articles/"
curl "http://localhost:8000/api/articles/?tag=AI"
curl "http://localhost:8000/api/articles/1/"
```

---

## Caching

- Configured via `django-redis` in `settings.py`:
  ```python
  CACHES = {
      "default": {
          "BACKEND": "django_redis.cache.RedisCache",
          "LOCATION": "redis://redis:6379/1",
          "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
          "KEY_PREFIX": "newsapi",
      }
  }
  ```

- View-level caching (example for DRF ViewSet):
  ```python
  from django.utils.decorators import method_decorator
  from django.views.decorators.cache import cache_page

  @method_decorator(cache_page(60 * 5), name="list")
  @method_decorator(cache_page(60 * 10), name="retrieve")
  class ArticleViewSet(...):
      ...
  ```

- Inspect keys / TTL:
  ```bash
  docker compose exec redis redis-cli KEYS 'newsapi:*'
  docker compose exec redis redis-cli TTL 'newsapi:...'
  ```

---

## Background Fetcher (every 6 hours)

The `fetcher` service runs a simple loop:
```bash
python manage.py wait_for_db &&
while true; do
  python manage.py fetch_articles --q technology --page-size 20 || true
  python manage.py tag_articles || true
  python manage.py summarize_articles --limit 5 || true
  sleep 21600  # 6h
done
```

Check logs:
```bash
docker compose logs -f fetcher
```

Stop/start independently:
```bash
docker compose stop fetcher
docker compose start fetcher
```

---

## Troubleshooting

- **App/DB/Redis not running** → `docker compose ps`, then `docker compose logs app|db|redis`
- **Redis import error** → ensure `django-redis` is in `requirements.txt`, rebuild image
- **Long summarization time** → use `--limit` (small batches) and/or run summarizer less frequently
- **Compose warning**: `version` is obsolete → safe to remove `version: "3.9"` from `docker-compose.yml`

---

## Project Scripts (common)

```bash
# Shell inside app
docker compose exec app bash

# Make migrations / migrate
docker compose exec app python manage.py makemigrations
docker compose exec app python manage.py migrate
```
