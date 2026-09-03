"""Proposal business logic, state machine transitions, and database queries."""

import math
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.enums import ProposalStatus, UserRole
from app.models.project import Project
from app.models.proposal import Proposal
from app.models.user import User
from app.proposals.schemas import ProposalCreate, ProposalStatusUpdate, ProposalUpdate



# ---------------------------------------------------------------------------
# State Machine Matrix
# ---------------------------------------------------------------------------

# Map of (from_status, to_status) -> allowed roles
ALLOWED_TRANSITIONS: dict[tuple[ProposalStatus, ProposalStatus], set[UserRole]] = {
    # Agency / Ministry submitting a draft proposal
    (ProposalStatus.DRAFT, ProposalStatus.SUBMITTED): {
        UserRole.PROJECT_AGENCY,
        UserRole.CENTRAL_MINISTRY,
    },
    # Agency / Ministry withdrawing a draft proposal
    (ProposalStatus.DRAFT, ProposalStatus.WITHDRAWN): {
        UserRole.PROJECT_AGENCY,
        UserRole.CENTRAL_MINISTRY,
    },
    # Agency / Ministry withdrawing a submitted proposal
    (ProposalStatus.SUBMITTED, ProposalStatus.WITHDRAWN): {
        UserRole.PROJECT_AGENCY,
        UserRole.CENTRAL_MINISTRY,
    },
    # Authority putting a submitted proposal under scrutiny
    (ProposalStatus.SUBMITTED, ProposalStatus.UNDER_SCRUTINY): {
        UserRole.DISTRICT_AUTHORITY,
        UserRole.STATE_GOVT,
        UserRole.CENTRAL_MINISTRY,
    },
    # Authority approving a proposal under scrutiny
    (ProposalStatus.UNDER_SCRUTINY, ProposalStatus.APPROVED): {
        UserRole.DISTRICT_AUTHORITY,
        UserRole.STATE_GOVT,
        UserRole.CENTRAL_MINISTRY,
    },
    # Authority rejecting a proposal under scrutiny
    (ProposalStatus.UNDER_SCRUTINY, ProposalStatus.REJECTED): {
        UserRole.DISTRICT_AUTHORITY,
        UserRole.STATE_GOVT,
        UserRole.CENTRAL_MINISTRY,
    },
    # Authority requesting revisions on a proposal under scrutiny
    (ProposalStatus.UNDER_SCRUTINY, ProposalStatus.REVISION_REQUESTED): {
        UserRole.DISTRICT_AUTHORITY,
        UserRole.STATE_GOVT,
        UserRole.CENTRAL_MINISTRY,
    },
    # Agency re-submitting after addressing revision remarks (loop-back)
    (ProposalStatus.REVISION_REQUESTED, ProposalStatus.SUBMITTED): {
        UserRole.PROJECT_AGENCY,
        UserRole.CENTRAL_MINISTRY,
    },
}


def validate_transition(
    current_status: ProposalStatus,
    target_status: ProposalStatus,
    user_role: UserRole,
    remarks: str | None,
) -> None:
    """Validate whether a status transition is permitted for the given role and remarks.

    Raises:
        HTTPException 400: If the transition is illegal or required remarks are missing.
        HTTPException 403: If the user's role is not authorized for this transition.
    """
    if current_status == target_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Proposal is already in status '{current_status.value}'",
        )

    transition_key = (current_status, target_status)
    if transition_key not in ALLOWED_TRANSITIONS:
        valid_targets = [
            to_st.value
            for (from_st, to_st) in ALLOWED_TRANSITIONS.keys()
            if from_st == current_status
        ]
        valid_str = ", ".join(valid_targets) if valid_targets else "None (Terminal State)"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid status transition from '{current_status.value}' to '{target_status.value}'. "
                f"Allowed transitions from '{current_status.value}': [{valid_str}]"
            ),
        )

    allowed_roles = ALLOWED_TRANSITIONS[transition_key]
    if user_role not in allowed_roles:
        roles_str = ", ".join(r.value for r in allowed_roles)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Role '{user_role.value}' is not authorized for status transition "
                f"'{current_status.value}' -> '{target_status.value}'. Authorized roles: [{roles_str}]"
            ),
        )

    # Remarks requirement check
    if target_status in (ProposalStatus.REJECTED, ProposalStatus.REVISION_REQUESTED):
        if not remarks or not remarks.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Remarks/comments are mandatory when setting status to '{target_status.value}'",
            )


