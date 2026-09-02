"""SQLAlchemy engine and session helpers."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from catalog_ingest.config import Settings, get_settings

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def get_engine(settings: Settings | None = None) -> Engine:
    global _engine, _SessionLocal
    settings = settings or get_settings()
    if _engine is None:
        _engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            future=True,
        )
        _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)
    return _engine


def get_session_factory(settings: Settings | None = None) -> sessionmaker[Session]:
    get_engine(settings)
    assert _SessionLocal is not None
    return _SessionLocal


@contextmanager
def session_scope(settings: Settings | None = None) -> Iterator[Session]:
    factory = get_session_factory(settings)
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def apply_ddl(settings: Settings | None = None) -> None:
    """Apply SQL files from sql/ in alphabetical order.

    Supports both PostgreSQL (full DDL) and SQLite (local dev mode).
    For SQLite, strips PostgreSQL-specific statements like EXTENSION and
    GENERATED ALWAYS AS STORED (computed columns) before executing.
    """
    settings = settings or get_settings()
    engine = get_engine(settings)
    sql_files = sorted(settings.sql_dir.glob("*.sql"))
    if not sql_files:
        raise FileNotFoundError(f"No SQL files found in {settings.sql_dir}")

    is_sqlite = settings.database_url.startswith("sqlite")

    with engine.begin() as conn:
        for path in sql_files:
            script = path.read_text(encoding="utf-8")

            if is_sqlite:
                # SQLite doesn't support: EXTENSION, GENERATED ALWAYS AS … STORED,
                # LANGUAGE plpgsql, TIMESTAMPTZ, DROP/CREATE TRIGGER, CREATE FUNCTION
                # We execute each statement individually and skip unsupported ones.
                import re as _re
                stmts = [s.strip() for s in script.split(";") if s.strip()]
                for stmt in stmts:
                    upper = stmt.upper()
                    if any(kw in upper for kw in [
                        "CREATE EXTENSION",
                        "LANGUAGE PLPGSQL",
                        "CREATE OR REPLACE FUNCTION",
                        "CREATE TRIGGER",
                        "DROP TRIGGER",
                        "EXECUTE PROCEDURE",
                    ]):
                        continue  # skip PostgreSQL-only DDL
                    # Remove GENERATED ALWAYS AS … STORED columns from CREATE TABLE
                    stmt = _re.sub(
                        r",\s*\w+\s+TEXT\s+GENERATED ALWAYS AS\s*\([^)]+\)\s+STORED",
                        "",
                        stmt,
                        flags=_re.IGNORECASE | _re.DOTALL,
                    )
                    # Replace TIMESTAMPTZ with TEXT (SQLite is typeless but labels help)
                    stmt = stmt.replace("TIMESTAMPTZ", "TEXT")
                    try:
                        conn.execute(text(stmt))
                    except Exception as exc:
                        import logging as _logging
                        _logging.getLogger(__name__).warning(
                            "SQLite DDL stmt skipped (%s): %s…", exc, stmt[:80]
                        )
            else:
                # PostgreSQL: use raw psycopg2 cursor for multi-statement scripts
                raw = conn.connection.dbapi_connection
                with raw.cursor() as cur:
                    cur.execute(script)

