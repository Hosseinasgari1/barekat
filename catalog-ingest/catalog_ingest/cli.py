"""Typer CLI for init-db and scrape."""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

import typer

# Allow `python -m catalog_ingest.cli` from catalog-ingest/
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from catalog_ingest.config import get_settings
from catalog_ingest.db import apply_ddl, session_scope
from catalog_ingest.http_client import RateLimitedClient
from catalog_ingest.pipeline import ingest_batch
from catalog_ingest.scrapers.demo import DemoScraper
from catalog_ingest.scrapers.snappmarket import SnappMarketScraper

app = typer.Typer(
    name="catalog-ingest",
    help="Master Product Catalog — scrape & ingest supermarket products.",
    add_completion=False,
)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("catalog_ingest.cli")


@app.command("init-db")
def init_db() -> None:
    """Create the products table and indexes from sql/*.sql."""
    settings = get_settings()
    typer.echo(f"Applying DDL to {settings.database_url}")
    apply_ddl(settings)
    typer.secho("Database ready.", fg=typer.colors.GREEN)


@app.command("scrape")
def scrape(
    source: str = typer.Option(
        "snappmarket",
        "--source",
        "-s",
        help="Source adapter: snappmarket | demo",
    ),
    category: Optional[str] = typer.Option(
        None,
        "--category",
        "-c",
        help="Comma-separated category IDs (overrides SNAPP_CATEGORY_IDS)",
    ),
    limit: Optional[int] = typer.Option(
        None,
        "--limit",
        "-n",
        help="Max products to ingest (useful for smoke tests)",
    ),
    batch_size: int = typer.Option(100, "--batch-size", help="Commit every N products"),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Parse & normalize only; do not write to the database",
    ),
) -> None:
    """Scrape products and upsert into the Master Product Catalog."""
    asyncio.run(
        _scrape(
            source=source,
            category=category,
            limit=limit,
            batch_size=batch_size,
            dry_run=dry_run,
        )
    )


async def _scrape(
    *,
    source: str,
    category: str | None,
    limit: int | None,
    batch_size: int,
    dry_run: bool,
) -> None:
    settings = get_settings()
    category_ids = (
        [x.strip() for x in category.split(",") if x.strip()]
        if category
        else None
    )

    total_received = total_upserted = total_skipped = total_errors = 0
    batch = []

    async def flush() -> None:
        nonlocal total_received, total_upserted, total_skipped, total_errors, batch
        if not batch:
            return
        if dry_run:
            from catalog_ingest.normalize import normalize_product

            ok = skip = err = 0
            for raw in batch:
                try:
                    normalize_product(raw)
                    ok += 1
                except ValueError:
                    skip += 1
                except Exception:  # noqa: BLE001
                    err += 1
            total_received += len(batch)
            total_upserted += ok
            total_skipped += skip
            total_errors += err
            typer.echo(f"[dry-run] normalized={ok} skipped={skip} errors={err}")
        else:
            with session_scope(settings) as session:
                stats = ingest_batch(session, batch)
            total_received += stats.received
            total_upserted += stats.upserted
            total_skipped += stats.skipped
            total_errors += stats.errors
            typer.echo(
                f"Batch committed: +{stats.upserted} upserted "
                f"(skipped={stats.skipped}, errors={stats.errors})"
            )
        batch.clear()

    if source == "demo":
        scraper = DemoScraper()
        async for raw in scraper.iter_products(category_ids=category_ids, limit=limit):
            batch.append(raw)
            if len(batch) >= batch_size:
                await flush()
    elif source == "snappmarket":
        async with RateLimitedClient(settings) as client:
            scraper = SnappMarketScraper(client, settings)
            async for raw in scraper.iter_products(category_ids=category_ids, limit=limit):
                batch.append(raw)
                if len(batch) >= batch_size:
                    await flush()
    else:
        typer.secho(f"Unknown source: {source}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2)

    await flush()

    typer.secho(
        f"Done. received={total_received} upserted={total_upserted} "
        f"skipped={total_skipped} errors={total_errors}"
        + (" (dry-run)" if dry_run else ""),
        fg=typer.colors.GREEN if total_errors == 0 else typer.colors.YELLOW,
    )


def main() -> None:
    app()


if __name__ == "__main__":
    main()
