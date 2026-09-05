"""Alembic migration environment configuration.

This file is the bridge between Alembic and our SQLAlchemy models.
It uses the SYNCHRONOUS psycopg2 driver for migrations — the async
asyncpg driver is used only by the FastAPI application (app/database.py).

Key setup:
1. Imports app.config.settings to get DATABASE_URL from .env
2. Imports all models via app.models to register them with Base.metadata
3. Creates the engine directly from DATABASE_URL (bypassing alembic.ini)
"""

from logging.config import fileConfig

from alembic import context
# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine, pool

# Import GeoAlchemy2 so its column types are registered with Alembic's
# autogenerate — without this, Geometry columns won't render correctly.
# pyrefly: ignore [missing-import]
import geoalchemy2  # noqa: F401

# Import all models to register them with Base.metadata.
# This single import pulls in every model via app/models/__init__.py.
from app.models import Base

# Import settings to get the database URL
from app.config import settings


# ---------------------------------------------------------------------------
# Alembic Config object — provides access to alembic.ini values
# ---------------------------------------------------------------------------
config = context.config

# Build the sync database URL.
# We strip any async driver prefix since Alembic uses psycopg2 (sync).
# NOTE: We do NOT use config.set_main_option() because configparser
# treats '%' as interpolation syntax, which breaks URL-encoded passwords.
db_url = settings.database_url
if "+asyncpg" in db_url:
    db_url = db_url.replace("+asyncpg", "")

# Set up Python logging from alembic.ini's [loggers] section
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata — Alembic uses this to detect schema changes
# when running `alembic revision --autogenerate`.
target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Migration runners
# ---------------------------------------------------------------------------


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Generates SQL scripts without connecting to the database.
    Useful for review or manual application.
    """
    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Creates the engine directly from the URL (not via configparser)
    to avoid issues with special characters in passwords.
    Uses NullPool to avoid holding connections after migration completes.
    """
    connectable = create_engine(db_url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

