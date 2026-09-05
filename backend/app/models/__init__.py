"""ORM models package.

Re-exports all models and the declarative Base so that a single import
registers every table with SQLAlchemy's metadata. This is critical for
Alembic autogenerate to detect all tables.

Usage:
    from app.models import Base, User, Project, ...
"""

from app.models.base import Base
from app.models.enums import (
    AnomalySeverity,
    CompensationStatus,
    DisputeStatus,
    DisputeType,
    DocumentStatus,
    DocumentType,
    LandType,
    NoticeType,
    NotificationSeverity,
    OwnershipType,
    PossessionStatus,
    ProjectStatus,
    ProposalStatus,
    RAndRStatus,
    RiskLevel,
    TaskPriority,
    TaskStatus,
    Urgency,
    UserRole,
    VerificationStatus,
    WorkflowStage,
)
from app.models.user import User
from app.models.project import Project
from app.models.land_parcel import LandParcel
from app.models.proposal import Proposal
from app.models.notification import Notification
from app.models.award import Award
from app.models.compensation import Compensation
from app.models.family import Family
from app.models.dispute import Dispute
from app.models.document import Document
from app.models.workflow_task import WorkflowTask
from app.models.field_verification import FieldVerification
from app.models.audit_log import AuditLog
from app.models.ai_risk import AIRiskPrediction, AIAnomaly, SystemNotification

__all__ = [
    # Base
    "Base",
    # Enums
    "AnomalySeverity",
    "CompensationStatus",
    "DisputeStatus",
    "DisputeType",
    "DocumentStatus",
    "DocumentType",
    "LandType",
    "NoticeType",
    "NotificationSeverity",
    "OwnershipType",
    "PossessionStatus",
    "ProjectStatus",
    "ProposalStatus",
    "RAndRStatus",
    "RiskLevel",
    "TaskPriority",
    "TaskStatus",
    "Urgency",
    "UserRole",
    "VerificationStatus",
    "WorkflowStage",
    # Core models
    "User",
    "Project",
    "LandParcel",
    "Proposal",
    "Notification",
    "Award",
    "Compensation",
    "Family",
    # New models
    "Dispute",
    "Document",
    "WorkflowTask",
    "FieldVerification",
    "AuditLog",
    "AIRiskPrediction",
    "AIAnomaly",
    "SystemNotification",
]
