"""Apply numbered SQL files to an initialized database without resetting data."""

import logging
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import Connection

logger = logging.getLogger(__name__)
MIGRATIONS_DIR = Path(__file__).with_name("migrations")


def migrate(connection: Connection, directory: Path = MIGRATIONS_DIR) -> None:
    """Caller owns the transaction. Serialize migration runners with a DB lock."""
    connection.execute(text("SELECT pg_advisory_xact_lock(7202601005)"))
    connection.execute(text(
        "CREATE TABLE IF NOT EXISTS schema_migrations "
        "(name text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())"
    ))
    applied = 0
    for path in sorted(directory.glob("*.sql")):
        if connection.execute(
            text("SELECT 1 FROM schema_migrations WHERE name = :name"), {"name": path.name}
        ).first():
            continue
        connection.exec_driver_sql(path.read_text(), execution_options={"no_parameters": True})
        connection.execute(
            text("INSERT INTO schema_migrations (name) VALUES (:name)"), {"name": path.name}
        )
        logger.info("Applied migration %s", path.name)
        applied += 1
    logger.info("Migrations complete; applied %s file(s)", applied)


if __name__ == "__main__":
    from db import engine

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        with engine.begin() as connection:
            migrate(connection)
    finally:
        engine.dispose()
