"""User model for authentication and role-based access control.

Stores all system users. The `role` column determines what actions a user
can perform (enforced at the API layer in Module 2).

NOTE: This model uses TimestampMixin but NOT AuditMixin, because
AuditMixin's created_by/updated_by columns reference users.id — which
would create a circular FK dependency on this table.
"""

import uuid

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin
from app.models.enums import UserRole


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=None,  # Generated in Python, not DB
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Login email — unique across the system",
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="bcrypt hash (Module 2 will enforce hashing)",
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=True, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    # State and district scope the user's jurisdiction.
    # NULL for central_ministry users who have national scope.
    state: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Jurisdiction state (NULL for central_ministry)",
    )
    district: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Jurisdiction district (NULL for state-level and central users)",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Soft toggle — inactive users cannot log in",
    )

    def __repr__(self) -> str:
        return f"<User {self.email} role={self.role.value}>"
