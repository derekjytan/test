"""Exercise real PostgreSQL migration transactions without touching app data."""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from migrate import migrate


def applied_names(connection):
    return set(connection.scalars(text("SELECT name FROM schema_migrations")))


def test_empty_directory_preserves_application_data(database, tmp_path):
    with database.begin() as connection:
        history = applied_names(connection)
        before = connection.execute(text(
            "SELECT id, title, updated_at FROM conversations ORDER BY id"
        )).all()
        migrate(connection, tmp_path)
    with database.connect() as connection:
        assert connection.execute(text(
            "SELECT id, title, updated_at FROM conversations ORDER BY id"
        )).all() == before
        assert applied_names(connection) == history


def test_migrations_apply_in_order_and_only_once(database, tmp_path):
    with database.connect() as connection:
        history = applied_names(connection)
    # Write the later file first to ensure directory enumeration is not the order.
    (tmp_path / "901_test_seed.sql").write_text(
        "INSERT INTO migration_example (note) VALUES ('100% ready');"
    )
    (tmp_path / "900_test_create.sql").write_text(
        "CREATE TABLE migration_example (note text NOT NULL);"
    )
    with database.begin() as connection:
        migrate(connection, tmp_path)
    # The CREATE and INSERT would fail or duplicate data if reapplied.
    with database.begin() as connection:
        migrate(connection, tmp_path)
    with database.connect() as connection:
        assert connection.scalars(text("SELECT note FROM migration_example")).all() == ["100% ready"]
        assert applied_names(connection) == history | {"900_test_create.sql", "901_test_seed.sql"}


def test_failed_batch_rolls_back_and_can_be_retried(database, tmp_path):
    with database.connect() as connection:
        history = applied_names(connection)
    (tmp_path / "900_test_create.sql").write_text("CREATE TABLE migration_example (note text);")
    failing = tmp_path / "901_test_insert.sql"
    failing.write_text("INSERT INTO migration_example (missing_column) VALUES ('fail');")
    with pytest.raises(DBAPIError):
        with database.begin() as connection:
            migrate(connection, tmp_path)
    with database.connect() as connection:
        assert connection.scalar(text("SELECT to_regclass('migration_example')")) is None
        assert applied_names(connection) == history
    failing.write_text("INSERT INTO migration_example (note) VALUES ('recovered');")
    with database.begin() as connection:
        migrate(connection, tmp_path)
    with database.connect() as connection:
        assert connection.scalar(text("SELECT note FROM migration_example")) == "recovered"
