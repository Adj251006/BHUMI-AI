"""Compensation, disputes, field verification, notifications, audit routers."""
import uuid
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
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
_COMP_CACHE: dict[str, tuple[float, list[dict]]] = {}

def invalidate_comp_cache():
    _COMP_CACHE.clear()

@comp_router.get("/")
async def list_compensation(
    status: Optional[str] = None,
    project_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    import time
    cache_key = f"{status}:{project_id}"
    now = time.time()
    if cache_key in _COMP_CACHE:
        ts, data = _COMP_CACHE[cache_key]
        if now - ts < 30.0:
            return data

    q = select(Compensation)
    if project_id:
        from app.models.award import Award
        from app.models.land_parcel import LandParcel
        q = q.join(Award, Compensation.award_id == Award.id).join(LandParcel, Award.parcel_id == LandParcel.id).where(LandParcel.project_id == project_id)
    if status:
        q = q.where(Compensation.status == status)
    result = await db.execute(q.order_by(Compensation.created_at.desc()).limit(100))
    items = result.scalars().all()
    data = [
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
    _COMP_CACHE[cache_key] = (now, data)
    return data


class AwardCalculationRequest(BaseModel):
    base_market_value_per_hectare: float = 2500000.0
    area_hectares: float = 1.5
    is_rural: bool = True
    distance_from_urban_boundary_km: float = 15.0
    structure_valuation: float = 350000.0
    trees_and_crops_valuation: float = 120000.0
    notification_date_iso: Optional[str] = None
    award_date_iso: Optional[str] = None


@comp_router.post("/calculate-award")
async def calculate_award_endpoint(
    body: AwardCalculationRequest,
    current_user: User = Depends(get_current_user),
):
    """Calculate statutory compensation award per Sections 26 to 30 of RFCTLARR Act 2013."""
    from app.compensation.calculator import calculate_statutory_award
    return calculate_statutory_award(
        base_market_value_per_hectare=body.base_market_value_per_hectare,
        area_hectares=body.area_hectares,
        is_rural=body.is_rural,
        distance_from_urban_boundary_km=body.distance_from_urban_boundary_km,
        structure_valuation=body.structure_valuation,
        trees_and_crops_valuation=body.trees_and_crops_valuation,
        notification_date_iso=body.notification_date_iso,
        award_date_iso=body.award_date_iso,
    )


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
    from app.models.award import Award
    result = await db.execute(
        select(Compensation, LandParcel.project_id)
        .join(Award, Compensation.award_id == Award.id)
        .join(LandParcel, Award.parcel_id == LandParcel.id)
        .where(Compensation.id == comp_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(404, "Compensation record not found")
    comp, real_project_id = row
    # Create workflow task for field officer
    task = WorkflowTask(
        id=uuid.uuid4(),
        project_id=real_project_id,
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
_DISPUTE_CACHE: dict[str, tuple[float, list[dict]]] = {}

def invalidate_dispute_cache():
    _DISPUTE_CACHE.clear()

@dispute_router.get("/")
async def list_disputes(
    project_id: Optional[uuid.UUID] = None,
    parcel_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    import time
    cache_key = f"{project_id}:{parcel_id}:{status}"
    now = time.time()
    if cache_key in _DISPUTE_CACHE:
        ts, data = _DISPUTE_CACHE[cache_key]
        if now - ts < 30.0:
            return data

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
    data = [
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
    _DISPUTE_CACHE[cache_key] = (now, data)
    return data


class DisputeCreate(BaseModel):
    parcel_id: uuid.UUID
    dispute_type: str = "measurement_dispute"
    title: str
    description: str
    court_case_number: Optional[str] = None
    hearing_date_iso: Optional[str] = None


@dispute_router.post("/")
async def file_dispute(
    body: DisputeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """File a statutory objection or dispute under Section 15 or Section 64 of RFCTLARR Act 2013."""
    from app.models.land_parcel import LandParcel
    from app.models.enums import DisputeType
    from app.audit.service import record_audit_event
    from app.models.ai_risk import SystemNotification

    p_res = await db.execute(select(LandParcel).where(LandParcel.id == body.parcel_id))
    parcel = p_res.scalar_one_or_none()
    if not parcel:
        raise HTTPException(404, "Parcel not found")

    dispute_type_enum = DisputeType.MEASUREMENT_DISPUTE
    try:
        dispute_type_enum = DisputeType(body.dispute_type)
    except Exception:
        pass

    hearing_dt = None
    if body.hearing_date_iso:
        try:
            hearing_dt = datetime.fromisoformat(body.hearing_date_iso).replace(tzinfo=timezone.utc)
        except Exception:
            pass

    dispute = Dispute(
        id=uuid.uuid4(),
        parcel_id=body.parcel_id,
        dispute_type=dispute_type_enum,
        status=DisputeStatus.OPEN,
        title=body.title,
        description=body.description,
        court_case_number=body.court_case_number,
        hearing_date=hearing_dt,
        created_by=current_user.id,
        updated_by=current_user.id,
    )
    db.add(dispute)

    notif = SystemNotification(
        id=uuid.uuid4(),
        title="Statutory Objection / Dispute Filed",
        message=f"New Section 15/64 objection filed for Survey {parcel.survey_number}: '{body.title}' by {current_user.email}.",
        severity="high",
        entity_type="Dispute",
        entity_id=dispute.id,
        is_read=False,
    )
    db.add(notif)

    await record_audit_event(
        db=db,
        action="FILE_STATUTORY_DISPUTE",
        entity_type="Dispute",
        entity_id=str(dispute.id),
        current_user=current_user,
        new_value={"parcel_id": str(parcel.id), "survey_number": parcel.survey_number, "type": dispute.dispute_type.value},
        description=f"Statutory objection filed for parcel {parcel.survey_number} under RFCTLARR Act 2013.",
    )
    await db.flush()

    return {
        "status": "success",
        "id": str(dispute.id),
        "dispute_type": dispute.dispute_type.value,
        "title": dispute.title,
        "message": "Statutory objection registered successfully. Assigned to Competent Authority for hearing.",
    }


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


@doc_router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    project_id: uuid.UUID = Form(...),
    document_type: str = Form("section_11_notice"),
    title: Optional[str] = Form(None),
    parcel_id: Optional[uuid.UUID] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a real statutory document, save to disk, and trigger AI compliance validation."""
    import os
    from app.models.enums import DocumentType
    from app.ai.documents import analyze_statutory_document
    from app.audit.service import record_audit_event

    content = await file.read()
    filename = file.filename or f"doc_{uuid.uuid4().hex[:8]}.pdf"
    file_id = uuid.uuid4()
    saved_filename = f"{file_id}_{filename}"
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, saved_filename)
    with open(file_path, "wb") as f:
        f.write(content)

    # Perform AI Statutory Compliance Check
    ai_result = analyze_statutory_document(
        filename=filename,
        document_type=document_type,
        file_bytes=content,
    )

    doc_type_enum = DocumentType.SECTION_11_NOTICE
    try:
        doc_type_enum = DocumentType(document_type)
    except Exception:
        pass

    doc = Document(
        id=file_id,
        project_id=project_id,
        parcel_id=parcel_id,
        document_type=doc_type_enum,
        title=title or filename,
        file_url=f"/uploads/{saved_filename}",
        file_name=filename,
        file_size_bytes=len(content),
        mime_type=file.content_type or "application/pdf",
        status=DocumentStatus.UNDER_REVIEW,
        extracted_fields=ai_result.get("extracted_fields"),
        validation_result=ai_result.get("validation_checklist"),
        ai_confidence_score=ai_result.get("confidence_score"),
        review_notes=ai_result.get("compliance_summary"),
        created_by=current_user.id,
        updated_by=current_user.id,
    )
    db.add(doc)
    await record_audit_event(
        db=db,
        action="UPLOAD_STATUTORY_DOCUMENT",
        entity_type="Document",
        entity_id=str(doc.id),
        current_user=current_user,
        new_value={"filename": filename, "type": document_type, "size_bytes": len(content)},
        description=f"Uploaded {document_type} '{filename}' with AI confidence {ai_result.get('confidence_score')}.",
    )
    await db.flush()
    return {
        "id": str(doc.id),
        "title": doc.title,
        "document_type": doc.document_type.value,
        "status": doc.status.value,
        "file_url": doc.file_url,
        "ai_confidence_score": doc.ai_confidence_score,
        "extracted_fields": doc.extracted_fields,
        "validation_checklist": doc.validation_result,
        "review_notes": doc.review_notes,
    }


@doc_router.put("/{doc_id}/status")
async def update_document_status(
    doc_id: uuid.UUID,
    new_status: str,
    review_notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in (
        UserRole.DISTRICT_AUTHORITY,
        UserRole.STATE_GOVT,
        UserRole.CENTRAL_MINISTRY,
        UserRole.PROJECT_AGENCY,
    ):
        raise HTTPException(403, "Insufficient permissions to update document verification status")
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


class StageTransitionRequest(BaseModel):
    project_id: uuid.UUID
    target_stage: str
    notes: Optional[str] = None


@workflow_router.get("/rules")
async def get_workflow_rules(
    current_user: User = Depends(get_current_user),
):
    """Retrieve RFCTLARR 2013 statutory workflow stage progression rules and SLAs."""
    from app.workflow.engine import STATUTORY_WORKFLOW_RULES
    return {k: v.__dict__ for k, v in STATUTORY_WORKFLOW_RULES.items()}


@workflow_router.post("/transition")
async def transition_project_stage(
    body: StageTransitionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Transition a project to a new statutory stage with full RFCTLARR Act (2013) compliance enforcement."""
    from app.models.project import Project
    from app.workflow.engine import validate_stage_transition, STATUTORY_WORKFLOW_RULES
    from app.audit.service import record_audit_event

    result = await db.execute(select(Project).where(Project.id == body.project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(404, "Project not found")

    old_stage = project.current_stage.value
    is_valid, error_msg = validate_stage_transition(
        current_stage=old_stage,
        target_stage=body.target_stage,
        user_role=current_user.role.value,
    )
    if not is_valid:
        raise HTTPException(400, detail=error_msg)

    project.current_stage = WorkflowStage(body.target_stage)
    
    await record_audit_event(
        db=db,
        action="STATUTORY_STAGE_TRANSITION",
        entity_type="Project",
        entity_id=str(project.id),
        current_user=current_user,
        old_value={"stage": old_stage},
        new_value={"stage": body.target_stage, "notes": body.notes},
        description=f"Project transitioned from {old_stage} to {body.target_stage} under RFCTLARR Act 2013.",
    )

    target_rule = STATUTORY_WORKFLOW_RULES.get(body.target_stage)
    if target_rule and target_rule.statutory_time_limit_days:
        from datetime import timedelta
        due = datetime.now(timezone.utc) + timedelta(days=target_rule.statutory_time_limit_days)
        new_task = WorkflowTask(
            id=uuid.uuid4(),
            project_id=project.id,
            stage=WorkflowStage(body.target_stage),
            title=f"Statutory Milestone: {target_rule.name}",
            description=f"Statutory compliance under {target_rule.section_ref}. SLA limit: {target_rule.statutory_time_limit_days} days.",
            status=TaskStatus.PENDING,
            priority=TaskPriority.HIGH,
            due_date=due,
            created_by=current_user.id,
            updated_by=current_user.id,
        )
        db.add(new_task)

    await db.flush()
    return {
        "status": "success",
        "project_id": str(project.id),
        "previous_stage": old_stage,
        "current_stage": project.current_stage.value,
        "message": f"Successfully transitioned to {target_rule.name if target_rule else body.target_stage}",
    }


_TASK_CACHE: dict[str, tuple[float, list[dict]]] = {}

def invalidate_task_cache():
    _TASK_CACHE.clear()

@workflow_router.get("/tasks")
@workflow_router.get("/tasks/")
async def list_tasks(
    project_id: Optional[uuid.UUID] = None,
    assigned_to: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    import time
    cache_key = f"{current_user.id}:{project_id}:{assigned_to}:{status}"
    now = time.time()
    if cache_key in _TASK_CACHE:
        ts, data = _TASK_CACHE[cache_key]
        if now - ts < 30.0:
            return data

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
    data = [
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
    _TASK_CACHE[cache_key] = (now, data)
    return data


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
    if (
        task.assigned_to != current_user.id
        and current_user.role not in (UserRole.DISTRICT_AUTHORITY, UserRole.STATE_GOVT, UserRole.CENTRAL_MINISTRY)
    ):
        raise HTTPException(403, "Not authorized to update this task")
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

    # AI GPS consistency check using spherical Haversine formula
    gps_mismatch = False
    gps_distance = None
    if (
        body.gps_latitude is not None
        and body.registered_latitude is not None
        and body.gps_longitude is not None
        and body.registered_longitude is not None
    ):
        import math
        R = 6371000.0  # Earth radius in meters
        phi1 = math.radians(body.registered_latitude)
        phi2 = math.radians(body.gps_latitude)
        delta_phi = math.radians(body.gps_latitude - body.registered_latitude)
        delta_lambda = math.radians(body.gps_longitude - body.registered_longitude)
        a = (
            math.sin(delta_phi / 2.0) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        gps_distance = round(R * c, 2)
        gps_mismatch = gps_distance > 100.0  # >100m mismatch flagged

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
_NOTIF_CACHE: dict[str, tuple[float, list[dict]]] = {}

def invalidate_notif_cache():
    _NOTIF_CACHE.clear()

@notif_router.get("/")
async def list_notifications(
    unread_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    import time
    cache_key = f"{current_user.id}:{unread_only}"
    now = time.time()
    if cache_key in _NOTIF_CACHE:
        ts, data = _NOTIF_CACHE[cache_key]
        if now - ts < 20.0:
            return data

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
    data = [
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
    _NOTIF_CACHE[cache_key] = (now, data)
    return data


@notif_router.get("/outbox")
async def list_outbox_notifications(
    current_user: User = Depends(get_current_user),
):
    """Returns the external SMS and Email communication dispatch outbox."""
    from app.notifications.gateway import NOTIFICATION_OUTBOX
    return NOTIFICATION_OUTBOX


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
    if n.recipient_id is not None and n.recipient_id != current_user.id and current_user.role != UserRole.CENTRAL_MINISTRY:
        raise HTTPException(403, "Not authorized to modify this notification")
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
            "prev_hash": l.prev_hash,
            "entry_hash": l.entry_hash,
        }
        for l in logs
    ]


@audit_router.get("/verify")
async def verify_audit_trail(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Verify cryptographic hash-chain integrity across all audit records."""
    if current_user.role not in (
        UserRole.CENTRAL_MINISTRY, UserRole.STATE_GOVT, UserRole.DISTRICT_AUTHORITY, UserRole.AUDITOR
    ):
        raise HTTPException(403, "Insufficient permissions to perform audit cryptographic verification")
    from app.audit.service import verify_chain_integrity
    return await verify_chain_integrity(db)
