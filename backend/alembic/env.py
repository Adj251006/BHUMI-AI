"""Alembic migration environment configuration.

This file is the bridge between Alembic and our SQLAlchemy models.
It uses the SYNCHRONOUS psycopg2 driver for migrations — the async
asyncpg driver is used only by the FastAPI application (app/database.py).

Key setup:
1. Imports app.config.settings to get DATABASE_URL from .env
2. Imports all models via app.models to register them with Base.metadata
3. Overrides the alembic.ini sqlalchemy.url with the real DATABASE_URL
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Import GeoAlchemy2 so its column types are registered with Alembic's
# autogenerate — without this, Geometry columns won't render correctly.
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

# Override the placeholder URL from alembic.ini with the real one from .env.
# We strip any async driver prefix since Alembic uses psycopg2 (sync).
db_url = settings.database_url
if "+asyncpg" in db_url:
    db_url = db_url.replace("+asyncpg", "")
config.set_main_option("sqlalchemy.url", db_url)

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
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Connects to the database and applies migrations directly.
    Uses NullPool to avoid holding connections after migration completes.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

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
