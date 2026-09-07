"""Database grounding tools and retrieval helpers for BHUMI Copilot.

Provides safe, read-only, sanitized data retrieval functions for the AI agent.
Guarantees zero leakage of PII (Aadhaar, PAN, passwords, bank account numbers).
"""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.award import Award
from app.models.compensation import Compensation
from app.models.dispute import Dispute
from app.models.enums import (
    CompensationStatus,
    DisputeStatus,
    PossessionStatus,
    RAndRStatus,
    TaskStatus,
)
from app.models.family import Family
from app.models.land_parcel import LandParcel
from app.models.project import Project
from app.models.ai_risk import AIRiskPrediction
from app.models.workflow_task import WorkflowTask
from app.models.audit_log import AuditLog
from app.models.document import Document


async def get_project_details(db: AsyncSession, project_id: uuid.UUID) -> Optional[Dict[str, Any]]:
    """Retrieve high-level project information."""
    result = await db.execute(select(Project).where(Project.id == project_id, Project.deleted_at.is_(None)))
    p = result.scalar_one_or_none()
    if not p:
        return None
    return {
        "id": str(p.id),
        "code": getattr(p, "code", str(p.id)[:8]),
        "name": p.name,
        "ministry": p.ministry,
        "sector": p.sector,
        "description": p.description,
        "status": p.status.value,
        "state": p.state,
        "district": p.district,
    }


async def get_project_risk(db: AsyncSession, project_id: uuid.UUID) -> Optional[Dict[str, Any]]:
    """Retrieve the latest AI risk prediction and factor breakdown."""
    result = await db.execute(
        select(AIRiskPrediction)
        .where(AIRiskPrediction.project_id == project_id)
        .order_by(AIRiskPrediction.created_at.desc())
        .limit(1)
    )
    r = result.scalar_one_or_none()
    if not r:
        return None
    return {
        "risk_level": r.risk_level.value,
        "risk_score": r.risk_score,
        "delay_probability": r.delay_probability,
        "delay_probability_pct": round(r.delay_probability * 100, 1),
        "expected_delay_days": r.expected_delay_days,
        "contributing_factors": r.contributing_factors or [],
        "explanation": r.explanation,
    }


async def get_project_parcels_summary(db: AsyncSession, project_id: uuid.UUID) -> Dict[str, Any]:
    """Retrieve parcel acquisition status and counts for a project."""
    parcels_res = await db.execute(
        select(LandParcel).where(LandParcel.project_id == project_id, LandParcel.deleted_at.is_(None))
    )
    parcels = parcels_res.scalars().all()
    total = len(parcels)
    possessed = sum(1 for p in parcels if p.possession_status == PossessionStatus.POSSESSED)
    awarded = sum(1 for p in parcels if p.possession_status == PossessionStatus.AWARDED)
    notice = sum(1 for p in parcels if p.possession_status == PossessionStatus.NOTICE_ISSUED)
    not_acquired = sum(1 for p in parcels if p.possession_status == PossessionStatus.NOT_ACQUIRED)
    total_area = sum(float(p.area_hectares or 0) for p in parcels)

    # Critical / high dispute parcels
    disputes_res = await db.execute(
        select(Dispute.parcel_id).where(Dispute.status == DisputeStatus.OPEN, Dispute.deleted_at.is_(None))
    )
    disputed_parcel_ids = set(disputes_res.scalars().all())
    critical_parcels = [
        {"id": str(p.id), "survey_number": p.survey_number, "village": p.village, "area": float(p.area_hectares)}
        for p in parcels
        if p.id in disputed_parcel_ids
    ][:10]

    return {
        "total_parcels": total,
        "total_area_hectares": round(total_area, 2),
        "possessed_parcels": possessed,
        "awarded_parcels": awarded,
        "notice_issued_parcels": notice,
        "not_acquired_parcels": not_acquired,
        "possession_rate_pct": round((possessed / total * 100), 1) if total > 0 else 0,
        "critical_disputed_count": len(critical_parcels),
        "sample_critical_parcels": critical_parcels,
    }


async def get_open_disputes(db: AsyncSession, project_id: Optional[uuid.UUID] = None) -> List[Dict[str, Any]]:
    """Retrieve open land/court disputes."""
    q = select(Dispute).where(Dispute.status == DisputeStatus.OPEN, Dispute.deleted_at.is_(None))
    if project_id:
        parcels_q = select(LandParcel.id).where(LandParcel.project_id == project_id)
        q = q.where(Dispute.parcel_id.in_(parcels_q))
    result = await db.execute(q.order_by(Dispute.created_at.desc()).limit(20))
    disputes = result.scalars().all()
    return [
        {
            "id": str(d.id),
            "parcel_id": str(d.parcel_id),
            "dispute_type": d.dispute_type,
            "title": d.title,
            "description": d.description,
            "court_case_number": d.court_case_number,
            "hearing_date": d.hearing_date.isoformat() if d.hearing_date else None,
        }
        for d in disputes
    ]


