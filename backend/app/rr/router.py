"""R&R (Rehabilitation & Resettlement) API endpoints."""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.family import Family
from app.models.audit_log import AuditLog
from app.models.enums import RAndRStatus, UserRole

router = APIRouter()


@router.get("/")
async def list_families(
    project_id: Optional[uuid.UUID] = None,
    parcel_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List affected families for R&R monitoring."""
    q = select(Family).where(Family.deleted_at.is_(None))
    if project_id:
        from app.models.land_parcel import LandParcel
        q = q.join(LandParcel, Family.parcel_id == LandParcel.id).where(LandParcel.project_id == project_id)
    if parcel_id:
        q = q.where(Family.parcel_id == parcel_id)
    if status:
        q = q.where(Family.r_and_r_status == status)

    result = await db.execute(q.order_by(Family.created_at.desc()).limit(100))
    families = result.scalars().all()
    return [
        {
            "id": str(f.id),
            "parcel_id": str(f.parcel_id),
            "head_of_household": f.head_of_household,
            "family_size": f.family_size,
            "annual_income": float(f.annual_income) if f.annual_income else None,
            "r_and_r_status": f.r_and_r_status.value,
            "resettlement_details": f.resettlement_details,
            "alternative_land_provided": f.alternative_land_provided,
            "employment_provided": f.employment_provided,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in families
    ]


@router.put("/{family_id}/status")
async def update_rr_status(
    family_id: uuid.UUID,
    new_status: str,
    alternative_land_provided: Optional[bool] = None,
    employment_provided: Optional[bool] = None,
    notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update R&R status for an affected family."""
    if current_user.role not in (UserRole.DISTRICT_AUTHORITY, UserRole.STATE_GOVT, UserRole.CENTRAL_MINISTRY):
        raise HTTPException(403, "Insufficient permissions to update R&R status")

    result = await db.execute(select(Family).where(Family.id == family_id))
    f = result.scalar_one_or_none()
    if not f:
        raise HTTPException(404, "Family record not found")

    old_status = f.r_and_r_status.value
    f.r_and_r_status = RAndRStatus(new_status)

    if alternative_land_provided is not None:
        f.alternative_land_provided = alternative_land_provided
    if employment_provided is not None:
        f.employment_provided = employment_provided

    log = AuditLog(
        id=uuid.uuid4(),
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action="UPDATE_RR_STATUS",
        entity_type="Family",
        entity_id=str(family_id),
        old_value={"status": old_status},
        new_value={"status": new_status, "notes": notes},
        description=f"R&R status updated from {old_status} to {new_status}",
    )
    db.add(log)
    await db.flush()

    return {
        "id": str(family_id),
        "r_and_r_status": f.r_and_r_status.value,
        "message": f"R&R status updated to {new_status}",
    }
