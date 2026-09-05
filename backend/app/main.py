"""FastAPI application entry point — BHUMI-AI Backend.

BHUMI-AI: Intelligent National Land Acquisition & Management Platform
SIH26016 — Ministry of Rural Development
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.auth.router import router as auth_router
from app.database import engine
from app.proposals.router import router as proposals_router
from app.parcels.router import router as parcels_router
from app.projects.router import router as projects_router
from app.analytics.router import router as analytics_router
from app.ai.router import router as ai_router
from app.rr.router import router as rr_router
from app.domain_routers import (
    comp_router,
    dispute_router,
    doc_router,
    workflow_router,
    field_router,
    notif_router,
    audit_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        print("✓ Database connection verified")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        raise

    yield

    await engine.dispose()
    print("✓ Database connections closed")


app = FastAPI(
    title="BHUMI-AI — National Land Acquisition & Management System",
    description=(
        "SIH26016 — Ministry of Rural Development. "
        "Intelligent National Land Acquisition & Management Platform. "
        "Combines GIS, workflow automation, document intelligence, "
        "predictive analytics and AI decision support."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])

# Core domain
app.include_router(projects_router, prefix="/api/projects", tags=["Projects"])
app.include_router(proposals_router, prefix="/proposals", tags=["Proposals"])
app.include_router(parcels_router, prefix="/api/parcels", tags=["Parcels (GIS)"])

# Analytics & AI
app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(ai_router, prefix="/api/ai", tags=["AI Services"])

# Operations
app.include_router(comp_router, prefix="/api/compensation", tags=["Compensation"])
app.include_router(dispute_router, prefix="/api/disputes", tags=["Disputes"])
app.include_router(doc_router, prefix="/api/documents", tags=["Documents"])
app.include_router(workflow_router, prefix="/api/workflow", tags=["Workflow"])
app.include_router(field_router, prefix="/api/field", tags=["Field Verification"])
app.include_router(rr_router, prefix="/api/rr", tags=["R&R Management"])
app.include_router(notif_router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(audit_router, prefix="/api/audit", tags=["Audit"])


@app.get("/health", tags=["System"])
async def health_check():
    """Verify that the API server and database are operational."""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected", "platform": "BHUMI-AI v1.0"}
    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}


@app.get("/api/citizen/track/{parcel_reference:path}")
async def citizen_track(parcel_reference: str):
    """Public citizen tracking endpoint — no auth required."""
    from app.database import AsyncSessionLocal
    from app.models.land_parcel import LandParcel
    from app.models.project import Project
    from app.models.award import Award
    from app.models.compensation import Compensation
    from app.models.family import Family
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        # Try to find by survey number or partial ID
        result = await db.execute(
            select(LandParcel).where(LandParcel.survey_number.ilike(f"%{parcel_reference}%")).limit(1)
        )
        parcel = result.scalar_one_or_none()

        if not parcel:
            return {"found": False, "message": "No parcel found with this reference. Please check the Parcel ID or Survey Number."}

        # Get project
        proj_r = await db.execute(select(Project).where(Project.id == parcel.project_id))
        project = proj_r.scalar_one_or_none()

        # Get award
        award_r = await db.execute(select(Award).where(Award.parcel_id == parcel.id))
        award = award_r.scalar_one_or_none()

        # Get compensation
        comp_data = None
        if award:
            comp_r = await db.execute(select(Compensation).where(Compensation.award_id == award.id).limit(1))
            comp = comp_r.scalar_one_or_none()
            if comp:
                comp_data = {
                    "assessed_amount": float(award.declared_amount),
                    "paid_amount": float(comp.disbursed_amount) if comp.status.value == "disbursed" else 0,
                    "pending_amount": float(comp.disbursed_amount) if comp.status.value != "disbursed" else 0,
                    "status": comp.status.value,
                    "payment_reference": comp.payment_reference,
                }

        # Timeline based on possession status
        status_val = parcel.possession_status.value
        timeline = [
            {"stage": "Preliminary Notification", "status": "completed", "icon": "check"},
            {"stage": "Survey & Measurement", "status": "completed" if status_val in ["notice_issued", "awarded", "possessed"] else "pending", "icon": "check" if status_val != "not_acquired" else "circle"},
            {"stage": "Award Declaration", "status": "completed" if status_val in ["awarded", "possessed"] else "in_progress" if status_val == "notice_issued" else "pending", "icon": "check" if status_val in ["awarded", "possessed"] else "dot"},
            {"stage": "Compensation", "status": "in_progress" if status_val == "awarded" else "completed" if status_val == "possessed" else "pending", "icon": "dot" if status_val == "awarded" else "check" if status_val == "possessed" else "circle"},
            {"stage": "R&R", "status": "pending" if status_val in ["not_acquired", "notice_issued"] else "in_progress", "icon": "circle"},
            {"stage": "Possession", "status": "completed" if status_val == "possessed" else "pending", "icon": "check" if status_val == "possessed" else "circle"},
        ]

        return {
            "found": True,
            "parcel": {
                "id": str(parcel.id),
                "survey_number": parcel.survey_number,
                "village": parcel.village,
                "district": parcel.district,
                "state": parcel.state,
                "area_hectares": float(parcel.area_hectares),
                "land_type": parcel.land_type.value,
                "possession_status": status_val,
            },
            "project": {
                "name": project.name if project else "Unknown",
                "ministry": project.ministry if project else "Unknown",
                "status": project.status.value if project else "unknown",
            },
            "timeline": timeline,
            "compensation": comp_data,
        }