async def get_compensation_backlog(db: AsyncSession, project_id: Optional[uuid.UUID] = None) -> Dict[str, Any]:
    """Retrieve compensation status metrics and pending records."""
    q = select(Compensation).where(Compensation.deleted_at.is_(None))
    if project_id:
        q = q.join(Award, Compensation.award_id == Award.id).join(LandParcel, Award.parcel_id == LandParcel.id).where(LandParcel.project_id == project_id)
    res = await db.execute(q)
    all_comp = res.scalars().all()

    pending = [c for c in all_comp if c.status in (CompensationStatus.PENDING, CompensationStatus.UNDER_VERIFICATION)]
    disbursed = [c for c in all_comp if c.status == CompensationStatus.DISBURSED]

    total_disbursed_amt = sum(float(c.disbursed_amount or 0) for c in disbursed)
    total_pending_amt = sum(float(c.disbursed_amount or 0) for c in pending)

    return {
        "total_records": len(all_comp),
        "pending_count": len(pending),
        "disbursed_count": len(disbursed),
        "disbursed_amount_crore": round(total_disbursed_amt / 1e7, 2),
        "pending_amount_crore": round(total_pending_amt / 1e7, 2),
        "sample_pending_beneficiaries": [
            {
                "id": str(c.id),
                "beneficiary_name": c.beneficiary_name,
                "amount": float(c.disbursed_amount or 0),
                "status": c.status.value,
            }
            for c in pending[:5]
        ],
    }


async def get_rr_summary(db: AsyncSession, project_id: Optional[uuid.UUID] = None) -> Dict[str, Any]:
    """Retrieve Rehabilitation & Resettlement statistics."""
    q = select(Family).where(Family.deleted_at.is_(None))
    if project_id:
        q = q.join(LandParcel, Family.parcel_id == LandParcel.id).where(LandParcel.project_id == project_id)
    res = await db.execute(q)
    families = res.scalars().all()

    total = len(families)
    eligible = sum(1 for f in families if f.r_and_r_status in (RAndRStatus.PLAN_APPROVED, RAndRStatus.RESETTLED, RAndRStatus.MONITORING, RAndRStatus.SURVEY_COMPLETED))
    allotted = sum(1 for f in families if f.r_and_r_status in (RAndRStatus.RESETTLED, RAndRStatus.MONITORING))
    pending = max(0, total - allotted)

    return {
        "total_displaced_families": total,
        "eligible_for_resettlement": eligible,
        "resettlement_allotted": allotted,
        "resettlement_pending": pending,
    }


async def get_workflow_tasks_summary(db: AsyncSession, project_id: Optional[uuid.UUID] = None) -> Dict[str, Any]:
    """Retrieve pending and overdue workflow tasks."""
    q = select(WorkflowTask).where(WorkflowTask.deleted_at.is_(None))
    if project_id:
        q = q.where(WorkflowTask.project_id == project_id)
    res = await db.execute(q)
    tasks = res.scalars().all()

    overdue = [t for t in tasks if t.status == TaskStatus.OVERDUE]
    in_progress = [t for t in tasks if t.status == TaskStatus.IN_PROGRESS]
    pending_review = [t for t in tasks if t.status == TaskStatus.PENDING_REVIEW]

    return {
        "total_tasks": len(tasks),
        "overdue_count": len(overdue),
        "in_progress_count": len(in_progress),
        "pending_review_count": len(pending_review),
        "sample_overdue_tasks": [
            {"id": str(t.id), "title": t.title, "priority": t.priority.value, "stage": t.stage.value}
            for t in overdue[:5]
        ],
    }


async def get_parcel_details(db: AsyncSession, parcel_id: uuid.UUID) -> Optional[Dict[str, Any]]:
    """Retrieve detailed sanitized info for a single parcel."""
    p_res = await db.execute(select(LandParcel).where(LandParcel.id == parcel_id, LandParcel.deleted_at.is_(None)))
    p = p_res.scalar_one_or_none()
    if not p:
        return None

    # Check for disputes
    disp_res = await db.execute(select(Dispute).where(Dispute.parcel_id == p.id, Dispute.deleted_at.is_(None)))
    disputes = disp_res.scalars().all()

    # Check for award/compensation
    award_res = await db.execute(select(Award).where(Award.parcel_id == p.id, Award.deleted_at.is_(None)))
    award = award_res.scalar_one_or_none()
    comp_info = None
    if award:
        comp_res = await db.execute(select(Compensation).where(Compensation.award_id == award.id))
        comp = comp_res.scalar_one_or_none()
        if comp:
            comp_info = {
                "assessed_amount": float(award.declared_amount or 0),
                "disbursed_amount": float(comp.disbursed_amount or 0),
                "status": comp.status.value,
            }

    return {
        "id": str(p.id),
        "survey_number": p.survey_number,
        "village": p.village,
        "taluka": p.taluka,
        "district": p.district,
        "state": p.state,
        "land_type": p.land_type.value,
        "area_hectares": float(p.area_hectares),
        "ownership_type": p.ownership_type.value,
        "possession_status": p.possession_status.value,
        "dispute_count": len(disputes),
        "has_open_dispute": any(d.status == DisputeStatus.OPEN for d in disputes),
        "compensation": comp_info,
    }


async def get_national_overview(db: AsyncSession) -> Dict[str, Any]:
    """Retrieve consolidated national level KPIs."""
    from app.analytics.service import AnalyticsService
    return await AnalyticsService.get_national_kpis(db)
