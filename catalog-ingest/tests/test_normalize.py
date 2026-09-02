"""Unit tests for normalization and dedupe keys."""

from catalog_ingest.normalize import (
    clean_text,
    make_dedupe_key,
    normalize_barcode,
    normalize_category,
    normalize_product,
    normalize_unit,
)
from catalog_ingest.scrapers.base import RawProduct
from catalog_ingest.scrapers.snappmarket import parse_product


def test_clean_text_collapses_whitespace():
    assert clean_text("  شیر   کم‌چرب  ") == "شیر کم‌چرب"
    assert clean_text("   ") is None
    assert clean_text(None) is None


def test_normalize_barcode_keeps_digits_only():
    assert normalize_barcode("6260-1234-56789") == "6260123456789"
    assert normalize_barcode("abc") is None
    assert normalize_barcode("123") is None


def test_make_dedupe_key_is_case_insensitive():
    assert make_dedupe_key("Milk", "Mihan") == make_dedupe_key(" milk ", "MIHAN")
    assert make_dedupe_key("Milk", None) == "milk|"


def test_normalize_category_hierarchy():
    assert normalize_category("لبنیات / شیر") == "لبنیات > شیر"
    assert normalize_category("A|B|C") == "A > B > C"
    assert normalize_category(None) == ""


def test_normalize_unit_maps_persian():
    assert normalize_unit("1 لیتر") == "1 L"
    assert normalize_unit("6 عدد") == "6 piece"


def test_normalize_product_roundtrip():
    raw = RawProduct(
        title="  روغن اویلا  ",
        source="demo",
        brand=" اویلا ",
        category="خواربار / روغن",
        barcode="6260-9876-54321",
        unit="1.8 لیتر",
        source_product_id="x1",
    )
    out = normalize_product(raw)
    assert out.title == "روغن اویلا"
    assert out.brand == "اویلا"
    assert out.category == "خواربار > روغن"
    assert out.barcode == "6260987654321"
    assert out.unit == "1.8 L"
    assert make_dedupe_key(out.title, out.brand) == "روغن اویلا|اویلا"


def test_parse_product_flexible_fields():
    item = {
        "product_id": "99",
        "name": "ماست کاله",
        "brand": {"title": "کاله"},
        "full_category": "لبنیات > ماست",
        "ean": "6260111222333",
        "images": [{"url": "https://example.com/y.jpg"}],
    }
    raw = parse_product(item)
    assert raw is not None
    assert raw.title == "ماست کاله"
    assert raw.brand == "کاله"
    assert raw.barcode == "6260111222333"
    assert raw.image_url == "https://example.com/y.jpg"
    assert raw.source_product_id == "99"


def test_parse_product_skips_missing_title():
    assert parse_product({"id": "1", "brand": "x"}) is None
