"""Environment-driven settings for catalog-ingest."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


def _float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return float(raw)


def _int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


@dataclass(frozen=True)
class Settings:
    database_url: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg2://postgres:postgres@localhost:5432/master_catalog",
        )
    )
    rate_limit_rps: float = field(default_factory=lambda: _float("RATE_LIMIT_RPS", 1.0))
    http_timeout_seconds: float = field(
        default_factory=lambda: _float("HTTP_TIMEOUT_SECONDS", 30.0)
    )
    http_max_retries: int = field(default_factory=lambda: _int("HTTP_MAX_RETRIES", 5))
    snapp_base_url: str = field(
        default_factory=lambda: os.getenv("SNAPP_BASE_URL", "https://api.snapp.market").rstrip("/")
    )
    snapp_vendor_code: str = field(
        default_factory=lambda: os.getenv("SNAPP_VENDOR_CODE", "0")
    )
    snapp_category_ids: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            x.strip()
            for x in os.getenv("SNAPP_CATEGORY_IDS", "1,2,3").split(",")
            if x.strip()
        )
    )
    snapp_page_size: int = field(default_factory=lambda: _int("SNAPP_PAGE_SIZE", 24))
    snapp_cookie: str | None = field(
        default_factory=lambda: os.getenv("SNAPP_COOKIE")
    )
    sql_dir: Path = field(default_factory=lambda: ROOT_DIR / "sql")


def get_settings() -> Settings:
    return Settings()
