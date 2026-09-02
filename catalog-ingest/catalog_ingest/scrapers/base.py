"""Base scraper contract and raw product DTO."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator


@dataclass
class RawProduct:
    """Unnormalized product payload from a source scraper."""

    title: str
    source: str
    source_product_id: str | None = None
    brand: str | None = None
    category: str | None = None
    barcode: str | None = None
    image_url: str | None = None
    unit: str | None = None
    description: str | None = None
    source_url: str | None = None
    extras: dict[str, Any] = field(default_factory=dict)


class BaseScraper(ABC):
    source_name: str = "unknown"

    @abstractmethod
    async def iter_products(
        self,
        *,
        category_ids: list[str] | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[RawProduct]:
        """Yield raw products from the upstream source."""
        if False:  # pragma: no cover — makes this an async generator for type checkers
            yield RawProduct(title="", source=self.source_name)
