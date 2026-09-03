"""Proposal model — formal request to acquire land for a project.

Tracks the proposal through its workflow:
  draft → submitted → under_scrutiny → approved / rejected / revision_requested

The `urgency` field supports provisions under Section 40 of the
LARR Act 2013 for urgent acquisitions.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AuditMixin, Base, TimestampMixin
from app.models.enums import ProposalStatus, Urgency


class Proposal(TimestampMixin, AuditMixin, Base):
    __tablename__ = "proposals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    submitted_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="User who created/submitted this proposal",
    )
    status: Mapped[ProposalStatus] = mapped_column(
        Enum(ProposalStatus, name="proposal_status", native_enum=True, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ProposalStatus.DRAFT,
        index=True,
    )
    purpose: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Detailed purpose / justification for the acquisition",
    )
    urgency: Mapped[Urgency] = mapped_column(
        Enum(Urgency, name="urgency", native_enum=True, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=Urgency.NORMAL,
    )
    remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Reviewer comments, objections, or instructions",
    )

    # Submission timestamp — NULL while in draft state.
    submitted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Set when status transitions from draft to submitted",
    )

    # Review tracking
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who approved/rejected the proposal",
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<Proposal {self.id} status={self.status.value}>"
