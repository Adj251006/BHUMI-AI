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
    - field_officer: Field-level officer for on-ground verification.
    - auditor: Read-only access to all data for audit purposes.
    - citizen: Landowner/affected party — can only view their own case.
    """

    CENTRAL_MINISTRY = "central_ministry"
    STATE_GOVT = "state_govt"
    DISTRICT_AUTHORITY = "district_authority"
    PROJECT_AGENCY = "project_agency"
    FIELD_OFFICER = "field_officer"
    AUDITOR = "auditor"
    CITIZEN = "citizen"


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


# ---------------------------------------------------------------------------
# Compensation (extended)
# ---------------------------------------------------------------------------


class CompensationStatusExtended(str, enum.Enum):
    """Extended compensation status including verification step."""

    PENDING = "pending"
    UNDER_VERIFICATION = "under_verification"
    PROCESSING = "processing"
    DISBURSED = "disbursed"
    FAILED = "failed"
    DISPUTED = "disputed"


# ---------------------------------------------------------------------------
# Dispute
# ---------------------------------------------------------------------------


class DisputeStatus(str, enum.Enum):
    """Status of a land acquisition dispute."""

    OPEN = "open"
    UNDER_REVIEW = "under_review"
    HEARING_SCHEDULED = "hearing_scheduled"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class DisputeType(str, enum.Enum):
    """Type/category of a dispute."""

    OWNERSHIP = "ownership"
    VALUATION = "valuation"
    BOUNDARY = "boundary"
    COMPENSATION = "compensation"
    RR = "rr"
    PROCEDURAL = "procedural"
    OTHER = "other"


# ---------------------------------------------------------------------------
# Document
# ---------------------------------------------------------------------------


class DocumentType(str, enum.Enum):
    """Types of documents in the land acquisition workflow."""

    PROPOSAL = "proposal"
    PRELIMINARY_NOTIFICATION = "preliminary_notification"
    SOCIAL_IMPACT_ASSESSMENT = "social_impact_assessment"
    SURVEY_REPORT = "survey_report"
    ENVIRONMENTAL_CLEARANCE = "environmental_clearance"
    AWARD = "award"
    COMPENSATION_ORDER = "compensation_order"
    RR_PLAN = "rr_plan"
    POSSESSION_CERTIFICATE = "possession_certificate"
    OBJECTION = "objection"
    COURT_ORDER = "court_order"
    FIELD_REPORT = "field_report"
    OTHER = "other"


class DocumentStatus(str, enum.Enum):
    """Verification/approval status of a document."""

    UPLOADED = "uploaded"
    UNDER_REVIEW = "under_review"
    AI_ANALYZED = "ai_analyzed"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUIRED = "revision_required"


# ---------------------------------------------------------------------------
# Workflow Task
# ---------------------------------------------------------------------------


class WorkflowStage(str, enum.Enum):
    """Stages in the land acquisition lifecycle workflow."""

    PROPOSAL = "proposal"
    LAND_IDENTIFICATION = "land_identification"
    VERIFICATION = "verification"
    NOTIFICATION = "notification"
    SURVEY = "survey"
    VALUATION = "valuation"
    OBJECTION = "objection"
    AWARD = "award"
    COMPENSATION = "compensation"
    RR = "rr"
    POSSESSION = "possession"
    CLOSURE = "closure"


class TaskStatus(str, enum.Enum):
    """Status of a workflow task."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    ESCALATED = "escalated"


class TaskPriority(str, enum.Enum):
    """Priority level of a workflow task."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ---------------------------------------------------------------------------
# Field Verification
# ---------------------------------------------------------------------------


class VerificationStatus(str, enum.Enum):
    """Status of a field verification submission."""

    SUBMITTED = "submitted"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVERIFICATION_REQUESTED = "reverification_requested"


# ---------------------------------------------------------------------------
# AI / Analytics
# ---------------------------------------------------------------------------


class RiskLevel(str, enum.Enum):
    """Risk level classification for projects and parcels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalySeverity(str, enum.Enum):
    """Severity of a detected anomaly."""

    INFO = "info"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationSeverity(str, enum.Enum):
    """Severity level for system notifications."""

    INFO = "info"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
