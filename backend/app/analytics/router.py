"""Analytics API — national, state, district, project level KPIs."""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.land_parcel import LandParcel
from app.models.compensation import Compensation
from app.models.family import Family
from app.models.dispute import Dispute
from app.models.ai_risk import AIRiskPrediction
from app.models.enums import ProjectStatus, PossessionStatus, CompensationStatus, DisputeStatus, RiskLevel

router = APIRouter()

@router.get("/national")
async def national_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """National-level KPI summary for the command center dashboard."""
    # Projects summary
    p_tot = (await db.execute(select(func.count()).select_from(Project).where(Project.deleted_at.is_(None)))).scalar_one()
    p_act = (await db.execute(select(func.count()).select_from(Project).where(Project.status == ProjectStatus.ACTIVE, Project.deleted_at.is_(None)))).scalar_one()
    p_comp = (await db.execute(select(func.count()).select_from(Project).where(Project.status == ProjectStatus.COMPLETED, Project.deleted_at.is_(None)))).scalar_one()

    # Parcels summary
    parc_tot = (await db.execute(select(func.count()).select_from(LandParcel))).scalar_one()
    parc_acq = (await db.execute(select(func.count()).select_from(LandParcel).where(LandParcel.possession_status == PossessionStatus.POSSESSED))).scalar_one()
    land_prop = (await db.execute(select(func.coalesce(func.sum(LandParcel.area_hectares), 0)))).scalar_one()
    land_acq = (await db.execute(select(func.coalesce(func.sum(LandParcel.area_hectares), 0)).where(LandParcel.possession_status == PossessionStatus.POSSESSED))).scalar_one()

    # Compensation summary
    comp_tot = (await db.execute(select(func.coalesce(func.sum(Compensation.disbursed_amount), 0)))).scalar_one()
    comp_paid = (await db.execute(select(func.coalesce(func.sum(Compensation.disbursed_amount), 0)).where(Compensation.status == CompensationStatus.DISBURSED))).scalar_one()
    comp_pend = (await db.execute(select(func.count()).select_from(Compensation).where(Compensation.status == CompensationStatus.PENDING))).scalar_one()

    # R&R and Disputes
    affected_families = (await db.execute(select(func.count()).select_from(Family))).scalar_one()
    disputed_parcels = (await db.execute(select(func.count()).select_from(Dispute).where(Dispute.status == DisputeStatus.OPEN))).scalar_one()

    # High risk projects count
    risk_r = await db.execute(select(AIRiskPrediction.project_id).where(AIRiskPrediction.risk_level.in_([RiskLevel.HIGH, RiskLevel.CRITICAL])))
    high_risk_projects = len(set(risk_r.scalars().all()))

    # State breakdown
    proj_r = await db.execute(select(Project.state, Project.status).where(Project.deleted_at.is_(None)))
    state_data = {}
    for st, status in proj_r.all():
        s = st or "National"
        if s not in state_data:
            state_data[s] = {"projects": 0, "active": 0, "completed": 0}
        state_data[s]["projects"] += 1
        if status == ProjectStatus.ACTIVE:
            state_data[s]["active"] += 1
        elif status == ProjectStatus.COMPLETED:
            state_data[s]["completed"] += 1

    return {
        "total_projects": p_tot,
        "active_projects": p_act,
        "completed_projects": p_comp,
        "total_parcels": parc_tot,
        "acquired_parcels": parc_acq,
        "acquisition_percentage": round((parc_acq / parc_tot * 100) if parc_tot else 0, 1),
        "land_proposed_hectares": round(float(land_prop), 2),
        "land_acquired_hectares": round(float(land_acq), 2),
        "compensation_assessed_crore": round(float(comp_tot) / 1e7, 2),
        "compensation_paid_crore": round(float(comp_paid) / 1e7, 2),
        "compensation_pending_count": comp_pend,
        "affected_families": affected_families,
        "disputed_parcels": disputed_parcels,
        "high_risk_projects": high_risk_projects,
        "state_breakdown": [{"state": k, **v} for k, v in state_data.items()],
    }

@router.get("/state/{state}")
async def state_analytics(
    state: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy.orm import defer
    proj_r = await db.execute(select(Project).where(Project.state == state, Project.deleted_at.is_(None)))
    projects = proj_r.scalars().all()
    parcel_r = await db.execute(select(LandParcel).options(defer(LandParcel.geometry)).where(LandParcel.state == state))
    parcels = parcel_r.scalars().all()
    # District breakdown
    district_data = {}
    for p in projects:
        d = p.district or "Unknown"
        if d not in district_data:
            district_data[d] = {"projects": 0, "active": 0}
        district_data[d]["projects"] += 1
        if p.status == ProjectStatus.ACTIVE:
            district_data[d]["active"] += 1

    return {
        "state": state,
        "total_projects": len(projects),
        "active_projects": sum(1 for p in projects if p.status == ProjectStatus.ACTIVE),
        "total_parcels": len(parcels),
        "acquired_parcels": sum(1 for p in parcels if p.possession_status == PossessionStatus.POSSESSED),
        "acquisition_percentage": round((sum(1 for p in parcels if p.possession_status == PossessionStatus.POSSESSED) / len(parcels) * 100) if parcels else 0, 1),
        "district_breakdown": [{"district": k, **v} for k, v in district_data.items()],
        "projects": [{"id": str(p.id), "name": p.name, "status": p.status.value, "district": p.district} for p in projects],
    }
