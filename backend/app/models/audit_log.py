"""AuditLog model — immutable record of all significant system actions."""

import uuid
from typing import Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, func

from app.models.base import Base


class AuditLog(Base):
    """Audit log — intentionally does NOT use TimestampMixin/AuditMixin.
    
    - No soft delete (audit logs must never be deleted).
    - No updated_at (audit logs are immutable after creation).
    - No created_by FK (would cause circular FK on system actions).
    """
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True,
        comment="User who performed the action (NULL for system actions)"
    )
    user_email: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Denormalized for historical accuracy"
    )
    user_role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="e.g., APPROVE_COMPENSATION")
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="e.g., Compensation")
    entity_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    old_value: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    new_value: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} on {self.entity_type}/{self.entity_id}>"
