"""Project model — top-level entity for a land acquisition project.

A project groups land parcels, proposals, notifications, awards,
compensations, and affected families under a single initiative
(e.g., "Mumbai-Pune Expressway Expansion").
"""

import uuid

from sqlalchemy import Enum, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AuditMixin, Base, TimestampMixin
from app.models.enums import ProjectStatus


class Project(TimestampMixin, AuditMixin, Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    ministry: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Sponsoring central ministry",
    )
    sector: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="e.g., Infrastructure, Water Resources, Housing",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, name="project_status", native_enum=True),
        nullable=False,
        default=ProjectStatus.PLANNING,
        index=True,
    )
    # Geographic scope. NULL for national-level projects.
    state: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    district: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<Project '{self.name}' status={self.status.value}>"
