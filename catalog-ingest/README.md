"""
# Master Product Catalog — Scraper & Ingestion

Standalone Python pipeline that scrapes supermarket product data (SnappMarket-style
JSON sources) and upserts into a PostgreSQL **Master Product Catalog** with
barcode / title+brand deduplication.

## Layout

```
catalog-ingest/
  sql/001_create_products.sql
  catalog_ingest/
    config.py, db.py, models.py
    http_client.py          # rate limit + UA rotation + retries
    normalize.py, pipeline.py
    scrapers/snappmarket.py # live adapter
    scrapers/demo.py        # offline fixture adapter
    cli.py
  tests/
```

## Prerequisites

1. PostgreSQL running (reuse barekat's docker-compose `db` service):

```bash
# from repo root
docker compose up -d db
```

2. Create the catalog database once:

```bash
docker exec -it barekat_db psql -U postgres -c "CREATE DATABASE master_catalog;"
```

## Setup

```bash
cd catalog-ingest
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux/macOS
# source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # or: cp .env.example .env
```

Edit `.env` if needed (`DATABASE_URL`, `RATE_LIMIT_RPS`, `SNAPP_CATEGORY_IDS`).

## Initialize schema

```bash
python -m catalog_ingest.cli init-db
```

## Scrape & ingest

**Offline smoke test (recommended first):**

```bash
# No database required — parse & normalize only
python -m catalog_ingest.cli scrape --source demo --limit 20 --dry-run

# Persist into PostgreSQL (requires init-db)
python -m catalog_ingest.cli scrape --source demo --limit 20
```

**Live SnappMarket (configure category IDs; keep rate low):**

```bash
python -m catalog_ingest.cli scrape --source snappmarket --limit 500
python -m catalog_ingest.cli scrape --source snappmarket --category 12,34 --limit 100
```

Verify:

```sql
SELECT count(*), count(barcode) FROM products;
SELECT title, brand, barcode, category FROM products LIMIT 20;
```

## Deduplication

| Priority | Conflict target | When |
|----------|-----------------|------|
| 1 | `(source, source_product_id)` | Same-source re-scrape |
| 2 | `barcode` (partial unique) | Barcode present |
| 3 | `dedupe_key` = `lower(title)\|lower(brand)` | No barcode |

## Safety notes

- SnappMarket has **no public product API**. Endpoints in the scraper are
  undocumented and may break or block you. Update `SNAPP_BASE_URL` / category IDs
  as needed.
- Keep `RATE_LIMIT_RPS` ≤ 1 for polite crawling; prefer off-peak hours.
- Scraping may violate the target site's Terms of Service — use only for
  internal / research purposes with legal clearance.
- Prefer `--limit` during development so you can stop early.

## Tests

```bash
pytest -q
```
"""
