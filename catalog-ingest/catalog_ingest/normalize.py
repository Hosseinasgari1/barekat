"""Normalize raw scraped fields into clean catalog values."""

from __future__ import annotations

import re
import unicodedata

from catalog_ingest.scrapers.base import RawProduct

_WS_RE = re.compile(r"\s+")
_BARCODE_RE = re.compile(r"[^0-9]")


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = unicodedata.normalize("NFKC", str(value))
    text = _WS_RE.sub(" ", text).strip()
    return text or None


def normalize_barcode(value: str | None) -> str | None:
    if value is None:
        return None
    digits = _BARCODE_RE.sub("", str(value))
    if len(digits) < 8:
        return None
    return digits


def make_dedupe_key(title: str, brand: str | None) -> str:
    t = clean_text(title) or ""
    b = clean_text(brand) or ""
    return f"{t.lower()}|{b.lower()}"


def normalize_category(value: str | None) -> str:
    cleaned = clean_text(value)
    if not cleaned:
        return ""
    # Collapse mixed separators into a single hierarchy delimiter
    parts = re.split(r"\s*[>/|\\]+\s*", cleaned)
    parts = [p for p in (clean_text(p) for p in parts) if p]
    return " > ".join(parts)


def normalize_unit(value: str | None) -> str | None:
    cleaned = clean_text(value)
    if not cleaned:
        return None
    replacements = {
        "کیلوگرم": "kg",
        "کیلو": "kg",
        "گرم": "g",
        "لیتر": "L",
        "میلی‌لیتر": "ml",
        "میلی لیتر": "ml",
        "عدد": "piece",
        "بسته": "pack",
    }
    out = cleaned
    for fa, en in replacements.items():
        out = out.replace(fa, en)
    return out


def normalize_product(raw: RawProduct) -> RawProduct:
    title = clean_text(raw.title)
    if not title:
        raise ValueError("Product title is required after normalization")
    return RawProduct(
        title=title,
        source=clean_text(raw.source) or raw.source,
        source_product_id=clean_text(raw.source_product_id),
        brand=clean_text(raw.brand),
        category=normalize_category(raw.category),
        barcode=normalize_barcode(raw.barcode),
        image_url=clean_text(raw.image_url),
        unit=normalize_unit(raw.unit),
        description=clean_text(raw.description),
        source_url=clean_text(raw.source_url),
        extras=raw.extras,
    )
