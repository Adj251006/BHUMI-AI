"""Initial schema — all tables, enums, indexes, and PostGIS extension.

Creates the complete database schema for the National Land Acquisition
& Management System. Tables are created in foreign-key dependency order
and dropped in reverse order.

Revision ID: 0001
Revises: -
Create Date: 2026-09-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2


# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 0. Enable PostGIS extension (idempotent)
    # ------------------------------------------------------------------
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

    # ------------------------------------------------------------------
    # 1. Create PostgreSQL enum types
    # ------------------------------------------------------------------
    # These are created explicitly so we have full control over naming
    # and can reference them in downgrade().
    user_role = postgresql.ENUM(
        "central_ministry", "state_govt", "district_authority", "project_agency",
        name="user_role", create_type=False,
    )
    project_status = postgresql.ENUM(
        "planning", "active", "completed", "suspended", "cancelled",
        name="project_status", create_type=False,
    )
    land_type = postgresql.ENUM(
        "agricultural", "residential", "commercial", "industrial",
        "forest", "government", "wasteland", "water_body",
        name="land_type", create_type=False,
    )
    ownership_type = postgresql.ENUM(
        "private", "government", "community", "disputed",
        name="ownership_type", create_type=False,
    )
    possession_status = postgresql.ENUM(
        "not_acquired", "notice_issued", "awarded", "possessed",
        name="possession_status", create_type=False,
    )
    proposal_status = postgresql.ENUM(
        "draft", "submitted", "under_scrutiny", "approved",
        "rejected", "revision_requested", "withdrawn",
        name="proposal_status", create_type=False,
    )
    urgency = postgresql.ENUM(
        "normal", "urgent", "suo_motu",
        name="urgency", create_type=False,
    )
    notice_type = postgresql.ENUM(
        "preliminary_notification", "hearing_notice", "declaration",
        "award_notice", "possession_notice",
        name="notice_type", create_type=False,
    )
    compensation_status = postgresql.ENUM(
        "pending", "processing", "disbursed", "failed", "disputed",
        name="compensation_status", create_type=False,
    )
    r_and_r_status = postgresql.ENUM(
        "identified", "survey_completed", "plan_approved",
        "resettled", "monitoring",
        name="r_and_r_status", create_type=False,
    )

    # Create all enum types in the database
    bind = op.get_bind()
    user_role.create(bind, checkfirst=True)
    project_status.create(bind, checkfirst=True)
    land_type.create(bind, checkfirst=True)
    ownership_type.create(bind, checkfirst=True)
    possession_status.create(bind, checkfirst=True)
    proposal_status.create(bind, checkfirst=True)
    urgency.create(bind, checkfirst=True)
    notice_type.create(bind, checkfirst=True)
    compensation_status.create(bind, checkfirst=True)
    r_and_r_status.create(bind, checkfirst=True)

    # ------------------------------------------------------------------
    # 2. users (no FK dependencies — must be created first)
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("district", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_users_email", "users", ["email"])

    # ------------------------------------------------------------------
    # 3. projects (FK → users)
    # ------------------------------------------------------------------
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("ministry", sa.String(255), nullable=False),
        sa.Column("sector", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", project_status, nullable=False,
                  server_default=sa.text("'planning'")),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("district", sa.String(100), nullable=True),
        # Audit columns
        sa.Column("created_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_projects_ministry", "projects", ["ministry"])
    op.create_index("idx_projects_status", "projects", ["status"])
    op.create_index("idx_projects_state", "projects", ["state"])

    # ------------------------------------------------------------------
    # 4. land_parcels (FK → projects, users)
    # ------------------------------------------------------------------
    op.create_table(
        "land_parcels",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        # PostGIS geometry column — MULTIPOLYGON with WGS 84 (SRID 4326)
        sa.Column("geometry", geoalchemy2.Geometry(
            geometry_type="MULTIPOLYGON", srid=4326,
            spatial_index=False,  # We create the GIST index explicitly below
        ), nullable=True),
        sa.Column("survey_number", sa.String(100), nullable=False),
        sa.Column("land_type", land_type, nullable=False),
        sa.Column("area_hectares", sa.Numeric(12, 4), nullable=False),
        sa.Column("state", sa.String(100), nullable=False),
        sa.Column("district", sa.String(100), nullable=False),
        sa.Column("taluka", sa.String(100), nullable=True),
        sa.Column("village", sa.String(100), nullable=True),
        sa.Column("ownership_type", ownership_type, nullable=True),
        sa.Column("possession_status", possession_status, nullable=False,
                  server_default=sa.text("'not_acquired'")),
        # Audit columns
        sa.Column("created_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_parcels_project", "land_parcels", ["project_id"])
    op.create_index("idx_parcels_survey_number", "land_parcels", ["survey_number"])
    op.create_index("idx_parcels_state_district", "land_parcels", ["state", "district"])
    op.create_index("idx_parcels_possession", "land_parcels", ["possession_status"])
    # Spatial GIST index for geo-queries (Module 4)
    op.create_index(
        "idx_parcels_geometry", "land_parcels", ["geometry"],
        postgresql_using="gist",
    )

    # ------------------------------------------------------------------
    # 5. proposals (FK → projects, users)
    # ------------------------------------------------------------------
    op.create_table(
        "proposals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("submitted_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", proposal_status, nullable=False,
                  server_default=sa.text("'draft'")),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("urgency", urgency, nullable=False,
                  server_default=sa.text("'normal'")),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        # Audit columns
        sa.Column("created_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_proposals_project", "proposals", ["project_id"])
    op.create_index("idx_proposals_status", "proposals", ["status"])
    op.create_index("idx_proposals_submitted_by", "proposals", ["submitted_by"])

    # ------------------------------------------------------------------
    # 6. notifications (FK → proposals, users)
    # ------------------------------------------------------------------
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("proposal_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("proposals.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("notice_type", notice_type, nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("document_url", sa.String(1000), nullable=True),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("issued_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        # Audit columns
        sa.Column("created_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_notifications_proposal", "notifications", ["proposal_id"])
    op.create_index("idx_notifications_type", "notifications", ["notice_type"])

    # ------------------------------------------------------------------
    # 7. awards (FK → land_parcels, users)
    # ------------------------------------------------------------------
    op.create_table(
        "awards",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("parcel_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("land_parcels.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("declared_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("market_value", sa.Numeric(15, 2), nullable=True),
        sa.Column("solatium_amount", sa.Numeric(15, 2), nullable=True),
        sa.Column("declared_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("declared_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        # Audit columns
        sa.Column("created_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_awards_parcel", "awards", ["parcel_id"])

    # ------------------------------------------------------------------
    # 8. compensations (FK → awards, users)
    # ------------------------------------------------------------------
    op.create_table(
        "compensations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("award_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("awards.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("beneficiary_name", sa.String(255), nullable=False),
        sa.Column("beneficiary_account", sa.String(50), nullable=True),
        sa.Column("disbursed_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("disbursed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payment_reference", sa.String(100), nullable=True),
        sa.Column("status", compensation_status, nullable=False,
                  server_default=sa.text("'pending'")),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        # Audit columns
        sa.Column("created_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_compensations_award", "compensations", ["award_id"])
    op.create_index("idx_compensations_status", "compensations", ["status"])

    # ------------------------------------------------------------------
    # 9. families (FK → land_parcels, users)
    # ------------------------------------------------------------------
    op.create_table(
        "families",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("parcel_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("land_parcels.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("head_of_household", sa.String(255), nullable=False),
        sa.Column("family_size", sa.Integer(), nullable=True),
        sa.Column("annual_income", sa.Numeric(12, 2), nullable=True),
        sa.Column("r_and_r_status", r_and_r_status, nullable=False,
                  server_default=sa.text("'identified'")),
        sa.Column("resettlement_details", postgresql.JSONB(), nullable=True),
        sa.Column("alternative_land_provided", sa.Boolean(), nullable=False,
                  server_default=sa.text("false")),
        sa.Column("employment_provided", sa.Boolean(), nullable=False,
                  server_default=sa.text("false")),
        # Audit columns
        sa.Column("created_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_families_parcel", "families", ["parcel_id"])
    op.create_index("idx_families_rnr_status", "families", ["r_and_r_status"])


def downgrade() -> None:
    """Drop all tables in reverse dependency order, then drop enum types."""

    # --- Tables (reverse order) ---
    op.drop_table("families")
    op.drop_table("compensations")
    op.drop_table("awards")
    op.drop_table("notifications")
    op.drop_table("proposals")
    op.drop_table("land_parcels")
    op.drop_table("projects")
    op.drop_table("users")

    # --- Enum types ---
    bind = op.get_bind()
    for enum_name in [
        "r_and_r_status", "compensation_status", "notice_type",
        "urgency", "proposal_status", "possession_status",
        "ownership_type", "land_type", "project_status", "user_role",
    ]:
        postgresql.ENUM(name=enum_name, create_type=False).drop(bind, checkfirst=True)

    # Note: We don't drop the postgis extension because other schemas
    # or Supabase internals may depend on it.
