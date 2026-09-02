"""Notification model — legal notices issued during the acquisition process.

Each notification is linked to a proposal and corresponds to a specific
section of the LARR Act 2013 (Sections 11, 15, 19, 23, 38).

The `document_url` field stores the Supabase Storage URL for the uploaded
notice document (PDF/image). Document upload logic is in Module 5.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AuditMixin, Base, TimestampMixin
from app.models.enums import NoticeType


class Notification(TimestampMixin, AuditMixin, Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    proposal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("proposals.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    notice_type: Mapped[NoticeType] = mapped_column(
        Enum(NoticeType, name="notice_type", native_enum=True),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    document_url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
        comment="Supabase Storage URL for the notice PDF/image",
    )
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Expiry date for time-bound notices (e.g., objection period)",
    )
    issued_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Authority who issued this notice",
    )

    def __repr__(self) -> str:
        return f"<Notification {self.notice_type.value} for proposal={self.proposal_id}>"
