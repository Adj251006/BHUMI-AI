"""FastAPI application entry point.

Minimal skeleton for Module 1. Provides:
- A /health endpoint to verify the API and database are running.
- Lifespan handler for database connection setup / teardown.

Endpoints for auth, proposals, map, etc. will be added in subsequent modules.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.auth.router import router as auth_router
from app.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    # --- Startup ---
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        print("✓ Database connection verified")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        raise

    yield  # Application runs here

    # --- Shutdown ---
    await engine.dispose()
    print("✓ Database connections closed")


app = FastAPI(
    title="National Land Acquisition & Management System",
    description=(
        "SIH26016 — Ministry of Rural Development. "
        "Digitises the end-to-end land acquisition lifecycle under the "
        "Right to Fair Compensation and Transparency in Land Acquisition, "
        "Rehabilitation and Resettlement Act, 2013."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# Register routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])



@app.get("/health", tags=["System"])
async def health_check():
    """Verify that the API server and database are operational.

    Returns:
        {"status": "healthy", "database": "connected"} on success.
        {"status": "unhealthy", "database": "<error>"} on failure.
    """
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}
