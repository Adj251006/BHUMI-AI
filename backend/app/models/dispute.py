"""Dispute model — tracks land acquisition disputes at the parcel level."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AuditMixin, Base, TimestampMixin
from app.models.enums import DisputeStatus, DisputeType


class Dispute(TimestampMixin, AuditMixin, Base):
    __tablename__ = "disputes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parcel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("land_parcels.id", ondelete="RESTRICT"),
        nullable=False, index=True, comment="Parcel this dispute is about"
    )
    dispute_type: Mapped[DisputeType] = mapped_column(
        Enum(DisputeType, name="dispute_type", native_enum=True, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    status: Mapped[DisputeStatus] = mapped_column(
        Enum(DisputeStatus, name="dispute_status", native_enum=True, values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=DisputeStatus.OPEN, index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    raised_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False,
        comment="User who filed the dispute"
    )
    resolved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True,
        comment="User who resolved the dispute"
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    court_case_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    hearing_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<Dispute {self.title} status={self.status.value}>"
