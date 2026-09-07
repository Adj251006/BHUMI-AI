"""Analytics API — national, state, district, project level KPIs."""
import time
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
_NATIONAL_CACHE = {"timestamp": 0.0, "data": None}
_STATE_CACHE: dict[str, tuple[float, dict]] = {}

def invalidate_analytics_cache():
    _NATIONAL_CACHE["data"] = None
    _STATE_CACHE.clear()

@router.get("/national")
async def national_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """National-level KPI summary for the command center dashboard."""
    now = time.time()
    if _NATIONAL_CACHE["data"] is not None and (now - _NATIONAL_CACHE["timestamp"] < 60):
        return _NATIONAL_CACHE["data"]

    from sqlalchemy import text

    # Unified single SQL aggregation to eliminate 14 sequential roundtrips over remote DB
    unified_sql = text("""
        SELECT 
            (SELECT count(*) FROM projects WHERE deleted_at IS NULL) as p_tot,
            (SELECT count(*) FROM projects WHERE status = 'active' AND deleted_at IS NULL) as p_act,
            (SELECT count(*) FROM projects WHERE status = 'completed' AND deleted_at IS NULL) as p_comp,
            (SELECT count(*) FROM land_parcels WHERE deleted_at IS NULL) as parc_tot,
            (SELECT count(*) FROM land_parcels WHERE possession_status = 'possessed' AND deleted_at IS NULL) as parc_acq,
            (SELECT coalesce(sum(area_hectares), 0) FROM land_parcels WHERE deleted_at IS NULL) as land_prop,
            (SELECT coalesce(sum(area_hectares), 0) FROM land_parcels WHERE possession_status = 'possessed' AND deleted_at IS NULL) as land_acq,
            (SELECT coalesce(sum(disbursed_amount), 0) FROM compensations) as comp_tot,
            (SELECT coalesce(sum(disbursed_amount), 0) FROM compensations WHERE status = 'disbursed') as comp_paid,
            (SELECT count(*) FROM compensations WHERE status = 'pending') as comp_pend,
            (SELECT count(*) FROM families) as affected_families,
            (SELECT count(*) FROM disputes WHERE status = 'open') as disputed_parcels,
            (SELECT count(DISTINCT project_id) FROM ai_risk_predictions WHERE risk_level IN ('high', 'critical')) as high_risk_projects;
    """)
    res_row = (await db.execute(unified_sql)).mappings().one()

    # State breakdown aggregated query
    state_sql = text("""
        SELECT coalesce(state, 'National') as st, status, count(*) as cnt
        FROM projects
        WHERE deleted_at IS NULL
        GROUP BY state, status;
    """)
    state_rows = (await db.execute(state_sql)).all()
    state_data = {}
    for st, status, cnt in state_rows:
        if st not in state_data:
            state_data[st] = {"projects": 0, "active": 0, "completed": 0}
        state_data[st]["projects"] += cnt
        if status == 'active':
            state_data[st]["active"] += cnt
        elif status == 'completed':
            state_data[st]["completed"] += cnt

    parc_tot = res_row["parc_tot"]
    parc_acq = res_row["parc_acq"]

    res = {
        "total_projects": res_row["p_tot"],
        "active_projects": res_row["p_act"],
        "completed_projects": res_row["p_comp"],
        "total_parcels": parc_tot,
        "acquired_parcels": parc_acq,
        "acquisition_percentage": round((parc_acq / parc_tot * 100) if parc_tot else 0, 1),
        "land_proposed_hectares": round(float(res_row["land_prop"]), 2),
        "land_acquired_hectares": round(float(res_row["land_acq"]), 2),
        "compensation_assessed_crore": round(float(res_row["comp_tot"]) / 1e7, 2),
        "compensation_paid_crore": round(float(res_row["comp_paid"]) / 1e7, 2),
        "compensation_pending_count": res_row["comp_pend"],
        "affected_families": res_row["affected_families"],
        "disputed_parcels": res_row["disputed_parcels"],
        "high_risk_projects": res_row["high_risk_projects"],
        "state_breakdown": [{"state": k, **v} for k, v in state_data.items()],
    }
    _NATIONAL_CACHE["data"] = res
    _NATIONAL_CACHE["timestamp"] = time.time()
    return res

@router.get("/state/{state}")
async def state_analytics(
    state: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = time.time()
    if state in _STATE_CACHE:
        ts, data = _STATE_CACHE[state]
        if now - ts < 60:
            return data

    from sqlalchemy import text
    from sqlalchemy.orm import defer
    proj_r = await db.execute(select(Project).where(Project.state == state, Project.deleted_at.is_(None)))
    projects = proj_r.scalars().all()

    # Fast parcel count without loading GIS geometries
    parcel_count_sql = text("""
        SELECT 
            count(*) as total,
            count(*) FILTER (WHERE possession_status = 'possessed') as acquired
        FROM land_parcels
        WHERE state = :state AND deleted_at IS NULL;
    """)
    p_row = (await db.execute(parcel_count_sql, {"state": state})).mappings().one()
    p_total = p_row["total"] or 0
    p_acquired = p_row["acquired"] or 0

    district_data = {}
    for p in projects:
        d = p.district or "Unknown"
        if d not in district_data:
            district_data[d] = {"projects": 0, "active": 0}
        district_data[d]["projects"] += 1
        if p.status == ProjectStatus.ACTIVE:
            district_data[d]["active"] += 1

    res = {
        "state": state,
        "total_projects": len(projects),
        "active_projects": sum(1 for p in projects if p.status == ProjectStatus.ACTIVE),
        "total_parcels": p_total,
        "acquired_parcels": p_acquired,
        "acquisition_percentage": round((p_acquired / p_total * 100) if p_total else 0, 1),
        "district_breakdown": [{"district": k, **v} for k, v in district_data.items()],
        "projects": [{"id": str(p.id), "name": p.name, "status": p.status.value, "district": p.district} for p in projects],
    }
    _STATE_CACHE[state] = (now, res)
    return res

async def warm_national_cache():
    """Pre-compute national analytics into memory at server startup."""
    from app.database import AsyncSessionLocal
    try:
        async with AsyncSessionLocal() as session:
            await national_analytics(db=session, current_user=None)
            print("✓ National analytics cache pre-warmed")
    except Exception as e:
        print(f"⚠️ Cache pre-warm note: {e}")
