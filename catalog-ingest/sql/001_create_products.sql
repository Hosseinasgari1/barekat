-- Master Product Catalog DDL (PostgreSQL)
-- Requires pgcrypto / gen_random_uuid (available in PostgreSQL 13+)

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS products (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title           TEXT NOT NULL,
    brand           TEXT,
    category        TEXT NOT NULL DEFAULT '',
    barcode         TEXT,
    image_url       TEXT,
    unit            TEXT,
    description     TEXT,
    source          TEXT NOT NULL,
    source_product_id TEXT,
    source_url      TEXT,
    dedupe_key      TEXT GENERATED ALWAYS AS (
                        lower(trim(title)) || '|' || lower(coalesce(brand, ''))
                    ) STORED,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Title search
CREATE INDEX IF NOT EXISTS idx_products_title_lower ON products (lower(title));

-- Unique barcode when present
CREATE UNIQUE INDEX IF NOT EXISTS uq_products_barcode
    ON products (barcode)
    WHERE barcode IS NOT NULL;

-- Title+brand dedupe when barcode is missing
CREATE UNIQUE INDEX IF NOT EXISTS uq_products_dedupe_key
    ON products (dedupe_key)
    WHERE barcode IS NULL;

-- Idempotent re-scrapes from the same source
CREATE UNIQUE INDEX IF NOT EXISTS uq_products_source_id
    ON products (source, source_product_id)
    WHERE source_product_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_products_category ON products (category);
CREATE INDEX IF NOT EXISTS idx_products_brand ON products (brand);

-- Keep updated_at current on row changes
CREATE OR REPLACE FUNCTION products_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_products_updated_at ON products;
CREATE TRIGGER trg_products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW
    EXECUTE PROCEDURE products_set_updated_at();
