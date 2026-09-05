"""Seed the database with realistic demo data for BHUMI-AI.

Run from the backend directory:
    python -m scripts.seed

Idempotent: skips seeding if data already exists.

Demo credentials:
    Central Admin:   admin@mord.gov.in       / admin123
    State Admin:     rajasthan@gov.in        / state123
    District Officer: jaipur@gov.in          / district123
    Project Auth:    rj-hwy@nhia.in          / project123
    Field Officer:   field.rahul@gov.in      / field123
    Auditor:         auditor@mord.gov.in     / audit123
    Citizen:         citizen@example.com     / citizen123
"""

import sys
import os
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from geoalchemy2 import WKTElement

from app.config import settings
from app.auth.security import hash_password
from app.models.base import Base
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
from app.models.enums import (
    UserRole, ProjectStatus, LandType, OwnershipType,
    PossessionStatus, ProposalStatus, Urgency, NoticeType,
    CompensationStatus, RAndRStatus, DisputeStatus, DisputeType,
    DocumentType, DocumentStatus, WorkflowStage, TaskStatus, TaskPriority,
    VerificationStatus, RiskLevel, AnomalySeverity,
)


def _sync_url(url: str) -> str:
    return url.replace("+asyncpg", "")


def seed(force: bool = False) -> None:
    engine = create_engine(_sync_url(settings.database_url), echo=False)

    # Ensure PostgreSQL enum types have newly added enum values
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        enum_additions = [
            ("user_role", ["field_officer", "auditor", "citizen"]),
            ("compensation_status", ["under_verification"]),
            ("task_status", ["not_started", "in_progress", "pending_review", "approved", "rejected", "blocked", "completed", "overdue", "escalated"]),
            ("dispute_status", ["open", "under_review", "hearing_scheduled", "resolved", "dismissed", "escalated"]),
            ("document_status", ["uploaded", "under_review", "ai_analyzed", "approved", "rejected", "revision_required"]),
        ]
        for enum_name, values in enum_additions:
            for val in values:
                try:
                    conn.execute(text(f"ALTER TYPE {enum_name} ADD VALUE IF NOT EXISTS '{val}';"))
                except Exception:
                    pass

    Base.metadata.create_all(bind=engine)

    if "--force" in sys.argv or "-f" in sys.argv:
        force = True

    with Session(engine) as session:
        if force:
            print("🔄 Truncating tables for fresh seed...")
            for tbl in ["ai_anomalies", "ai_risk_predictions", "system_notifications",
                        "audit_logs", "field_verifications", "workflow_tasks", "documents", "disputes",
                        "families", "compensations", "awards", "notifications", "proposals", "land_parcels",
                        "projects", "users"]:
                try:
                    session.execute(text(f"TRUNCATE TABLE {tbl} RESTART IDENTITY CASCADE;"))
                except Exception:
                    pass
            session.commit()

        existing = session.execute(text("SELECT count(*) FROM users")).scalar()
        if existing and existing > 0:
            print("⚠  Database already contains data. Skipping seed.")
            print("   Pass --force or -f to re-seed.")
            return

        now = datetime.now(timezone.utc)
        pwd = hash_password("admin123")
        pwd_state = hash_password("state123")
        pwd_district = hash_password("district123")
        pwd_project = hash_password("project123")
        pwd_field = hash_password("field123")
        pwd_audit = hash_password("audit123")
        pwd_citizen = hash_password("citizen123")

        # ================================================================
        # USERS
        # ================================================================
        u_central = User(id=uuid.uuid4(), email="admin@mord.gov.in", password_hash=pwd,
                         full_name="Rajesh Kumar (Central Admin)", role=UserRole.CENTRAL_MINISTRY, is_active=True)
        u_state_rj = User(id=uuid.uuid4(), email="rajasthan@gov.in", password_hash=pwd_state,
                          full_name="Priya Sharma (Rajasthan)", role=UserRole.STATE_GOVT,
                          state="Rajasthan", is_active=True)
        u_state_mh = User(id=uuid.uuid4(), email="maharashtra@gov.in", password_hash=pwd_state,
                          full_name="Suresh Naik (Maharashtra)", role=UserRole.STATE_GOVT,
                          state="Maharashtra", is_active=True)
        u_district_jaipur = User(id=uuid.uuid4(), email="jaipur@gov.in", password_hash=pwd_district,
                                 full_name="Amit Verma (Jaipur DO)", role=UserRole.DISTRICT_AUTHORITY,
                                 state="Rajasthan", district="Jaipur", is_active=True)
        u_district_pune = User(id=uuid.uuid4(), email="pune@gov.in", password_hash=pwd_district,
                               full_name="Sneha Patil (Pune DO)", role=UserRole.DISTRICT_AUTHORITY,
                               state="Maharashtra", district="Pune", is_active=True)
        u_project = User(id=uuid.uuid4(), email="rj-hwy@nhia.in", password_hash=pwd_project,
                         full_name="Sunita Reddy (NHAI PM)", role=UserRole.PROJECT_AGENCY,
                         state="Rajasthan", district="Jaipur", is_active=True)
        u_field = User(id=uuid.uuid4(), email="field.rahul@gov.in", password_hash=pwd_field,
                       full_name="Rahul Sharma (Field Officer)", role=UserRole.FIELD_OFFICER,
                       state="Rajasthan", district="Jaipur", is_active=True)
        u_auditor = User(id=uuid.uuid4(), email="auditor@mord.gov.in", password_hash=pwd_audit,
                         full_name="CAG Auditor", role=UserRole.AUDITOR, is_active=True)
        u_citizen = User(id=uuid.uuid4(), email="citizen@example.com", password_hash=pwd_citizen,
                         full_name="Ram Lal (Citizen)", role=UserRole.CITIZEN,
                         state="Rajasthan", district="Jaipur", is_active=True)

        all_users = [u_central, u_state_rj, u_state_mh, u_district_jaipur, u_district_pune,
                     u_project, u_field, u_auditor, u_citizen]
        session.add_all(all_users)
        session.flush()

        # ================================================================
        # PROJECTS — 20+ projects across 6 states
        # ================================================================
        def mkproject(name, ministry, sector, state, district, status, desc=""):
            return Project(id=uuid.uuid4(), name=name, ministry=ministry, sector=sector,
                          description=desc, status=status, state=state, district=district,
                          created_by=u_central.id, updated_by=u_central.id)

        # FLAGSHIP: RJ-HWY-024
        p_rjhwy = mkproject(
            "Delhi-Jaipur Highway Expansion", "Ministry of Road Transport & Highways",
            "Infrastructure", "Rajasthan", "Jaipur", ProjectStatus.ACTIVE,
            "Six-lane expansion of NH-48 from Delhi border to Jaipur. Total corridor: 280km."
        )
        # Give it a fixed UUID for demo purposes
        p_rjhwy.id = uuid.UUID("12345678-1234-5678-1234-567812345678")

        projects = [
            p_rjhwy,
            mkproject("Mumbai-Pune Expressway Expansion", "Ministry of Road Transport & Highways",
                     "Infrastructure", "Maharashtra", "Pune", ProjectStatus.ACTIVE),
            mkproject("Krishna River Dam", "Ministry of Jal Shakti",
                     "Water Resources", "Karnataka", "Raichur", ProjectStatus.PLANNING,
                     "Multi-purpose dam for irrigation and hydropower."),
            mkproject("PMAY Housing Scheme Pune", "Ministry of Housing & Urban Affairs",
                     "Housing", "Maharashtra", "Pune", ProjectStatus.ACTIVE),
            mkproject("Rajasthan Solar Park Phase-2", "Ministry of New & Renewable Energy",
                     "Energy", "Rajasthan", "Barmer", ProjectStatus.ACTIVE),
            mkproject("Gujarat Bullet Train Corridor", "Ministry of Railways",
                     "Infrastructure", "Gujarat", "Surat", ProjectStatus.ACTIVE),
            mkproject("UP Expressway Extension", "Ministry of Road Transport & Highways",
                     "Infrastructure", "Uttar Pradesh", "Lucknow", ProjectStatus.ACTIVE),
            mkproject("MP Narmada Canal Project", "Ministry of Jal Shakti",
                     "Water Resources", "Madhya Pradesh", "Jabalpur", ProjectStatus.PLANNING),
            mkproject("Karnataka Industrial Corridor", "Ministry of Commerce & Industry",
                     "Industrial", "Karnataka", "Bengaluru", ProjectStatus.ACTIVE),
            mkproject("Rajasthan Metro Phase-1", "Ministry of Housing & Urban Affairs",
                     "Infrastructure", "Rajasthan", "Jodhpur", ProjectStatus.PLANNING),
            mkproject("Haryana Outer Ring Road", "Ministry of Road Transport & Highways",
                     "Infrastructure", "Haryana", "Gurugram", ProjectStatus.ACTIVE),
            mkproject("Odisha Port Expansion", "Ministry of Ports & Shipping",
                     "Infrastructure", "Odisha", "Puri", ProjectStatus.ACTIVE),
            mkproject("Tamil Nadu Coastal Highway", "Ministry of Road Transport & Highways",
                     "Infrastructure", "Tamil Nadu", "Chennai", ProjectStatus.ACTIVE),
            mkproject("Bihar Smart City", "Ministry of Housing & Urban Affairs",
                     "Housing", "Bihar", "Patna", ProjectStatus.PLANNING),
            mkproject("Delhi-Meerut RRTS", "Ministry of Housing & Urban Affairs",
                     "Infrastructure", "Uttar Pradesh", "Meerut", ProjectStatus.ACTIVE),
            mkproject("Andhra Pradesh Greenfield Airport", "Ministry of Civil Aviation",
                     "Infrastructure", "Andhra Pradesh", "Amaravati", ProjectStatus.PLANNING),
            mkproject("Punjab Canal Modernization", "Ministry of Jal Shakti",
                     "Water Resources", "Punjab", "Ludhiana", ProjectStatus.ACTIVE),
            mkproject("Telangana IT Hub Expansion", "Ministry of Commerce & Industry",
                     "Industrial", "Telangana", "Hyderabad", ProjectStatus.ACTIVE),
            mkproject("West Bengal Industrial Park", "Ministry of Commerce & Industry",
                     "Industrial", "West Bengal", "Kolkata", ProjectStatus.PLANNING),
            mkproject("Uttarakhand Hydro Power", "Ministry of New & Renewable Energy",
                     "Energy", "Uttarakhand", "Dehradun", ProjectStatus.ACTIVE),
            mkproject("Assam River Bridge Network", "Ministry of Road Transport & Highways",
                     "Infrastructure", "Assam", "Guwahati", ProjectStatus.ACTIVE),
            mkproject("Kerala Coastal Protection", "Ministry of Jal Shakti",
                     "Water Resources", "Kerala", "Kochi", ProjectStatus.COMPLETED),
        ]
        session.add_all(projects)
        session.flush()

        # ================================================================
        # PARCELS for RJ-HWY-024 — 500 parcels (7 critical, 52 comp pending, 18 disputed)
        # ================================================================
        rjhwy_parcels = []
        critical_parcel_ids = []
        
        # Critical parcel IDs
        critical_ids = [
            uuid.UUID("aaaaaaaa-0001-4000-8000-000000000001"),
            uuid.UUID("aaaaaaaa-0002-4000-8000-000000000002"),
            uuid.UUID("aaaaaaaa-0003-4000-8000-000000000003"),
            uuid.UUID("aaaaaaaa-0004-4000-8000-000000000004"),
            uuid.UUID("aaaaaaaa-0005-4000-8000-000000000005"),
            uuid.UUID("aaaaaaaa-0006-4000-8000-000000000006"),
            uuid.UUID("aaaaaaaa-0007-4000-8000-000000000007"),
        ]

        villages = ["Chomu", "Kotputli", "Shahpura", "Dausa", "Bandikui", "Alwar", "Bhiwadi"]
        talukas = ["Chomu", "Kotputli", "Shahpura", "Dausa", "Bandikui", "Alwar", "Bhiwadi"]
        
        # Jaipur coordinates roughly 26.9N, 75.8E — corridor heading NE toward Delhi
        base_lat, base_lon = 26.9, 75.8

        for i in range(500):
            is_critical = i < 7
            is_disputed = 7 <= i < 25  # 18 disputed
            is_comp_pending = 25 <= i < 77  # 52 compensation pending
            is_acquired = i >= 90  # 410 acquired (of 500)

            pid = critical_ids[i] if is_critical else uuid.uuid4()
            if is_critical:
                critical_parcel_ids.append(str(pid))

            # Spread along ~280km corridor NE of Jaipur
            segment = i / 500
            lat = base_lat + segment * 2.5 + (i % 7) * 0.001
            lon = base_lon + segment * 3.0 + (i % 5) * 0.001

            d_lat = 0.002
            d_lon = 0.002
            geom_wkt = (
                f"MULTIPOLYGON((({lon} {lat}, {lon+d_lon} {lat}, "
                f"{lon+d_lon} {lat+d_lat}, {lon} {lat+d_lat}, {lon} {lat})))"
            )

            status = PossessionStatus.POSSESSED if is_acquired else \
                     PossessionStatus.AWARDED if is_comp_pending else \
                     PossessionStatus.NOTICE_ISSUED if is_disputed else \
                     PossessionStatus.NOT_ACQUIRED

            village_idx = i % len(villages)
            p = LandParcel(
                id=pid,
                project_id=p_rjhwy.id,
                geometry=WKTElement(geom_wkt, srid=4326),
                survey_number=f"{100 + (i // 10)}/{i % 10 + 1}",
                land_type=LandType.AGRICULTURAL if i % 3 != 0 else LandType.RESIDENTIAL,
                area_hectares=Decimal(f"{1.0 + (i % 5) * 0.4:.4f}"),
                state="Rajasthan",
                district="Jaipur",
                taluka=talukas[village_idx],
                village=villages[village_idx],
                ownership_type=OwnershipType.DISPUTED if is_disputed else OwnershipType.PRIVATE,
                possession_status=status,
                created_by=u_district_jaipur.id,
                updated_by=u_district_jaipur.id,
            )
            rjhwy_parcels.append(p)

        session.add_all(rjhwy_parcels)
        session.flush()

        # ================================================================
        # Parcels for other projects (sample)
        # ================================================================
        other_parcels = [
            LandParcel(
                id=uuid.uuid4(), project_id=projects[1].id,
                geometry=WKTElement("MULTIPOLYGON(((73.85 18.52, 73.86 18.52, 73.86 18.53, 73.85 18.53, 73.85 18.52)))", srid=4326),
                survey_number="SY-42/1A", land_type=LandType.AGRICULTURAL, area_hectares=Decimal("12.5"),
                state="Maharashtra", district="Pune", taluka="Maval", village="Talegaon",
                ownership_type=OwnershipType.PRIVATE, possession_status=PossessionStatus.NOTICE_ISSUED,
                created_by=u_district_pune.id, updated_by=u_district_pune.id,
            ),
            LandParcel(
                id=uuid.uuid4(), project_id=projects[1].id,
                geometry=WKTElement("MULTIPOLYGON(((73.87 18.53, 73.88 18.53, 73.88 18.54, 73.87 18.54, 73.87 18.53)))", srid=4326),
                survey_number="SY-43/2B", land_type=LandType.AGRICULTURAL, area_hectares=Decimal("8.3"),
                state="Maharashtra", district="Pune", taluka="Maval", village="Dehu Road",
                ownership_type=OwnershipType.PRIVATE, possession_status=PossessionStatus.POSSESSED,
                created_by=u_district_pune.id, updated_by=u_district_pune.id,
            ),
        ]
        session.add_all(other_parcels)
        session.flush()

        # ================================================================
        # PROPOSALS
        # ================================================================
        proposals = [
            Proposal(
                id=uuid.uuid4(), project_id=p_rjhwy.id,
                submitted_by=u_project.id, status=ProposalStatus.APPROVED,
                purpose="Land acquisition for 6-lane highway expansion on NH-48. SIA completed, clearances obtained.",
                urgency=Urgency.NORMAL, remarks="SIA report satisfactory. All clearances verified.",
                submitted_at=now - timedelta(days=90), reviewed_by=u_state_rj.id,
                reviewed_at=now - timedelta(days=60), created_by=u_project.id,
            ),
            Proposal(
                id=uuid.uuid4(), project_id=projects[2].id,
                submitted_by=u_project.id, status=ProposalStatus.UNDER_SCRUTINY,
                purpose="Acquisition for Krishna River Dam reservoir. Urgent water security need.",
                urgency=Urgency.URGENT, remarks=None,
                submitted_at=now - timedelta(days=10),
                created_by=u_project.id,
            ),
        ]
        session.add_all(proposals)
        session.flush()

        # ================================================================
        # AWARDS for critical parcels
        # ================================================================
        awards = []
        compensations = []
        for i, parcel in enumerate(rjhwy_parcels[:90]):  # First 90 get awards
            area = float(parcel.area_hectares)
            market_val = area * 3500000  # 35L/hectare market value
            declared = market_val * 2  # 2x with solatium per LARR
            a = Award(
                id=uuid.uuid4(), parcel_id=parcel.id,
                declared_amount=Decimal(str(declared)),
                market_value=Decimal(str(market_val)),
                solatium_amount=Decimal(str(market_val)),
                declared_at=now - timedelta(days=30 + i),
                declared_by=u_district_jaipur.id, created_by=u_district_jaipur.id,
            )
            awards.append(a)

            # Compensation (52 pending = i < 52 → PENDING, rest DISBURSED)
            status = CompensationStatus.PENDING if i < 52 else CompensationStatus.DISBURSED
            c = Compensation(
                id=uuid.uuid4(), award_id=a.id,
                beneficiary_name=f"Owner {parcel.survey_number}",
                beneficiary_account=f"SBI-XXXXX{i:04d}",
                disbursed_amount=Decimal(str(declared)),
                disbursed_at=now - timedelta(days=10) if status == CompensationStatus.DISBURSED else None,
                payment_reference=f"NEFT-{i:06d}" if status == CompensationStatus.DISBURSED else None,
                status=status,
                created_by=u_district_jaipur.id,
            )
            compensations.append(c)

        # Special anomaly compensation (unusually high — for AI demo)
        anomaly_award = Award(
            id=uuid.uuid4(), parcel_id=rjhwy_parcels[50].id,
            declared_amount=Decimal("18000000"),  # 1.8 crore — unusual
            market_value=Decimal("9000000"),
            solatium_amount=Decimal("9000000"),
            declared_at=now - timedelta(days=5),
            declared_by=u_district_jaipur.id, created_by=u_district_jaipur.id,
        )
        anomaly_comp = Compensation(
            id=uuid.uuid4(), award_id=anomaly_award.id,
            beneficiary_name="Ram Lal (High Value Case)",
            disbursed_amount=Decimal("18000000"),
            status=CompensationStatus.PENDING,
            created_by=u_district_jaipur.id,
        )
        awards.append(anomaly_award)
        compensations.append(anomaly_comp)

        session.add_all(awards)
        session.add_all(compensations)
        session.flush()

        # ================================================================
        # DISPUTES — 18 disputed parcels
        # ================================================================
        dispute_types = [DisputeType.OWNERSHIP, DisputeType.VALUATION, DisputeType.BOUNDARY,
                         DisputeType.COMPENSATION, DisputeType.PROCEDURAL]
        disputes = []
        for i, parcel in enumerate(rjhwy_parcels[7:25]):  # 18 disputed parcels
            d = Dispute(
                id=uuid.uuid4(), parcel_id=parcel.id,
                dispute_type=dispute_types[i % len(dispute_types)],
                status=DisputeStatus.OPEN if i < 12 else DisputeStatus.UNDER_REVIEW,
                title=f"Dispute on parcel {parcel.survey_number} — {dispute_types[i % len(dispute_types)].value}",
                description=f"Landowner contesting {dispute_types[i % len(dispute_types)].value} for parcel {parcel.survey_number} in village {parcel.village}.",
                raised_by=u_citizen.id, created_by=u_citizen.id,
                court_case_number=f"RC/{2026}/{1000 + i}" if i < 5 else None,
            )
            disputes.append(d)
        session.add_all(disputes)
        session.flush()

        # ================================================================
        # FAMILIES (R&R) — 31 pending
        # ================================================================
        families = []
        for i, parcel in enumerate(rjhwy_parcels[:31]):
            status = RAndRStatus.IDENTIFIED if i < 15 else RAndRStatus.SURVEY_COMPLETED
            f = Family(
                id=uuid.uuid4(), parcel_id=parcel.id,
                head_of_household=f"Family Head {i+1}",
                family_size=3 + (i % 5),
                annual_income=Decimal(str(80000 + i * 5000)),
                r_and_r_status=status,
                alternative_land_provided=False,
                employment_provided=i % 3 == 0,
                created_by=u_district_jaipur.id,
            )
            families.append(f)
        session.add_all(families)
        session.flush()

        # ================================================================
        # DOCUMENTS
        # ================================================================
        docs = [
            Document(
                id=uuid.uuid4(), project_id=p_rjhwy.id,
                document_type=DocumentType.AWARD, title="Award Order — Parcel 124/2",
                status=DocumentStatus.UNDER_REVIEW, version=1,
                file_name="award_124_2.pdf",
                extracted_fields={"project_id": "RJ-HWY-024", "survey_number": "124/2", "award_amount": "18400000"},
                validation_result={"status": "requires_review", "issues": ["Amount mismatch", "Missing signature"]},
                ai_confidence_score=0.88,
                created_by=u_project.id,
            ),
            Document(
                id=uuid.uuid4(), project_id=p_rjhwy.id,
                document_type=DocumentType.PRELIMINARY_NOTIFICATION,
                title="Section 11 Notification — RJ-HWY-024",
                status=DocumentStatus.APPROVED, version=1,
                file_name="section11_notification.pdf",
                created_by=u_district_jaipur.id,
            ),
            Document(
                id=uuid.uuid4(), project_id=p_rjhwy.id,
                document_type=DocumentType.SOCIAL_IMPACT_ASSESSMENT,
                title="Social Impact Assessment Report",
                status=DocumentStatus.APPROVED, version=2,
                file_name="sia_report_v2.pdf",
                created_by=u_project.id,
            ),
        ]
        session.add_all(docs)
        session.flush()

        # ================================================================
        # WORKFLOW TASKS
        # ================================================================
        tasks = [
            WorkflowTask(
                id=uuid.uuid4(), project_id=p_rjhwy.id, parcel_id=rjhwy_parcels[0].id,
                stage=WorkflowStage.COMPENSATION, title="Verify compensation documents — Parcel 100/1",
                assigned_to=u_field.id, status=TaskStatus.IN_PROGRESS,
                priority=TaskPriority.HIGH,
                due_date=now + timedelta(days=3),
                created_by=u_district_jaipur.id, updated_by=u_district_jaipur.id,
            ),
            WorkflowTask(
                id=uuid.uuid4(), project_id=p_rjhwy.id,
                stage=WorkflowStage.VERIFICATION, title="Field verification — Block B parcels",
                assigned_to=u_field.id, status=TaskStatus.PENDING_REVIEW,
                priority=TaskPriority.CRITICAL,
                due_date=now - timedelta(days=2),  # Overdue
                is_escalated=True,
                created_by=u_district_jaipur.id, updated_by=u_district_jaipur.id,
            ),
            WorkflowTask(
                id=uuid.uuid4(), project_id=p_rjhwy.id,
                stage=WorkflowStage.AWARD, title="District approval for 15 award orders",
                assigned_to=u_district_jaipur.id, status=TaskStatus.OVERDUE,
                priority=TaskPriority.CRITICAL,
                due_date=now - timedelta(days=5),
                is_escalated=False,
                created_by=u_state_rj.id, updated_by=u_state_rj.id,
            ),
        ]
        session.add_all(tasks)
        session.flush()

        # ================================================================
        # AI RISK PREDICTIONS
        # ================================================================
        risk_data = [
            (p_rjhwy.id, RiskLevel.HIGH, 0.82, 0.82, 23, [
                {"factor": "Compensation backlog", "contribution_pct": 36, "description": "52 cases pending verification"},
                {"factor": "Land disputes", "contribution_pct": 29, "description": "18 active disputes, 7 critical"},
                {"factor": "R&R pending", "contribution_pct": 21, "description": "31 families not resettled"},
                {"factor": "Approval delay", "contribution_pct": 14, "description": "5 approvals overdue >7 days"},
            ], critical_parcel_ids,
            "Project RJ-HWY-024 has an estimated 82% probability of missing its possession target. "
            "The major contributors are 52 pending compensation cases, 18 disputed parcels and 31 pending R&R cases."),
            (projects[1].id, RiskLevel.MEDIUM, 0.45, 0.45, 8, [
                {"factor": "Survey incomplete", "contribution_pct": 55, "description": "3 parcels pending survey"},
                {"factor": "Compensation pending", "contribution_pct": 45, "description": "7 cases pending"},
            ], [], "Medium risk due to pending surveys."),
            (projects[4].id, RiskLevel.LOW, 0.15, 0.15, 0, [], [], "Project on track with minimal risk."),
            (projects[5].id, RiskLevel.CRITICAL, 0.91, 0.91, 45, [
                {"factor": "Court injunction", "contribution_pct": 60, "description": "Active stay order"},
                {"factor": "Land disputes", "contribution_pct": 40, "description": "12 ownership disputes"},
            ], [], "Critical: Court injunction delaying entire corridor."),
        ]
        ai_risks = []
        for proj_id, level, score, prob, delay, factors, critical_ids_list, explanation in risk_data:
            r = AIRiskPrediction(
                id=uuid.uuid4(), project_id=proj_id, risk_level=level,
                risk_score=score, delay_probability=prob, expected_delay_days=delay,
                contributing_factors=factors, critical_parcel_ids=critical_ids_list,
                explanation=explanation, model_version="mock-v1.0",
            )
            ai_risks.append(r)
        session.add_all(ai_risks)
        session.flush()

        # ================================================================
        # AI ANOMALIES
        # ================================================================
        anomalies = [
            AIAnomaly(
                id=uuid.uuid4(), entity_type="Compensation", entity_id=str(anomaly_comp.id),
                anomaly_type="unusual_value", severity=AnomalySeverity.HIGH,
                description="Compensation amount Rs 1.8 crore is 4.2x the district average for similar land type.",
                detected_value="18000000", expected_range="3500000-8000000",
                is_resolved=False,
            ),
            AIAnomaly(
                id=uuid.uuid4(), entity_type="LandParcel", entity_id=str(rjhwy_parcels[10].id),
                anomaly_type="duplicate_survey_number", severity=AnomalySeverity.MEDIUM,
                description="Survey number 101/1 appears in two different parcels — possible data entry error.",
                detected_value="101/1", expected_range=None, is_resolved=False,
            ),
            AIAnomaly(
                id=uuid.uuid4(), entity_type="FieldVerification", entity_id="fv-demo-001",
                anomaly_type="gps_mismatch", severity=AnomalySeverity.MEDIUM,
                description="GPS coordinates captured during field verification are 320m from registered parcel location.",
                detected_value="26.9180, 75.7960", expected_range="within 100m of 26.9150, 75.7920",
                is_resolved=False,
            ),
        ]
        session.add_all(anomalies)
        session.flush()

        # ================================================================
        # SYSTEM NOTIFICATIONS
        # ================================================================
        notifications = [
            SystemNotification(
                id=uuid.uuid4(), recipient_id=None,  # Broadcast
                title="CRITICAL: RJ-HWY-024 at 82% delay risk",
                message="Project RJ-HWY-024 has an 82% probability of missing its possession target. Immediate action required on 7 critical parcels.",
                severity="critical", entity_type="Project", entity_id=str(p_rjhwy.id),
                link_url=f"/projects/{p_rjhwy.id}", action_label="View Project",
            ),
            SystemNotification(
                id=uuid.uuid4(), recipient_id=u_district_jaipur.id,
                title="HIGH: 7 disputed parcels blocking project progress",
                message="7 high-impact disputed parcels are blocking compensation and possession for RJ-HWY-024.",
                severity="high", entity_type="Project", entity_id=str(p_rjhwy.id),
                link_url=f"/projects/{p_rjhwy.id}/disputes", action_label="View Disputes",
            ),
            SystemNotification(
                id=uuid.uuid4(), recipient_id=u_field.id,
                title="New Field Verification Task Assigned",
                message="You have been assigned to verify compensation documents for Parcel 100/1. Due: 3 days.",
                severity="high", entity_type="WorkflowTask",
            ),
            SystemNotification(
                id=uuid.uuid4(), recipient_id=u_central.id,
                title="MEDIUM: 31 compensation cases require verification",
                message="31 compensation cases for RJ-HWY-024 are pending field verification.",
                severity="medium", entity_type="Project", entity_id=str(p_rjhwy.id),
            ),
            SystemNotification(
                id=uuid.uuid4(), recipient_id=None,
                title="Anomaly detected: Unusual compensation value",
                message="A compensation value of Rs 1.8 crore was detected — 4.2x the district average. Manual review recommended.",
                severity="high", entity_type="Compensation",
                action_label="Review Anomaly",
            ),
        ]
        session.add_all(notifications)

        # ================================================================
        # AUDIT LOGS (sample history)
        # ================================================================
        audit_logs = [
            AuditLog(
                id=uuid.uuid4(), user_id=u_district_jaipur.id,
                user_email=u_district_jaipur.email, user_role="district_authority",
                action="APPROVE_PROPOSAL", entity_type="Proposal", entity_id=str(proposals[0].id),
                old_value={"status": "under_scrutiny"}, new_value={"status": "approved"},
                description="Proposal approved after SIA review.",
                timestamp=now - timedelta(days=60),
            ),
            AuditLog(
                id=uuid.uuid4(), user_id=u_state_rj.id,
                user_email=u_state_rj.email, user_role="state_govt",
                action="APPROVE_COMPENSATION", entity_type="Compensation", entity_id=str(compensations[0].id),
                old_value={"status": "processing"}, new_value={"status": "disbursed"},
                description="Compensation approved and disbursed.",
                timestamp=now - timedelta(days=10),
            ),
        ]
        session.add_all(audit_logs)
        session.commit()

        print("✓ BHUMI-AI seed data inserted successfully:")
        print(f"  • Users:              {len(all_users)}")
        print(f"  • Projects:           {len(projects)}")
        print(f"  • Land Parcels:       {len(rjhwy_parcels) + len(other_parcels)}")
        print(f"  • Awards:             {len(awards)}")
        print(f"  • Compensations:      {len(compensations)}")
        print(f"  • Disputes:           {len(disputes)}")
        print(f"  • Families (R&R):     {len(families)}")
        print(f"  • Documents:          {len(docs)}")
        print(f"  • Workflow Tasks:     {len(tasks)}")
        print(f"  • AI Risk Predictions:{len(ai_risks)}")
        print(f"  • AI Anomalies:       {len(anomalies)}")
        print(f"  • Notifications:      {len(notifications)}")
        print(f"\n  Demo credentials:")
        print(f"    Central Admin: admin@mord.gov.in / admin123")
        print(f"    State Admin:   rajasthan@gov.in / state123")
        print(f"    District:      jaipur@gov.in / district123")
        print(f"    Project Auth:  rj-hwy@nhia.in / project123")
        print(f"    Field Officer: field.rahul@gov.in / field123")


if __name__ == "__main__":
    seed()
