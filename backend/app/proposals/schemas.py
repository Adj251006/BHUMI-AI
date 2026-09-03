"""Pydantic schemas for land acquisition proposal requests and responses."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import ProposalStatus, Urgency


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------


class ProposalCreate(BaseModel):
    """POST /proposals request payload."""

    project_id: uuid.UUID = Field(
        ...,
        description="ID of the project this land acquisition proposal belongs to",
    )
    purpose: str = Field(
        ...,
        min_length=10,
        description="Detailed purpose / justification for the land acquisition under LARR Act 2013",
        examples=["Land acquisition for 6-lane expressway expansion between Pune and Solapur."],
    )
    urgency: Urgency = Field(
        default=Urgency.NORMAL,
        description="Urgency classification (normal, urgent under Sec 40, or suo_motu)",
    )
    status: ProposalStatus = Field(
        default=ProposalStatus.DRAFT,
        description="Initial status — must be 'draft' or 'submitted'",
    )


class ProposalUpdate(BaseModel):
    """PUT /proposals/{id} request payload (only editable in draft or revision_requested)."""

    purpose: str | None = Field(
        default=None,
        min_length=10,
        description="Updated purpose / justification details",
    )
    urgency: Urgency | None = Field(
        default=None,
        description="Updated urgency level",
    )


class ProposalStatusUpdate(BaseModel):
    """PATCH /proposals/{id}/status request payload for workflow state transitions."""

    status: ProposalStatus = Field(
        ...,
        description="Target proposal status",
    )
    remarks: str | None = Field(
        default=None,
        description="Reviewer comments or objections (mandatory for rejection or revision request)",
        examples=["SIA report incomplete — please attach environmental impact study."],
    )


# ---------------------------------------------------------------------------
# Response Schemas
# ---------------------------------------------------------------------------


class ProposalResponse(BaseModel):
    """Full details of a land acquisition proposal."""

    id: uuid.UUID
    project_id: uuid.UUID
    submitted_by: uuid.UUID
    status: ProposalStatus
    purpose: str
    urgency: Urgency
    remarks: str | None
    submitted_at: datetime | None
    reviewed_by: uuid.UUID | None
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    # Optional enriched context
    project_name: str | None = None
    submitter_name: str | None = None
    reviewer_name: str | None = None

    model_config = {
        "from_attributes": True,
    }


class ProposalListResponse(BaseModel):
    """Paginated list of proposals."""

    items: list[ProposalResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
