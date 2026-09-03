"""FastAPI router for land acquisition proposal management."""

import math
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.enums import ProposalStatus
from app.models.user import User
from app.proposals.schemas import (
    ProposalCreate,
    ProposalListResponse,
    ProposalResponse,
    ProposalStatusUpdate,
    ProposalUpdate,
)
from app.proposals import service


router = APIRouter()


# ---------------------------------------------------------------------------
# POST /proposals — Create Proposal
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=ProposalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a proposal",
    description="Create a new land acquisition proposal in 'draft' or 'submitted' status.",
    responses={
        201: {"description": "Proposal created successfully"},
        400: {"description": "Invalid initial status or project ID"},
        403: {"description": "Insufficient permissions (not project_agency or central_ministry)"},
        404: {"description": "Project not found"},
    },
)
async def create_proposal(
    payload: ProposalCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProposalResponse:
    """Create a new land acquisition proposal."""
    proposal = await service.create_proposal(db, payload, current_user)
    return ProposalResponse.model_validate(proposal)


# ---------------------------------------------------------------------------
# GET /proposals — List Proposals
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=ProposalListResponse,
    summary="List proposals",
    description="Retrieve paginated proposals scoped by jurisdiction and optional status/project filters.",
)
async def list_proposals(
    status_filter: ProposalStatus | None = Query(default=None, alias="status", description="Filter by status"),
    project_id: uuid.UUID | None = Query(default=None, description="Filter by project ID"),
    submitted_by: uuid.UUID | None = Query(default=None, description="Filter by submitting user ID"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProposalListResponse:
    """List proposals matching filter criteria."""
    items, total = await service.list_proposals(
        db=db,
        current_user=current_user,
        status_filter=status_filter,
        project_id_filter=project_id,
        submitted_by_filter=submitted_by,
        page=page,
        page_size=page_size,
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return ProposalListResponse(
        items=[ProposalResponse(**item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


# ---------------------------------------------------------------------------
# GET /proposals/{id} — Get Proposal Details
# ---------------------------------------------------------------------------


@router.get(
    "/{proposal_id}",
    response_model=ProposalResponse,
    summary="Get proposal by ID",
    description="Fetch single proposal details by ID.",
    responses={
        404: {"description": "Proposal not found"},
    },
)
async def get_proposal(
    proposal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProposalResponse:
    """Get single proposal details."""
    proposal = await service.get_proposal(db, proposal_id)
    return ProposalResponse.model_validate(proposal)


# ---------------------------------------------------------------------------
# PUT /proposals/{id} — Update Proposal Text
# ---------------------------------------------------------------------------


@router.put(
    "/{proposal_id}",
    response_model=ProposalResponse,
    summary="Update proposal content",
    description="Update purpose/urgency of a proposal. Permitted only in 'draft' or 'revision_requested' status.",
    responses={
        400: {"description": "Proposal is not in draft or revision_requested status"},
        403: {"description": "Only the submitting agency can edit the proposal"},
        404: {"description": "Proposal not found"},
    },
)
async def update_proposal(
    proposal_id: uuid.UUID,
    payload: ProposalUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProposalResponse:
    """Update editable content of a proposal."""
    proposal = await service.update_proposal_content(db, proposal_id, payload, current_user)
    return ProposalResponse.model_validate(proposal)


# ---------------------------------------------------------------------------
# PATCH /proposals/{id}/status — State Transition
# ---------------------------------------------------------------------------


@router.patch(
    "/{proposal_id}/status",
    response_model=ProposalResponse,
    summary="Update proposal status",
    description="Perform workflow state transition on a proposal.",
    responses={
        400: {"description": "Invalid transition or missing required remarks"},
        403: {"description": "Role not authorized for this transition"},
        404: {"description": "Proposal not found"},
    },
)
async def update_proposal_status(
    proposal_id: uuid.UUID,
    payload: ProposalStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProposalResponse:
    """Perform a state machine transition on a proposal."""
    proposal = await service.update_proposal_status(db, proposal_id, payload, current_user)
    return ProposalResponse.model_validate(proposal)
