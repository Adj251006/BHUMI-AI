"""Statutory RFCTLARR (2013) Workflow State Machine Engine.

Enforces statutory transitions, statutory SLA limits, required statutory
documents, and role authorization under the Right to Fair Compensation
and Transparency in Land Acquisition, Rehabilitation and Resettlement Act, 2013.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
from app.models.enums import UserRole, WorkflowStage


@dataclass(frozen=True)
class StatutoryStageRule:
    stage: str
    name: str
    section_ref: str
    allowed_next_stages: List[str]
    statutory_time_limit_days: Optional[int]
    required_document_types: List[str]
    authorized_roles: List[str]
    description: str


STATUTORY_WORKFLOW_RULES: Dict[str, StatutoryStageRule] = {
    "proposal": StatutoryStageRule(
        stage="proposal",
        name="Project Proposal Submission",
        section_ref="Section 3 / Administrative Requisition",
        allowed_next_stages=["preliminary_survey"],
        statutory_time_limit_days=30,
        required_document_types=["project_proposal", "administrative_approval"],
        authorized_roles=["project_agency", "state_govt", "central_ministry"],
        description="Initial acquisition requisition submitted by the Requiring Body.",
    ),
    "preliminary_survey": StatutoryStageRule(
        stage="preliminary_survey",
        name="Preliminary Cadastral Survey",
        section_ref="Section 12 / Preliminary Survey",
        allowed_next_stages=["section_4_sia", "proposal"],
        statutory_time_limit_days=60,
        required_document_types=["cadastral_map", "survey_report"],
        authorized_roles=["district_authority", "state_govt"],
        description="On-ground cadastral surveying, land classification, and GPS boundary demarcations.",
    ),
    "section_4_sia": StatutoryStageRule(
        stage="section_4_sia",
        name="Social Impact Assessment (SIA)",
        section_ref="Section 4 to Section 9 (Chapter II)",
        allowed_next_stages=["section_11_notification", "proposal"],
        statutory_time_limit_days=180,
        required_document_types=["sia_report", "expert_group_appraisal"],
        authorized_roles=["district_authority", "state_govt"],
        description="Consultation with Gram Sabha, appraisal by independent multidisciplinary Expert Group, and consent assessment (70% for PPP, 80% for Private).",
    ),
    "section_11_notification": StatutoryStageRule(
        stage="section_11_notification",
        name="Section 11 Preliminary Notification",
        section_ref="Section 11(1) Gazette Publication",
        allowed_next_stages=["section_15_hearing"],
        statutory_time_limit_days=365,
        required_document_types=["section_11_gazette_notice"],
        authorized_roles=["district_authority", "state_govt"],
        description="Publication in Official Gazette, two local newspapers, and panchayat/collectorate offices.",
    ),
    "section_15_hearing": StatutoryStageRule(
        stage="section_15_hearing",
        name="Section 15 Hearing of Objections",
        section_ref="Section 15(1) - 60-Day Hearing Limit",
        allowed_next_stages=["section_19_declaration", "section_11_notification"],
        statutory_time_limit_days=60,
        required_document_types=["objection_hearing_report"],
        authorized_roles=["district_authority"],
        description="Any person interested can raise objections within 60 days on area, suitability, or public purpose.",
    ),
    "section_19_declaration": StatutoryStageRule(
        stage="section_19_declaration",
        name="Section 19 Declaration of Acquisition",
        section_ref="Section 19(1) Final Declaration",
        allowed_next_stages=["section_21_notice"],
        statutory_time_limit_days=365,
        required_document_types=["section_19_declaration_gazette", "rr_summary"],
        authorized_roles=["state_govt", "central_ministry", "district_authority"],
        description="Must be published within 12 months from Section 11 notice. Lapses if not published within statutory window.",
    ),
    "section_21_notice": StatutoryStageRule(
        stage="section_21_notice",
        name="Section 21 Public Notice to Interested Persons",
        section_ref="Section 21 - Claims for Compensation",
        allowed_next_stages=["section_23_award"],
        statutory_time_limit_days=60,
        required_document_types=["section_21_notice_copies"],
        authorized_roles=["district_authority"],
        description="Public notice requiring all landowners and interested persons to appear and claim compensation.",
    ),
    "section_23_award": StatutoryStageRule(
        stage="section_23_award",
        name="Section 23 Enquiry & Collector's Award",
        section_ref="Sections 23, 26-30 (First Schedule)",
        allowed_next_stages=["compensation"],
        statutory_time_limit_days=365,
        required_document_types=["collector_award_order", "solatium_computation_sheet"],
        authorized_roles=["district_authority"],
        description="Formal enquiry and determination of market value + multiplier factor + 100% Solatium + 12% additional interest.",
    ),
    "compensation": StatutoryStageRule(
        stage="compensation",
        name="Compensation Disbursement (DBT)",
        section_ref="Section 77 / Direct Benefit Transfer",
        allowed_next_stages=["rehabilitation_resettlement", "possession"],
        statutory_time_limit_days=90,
        required_document_types=["dbt_payment_scroll", "bank_reconciliation_cert"],
        authorized_roles=["district_authority", "state_govt"],
        description="Full payment tendered to landowners via electronic bank transfer prior to physical possession.",
    ),
    "rehabilitation_resettlement": StatutoryStageRule(
        stage="rehabilitation_resettlement",
        name="R&R Infrastructure & Entitlements",
        section_ref="Chapter V / Second & Third Schedules",
        allowed_next_stages=["possession"],
        statutory_time_limit_days=180,
        required_document_types=["rr_allotment_order", "paf_handover_cert"],
        authorized_roles=["district_authority", "state_govt"],
        description="Housing allotments, subsistence allowance, and resettlement amenities provided to Project-Affected Families.",
    ),
    "possession": StatutoryStageRule(
        stage="possession",
        name="Physical Possession of Land",
        section_ref="Section 38 & Section 40",
        allowed_next_stages=["completed"],
        statutory_time_limit_days=30,
        required_document_types=["possession_certificate", "panchnama"],
        authorized_roles=["district_authority"],
        description="Collector takes possession encumbrance-free; land vests absolutely in Government.",
    ),
    "completed": StatutoryStageRule(
        stage="completed",
        name="Project Handover & Land Bank Ingestion",
        section_ref="Post-Acquisition Asset Management",
        allowed_next_stages=[],
        statutory_time_limit_days=None,
        required_document_types=["handover_takeover_note"],
        authorized_roles=["project_agency", "district_authority", "state_govt", "central_ministry"],
        description="Land entered into National Acquired Land Bank with geo-tagged boundary monitoring.",
    ),
}


def validate_stage_transition(
    current_stage: str,
    target_stage: str,
    user_role: str,
) -> Tuple[bool, Optional[str]]:
    """Validates if a transition from current_stage to target_stage is allowed by RFCTLARR rules."""
    rule = STATUTORY_WORKFLOW_RULES.get(current_stage)
    if not rule:
        return False, f"Invalid current workflow stage: '{current_stage}'"

    target_rule = STATUTORY_WORKFLOW_RULES.get(target_stage)
    if not target_rule:
        return False, f"Invalid target workflow stage: '{target_stage}'"

    # Check allowed next stages
    if target_stage not in rule.allowed_next_stages:
        return (
            False,
            f"Statutory violation: Stage transition from '{rule.name}' to '{target_rule.name}' "
            f"is prohibited under RFCTLARR Act (2013). Allowed next stages: {rule.allowed_next_stages}",
        )

    # Check authorized role
    if user_role not in target_rule.authorized_roles and user_role != "central_ministry":
        return (
            False,
            f"Role authorization error: User role '{user_role}' is not empowered to enact transition "
            f"to '{target_rule.name}'. Authorized roles: {target_rule.authorized_roles}",
        )

    return True, None
