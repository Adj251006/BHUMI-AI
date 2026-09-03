"""Compensation model — tracks disbursement of award money to beneficiaries.

Each compensation record represents a payment to a specific beneficiary
for a given award. Multiple compensations may exist for one award if the
parcel has multiple owners/stakeholders.

The status field tracks the payment lifecycle:
  pending → processing → disbursed / failed / disputed
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AuditMixin, Base, TimestampMixin
from app.models.enums import CompensationStatus


class Compensation(TimestampMixin, AuditMixin, Base):
    __tablename__ = "compensations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    award_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("awards.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    beneficiary_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    beneficiary_account: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Bank account identifier (masked in API responses)",
    )
    disbursed_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        comment="Amount disbursed to this beneficiary (in INR)",
    )
    disbursed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="NULL until status = disbursed",
    )
    payment_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="NEFT/RTGS/UPI reference number",
    )
    status: Mapped[CompensationStatus] = mapped_column(
        Enum(CompensationStatus, name="compensation_status", native_enum=True, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=CompensationStatus.PENDING,
        index=True,
    )
    failure_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Reason for failure or dispute (NULL if status is not failed/disputed)",
    )

    def __repr__(self) -> str:
        return f"<Compensation beneficiary='{self.beneficiary_name}' status={self.status.value}>"
