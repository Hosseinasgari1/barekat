"""Offline demo scraper — loads fixture JSON so the pipeline can be verified without live HTTP."""

from __future__ import annotations

import json
from pathlib import Path
from typing import AsyncIterator

from catalog_ingest.scrapers.base import BaseScraper, RawProduct
from catalog_ingest.scrapers.snappmarket import parse_product

FIXTURE_PATH = Path(__file__).resolve().parent.parent.parent / "tests" / "fixtures" / "sample_products.json"


class DemoScraper(BaseScraper):
    source_name = "demo"

    def __init__(self, fixture_path: Path | None = None) -> None:
        self.fixture_path = fixture_path or FIXTURE_PATH

    async def iter_products(
        self,
        *,
        category_ids: list[str] | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[RawProduct]:
        data = json.loads(self.fixture_path.read_text(encoding="utf-8"))
        produced = 0
        for item in data:
            if limit is not None and produced >= limit:
                return
            raw = parse_product(item)
            if raw is None:
                continue
            raw.source = self.source_name
            produced += 1
            yield raw
