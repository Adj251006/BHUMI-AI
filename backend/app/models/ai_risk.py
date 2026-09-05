"""AI Risk and Anomaly models — stores predictions and anomaly flags."""

import uuid
from typing import Optional

from sqlalchemy import Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin
from app.models.enums import AnomalySeverity, RiskLevel


class AIRiskPrediction(TimestampMixin, Base):
    """Stores the latest AI risk prediction for a project."""
    __tablename__ = "ai_risk_predictions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False, index=True, unique=False,
    )
    risk_level: Mapped[RiskLevel] = mapped_column(
        Enum(RiskLevel, name="risk_level", native_enum=True, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    risk_score: Mapped[float] = mapped_column(Float, nullable=False, comment="0.0 to 1.0 risk score")
    delay_probability: Mapped[float] = mapped_column(Float, nullable=False, comment="0.0 to 1.0 probability of delay")
    expected_delay_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Breakdown of contributing factors (JSON list of {factor, contribution_pct, description})
    contributing_factors: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # Critical parcel IDs identified by the model
    critical_parcel_ids: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # AI-generated explanation text
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Model metadata
    model_version: Mapped[str] = mapped_column(String(50), nullable=False, default="mock-v1.0")

    def __repr__(self) -> str:
        return f"<AIRiskPrediction project={self.project_id} risk={self.risk_level.value} delay={self.delay_probability:.0%}>"


class AIAnomaly(TimestampMixin, Base):
    """Records a detected data anomaly that requires human review."""
    __tablename__ = "ai_anomalies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="e.g., Compensation, LandParcel")
    entity_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    anomaly_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="e.g., unusual_value, duplicate_record")
    severity: Mapped[AnomalySeverity] = mapped_column(
        Enum(AnomalySeverity, name="anomaly_severity", native_enum=True, values_callable=lambda x: [e.value for e in x]),
        nullable=False, index=True,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    detected_value: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    expected_range: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_resolved: Mapped[bool] = mapped_column(default=False, nullable=False)
    resolved_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    def __repr__(self) -> str:
        return f"<AIAnomaly {self.anomaly_type} on {self.entity_type}/{self.entity_id}>"


class SystemNotification(TimestampMixin, Base):
    """System-level notifications with severity levels."""
    __tablename__ = "system_notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipient_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True, index=True, comment="NULL = broadcast to all"
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="info", index=True)
    link_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    action_label: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_read: Mapped[bool] = mapped_column(default=False, nullable=False)
    entity_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    entity_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    def __repr__(self) -> str:
        return f"<SystemNotification '{self.title}' severity={self.severity}>"
