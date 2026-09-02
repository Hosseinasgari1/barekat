"""
Quick smoke test for parse_product fixes.
Run from catalog-ingest/ with:
    .venv\\Scripts\\python.exe test_parse_fix.py
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))
from catalog_ingest.scrapers.snappmarket import parse_product, _extract_udid_from_cookie

# Load real API data
data = json.loads(Path("pb_products.json").read_text(encoding="utf-8"))
items = data.get("items", [])

print(f"\n{'='*60}")
print(f"Testing parse_product on {len(items)} real items from pb_products.json")
print(f"{'='*60}\n")

parsed_ok = 0
missing_image = 0
with_image = 0

for item in items:
    raw = parse_product(item, category_hint="test-category")
    if raw is None:
        print(f"  SKIP (no title): {item}")
        continue
    parsed_ok += 1
    if raw.image_url:
        with_image += 1
        print(f"  OK  {raw.title[:50]:<50}  image={raw.image_url[:60]}")
    else:
        missing_image += 1
        print(f"  !!  {raw.title[:50]:<50}  NO IMAGE")

print(f"\n{'='*60}")
print(f"Results: parsed={parsed_ok}, with_image={with_image}, missing_image={missing_image}")

if with_image == 0 and parsed_ok > 0:
    print("\nFAIL: All products are missing images -- image parse fix did NOT work!")
    sys.exit(1)
elif missing_image == 0:
    print("\nPASS: All products have images -- image parse fix works!")
else:
    print(f"\nPARTIAL: {with_image}/{parsed_ok} products have images")

# Test UDID extraction
print(f"\n{'='*60}")
print("Testing UDID extraction from cookie string")
print(f"{'='*60}")
cookie = "Canary=never; UDID=e4195c0b-608f-470d-beff-d4f2f20ae8b5; TS015cb371=abc123"
udid = _extract_udid_from_cookie(cookie)
print(f"Cookie: {cookie[:80]}")
print(f"Extracted UDID: {udid}")
assert udid == "e4195c0b-608f-470d-beff-d4f2f20ae8b5", f"UDID extraction FAILED: got {udid!r}"
print("PASS: UDID extraction works!\n")
