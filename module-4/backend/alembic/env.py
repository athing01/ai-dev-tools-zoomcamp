"""Alembic environment configuration for TaskFlow.

This module configures Alembic to use the shared SQLAlchemy metadata from
``taskflow_backend.db.base`` and ``taskflow_backend.db.models``.

The database URL is read from the ``DATABASE_URL`` environment variable.
If the variable is missing or malformed, Alembic fails explicitly — there
is no SQLite fallback and no silent default.
"""

from __future__ import annotations

import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Import the shared declarative base and ORM model so that Alembic can
# detect the schema from the metadata rather than inventing it.
from taskflow_backend.db.base import Base
from taskflow_backend.db.models import TaskModel  # noqa: F401  (registers model)

# Alembic Config object, provides access to values within the .ini file.
config = context.config

# Interpret the config file for Python logging. This line sets up
# loggers basically only to the console unless configured otherwise.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate / offline operations.
target_metadata = Base.metadata


def _get_database_url() -> str:
    """Return the database URL for migrations.

    Reads ``DATABASE_URL`` from the environment. Fails explicitly when
    the variable is missing or empty — there is no SQLite fallback.
    """
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is not set. The migration requires a PostgreSQL "
            "connection URL (e.g. postgresql+psycopg://…). "
            "There is no SQLite runtime fallback."
        )
    return database_url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Configures SQL to be emitted to the target database without using
    a connection pool.
    """
    url = _get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Creates an engine and associates a connection with the context.
    """
    url = _get_database_url()

    # Build the engine from the resolved URL so that the same value is
    # used for both migration execution and connection.
    section = {
        "sqlalchemy.url": url,
        "sqlalchemy.poolclass": pool.NullPool,
    }
    connectable = engine_from_config(section, prefix="sqlalchemy.")

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()