# ---------------------------------------------------------------------------
# Service Operations
# ---------------------------------------------------------------------------


async def create_proposal(
    db: AsyncSession,
    payload: ProposalCreate,
    current_user: User,
) -> Proposal:
    """Create a new land acquisition proposal."""
    # 1. Verify role authority to create proposal
    if current_user.role not in (UserRole.PROJECT_AGENCY, UserRole.CENTRAL_MINISTRY):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project_agency or central_ministry users can create proposals",
        )

    # 2. Verify project exists
    project_result = await db.execute(
        select(Project).where(Project.id == payload.project_id, Project.deleted_at.is_(None))
    )
    project = project_result.scalar_one_or_none()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{payload.project_id}' not found",
        )

    # 3. Validate initial status
    if payload.status not in (ProposalStatus.DRAFT, ProposalStatus.SUBMITTED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Initial proposal status must be 'draft' or 'submitted'",
        )

    now = datetime.now(timezone.utc)
    submitted_at = now if payload.status == ProposalStatus.SUBMITTED else None

    proposal = Proposal(
        id=uuid.uuid4(),
        project_id=payload.project_id,
        submitted_by=current_user.id,
        status=payload.status,
        purpose=payload.purpose,
        urgency=payload.urgency,
        remarks=None,
        submitted_at=submitted_at,
        created_by=current_user.id,
        updated_by=current_user.id,
    )
    db.add(proposal)
    await db.flush()
    await db.refresh(proposal)
    return proposal



async def get_raw_proposal(
    db: AsyncSession,
    proposal_id: uuid.UUID,
) -> Proposal:
    """Fetch raw Proposal ORM model instance by ID."""
    result = await db.execute(
        select(Proposal).where(Proposal.id == proposal_id, Proposal.deleted_at.is_(None))
    )
    proposal = result.scalar_one_or_none()
    if proposal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proposal with ID '{proposal_id}' not found",
        )
    return proposal


async def get_proposal(
    db: AsyncSession,
    proposal_id: uuid.UUID,
) -> dict:
    """Get a single proposal by ID with enriched project, submitter, and reviewer names."""
    submitter_alias = aliased(User, name="submitter")
    reviewer_alias = aliased(User, name="reviewer")

    query = (
        select(
            Proposal,
            Project.name.label("project_name"),
            submitter_alias.full_name.label("submitter_name"),
            reviewer_alias.full_name.label("reviewer_name"),
        )
        .join(Project, Proposal.project_id == Project.id)
        .join(submitter_alias, Proposal.submitted_by == submitter_alias.id)
        .outerjoin(reviewer_alias, Proposal.reviewed_by == reviewer_alias.id)
        .where(Proposal.id == proposal_id, Proposal.deleted_at.is_(None))
    )

    result = await db.execute(query)
    row = result.first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proposal with ID '{proposal_id}' not found",
        )

    proposal_obj, proj_name, sub_name, rev_name = row
    return {
        "id": proposal_obj.id,
        "project_id": proposal_obj.project_id,
        "submitted_by": proposal_obj.submitted_by,
        "status": proposal_obj.status,
        "purpose": proposal_obj.purpose,
        "urgency": proposal_obj.urgency,
        "remarks": proposal_obj.remarks,
        "submitted_at": proposal_obj.submitted_at,
        "reviewed_by": proposal_obj.reviewed_by,
        "reviewed_at": proposal_obj.reviewed_at,
        "created_at": proposal_obj.created_at,
        "updated_at": proposal_obj.updated_at,
        "project_name": proj_name,
        "submitter_name": sub_name,
        "reviewer_name": rev_name,
    }



