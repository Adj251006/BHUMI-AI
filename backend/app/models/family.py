"""Family model — affected families for Rehabilitation & Resettlement (R&R).

Tracks families displaced by land acquisition, per Chapter V of the
LARR Act 2013. Each family is linked to the parcel they are affected by.

The `resettlement_details` JSONB column stores flexible structured data
(new address, allotment number, facilities provided, etc.) without
over-engineering the schema at this stage.
"""

import uuid
from decimal import Decimal

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AuditMixin, Base, TimestampMixin
from app.models.enums import RAndRStatus


class Family(TimestampMixin, AuditMixin, Base):
    __tablename__ = "families"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    parcel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("land_parcels.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="The parcel this family is displaced from",
    )
    head_of_household: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    family_size: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    annual_income: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
        comment="Annual household income in INR (for R&R eligibility)",
    )
    r_and_r_status: Mapped[RAndRStatus] = mapped_column(
        Enum(RAndRStatus, name="r_and_r_status", native_enum=True, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=RAndRStatus.IDENTIFIED,
        index=True,
    )
    resettlement_details: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Flexible JSON: new address, allotment number, facilities, etc.",
    )
    alternative_land_provided: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether alternative land has been allotted to this family",
    )
    employment_provided: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether employment has been offered per R&R package",
    )

    def __repr__(self) -> str:
        return f"<Family head='{self.head_of_household}' status={self.r_and_r_status.value}>"
