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

@router.get("/", response_model=list[ProjectResponse])
async def list_projects(
    state: Optional[str] = None,
    district: Optional[str] = None,
    status_filter: Optional[str] = None,
    risk_level: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(Project).where(Project.deleted_at.is_(None))
    if state:
        q = q.where(Project.state == state)
    if district:
        q = q.where(Project.district == district)
    if status_filter:
        q = q.where(Project.status == status_filter)
    # Jurisdiction scoping
    from app.models.enums import UserRole
    if current_user.role == UserRole.STATE_GOVT and current_user.state:
        q = q.where(Project.state == current_user.state)
    elif current_user.role == UserRole.DISTRICT_AUTHORITY:
        if current_user.state:
            q = q.where(Project.state == current_user.state)
        if current_user.district:
            q = q.where(Project.district == current_user.district)

    result = await db.execute(q.order_by(Project.created_at.desc()))
    projects = result.scalars().all()

    enriched = []
    for p in projects:
        pr = await _enrich_project(db, p)
        if risk_level and pr.get("risk_level") != risk_level:
            continue
        enriched.append(ProjectResponse(**pr))
    return enriched

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
        comp_r = await db.execute(select(func.count()).select_from(Compensation).where(Compensation.status == CompensationStatus.PENDING))
        d["compensation_pending"] = comp_r.scalar_one()
        disp_r = await db.execute(select(func.count()).select_from(Dispute).where(Dispute.parcel_id.in_(parcel_ids), Dispute.status == DisputeStatus.OPEN))
        d["disputed_parcels"] = disp_r.scalar_one()
    # R&R
    rr_r = await db.execute(select(func.count()).select_from(Family).where(Family.parcel_id.in_(parcel_ids if parcel_ids else [uuid.uuid4()])))
    d["rr_pending"] = rr_r.scalar_one()
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