async def list_proposals(
    db: AsyncSession,
    current_user: User,
    status_filter: ProposalStatus | None = None,
    project_id_filter: uuid.UUID | None = None,
    submitted_by_filter: uuid.UUID | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[dict], int]:
    """List proposals with filtering, pagination, and jurisdiction scoping."""
    # Build query joining Project for name
    query = (
        select(
            Proposal,
            Project.name.label("project_name"),
            User.full_name.label("submitter_name"),
        )
        .join(Project, Proposal.project_id == Project.id)
        .join(User, Proposal.submitted_by == User.id)
        .where(Proposal.deleted_at.is_(None))
    )

    # 1. Apply filters
    if status_filter:
        query = query.where(Proposal.status == status_filter)
    if project_id_filter:
        query = query.where(Proposal.project_id == project_id_filter)
    if submitted_by_filter:
        query = query.where(Proposal.submitted_by == submitted_by_filter)

    # 2. Jurisdiction Scoping based on User Role
    if current_user.role == UserRole.STATE_GOVT and current_user.state:
        query = query.where(Project.state == current_user.state)
    elif current_user.role == UserRole.DISTRICT_AUTHORITY:
        if current_user.state:
            query = query.where(Project.state == current_user.state)
        if current_user.district:
            query = query.where(Project.district == current_user.district)
    elif current_user.role == UserRole.PROJECT_AGENCY:
        # Agency users see proposals for their jurisdiction or submitted by themselves
        query = query.where(Proposal.submitted_by == current_user.id)

    # 3. Count total records
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # 4. Paginate
    offset = (page - 1) * page_size
    query = query.order_by(Proposal.created_at.desc()).offset(offset).limit(page_size)

    result = await db.execute(query)
    rows = result.all()

    # Format result list
    items = []
    for proposal_obj, proj_name, sub_name in rows:
        item_dict = {
            "id": proposal_obj.id,
            "project_id": proposal_obj.project_id,
            "submitted_by": proposal_obj.submitted_by,
            "status": proposal_obj.status,
            "purpose": proposal_obj.purpose,
            "urgency": proposal_obj.urgency,
            "remarks": proposal_obj.remarks,
            "submitted_at": proposal_obj.submitted_at,
            "reviewed_by": proposal_obj.reviewed_by,
            "reviewed_at": proposal_obj.reviewed_at,
            "created_at": proposal_obj.created_at,
            "updated_at": proposal_obj.updated_at,
            "project_name": proj_name,
            "submitter_name": sub_name,
            "reviewer_name": None,
        }
        items.append(item_dict)

    return items, total


async def update_proposal_content(
    db: AsyncSession,
    proposal_id: uuid.UUID,
    payload: ProposalUpdate,
    current_user: User,
) -> Proposal:
    """Update editable content of a proposal (only permitted in draft or revision_requested state)."""
    proposal = await get_raw_proposal(db, proposal_id)

    # Check state restriction
    if proposal.status not in (ProposalStatus.DRAFT, ProposalStatus.REVISION_REQUESTED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Proposal content cannot be edited while in status '{proposal.status.value}'",
        )

    # Check creator ownership
    if current_user.role != UserRole.CENTRAL_MINISTRY and proposal.submitted_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the submitting agency can edit this proposal",
        )

    if payload.purpose is not None:
        proposal.purpose = payload.purpose
    if payload.urgency is not None:
        proposal.urgency = payload.urgency

    proposal.updated_by = current_user.id
    await db.flush()
    await db.refresh(proposal)
    return proposal


async def update_proposal_status(
    db: AsyncSession,
    proposal_id: uuid.UUID,
    payload: ProposalStatusUpdate,
    current_user: User,
) -> Proposal:
    """Perform state machine transition on a proposal."""
    proposal = await get_raw_proposal(db, proposal_id)

    # Validate transition & user role
    validate_transition(
        current_status=proposal.status,
        target_status=payload.status,
        user_role=current_user.role,
        remarks=payload.remarks,
    )

    now = datetime.now(timezone.utc)

    # Apply status transition & update timestamps / reviewer info
    proposal.status = payload.status
    proposal.updated_by = current_user.id

    if payload.remarks is not None:
        proposal.remarks = payload.remarks

    if payload.status == ProposalStatus.SUBMITTED:
        proposal.submitted_at = now
    elif payload.status in (
        ProposalStatus.APPROVED,
        ProposalStatus.REJECTED,
        ProposalStatus.REVISION_REQUESTED,
        ProposalStatus.UNDER_SCRUTINY,
    ):
        proposal.reviewed_by = current_user.id
        proposal.reviewed_at = now

    await db.flush()
    await db.refresh(proposal)
    return proposal

