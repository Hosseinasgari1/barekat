"""Ingest normalized products into the catalog database with dedupe upserts.

Supports both PostgreSQL (full ON CONFLICT syntax) and SQLite (local dev mode
where Django's migration-created products table is used).
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Sequence

from sqlalchemy import text
from sqlalchemy.orm import Session

from catalog_ingest.normalize import normalize_product
from catalog_ingest.scrapers.base import RawProduct

logger = logging.getLogger(__name__)


@dataclass
class IngestStats:
    received: int = 0
    upserted: int = 0
    skipped: int = 0
    errors: int = 0


# ---------------------------------------------------------------------------
# PostgreSQL upsert SQL (full ON CONFLICT support with partial indexes)
# ---------------------------------------------------------------------------

# Prefer source+id when present; else barcode; else title+brand (dedupe_key).
_PG_UPSERT_SQL = text(
    """
    INSERT INTO products (
        title, brand, category, barcode, image_url, unit, description,
        source, source_product_id, source_url
    ) VALUES (
        :title, :brand, :category, :barcode, :image_url, :unit, :description,
        :source, :source_product_id, :source_url
    )
    ON CONFLICT (source, source_product_id)
        WHERE source_product_id IS NOT NULL
    DO UPDATE SET
        title = EXCLUDED.title,
        brand = EXCLUDED.brand,
        category = EXCLUDED.category,
        barcode = COALESCE(EXCLUDED.barcode, products.barcode),
        image_url = COALESCE(EXCLUDED.image_url, products.image_url),
        unit = COALESCE(EXCLUDED.unit, products.unit),
        description = COALESCE(EXCLUDED.description, products.description),
        source_url = COALESCE(EXCLUDED.source_url, products.source_url)
    """
)

_PG_UPSERT_BY_BARCODE_SQL = text(
    """
    INSERT INTO products (
        title, brand, category, barcode, image_url, unit, description,
        source, source_product_id, source_url
    ) VALUES (
        :title, :brand, :category, :barcode, :image_url, :unit, :description,
        :source, :source_product_id, :source_url
    )
    ON CONFLICT (barcode)
        WHERE barcode IS NOT NULL
    DO UPDATE SET
        title = EXCLUDED.title,
        brand = COALESCE(EXCLUDED.brand, products.brand),
        category = COALESCE(NULLIF(EXCLUDED.category, ''), products.category),
        image_url = COALESCE(EXCLUDED.image_url, products.image_url),
        unit = COALESCE(EXCLUDED.unit, products.unit),
        description = COALESCE(EXCLUDED.description, products.description),
        source = EXCLUDED.source,
        source_product_id = COALESCE(EXCLUDED.source_product_id, products.source_product_id),
        source_url = COALESCE(EXCLUDED.source_url, products.source_url)
    """
)

_PG_UPSERT_BY_DEDUPE_SQL = text(
    """
    INSERT INTO products (
        title, brand, category, barcode, image_url, unit, description,
        source, source_product_id, source_url
    ) VALUES (
        :title, :brand, :category, :barcode, :image_url, :unit, :description,
        :source, :source_product_id, :source_url
    )
    ON CONFLICT (dedupe_key)
        WHERE barcode IS NULL
    DO UPDATE SET
        category = COALESCE(NULLIF(EXCLUDED.category, ''), products.category),
        image_url = COALESCE(EXCLUDED.image_url, products.image_url),
        unit = COALESCE(EXCLUDED.unit, products.unit),
        description = COALESCE(EXCLUDED.description, products.description),
        source = EXCLUDED.source,
        source_product_id = COALESCE(EXCLUDED.source_product_id, products.source_product_id),
        source_url = COALESCE(EXCLUDED.source_url, products.source_url)
    """
)


# ---------------------------------------------------------------------------
# SQLite upsert helpers (Django migration schema: id=char(32), no dedupe_key)
# ---------------------------------------------------------------------------

_SQLITE_CHECK_SOURCE_ID = text(
    "SELECT id FROM products WHERE source = :source AND source_product_id = :source_product_id LIMIT 1"
)
_SQLITE_CHECK_BARCODE = text(
    "SELECT id FROM products WHERE barcode = :barcode LIMIT 1"
)
_SQLITE_CHECK_DEDUPE = text(
    "SELECT id FROM products WHERE lower(title) = lower(:title) AND (brand IS NULL OR lower(brand) = lower(:brand)) LIMIT 1"
)
_SQLITE_INSERT = text(
    """
    INSERT INTO products (
        id, title, brand, category, barcode, image_url, unit, description,
        source, source_product_id, source_url, created_at, updated_at
    ) VALUES (
        :id, :title, :brand, :category, :barcode, :image_url, :unit, :description,
        :source, :source_product_id, :source_url, :created_at, :updated_at
    )
    """
)
_SQLITE_UPDATE = text(
    """
    UPDATE products SET
        title = :title,
        brand = :brand,
        category = CASE WHEN :category != '' THEN :category ELSE category END,
        barcode = COALESCE(:barcode, barcode),
        image_url = COALESCE(:image_url, image_url),
        unit = COALESCE(:unit, unit),
        description = COALESCE(:description, description),
        source = :source,
        source_product_id = COALESCE(:source_product_id, source_product_id),
        source_url = COALESCE(:source_url, source_url),
        updated_at = :updated_at
    WHERE id = :id
    """
)


def _is_sqlite(session: Session) -> bool:
    return session.bind.dialect.name == "sqlite"  # type: ignore[union-attr]


def _row(product: RawProduct) -> dict:
    return {
        "title": product.title,
        "brand": product.brand,
        "category": product.category or "",
        "barcode": product.barcode,
        "image_url": product.image_url,
        "unit": product.unit,
        "description": product.description,
        "source": product.source,
        "source_product_id": product.source_product_id,
        "source_url": product.source_url,
    }


def _upsert_sqlite(session: Session, product: RawProduct) -> None:
    """Upsert using check-then-insert/update for SQLite compatibility."""
    now = datetime.now(timezone.utc).isoformat()
    params = _row(product)

    existing_id: str | None = None

    # Check by source + source_product_id first
    if product.source_product_id:
        row = session.execute(
            _SQLITE_CHECK_SOURCE_ID,
            {"source": product.source, "source_product_id": product.source_product_id},
        ).fetchone()
        if row:
            existing_id = row[0]

    # Then by barcode
    if existing_id is None and product.barcode:
        row = session.execute(_SQLITE_CHECK_BARCODE, {"barcode": product.barcode}).fetchone()
        if row:
            existing_id = row[0]

    # Then by title+brand dedupe
    if existing_id is None:
        row = session.execute(
            _SQLITE_CHECK_DEDUPE,
            {"title": product.title, "brand": product.brand or ""},
        ).fetchone()
        if row:
            existing_id = row[0]

    if existing_id:
        session.execute(_SQLITE_UPDATE, {**params, "id": existing_id, "updated_at": now})
    else:
        new_id = uuid.uuid4().hex  # char(32) without dashes, as Django uses
        session.execute(
            _SQLITE_INSERT,
            {**params, "id": new_id, "created_at": now, "updated_at": now},
        )


def upsert_product(session: Session, product: RawProduct) -> None:
    """Upsert a single normalized product using the appropriate conflict target."""
    if _is_sqlite(session):
        _upsert_sqlite(session, product)
        return

    # PostgreSQL path
    params = _row(product)
    if product.source_product_id:
        session.execute(_PG_UPSERT_SQL, params)
    elif product.barcode:
        session.execute(_PG_UPSERT_BY_BARCODE_SQL, params)
    else:
        session.execute(_PG_UPSERT_BY_DEDUPE_SQL, params)


def ingest_batch(session: Session, raw_products: Sequence[RawProduct]) -> IngestStats:
    stats = IngestStats(received=len(raw_products))
    for raw in raw_products:
        try:
            normalized = normalize_product(raw)
        except ValueError as exc:
            logger.warning("Skip invalid product: %s (%s)", raw.title, exc)
            stats.skipped += 1
            continue
        try:
            with session.begin_nested():
                upsert_product(session, normalized)
            stats.upserted += 1
        except Exception:  # noqa: BLE001
            logger.exception("Failed to upsert product title=%r", normalized.title)
            stats.errors += 1
    return stats


def ingest_many(session: Session, products: Iterable[RawProduct], batch_size: int = 100) -> IngestStats:
    total = IngestStats()
    batch: list[RawProduct] = []
    for product in products:
        batch.append(product)
        if len(batch) >= batch_size:
            part = ingest_batch(session, batch)
            total.received += part.received
            total.upserted += part.upserted
            total.skipped += part.skipped
            total.errors += part.errors
            batch.clear()
    if batch:
        part = ingest_batch(session, batch)
        total.received += part.received
        total.upserted += part.upserted
        total.skipped += part.skipped
        total.errors += part.errors
    return total
