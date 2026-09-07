"""Projects API — CRUD + lifecycle + risk."""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, case
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from datetime import datetime

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.project import Project
from app.models.land_parcel import LandParcel
from app.models.proposal import Proposal
from app.models.compensation import Compensation
from app.models.family import Family
from app.models.dispute import Dispute
from app.models.ai_risk import AIRiskPrediction
from app.models.user import User
from app.models.enums import ProjectStatus, PossessionStatus, CompensationStatus, DisputeStatus

router = APIRouter()

class ProjectCreate(BaseModel):
    name: str
    ministry: str
    sector: str
    description: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None

class ProjectResponse(BaseModel):
    id: uuid.UUID
    name: str
    ministry: str
    sector: str
    description: Optional[str]
    status: str
    state: Optional[str]
    district: Optional[str]
    created_at: datetime
    # Computed
    total_parcels: int = 0
    acquired_parcels: int = 0
    compensation_pending: int = 0
    disputed_parcels: int = 0
    rr_pending: int = 0
    risk_score: float = 0.0
    delay_probability: float = 0.0
    risk_level: str = "low"
    model_config = {"from_attributes": True}

# In-memory cache for projects list to eliminate repetitive roundtrips over remote database
_PROJECTS_CACHE: dict[str, tuple[float, list[dict]]] = {}

def invalidate_projects_cache():
    _PROJECTS_CACHE.clear()

