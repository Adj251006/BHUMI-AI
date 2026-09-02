"""Database engine and session management.

Provides:
- An async SQLAlchemy engine (via asyncpg) for the FastAPI application.
- An async session factory for dependency injection in route handlers.
- A URL helper to convert between sync/async PostgreSQL drivers.

The sync psycopg2 driver is used separately by Alembic (alembic/env.py)
and the seed script (scripts/seed.py) — see those files for details.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings


def _to_async_url(url: str) -> str:
    """Convert a standard postgresql:// URL to use the asyncpg driver.

    Examples:
        postgresql://user:pass@host/db  →  postgresql+asyncpg://user:pass@host/db
        postgresql+asyncpg://...        →  (unchanged)
    """
    if "asyncpg" in url:
        return url
    return url.replace("postgresql://", "postgresql+asyncpg://", 1)


# ---------------------------------------------------------------------------
# Async engine for the FastAPI application
# ---------------------------------------------------------------------------

engine = create_async_engine(
    _to_async_url(settings.database_url),
    # Pool settings are conservative — Supabase free tier allows ~60 connections.
    pool_size=5,
    max_overflow=10,
    # Verify connections before checkout (handles Supabase idle disconnects).
    pool_pre_ping=True,
    # Log SQL in development mode only.
    echo=(settings.environment == "development"),
)

# ---------------------------------------------------------------------------
# Async session factory
# ---------------------------------------------------------------------------

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a database session per request.

    Usage in a route handler:
        @router.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            ...

    Commits on success, rolls back on any exception.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
