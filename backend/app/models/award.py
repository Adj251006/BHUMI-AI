"""Award model — compensation award declared for a land parcel.

An award is the Collector's determination of compensation amount for a
specific parcel, per Section 23 of the LARR Act 2013.

The total declared_amount should equal market_value + solatium_amount.
The LARR Act mandates solatium at 100% of the market value (Section 30).
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AuditMixin, Base, TimestampMixin


class Award(TimestampMixin, AuditMixin, Base):
    __tablename__ = "awards"

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
        comment="The land parcel this award compensates",
    )
    declared_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        comment="Total compensation = market_value + solatium (in INR)",
    )
    market_value: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        comment="Market value determined by the Collector",
    )
    solatium_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        comment="100% solatium per LARR Act Section 30",
    )
    declared_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    declared_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Collector / authority who declared the award",
    )

    def __repr__(self) -> str:
        return f"<Award parcel={self.parcel_id} amount=₹{self.declared_amount}>"