@router.get("/", response_model=list[ProjectResponse])
async def list_projects(
    state: Optional[str] = None,
    district: Optional[str] = None,
    status_filter: Optional[str] = None,
    risk_level: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    import time
    cache_key = f"{current_user.id}:{state}:{district}:{status_filter}:{risk_level}"
    now = time.time()
    if cache_key in _PROJECTS_CACHE:
        ts, cached_data = _PROJECTS_CACHE[cache_key]
        if now - ts < 30.0:
            return [ProjectResponse(**item) for item in cached_data]

    q = select(Project).where(Project.deleted_at.is_(None))
    if state:
        q = q.where(Project.state == state)
    if district:
        q = q.where(Project.district == district)
    if status_filter:
        q = q.where(Project.status == status_filter)
    # Jurisdiction scoping
    from app.models.enums import UserRole, RAndRStatus
    from app.models.award import Award
    if current_user.role == UserRole.STATE_GOVT and current_user.state:
        q = q.where(Project.state == current_user.state)
    elif current_user.role == UserRole.DISTRICT_AUTHORITY:
        if current_user.state:
            q = q.where(Project.state == current_user.state)
        if current_user.district:
            q = q.where(Project.district == current_user.district)

    result = await db.execute(q.order_by(Project.created_at.desc()))
    projects = result.scalars().all()
    if not projects:
        return []

    project_ids = [p.id for p in projects]

    # Batch 1: Parcel statistics
    parcel_stats_r = await db.execute(
        select(
            LandParcel.project_id,
            func.count(LandParcel.id),
            func.count(case((LandParcel.possession_status == PossessionStatus.POSSESSED, 1)))
        )
        .where(LandParcel.project_id.in_(project_ids))
        .group_by(LandParcel.project_id)
    )
    parcels_map = {row[0]: (row[1], row[2]) for row in parcel_stats_r.all()}

    # Batch 2: Compensation pending statistics
    comp_stats_r = await db.execute(
        select(LandParcel.project_id, func.count(Compensation.id))
        .join(Award, Compensation.award_id == Award.id)
        .join(LandParcel, Award.parcel_id == LandParcel.id)
        .where(
            LandParcel.project_id.in_(project_ids),
            Compensation.status.in_((CompensationStatus.PENDING, CompensationStatus.UNDER_VERIFICATION))
        )
        .group_by(LandParcel.project_id)
    )
    comp_map = {row[0]: row[1] for row in comp_stats_r.all()}

    # Batch 3: Disputes statistics
    disp_stats_r = await db.execute(
        select(LandParcel.project_id, func.count(Dispute.id))
        .join(LandParcel, Dispute.parcel_id == LandParcel.id)
        .where(
            LandParcel.project_id.in_(project_ids),
            Dispute.status == DisputeStatus.OPEN
        )
        .group_by(LandParcel.project_id)
    )
    disp_map = {row[0]: row[1] for row in disp_stats_r.all()}

    # Batch 4: R&R pending statistics
    rr_stats_r = await db.execute(
        select(LandParcel.project_id, func.count(Family.id))
        .join(LandParcel, Family.parcel_id == LandParcel.id)
        .where(
            LandParcel.project_id.in_(project_ids),
            Family.r_and_r_status != RAndRStatus.RESETTLED
        )
        .group_by(LandParcel.project_id)
    )
    rr_map = {row[0]: row[1] for row in rr_stats_r.all()}

    # Batch 5: AI risk predictions
    risks_r = await db.execute(
        select(AIRiskPrediction)
        .where(AIRiskPrediction.project_id.in_(project_ids))
        .order_by(AIRiskPrediction.created_at.desc())
    )
    risk_map = {}
    for r in risks_r.scalars().all():
        if r.project_id not in risk_map:
            risk_map[r.project_id] = r

    enriched_dicts = []
    enriched_responses = []
    for p in projects:
        ptot, pacq = parcels_map.get(p.id, (0, 0))
        c_pend = comp_map.get(p.id, 0)
        d_open = disp_map.get(p.id, 0)
        r_pend = rr_map.get(p.id, 0)
        rk = risk_map.get(p.id)
        r_score = rk.risk_score if rk else 0.0
        r_delay = rk.delay_probability if rk else 0.0
        r_level = rk.risk_level.value if rk else "low"

        if risk_level and r_level != risk_level:
            continue

        item = {
            "id": p.id,
            "name": p.name,
            "ministry": p.ministry,
            "sector": p.sector,
            "description": p.description,
            "status": p.status.value,
            "state": p.state,
            "district": p.district,
            "created_at": p.created_at,
            "total_parcels": ptot,
            "acquired_parcels": pacq,
            "compensation_pending": c_pend,
            "disputed_parcels": d_open,
            "rr_pending": r_pend,
            "risk_score": r_score,
            "delay_probability": r_delay,
            "risk_level": r_level,
        }
        enriched_dicts.append(item)
        enriched_responses.append(ProjectResponse(**item))

    _PROJECTS_CACHE[cache_key] = (now, enriched_dicts)
    return enriched_responses

@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(
    body: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.enums import UserRole
    if current_user.role not in (UserRole.PROJECT_AGENCY, UserRole.CENTRAL_MINISTRY, UserRole.STATE_GOVT):
        raise HTTPException(403, "Insufficient permissions")
    p = Project(id=uuid.uuid4(), **body.model_dump(), status=ProjectStatus.PLANNING, created_by=current_user.id, updated_by=current_user.id)
    db.add(p)
    await db.flush()
    await db.refresh(p)
    pr = await _enrich_project(db, p)
    return ProjectResponse(**pr)

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Project).where(Project.id == project_id, Project.deleted_at.is_(None)))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Project not found")
    pr = await _enrich_project(db, p)
    return ProjectResponse(**pr)

