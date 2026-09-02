"""ORM models package.

Re-exports all models and the declarative Base so that a single import
registers every table with SQLAlchemy's metadata. This is critical for
Alembic autogenerate to detect all tables.

Usage:
    from app.models import Base, User, Project, ...
"""

from app.models.base import Base
from app.models.enums import (
    CompensationStatus,
    LandType,
    NoticeType,
    OwnershipType,
    PossessionStatus,
    ProjectStatus,
    ProposalStatus,
    RAndRStatus,
    Urgency,
    UserRole,
)
from app.models.user import User
from app.models.project import Project
from app.models.land_parcel import LandParcel
from app.models.proposal import Proposal
from app.models.notification import Notification
from app.models.award import Award
from app.models.compensation import Compensation
from app.models.family import Family

__all__ = [
    # Base
    "Base",
    # Enums
    "CompensationStatus",
    "LandType",
    "NoticeType",
    "OwnershipType",
    "PossessionStatus",
    "ProjectStatus",
    "ProposalStatus",
    "RAndRStatus",
    "Urgency",
    "UserRole",
    # Models
    "User",
    "Project",
    "LandParcel",
    "Proposal",
    "Notification",
    "Award",
    "Compensation",
    "Family",
]
