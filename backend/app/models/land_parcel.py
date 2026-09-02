"""Land parcel model — individual plot of land within a project.

Each parcel has a PostGIS MULTIPOLYGON geometry (nullable, added during
the geo-tagging step in Module 4) and tracks its acquisition status
through the possession lifecycle.

The geometry column uses SRID 4326 (WGS 84) for compatibility with
Leaflet.js / OpenStreetMap tiles, which expect lat/lon coordinates.
"""

import uuid
from decimal import Decimal

from geoalchemy2 import Geometry
from sqlalchemy import Enum, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AuditMixin, Base, TimestampMixin
from app.models.enums import LandType, OwnershipType, PossessionStatus


class LandParcel(TimestampMixin, AuditMixin, Base):
    __tablename__ = "land_parcels"
    __table_args__ = (
        # Composite index for location-based filtering on the dashboard.
        Index("idx_parcels_state_district", "state", "district"),
    )

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
        comment="Parent project this parcel belongs to",
    )

    # PostGIS geometry — nullable because parcels may be registered
    # before geo-tagging is done (Module 4).
    # spatial_index=False here; we create the GIST index explicitly below
    # to keep migration control in Alembic.
    geometry = mapped_column(
        Geometry(
            geometry_type="MULTIPOLYGON",
            srid=4326,
            spatial_index=False,
        ),
        nullable=True,
    )

    survey_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Revenue survey number (e.g., SY-42/1A)",
    )
    land_type: Mapped[LandType] = mapped_column(
        Enum(LandType, name="land_type", native_enum=True),
        nullable=False,
    )
    area_hectares: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        nullable=False,
        comment="Total area in hectares",
    )

    # Location
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    taluka: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Sub-district / taluka / tehsil",
    )
    village: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Ownership and acquisition status
    ownership_type: Mapped[OwnershipType | None] = mapped_column(
        Enum(OwnershipType, name="ownership_type", native_enum=True),
        nullable=True,
    )
    possession_status: Mapped[PossessionStatus] = mapped_column(
        Enum(PossessionStatus, name="possession_status", native_enum=True),
        nullable=False,
        default=PossessionStatus.NOT_ACQUIRED,
        index=True,
    )

    def __repr__(self) -> str:
        return f"<LandParcel {self.survey_number} ({self.state}/{self.district})>"