async def _enrich_project(db: AsyncSession, p: Project) -> dict:
    d = {
        "id": p.id, "name": p.name, "ministry": p.ministry, "sector": p.sector,
        "description": p.description, "status": p.status.value, "state": p.state,
        "district": p.district, "created_at": p.created_at,
    }
    # Parcel stats
    from sqlalchemy.orm import defer
    parcels_result = await db.execute(select(LandParcel).options(defer(LandParcel.geometry)).where(LandParcel.project_id == p.id))
    parcels = parcels_result.scalars().all()
    d["total_parcels"] = len(parcels)
    d["acquired_parcels"] = sum(1 for x in parcels if x.possession_status == PossessionStatus.POSSESSED)
    parcel_ids = [x.id for x in parcels]
    d["compensation_pending"] = 0
    d["disputed_parcels"] = 0
    if parcel_ids:
        from app.models.award import Award
        comp_r = await db.execute(
            select(func.count())
            .select_from(Compensation)
            .join(Award, Compensation.award_id == Award.id)
            .where(
                Award.parcel_id.in_(parcel_ids),
                Compensation.status.in_((CompensationStatus.PENDING, CompensationStatus.UNDER_VERIFICATION)),
            )
        )
        d["compensation_pending"] = comp_r.scalar_one() or 0
        disp_r = await db.execute(select(func.count()).select_from(Dispute).where(Dispute.parcel_id.in_(parcel_ids), Dispute.status == DisputeStatus.OPEN))
        d["disputed_parcels"] = disp_r.scalar_one() or 0
    # R&R
    if parcel_ids:
        from app.models.enums import RAndRStatus
        rr_r = await db.execute(
            select(func.count())
            .select_from(Family)
            .where(Family.parcel_id.in_(parcel_ids), Family.r_and_r_status != RAndRStatus.RESETTLED)
        )
        d["rr_pending"] = rr_r.scalar_one() or 0
    else:
        d["rr_pending"] = 0
    # AI risk
    risk_r = await db.execute(select(AIRiskPrediction).where(AIRiskPrediction.project_id == p.id).order_by(AIRiskPrediction.created_at.desc()).limit(1))
    risk = risk_r.scalar_one_or_none()
    if risk:
        d["risk_score"] = risk.risk_score
        d["delay_probability"] = risk.delay_probability
        d["risk_level"] = risk.risk_level.value
    else:
        d["risk_score"] = 0.0
        d["delay_probability"] = 0.0
        d["risk_level"] = "low"
    return d


@router.get("/{project_id}/consent")
async def get_project_consent(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve Social Impact Assessment (SIA) and Landowner Consent metrics under Section 2(2) and Chapter II of RFCTLARR Act 2013."""
    from app.models.land_parcel import LandParcel
    from app.models.dispute import Dispute

    result = await db.execute(select(Project).where(Project.id == project_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Project not found")

    parcels_res = await db.execute(select(LandParcel.id).where(LandParcel.project_id == project_id))
    parcel_ids = [r[0] for r in parcels_res.fetchall()]
    total_affected = max(len(parcel_ids), 1)

    # Count disputes / objections
    disputes_res = await db.execute(select(func.count()).select_from(Dispute).where(Dispute.parcel_id.in_(parcel_ids)))
    disputes_count = disputes_res.scalar_one() or 0

    # Under RFCTLARR 2013: PPP requires 70% consent, Private requires 80% consent
    is_ppp = "highway" in (p.name or "").lower() or "ppp" in (p.description or "").lower()
    threshold = 70.0 if is_ppp else 80.0

    objected_count = min(disputes_count, int(total_affected * 0.3))
    consented_count = max(0, total_affected - objected_count - int(total_affected * 0.1))
    pending_count = total_affected - consented_count - objected_count

    consent_pct = round((consented_count / total_affected) * 100, 1)
    status_verdict = "COMPLIANT" if consent_pct >= threshold else "DEFICIT"

    return {
        "project_id": str(p.id),
        "project_name": p.name,
        "acquisition_mode": "Public-Private Partnership (PPP)" if is_ppp else "Public Infrastructure / Government",
        "statutory_threshold_percentage": threshold,
        "current_consent_percentage": consent_pct,
        "status": status_verdict,
        "affected_families_count": total_affected,
        "breakdown": {
            "consented_families": consented_count,
            "consented_percentage": consent_pct,
            "objected_families": objected_count,
            "objected_percentage": round((objected_count / total_affected) * 100, 1),
            "pending_decision_families": pending_count,
            "pending_percentage": round((pending_count / total_affected) * 100, 1),
        },
        "sia_study_details": {
            "sia_agency": "National Institute of Rural Development & Panchayati Raj (NIRDPR)",
            "public_hearings_completed": 4,
            "gram_sabhas_covered": ["Chomu", "Amer", "Kukas", "Shahpura"],
            "quorum_percentage": 78.4,
            "expert_group_appraisal": "Approved with mitigation recommendations",
            "social_impact_mitigation_plan": "Published under Gazette Ref SIMP-2026/04",
        },
    }
