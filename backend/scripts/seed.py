"""Seed the database with realistic sample data for development and demos.

Run from the backend directory:
    python -m scripts.seed

This script uses a SYNCHRONOUS SQLAlchemy engine (psycopg2) for simplicity.
It is NOT part of the async application runtime.

Idempotent: skips seeding if data already exists.
"""

import sys
import os
import uuid
from datetime import datetime, timedelta, timezone

# Ensure the backend directory is on the Python path so `from app...` works
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.config import settings
from app.models.base import Base
from app.models.user import User
from app.models.project import Project
from app.models.land_parcel import LandParcel
from app.models.proposal import Proposal
from app.models.notification import Notification
from app.models.award import Award
from app.models.compensation import Compensation
from app.models.family import Family
from app.models.enums import (
    UserRole, ProjectStatus, LandType, OwnershipType,
    PossessionStatus, ProposalStatus, Urgency, NoticeType,
    CompensationStatus, RAndRStatus,
)

# GeoAlchemy2 WKT helper for geometry values
from geoalchemy2 import WKTElement


def _sync_url(url: str) -> str:
    """Strip async driver prefix if present — this script uses psycopg2."""
    return url.replace("+asyncpg", "")


def seed() -> None:
    """Populate the database with sample data."""
    engine = create_engine(_sync_url(settings.database_url), echo=False)

    with Session(engine) as session:
        # --- Idempotency check ---
        existing = session.execute(text("SELECT count(*) FROM users")).scalar()
        if existing and existing > 0:
            print("⚠  Database already contains data. Skipping seed.")
            print("   To re-seed, truncate all tables first:")
            print("   TRUNCATE families, compensations, awards, notifications,")
            print("            proposals, land_parcels, projects, users CASCADE;")
            return

        now = datetime.now(timezone.utc)

        # ==============================================================
        # USERS — one per role
        # ==============================================================
        users = {
            "central": User(
                id=uuid.uuid4(),
                email="admin@mord.gov.in",
                # Placeholder hash — Module 2 will add proper bcrypt hashing.
                password_hash="$placeholder$_not_a_real_hash",
                full_name="Rajesh Kumar",
                role=UserRole.CENTRAL_MINISTRY,
                state=None,
                district=None,
                is_active=True,
            ),
            "state": User(
                id=uuid.uuid4(),
                email="collector@maharashtra.gov.in",
                password_hash="$placeholder$_not_a_real_hash",
                full_name="Priya Sharma",
                role=UserRole.STATE_GOVT,
                state="Maharashtra",
                district=None,
                is_active=True,
            ),
            "district": User(
                id=uuid.uuid4(),
                email="dc@pune.gov.in",
                password_hash="$placeholder$_not_a_real_hash",
                full_name="Amit Patel",
                role=UserRole.DISTRICT_AUTHORITY,
                state="Maharashtra",
                district="Pune",
                is_active=True,
            ),
            "agency": User(
                id=uuid.uuid4(),
                email="pm@nhai.gov.in",
                password_hash="$placeholder$_not_a_real_hash",
                full_name="Sunita Reddy",
                role=UserRole.PROJECT_AGENCY,
                state="Maharashtra",
                district="Pune",
                is_active=True,
            ),
        }
        session.add_all(users.values())
        session.flush()  # Assign IDs before referencing them

        # ==============================================================
        # PROJECTS
        # ==============================================================
        projects = {
            "highway": Project(
                id=uuid.uuid4(),
                name="Mumbai-Pune Expressway Expansion",
                ministry="Ministry of Road Transport & Highways",
                sector="Infrastructure",
                description=(
                    "Six-lane expansion of the existing Mumbai-Pune Expressway "
                    "corridor covering Talegaon to Dehu Road section."
                ),
                status=ProjectStatus.ACTIVE,
                state="Maharashtra",
                district="Pune",
                created_by=users["central"].id,
            ),
            "dam": Project(
                id=uuid.uuid4(),
                name="Krishna River Dam Project",
                ministry="Ministry of Jal Shakti",
                sector="Water Resources",
                description="Multi-purpose dam for irrigation and hydropower on the Krishna river.",
                status=ProjectStatus.PLANNING,
                state="Karnataka",
                district="Raichur",
                created_by=users["central"].id,
            ),
            "housing": Project(
                id=uuid.uuid4(),
                name="Affordable Housing Scheme — Pune",
                ministry="Ministry of Housing & Urban Affairs",
                sector="Housing",
                description="PMAY affordable housing project on acquired government wasteland.",
                status=ProjectStatus.ACTIVE,
                state="Maharashtra",
                district="Pune",
                created_by=users["central"].id,
            ),
        }
        session.add_all(projects.values())
        session.flush()

        # ==============================================================
        # LAND PARCELS (with sample PostGIS geometries near Pune & Raichur)
        # ==============================================================
        parcels = [
            LandParcel(
                id=uuid.uuid4(),
                project_id=projects["highway"].id,
                geometry=WKTElement(
                    "MULTIPOLYGON(((73.85 18.52, 73.86 18.52, 73.86 18.53, "
                    "73.85 18.53, 73.85 18.52)))",
                    srid=4326,
                ),
                survey_number="SY-42/1A",
                land_type=LandType.AGRICULTURAL,
                area_hectares=12.5000,
                state="Maharashtra",
                district="Pune",
                taluka="Maval",
                village="Talegaon",
                ownership_type=OwnershipType.PRIVATE,
                possession_status=PossessionStatus.NOTICE_ISSUED,
                created_by=users["district"].id,
            ),
            LandParcel(
                id=uuid.uuid4(),
                project_id=projects["highway"].id,
                geometry=WKTElement(
                    "MULTIPOLYGON(((73.87 18.53, 73.88 18.53, 73.88 18.54, "
                    "73.87 18.54, 73.87 18.53)))",
                    srid=4326,
                ),
                survey_number="SY-43/2B",
                land_type=LandType.AGRICULTURAL,
                area_hectares=8.3000,
                state="Maharashtra",
                district="Pune",
                taluka="Maval",
                village="Dehu Road",
                ownership_type=OwnershipType.PRIVATE,
                possession_status=PossessionStatus.NOT_ACQUIRED,
                created_by=users["district"].id,
            ),
            LandParcel(
                id=uuid.uuid4(),
                project_id=projects["housing"].id,
                geometry=WKTElement(
                    "MULTIPOLYGON(((73.90 18.55, 73.91 18.55, 73.91 18.56, "
                    "73.90 18.56, 73.90 18.55)))",
                    srid=4326,
                ),
                survey_number="SY-105/3",
                land_type=LandType.WASTELAND,
                area_hectares=25.0000,
                state="Maharashtra",
                district="Pune",
                taluka="Haveli",
                village="Wagholi",
                ownership_type=OwnershipType.GOVERNMENT,
                possession_status=PossessionStatus.POSSESSED,
                created_by=users["district"].id,
            ),
            LandParcel(
                id=uuid.uuid4(),
                project_id=projects["dam"].id,
                geometry=WKTElement(
                    "MULTIPOLYGON(((76.40 16.20, 76.42 16.20, 76.42 16.22, "
                    "76.40 16.22, 76.40 16.20)))",
                    srid=4326,
                ),
                survey_number="SY-201/1",
                land_type=LandType.AGRICULTURAL,
                area_hectares=150.0000,
                state="Karnataka",
                district="Raichur",
                taluka="Sindhanur",
                village="Hatti",
                ownership_type=OwnershipType.COMMUNITY,
                possession_status=PossessionStatus.NOT_ACQUIRED,
                created_by=users["district"].id,
            ),
            LandParcel(
                id=uuid.uuid4(),
                project_id=projects["highway"].id,
                geometry=WKTElement(
                    "MULTIPOLYGON(((73.82 18.50, 73.83 18.50, 73.83 18.51, "
                    "73.82 18.51, 73.82 18.50)))",
                    srid=4326,
                ),
                survey_number="SY-67/4",
                land_type=LandType.COMMERCIAL,
                area_hectares=3.2000,
                state="Maharashtra",
                district="Pune",
                taluka="Maval",
                village="Lonavala",
                ownership_type=OwnershipType.PRIVATE,
                possession_status=PossessionStatus.AWARDED,
                created_by=users["district"].id,
            ),
        ]
        session.add_all(parcels)
        session.flush()

        # ==============================================================
        # PROPOSALS
        # ==============================================================
        proposals = [
            Proposal(
                id=uuid.uuid4(),
                project_id=projects["highway"].id,
                submitted_by=users["agency"].id,
                status=ProposalStatus.APPROVED,
                purpose=(
                    "Land acquisition for 6-lane expressway expansion between "
                    "Talegaon and Dehu Road sections. Environmental clearance "
                    "obtained. Social Impact Assessment completed."
                ),
                urgency=Urgency.NORMAL,
                remarks="SIA report satisfactory. All clearances verified.",
                submitted_at=now - timedelta(days=45),
                reviewed_by=users["state"].id,
                reviewed_at=now - timedelta(days=15),
                created_by=users["agency"].id,
            ),
            Proposal(
                id=uuid.uuid4(),
                project_id=projects["dam"].id,
                submitted_by=users["agency"].id,
                status=ProposalStatus.UNDER_SCRUTINY,
                purpose=(
                    "Acquisition of agricultural and community land for Krishna "
                    "River Dam reservoir area. Estimated 150 hectares required."
                ),
                urgency=Urgency.URGENT,
                remarks=None,
                submitted_at=now - timedelta(days=10),
                reviewed_by=None,
                reviewed_at=None,
                created_by=users["agency"].id,
            ),
            Proposal(
                id=uuid.uuid4(),
                project_id=projects["housing"].id,
                submitted_by=users["agency"].id,
                status=ProposalStatus.DRAFT,
                purpose=(
                    "Acquisition of government wasteland for PMAY affordable "
                    "housing scheme in Wagholi, Pune."
                ),
                urgency=Urgency.NORMAL,
                remarks=None,
                submitted_at=None,  # Still in draft
                reviewed_by=None,
                reviewed_at=None,
                created_by=users["agency"].id,
            ),
        ]
        session.add_all(proposals)
        session.flush()

        # ==============================================================
        # NOTIFICATIONS
        # ==============================================================
        notifications = [
            Notification(
                id=uuid.uuid4(),
                proposal_id=proposals[0].id,
                notice_type=NoticeType.PRELIMINARY_NOTIFICATION,
                title="Preliminary Notification — Mumbai-Pune Expressway Expansion",
                description=(
                    "Notice under Section 11 of LARR Act 2013 for proposed "
                    "land acquisition in Talegaon and Dehu Road villages."
                ),
                document_url=None,  # Supabase Storage URL added in Module 5
                issued_at=now - timedelta(days=40),
                expires_at=now - timedelta(days=10),
                issued_by=users["district"].id,
                created_by=users["district"].id,
            ),
            Notification(
                id=uuid.uuid4(),
                proposal_id=proposals[0].id,
                notice_type=NoticeType.DECLARATION,
                title="Declaration — Mumbai-Pune Expressway Expansion",
                description="Declaration under Section 19 of LARR Act 2013.",
                document_url=None,
                issued_at=now - timedelta(days=5),
                expires_at=None,
                issued_by=users["district"].id,
                created_by=users["district"].id,
            ),
        ]
        session.add_all(notifications)
        session.flush()

        # ==============================================================
        # AWARDS
        # ==============================================================
        awards = [
            Award(
                id=uuid.uuid4(),
                parcel_id=parcels[0].id,
                declared_amount=15000000.00,  # ₹1.5 crore total
                market_value=7500000.00,      # ₹75 lakh market value
                solatium_amount=7500000.00,   # 100% solatium per Section 30
                declared_at=now - timedelta(days=3),
                declared_by=users["district"].id,
                created_by=users["district"].id,
            ),
            Award(
                id=uuid.uuid4(),
                parcel_id=parcels[4].id,
                declared_amount=45000000.00,  # ₹4.5 crore (commercial land)
                market_value=22500000.00,
                solatium_amount=22500000.00,
                declared_at=now - timedelta(days=20),
                declared_by=users["district"].id,
                created_by=users["district"].id,
            ),
        ]
        session.add_all(awards)
        session.flush()

        # ==============================================================
        # COMPENSATIONS
        # ==============================================================
        compensations = [
            Compensation(
                id=uuid.uuid4(),
                award_id=awards[0].id,
                beneficiary_name="Ramesh Jadhav",
                beneficiary_account="SBI-XXXXX1234",
                disbursed_amount=15000000.00,
                disbursed_at=None,  # Pending disbursement
                payment_reference=None,
                status=CompensationStatus.PENDING,
                failure_reason=None,
                created_by=users["district"].id,
            ),
            Compensation(
                id=uuid.uuid4(),
                award_id=awards[1].id,
                beneficiary_name="Kavita Deshmukh",
                beneficiary_account="BOB-XXXXX5678",
                disbursed_amount=45000000.00,
                disbursed_at=now - timedelta(days=10),
                payment_reference="NEFT-REF-20260824-001",
                status=CompensationStatus.DISBURSED,
                failure_reason=None,
                created_by=users["district"].id,
            ),
        ]
        session.add_all(compensations)
        session.flush()

        # ==============================================================
        # FAMILIES (R&R tracking)
        # ==============================================================
        families = [
            Family(
                id=uuid.uuid4(),
                parcel_id=parcels[0].id,
                head_of_household="Ramesh Jadhav",
                family_size=5,
                annual_income=180000.00,
                r_and_r_status=RAndRStatus.SURVEY_COMPLETED,
                resettlement_details={
                    "current_address": "Village Talegaon, Taluka Maval, Dist. Pune",
                    "proposed_resettlement": "R&R Colony, Sector 12, Talegaon",
                    "allotment_number": None,
                },
                alternative_land_provided=False,
                employment_provided=False,
                created_by=users["district"].id,
            ),
            Family(
                id=uuid.uuid4(),
                parcel_id=parcels[4].id,
                head_of_household="Kavita Deshmukh",
                family_size=3,
                annual_income=420000.00,
                r_and_r_status=RAndRStatus.RESETTLED,
                resettlement_details={
                    "current_address": "Shop 5, Market Road, Lonavala",
                    "new_address": "Shop 12, New Market Complex, Lonavala",
                    "allotment_number": "NMC-L-012",
                    "relocation_date": "2026-08-20",
                },
                alternative_land_provided=True,
                employment_provided=False,
                created_by=users["district"].id,
            ),
            Family(
                id=uuid.uuid4(),
                parcel_id=parcels[3].id,
                head_of_household="Basavaraj Patil",
                family_size=7,
                annual_income=120000.00,
                r_and_r_status=RAndRStatus.IDENTIFIED,
                resettlement_details=None,
                alternative_land_provided=False,
                employment_provided=False,
                created_by=users["district"].id,
            ),
        ]
        session.add_all(families)

        # --- Commit all seed data ---
        session.commit()

        print("✓ Seed data inserted successfully:")
        print(f"  • Users:         {len(users)}")
        print(f"  • Projects:      {len(projects)}")
        print(f"  • Land Parcels:  {len(parcels)}")
        print(f"  • Proposals:     {len(proposals)}")
        print(f"  • Notifications: {len(notifications)}")
        print(f"  • Awards:        {len(awards)}")
        print(f"  • Compensations: {len(compensations)}")
        print(f"  • Families:      {len(families)}")


if __name__ == "__main__":
    seed()
