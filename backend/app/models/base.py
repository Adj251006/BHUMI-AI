"""SQLAlchemy declarative base and common mixins.

All models inherit from Base and use the following mixins:
- TimestampMixin: created_at, updated_at, deleted_at (soft delete)
- AuditMixin: created_by, updated_by foreign keys to users table

Convention: Every model uses UUID primary keys, timezone-aware timestamps,
and soft deletes (deleted_at IS NOT NULL means the record is logically removed).
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""

    pass


class TimestampMixin:
    """Adds created_at, updated_at, and deleted_at columns.

    - created_at: Set by the database via server_default on INSERT.
    - updated_at: Set by SQLAlchemy ORM on every flush that modifies the row.
    - deleted_at: NULL = active record. A timestamp = soft-deleted.
      Queries should filter on `deleted_at IS NULL` to exclude soft-deleted rows.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )


class AuditMixin:
    """Adds created_by and updated_by FK columns referencing the users table.

    Both columns are nullable because:
    - System-generated records may not have a user context.
    - Seed data is inserted outside the normal request lifecycle.

    WARNING: Do NOT apply this mixin to the User model itself — it would
    create a circular FK dependency. User handles timestamps via
    TimestampMixin only.
    """

    @declared_attr
    def created_by(cls) -> Mapped[Optional[uuid.UUID]]:
        return mapped_column(
            UUID(as_uuid=True),
            ForeignKey("users.id"),
            nullable=True,
        )

    @declared_attr
    def updated_by(cls) -> Mapped[Optional[uuid.UUID]]:
        return mapped_column(
            UUID(as_uuid=True),
            ForeignKey("users.id"),
            nullable=True,
        )
