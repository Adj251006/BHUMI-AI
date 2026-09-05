"""FieldVerification model — records on-ground verification by field officers."""

import uuid
from typing import Optional

from sqlalchemy import Boolean, Enum, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AuditMixin, Base, TimestampMixin
from app.models.enums import VerificationStatus


class FieldVerification(TimestampMixin, AuditMixin, Base):
    __tablename__ = "field_verifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parcel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("land_parcels.id", ondelete="RESTRICT"),
        nullable=False, index=True,
    )
    task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflow_tasks.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    officer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True,
        comment="Field officer who conducted the verification"
    )
    status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus, name="verification_status", native_enum=True, values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=VerificationStatus.SUBMITTED, index=True,
    )
    # GPS coordinates captured at time of verification
    gps_latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gps_longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gps_accuracy_meters: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    # Registered parcel coordinates for comparison
    registered_latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    registered_longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    # AI GPS consistency check
    gps_mismatch_detected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    gps_distance_meters: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="Distance between captured and registered GPS")
    # Evidence
    photo_urls: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, comment="List of photo URLs captured during verification")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Review
    reviewed_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<FieldVerification parcel={self.parcel_id} officer={self.officer_id} status={self.status.value}>"
