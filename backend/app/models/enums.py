"""PostgreSQL-backed enum types used across the data model.

Each enum inherits from both `str` and `enum.Enum` so that:
- SQLAlchemy stores the string value in PostgreSQL as a native ENUM type.
- Python code can compare with string literals: status == "draft"
- FastAPI/Pydantic JSON serialization works automatically.

Naming convention: PostgreSQL enum type names use snake_case
(e.g., 'user_role', 'project_status'). These names appear in the
database schema and Alembic migrations.
"""

import enum


# ---------------------------------------------------------------------------
# User / Auth
# ---------------------------------------------------------------------------


class UserRole(str, enum.Enum):
    """Roles for role-based access control (RBAC).

    - central_ministry: National-level oversight, can view all data.
    - state_govt: State-level authority (e.g., State Revenue Secretary).
    - district_authority: District Collector / Deputy Commissioner.
    - project_agency: The agency executing the project (e.g., NHAI).
    """

    CENTRAL_MINISTRY = "central_ministry"
    STATE_GOVT = "state_govt"
    DISTRICT_AUTHORITY = "district_authority"
    PROJECT_AGENCY = "project_agency"


# ---------------------------------------------------------------------------
# Project
# ---------------------------------------------------------------------------


class ProjectStatus(str, enum.Enum):
    """Lifecycle status of a land acquisition project."""

    PLANNING = "planning"
    ACTIVE = "active"
    COMPLETED = "completed"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


# ---------------------------------------------------------------------------
# Land Parcel
# ---------------------------------------------------------------------------


class LandType(str, enum.Enum):
    """Classification of land per Indian revenue records."""

    AGRICULTURAL = "agricultural"
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    FOREST = "forest"
    GOVERNMENT = "government"
    WASTELAND = "wasteland"
    WATER_BODY = "water_body"


class OwnershipType(str, enum.Enum):
    """Ownership classification of a land parcel."""

    PRIVATE = "private"
    GOVERNMENT = "government"
    COMMUNITY = "community"
    DISPUTED = "disputed"


class PossessionStatus(str, enum.Enum):
    """Tracks the acquisition stage of a land parcel.

    Progression: not_acquired → notice_issued → awarded → possessed
    """

    NOT_ACQUIRED = "not_acquired"
    NOTICE_ISSUED = "notice_issued"
    AWARDED = "awarded"
    POSSESSED = "possessed"


# ---------------------------------------------------------------------------
# Proposal
# ---------------------------------------------------------------------------


class ProposalStatus(str, enum.Enum):
    """Workflow states for a land acquisition proposal.

    Typical flow:
        draft → submitted → under_scrutiny → approved
                                           → rejected
                                           → revision_requested → submitted (resubmit)

    Terminal states: approved, rejected, withdrawn.
    """

    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_SCRUTINY = "under_scrutiny"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUESTED = "revision_requested"
    WITHDRAWN = "withdrawn"


class Urgency(str, enum.Enum):
    """Urgency level per LARR Act 2013 provisions.

    - normal: Standard acquisition process (Sections 11–38).
    - urgent: Urgent acquisition (Section 40) — requires special justification
              and approval from the appropriate government.
    - suo_motu: Government-initiated acquisition without a specific requisition.
    """

    NORMAL = "normal"
    URGENT = "urgent"
    SUO_MOTU = "suo_motu"


# ---------------------------------------------------------------------------
# Notification
# ---------------------------------------------------------------------------


class NoticeType(str, enum.Enum):
    """Types of legal notices under the LARR Act 2013.

    Maps to specific sections of the Act:
    - preliminary_notification: Section 11 (intent to acquire)
    - hearing_notice: Section 15 (hearing of objections)
    - declaration: Section 19 (declaration of acquisition)
    - award_notice: Section 23 (Collector's award)
    - possession_notice: Section 38 (taking possession)
    """

    PRELIMINARY_NOTIFICATION = "preliminary_notification"
    HEARING_NOTICE = "hearing_notice"
    DECLARATION = "declaration"
    AWARD_NOTICE = "award_notice"
    POSSESSION_NOTICE = "possession_notice"


# ---------------------------------------------------------------------------
# Compensation
# ---------------------------------------------------------------------------


class CompensationStatus(str, enum.Enum):
    """Disbursement status of compensation to land owners/beneficiaries."""

    PENDING = "pending"
    PROCESSING = "processing"
    DISBURSED = "disbursed"
    FAILED = "failed"
    DISPUTED = "disputed"


# ---------------------------------------------------------------------------
# Rehabilitation & Resettlement (R&R)
# ---------------------------------------------------------------------------


class RAndRStatus(str, enum.Enum):
    """R&R status for affected families, per Chapter V of LARR Act 2013.

    Progression: identified → survey_completed → plan_approved
                 → resettled → monitoring
    """

    IDENTIFIED = "identified"
    SURVEY_COMPLETED = "survey_completed"
    PLAN_APPROVED = "plan_approved"
    RESETTLED = "resettled"
    MONITORING = "monitoring"
