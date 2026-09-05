"""Compensation, disputes, field verification, notifications, audit routers."""
import uuid
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.compensation import Compensation
from app.models.dispute import Dispute
from app.models.document import Document
from app.models.workflow_task import WorkflowTask
from app.models.field_verification import FieldVerification
from app.models.audit_log import AuditLog
from app.models.ai_risk import SystemNotification
from app.models.land_parcel import LandParcel
from app.models.enums import (
    CompensationStatus, DisputeStatus, DocumentStatus, TaskStatus,
    TaskPriority, VerificationStatus, WorkflowStage, UserRole
)

# ============================================================
# COMPENSATION ROUTER
# ============================================================
comp_router = APIRouter()


@comp_router.get("/")
async def list_compensation(
    status: Optional[str] = None,
    project_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(Compensation)
    if project_id:
        from app.models.award import Award
        from app.models.land_parcel import LandParcel
        q = q.join(Award, Compensation.award_id == Award.id).join(LandParcel, Award.parcel_id == LandParcel.id).where(LandParcel.project_id == project_id)
    if status:
        q = q.where(Compensation.status == status)
    result = await db.execute(q.order_by(Compensation.created_at.desc()).limit(100))
    items = result.scalars().all()
    return [
        {
            "id": str(c.id),
            "award_id": str(c.award_id),
            "beneficiary_name": c.beneficiary_name,
            "disbursed_amount": float(c.disbursed_amount),
            "status": c.status.value,
            "disbursed_at": c.disbursed_at.isoformat() if c.disbursed_at else None,
            "payment_reference": c.payment_reference,
            "failure_reason": c.failure_reason,
        }
        for c in items
    ]


@comp_router.put("/{comp_id}/status")
async def update_compensation_status(
    comp_id: uuid.UUID,
    new_status: str,
    notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in (UserRole.DISTRICT_AUTHORITY, UserRole.CENTRAL_MINISTRY, UserRole.STATE_GOVT):
        raise HTTPException(403, "Insufficient permissions")
    result = await db.execute(select(Compensation).where(Compensation.id == comp_id))
    comp = result.scalar_one_or_none()
    if not comp:
        raise HTTPException(404, "Compensation record not found")
    old_status = comp.status.value
    comp.status = CompensationStatus(new_status)
    if new_status == "disbursed":
        comp.disbursed_at = datetime.now(timezone.utc)
    # Audit log
    log = AuditLog(
        id=uuid.uuid4(),
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action="UPDATE_COMPENSATION_STATUS",
        entity_type="Compensation",
        entity_id=str(comp_id),
        old_value={"status": old_status},
        new_value={"status": new_status, "notes": notes},
        description=f"Status changed from {old_status} to {new_status}",
    )
    db.add(log)
    await db.flush()
    return {"id": str(comp_id), "status": comp.status.value, "message": "Status updated"}


@comp_router.post("/{comp_id}/assign-verification")
async def assign_field_verification(
    comp_id: uuid.UUID,
    officer_id: uuid.UUID,
    due_date_str: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in (UserRole.DISTRICT_AUTHORITY, UserRole.CENTRAL_MINISTRY):
        raise HTTPException(403, "Only district authority can assign verification")
    result = await db.execute(select(Compensation).where(Compensation.id == comp_id))
    comp = result.scalar_one_or_none()
    if not comp:
        raise HTTPException(404, "Compensation record not found")
    # Create workflow task for field officer
    task = WorkflowTask(
        id=uuid.uuid4(),
        project_id=comp.award_id,  # Using award_id as project ref
        stage=WorkflowStage.COMPENSATION,
        title=f"Verify compensation documents for beneficiary: {comp.beneficiary_name}",
        assigned_to=officer_id,
        status=TaskStatus.IN_PROGRESS,
        priority=TaskPriority.HIGH,
        due_date=datetime.fromisoformat(due_date_str).replace(tzinfo=timezone.utc),
        created_by=current_user.id,
        updated_by=current_user.id,
    )
    db.add(task)
    comp.status = CompensationStatus.UNDER_VERIFICATION
    # Notification for field officer
    notif = SystemNotification(
        id=uuid.uuid4(),
        recipient_id=officer_id,
        title="New Field Verification Task",
        message=f"You have been assigned to verify compensation documents for {comp.beneficiary_name}. Due: {due_date_str}",
        severity="high",
        entity_type="WorkflowTask",
        entity_id=str(task.id),
    )
    db.add(notif)
    await db.flush()
    return {"task_id": str(task.id), "message": "Field verification assigned"}


# ============================================================
# DISPUTES ROUTER
# ============================================================
dispute_router = APIRouter()


@dispute_router.get("/")
async def list_disputes(
    project_id: Optional[uuid.UUID] = None,
    parcel_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(Dispute).where(Dispute.deleted_at.is_(None))
    if project_id:
        from app.models.land_parcel import LandParcel
        q = q.join(LandParcel, Dispute.parcel_id == LandParcel.id).where(LandParcel.project_id == project_id)
    if parcel_id:
        q = q.where(Dispute.parcel_id == parcel_id)
    if status:
        q = q.where(Dispute.status == status)
    result = await db.execute(q.order_by(Dispute.created_at.desc()).limit(100))
    items = result.scalars().all()
    return [
        {
            "id": str(d.id),
            "parcel_id": str(d.parcel_id),
            "dispute_type": d.dispute_type.value,
            "status": d.status.value,
            "title": d.title,
            "description": d.description,
            "court_case_number": d.court_case_number,
            "hearing_date": d.hearing_date.isoformat() if d.hearing_date else None,
            "resolved_at": d.resolved_at.isoformat() if d.resolved_at else None,
            "resolution_notes": d.resolution_notes,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in items
    ]


@dispute_router.put("/{dispute_id}/resolve")
async def resolve_dispute(
    dispute_id: uuid.UUID,
    resolution_notes: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in (UserRole.DISTRICT_AUTHORITY, UserRole.STATE_GOVT, UserRole.CENTRAL_MINISTRY):
        raise HTTPException(403, "Insufficient permissions")
    result = await db.execute(select(Dispute).where(Dispute.id == dispute_id))
    d = result.scalar_one_or_none()
    if not d:
        raise HTTPException(404, "Dispute not found")
    old_status = d.status.value
    d.status = DisputeStatus.RESOLVED
    d.resolved_by = current_user.id
    d.resolved_at = datetime.now(timezone.utc)
    d.resolution_notes = resolution_notes
    log = AuditLog(
        id=uuid.uuid4(),
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action="RESOLVE_DISPUTE",
        entity_type="Dispute",
        entity_id=str(dispute_id),
        old_value={"status": old_status},
        new_value={"status": "resolved", "resolution_notes": resolution_notes},
    )
    db.add(log)
    await db.flush()
    try:
        from app.ai.router import recalculate_project_risk
        from app.models.land_parcel import LandParcel
        p_res = await db.execute(select(LandParcel.project_id).where(LandParcel.id == d.parcel_id))
        proj_id = p_res.scalar()
        if proj_id:
            await recalculate_project_risk(proj_id, db)
    except Exception:
        pass
    await db.commit()
    return {"id": str(dispute_id), "status": "resolved", "message": "Dispute resolved"}


# ============================================================
# DOCUMENTS ROUTER
# ============================================================
doc_router = APIRouter()


@doc_router.get("/")
async def list_documents(
    project_id: Optional[uuid.UUID] = None,
    parcel_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(Document).where(Document.deleted_at.is_(None))
    if project_id:
        q = q.where(Document.project_id == project_id)
    if parcel_id:
        q = q.where(Document.parcel_id == parcel_id)
    result = await db.execute(q.order_by(Document.created_at.desc()).limit(100))
    items = result.scalars().all()
    return [
        {
            "id": str(d.id),
            "project_id": str(d.project_id) if d.project_id else None,
            "parcel_id": str(d.parcel_id) if d.parcel_id else None,
            "document_type": d.document_type.value,
            "title": d.title,
            "file_url": d.file_url,
            "file_name": d.file_name,
            "version": d.version,
            "status": d.status.value,
            "extracted_fields": d.extracted_fields,
            "validation_result": d.validation_result,
            "ai_confidence_score": d.ai_confidence_score,
            "review_notes": d.review_notes,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in items
    ]


@doc_router.put("/{doc_id}/status")
async def update_document_status(
    doc_id: uuid.UUID,
    new_status: str,
    review_notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Document not found")
    doc.status = DocumentStatus(new_status)
    if review_notes:
        doc.review_notes = review_notes
    await db.flush()
    return {"id": str(doc_id), "status": doc.status.value}


# ============================================================
# WORKFLOW ROUTER
# ============================================================
workflow_router = APIRouter()


@workflow_router.get("/tasks")
async def list_tasks(
    project_id: Optional[uuid.UUID] = None,
    assigned_to: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(WorkflowTask).where(WorkflowTask.deleted_at.is_(None))
    # Field officers see only their tasks
    if current_user.role == UserRole.FIELD_OFFICER:
        q = q.where(WorkflowTask.assigned_to == current_user.id)
    elif assigned_to:
        q = q.where(WorkflowTask.assigned_to == assigned_to)
    if project_id:
        q = q.where(WorkflowTask.project_id == project_id)
    if status:
        q = q.where(WorkflowTask.status == status)
    result = await db.execute(q.order_by(WorkflowTask.created_at.desc()).limit(100))
    tasks = result.scalars().all()
    return [
        {
            "id": str(t.id),
            "project_id": str(t.project_id),
            "parcel_id": str(t.parcel_id) if t.parcel_id else None,
            "stage": t.stage.value,
            "title": t.title,
            "description": t.description,
            "assigned_to": str(t.assigned_to) if t.assigned_to else None,
            "status": t.status.value,
            "priority": t.priority.value,
            "due_date": t.due_date.isoformat() if t.due_date else None,
            "completed_at": t.completed_at.isoformat() if t.completed_at else None,
            "is_escalated": t.is_escalated,
            "notes": t.notes,
        }
        for t in tasks
    ]


@workflow_router.put("/tasks/{task_id}/status")
async def update_task_status(
    task_id: uuid.UUID,
    new_status: str,
    notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(WorkflowTask).where(WorkflowTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(404, "Task not found")
    old_status = task.status.value
    task.status = TaskStatus(new_status)
    if new_status == "completed":
        task.completed_at = datetime.now(timezone.utc)
    if notes:
        task.notes = notes
    log = AuditLog(
        id=uuid.uuid4(),
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action="UPDATE_TASK_STATUS",
        entity_type="WorkflowTask",
        entity_id=str(task_id),
        old_value={"status": old_status},
        new_value={"status": new_status},
    )
    db.add(log)
    await db.flush()
    return {"id": str(task_id), "status": task.status.value}


# ============================================================
# FIELD VERIFICATION ROUTER
# ============================================================
field_router = APIRouter()


class VerificationCreate(BaseModel):
    parcel_id: uuid.UUID
    task_id: Optional[uuid.UUID] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    gps_accuracy_meters: Optional[float] = None
    registered_latitude: Optional[float] = None
    registered_longitude: Optional[float] = None
    photo_urls: Optional[list] = None
    notes: Optional[str] = None


@field_router.post("/verify")
async def submit_verification(
    body: VerificationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in (UserRole.FIELD_OFFICER, UserRole.DISTRICT_AUTHORITY, UserRole.CENTRAL_MINISTRY):
        raise HTTPException(403, "Only field officers can submit verifications")

    # AI GPS consistency check
    gps_mismatch = False
    gps_distance = None
    if (body.gps_latitude and body.registered_latitude):
        import math
        dlat = body.gps_latitude - body.registered_latitude
        dlon = (body.gps_longitude or 0) - (body.registered_longitude or 0)
        gps_distance = math.sqrt(dlat**2 + dlon**2) * 111000  # approx meters
        gps_mismatch = gps_distance > 100  # >100m mismatch flagged

    v = FieldVerification(
        id=uuid.uuid4(),
        parcel_id=body.parcel_id,
        task_id=body.task_id,
        officer_id=current_user.id,
        status=VerificationStatus.PENDING_REVIEW,
        gps_latitude=body.gps_latitude,
        gps_longitude=body.gps_longitude,
        gps_accuracy_meters=body.gps_accuracy_meters,
        registered_latitude=body.registered_latitude,
        registered_longitude=body.registered_longitude,
        gps_mismatch_detected=gps_mismatch,
        gps_distance_meters=gps_distance,
        photo_urls={"urls": body.photo_urls or []},
        notes=body.notes,
        created_by=current_user.id,
        updated_by=current_user.id,
    )
    db.add(v)

    # Update task status if linked
    if body.task_id:
        task_r = await db.execute(select(WorkflowTask).where(WorkflowTask.id == body.task_id))
        task = task_r.scalar_one_or_none()
        if task:
            task.status = TaskStatus.PENDING_REVIEW

    await db.flush()
    return {
        "id": str(v.id),
        "status": v.status.value,
        "gps_mismatch_detected": gps_mismatch,
        "gps_distance_meters": round(gps_distance, 1) if gps_distance else None,
        "message": "Verification submitted. Pending district officer review." +
                   (" GPS location mismatch detected — manual review recommended." if gps_mismatch else ""),
    }


@field_router.put("/verify/{verification_id}/review")
async def review_verification(
    verification_id: uuid.UUID,
    decision: str,  # "approved" | "rejected" | "reverification_requested"
    review_notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in (UserRole.DISTRICT_AUTHORITY, UserRole.STATE_GOVT, UserRole.CENTRAL_MINISTRY):
        raise HTTPException(403, "Only district officers can review verifications")
    result = await db.execute(select(FieldVerification).where(FieldVerification.id == verification_id))
    v = result.scalar_one_or_none()
    if not v:
        raise HTTPException(404, "Verification not found")

    status_map = {
        "approved": VerificationStatus.APPROVED,
        "rejected": VerificationStatus.REJECTED,
        "reverification_requested": VerificationStatus.REVERIFICATION_REQUESTED,
    }
    if decision not in status_map:
        raise HTTPException(400, "Invalid decision. Use: approved | rejected | reverification_requested")

    v.status = status_map[decision]
    v.reviewed_by = current_user.id
    v.review_notes = review_notes

    log = AuditLog(
        id=uuid.uuid4(),
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action="REVIEW_FIELD_VERIFICATION",
        entity_type="FieldVerification",
        entity_id=str(verification_id),
        old_value={"status": "pending_review"},
        new_value={"status": decision, "notes": review_notes},
    )
    db.add(log)
    await db.flush()
    return {"id": str(verification_id), "status": v.status.value, "message": f"Verification {decision}"}


# ============================================================
# NOTIFICATIONS ROUTER
# ============================================================
notif_router = APIRouter()


@notif_router.get("/")
async def list_notifications(
    unread_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy import or_
    q = select(SystemNotification).where(
        or_(
            SystemNotification.recipient_id == current_user.id,
            SystemNotification.recipient_id.is_(None),
        )
    )
    if unread_only:
        q = q.where(SystemNotification.is_read == False)  # noqa: E712
    result = await db.execute(q.order_by(SystemNotification.created_at.desc()).limit(50))
    items = result.scalars().all()
    return [
        {
            "id": str(n.id),
            "title": n.title,
            "message": n.message,
            "severity": n.severity,
            "link_url": n.link_url,
            "action_label": n.action_label,
            "is_read": n.is_read,
            "entity_type": n.entity_type,
            "entity_id": n.entity_id,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in items
    ]


@notif_router.put("/read-all")
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy import update, or_
    await db.execute(
        update(SystemNotification)
        .where(
            or_(
                SystemNotification.recipient_id == current_user.id,
                SystemNotification.recipient_id.is_(None),
            )
        )
        .values(is_read=True)
    )
    await db.flush()
    return {"message": "All notifications marked as read", "is_read": True}


@notif_router.put("/{notif_id}/read")
async def mark_read(
    notif_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(SystemNotification).where(SystemNotification.id == notif_id))
    n = result.scalar_one_or_none()
    if not n:
        raise HTTPException(404, "Notification not found")
    n.is_read = True
    await db.flush()
    return {"id": str(notif_id), "is_read": True}


# ============================================================
# AUDIT ROUTER
# ============================================================
audit_router = APIRouter()


@audit_router.get("/")
async def list_audit_logs(
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in (
        UserRole.CENTRAL_MINISTRY, UserRole.STATE_GOVT, UserRole.DISTRICT_AUTHORITY, UserRole.AUDITOR
    ):
        raise HTTPException(403, "Insufficient permissions to view audit logs")

    q = select(AuditLog)
    if entity_type:
        q = q.where(AuditLog.entity_type == entity_type)
    if entity_id:
        q = q.where(AuditLog.entity_id == entity_id)
    if action:
        q = q.where(AuditLog.action == action)
    result = await db.execute(q.order_by(AuditLog.timestamp.desc()).limit(min(limit, 200)))
    logs = result.scalars().all()
    return [
        {
            "id": str(l.id),
            "timestamp": l.timestamp.isoformat() if l.timestamp else None,
            "user_email": l.user_email,
            "user_role": l.user_role,
            "action": l.action,
            "entity_type": l.entity_type,
            "entity_id": l.entity_id,
            "old_value": l.old_value,
            "new_value": l.new_value,
            "description": l.description,
        }
        for l in logs
    ]
