"""Module 3 Verification Script — Proposal Submission & Approval Workflow.

Run from backend directory:
    python -m scripts.test_module3
"""

import asyncio
import os
import sys
import uuid

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
import psycopg2

from app.config import settings
from app.main import app


def get_existing_project_id() -> str:
    """Fetch an existing project ID from the database for testing."""
    conn = psycopg2.connect(
        host="15.165.245.138",
        port=5432,
        database="postgres",
        user="postgres.ffxsuugwobmwjbguglqi",
        password="Aaryan@251006",
        sslmode="require",
    )
    cur = conn.cursor()
    cur.execute("SELECT id FROM projects WHERE deleted_at IS NULL LIMIT 1")
    row = cur.fetchone()
    conn.close()
    if not row:
        raise RuntimeError("No projects found in database. Run seed script first.")
    return str(row[0])


async def run_async_tests():
    print("===========================================================")
    print("  MODULE 3 VERIFICATION — Proposals & Workflow Test Suite")
    print("===========================================================")
    print()

    project_id = get_existing_project_id()
    print(f"✓ Using existing seed project ID: {project_id}")
    print()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:

        # -------------------------------------------------------------
        # Step 0: Authenticate seed users for all 4 roles
        # -------------------------------------------------------------
        print("[0/5] Authenticating seed users for all 4 roles...")

        # Central Ministry
        resp = await client.post("/auth/login", json={"email": "admin@mord.gov.in", "password": "Test@1234"})
        assert resp.status_code == 200, f"Login failed: {resp.text}"
        central_token = resp.json()["access_token"]

        # State Govt
        resp = await client.post("/auth/login", json={"email": "collector@maharashtra.gov.in", "password": "Test@1234"})
        assert resp.status_code == 200
        state_token = resp.json()["access_token"]

        # District Authority
        resp = await client.post("/auth/login", json={"email": "dc@pune.gov.in", "password": "Test@1234"})
        assert resp.status_code == 200
        district_token = resp.json()["access_token"]

        # Project Agency
        resp = await client.post("/auth/login", json={"email": "pm@nhai.gov.in", "password": "Test@1234"})
        assert resp.status_code == 200
        agency_token = resp.json()["access_token"]

        print("  ✓ Authenticated central_ministry, state_govt, district_authority, project_agency")

        # -------------------------------------------------------------
        # Step 1: Proposal Creation & Authorization
        # -------------------------------------------------------------
        print("[1/5] Testing Proposal Creation & Authorization...")

        # 1.1 Project Agency creates DRAFT proposal
        resp = await client.post(
            "/proposals",
            json={
                "project_id": project_id,
                "purpose": "Land acquisition for 4-lane bypass road around Pune highway congestion area.",
                "urgency": "normal",
                "status": "draft",
            },
            headers={"Authorization": f"Bearer {agency_token}"},
        )
        assert resp.status_code == 201, f"Create draft failed: {resp.text}"
        draft_prop = resp.json()
        draft_id = draft_prop["id"]
        assert draft_prop["status"] == "draft"
        assert draft_prop["submitted_at"] is None
        print("  ✓ POST /proposals (Agency creating DRAFT proposal) -> 201 Created")

        # 1.2 Central Ministry creates SUBMITTED proposal
        resp = await client.post(
            "/proposals",
            json={
                "project_id": project_id,
                "purpose": "National priority land acquisition for rail freight corridor connection.",
                "urgency": "urgent",
                "status": "submitted",
            },
            headers={"Authorization": f"Bearer {central_token}"},
        )
        assert resp.status_code == 201
        submitted_prop = resp.json()
        assert submitted_prop["status"] == "submitted"
        assert submitted_prop["submitted_at"] is not None
        print("  ✓ POST /proposals (Central Ministry creating SUBMITTED proposal) -> 201 Created")

        # 1.3 District Authority attempts to create proposal (should be forbidden)
        resp = await client.post(
            "/proposals",
            json={
                "project_id": project_id,
                "purpose": "Unauthorized creation attempt by district collector.",
                "status": "draft",
            },
            headers={"Authorization": f"Bearer {district_token}"},
        )
        assert resp.status_code == 403
        print("  ✓ POST /proposals (District Authority forbidden to create) -> 403 Forbidden")

        # 1.4 Creation with non-existent project_id
        resp = await client.post(
            "/proposals",
            json={
                "project_id": str(uuid.uuid4()),
                "purpose": "Land acquisition for imaginary non-existent project.",
                "status": "draft",
            },
            headers={"Authorization": f"Bearer {agency_token}"},
        )
        assert resp.status_code == 404
        print("  ✓ POST /proposals (Non-existent project) -> 404 Not Found")

        # -------------------------------------------------------------
        # Step 2: Editing Proposal Content
        # -------------------------------------------------------------
        print("[2/5] Testing Proposal Editing (DRAFT / REVISION_REQUESTED state)...")

        # 2.1 Agency creator updates draft proposal
        resp = await client.put(
            f"/proposals/{draft_id}",
            json={
                "purpose": "Updated purpose: Land acquisition for 6-lane bypass road with elevated corridor.",
                "urgency": "urgent",
            },
            headers={"Authorization": f"Bearer {agency_token}"},
        )
        assert resp.status_code == 200
        updated_prop = resp.json()
        assert "6-lane bypass" in updated_prop["purpose"]
        assert updated_prop["urgency"] == "urgent"
        print("  ✓ PUT /proposals/{id} (Creator editing DRAFT proposal) -> 200 OK")

        # -------------------------------------------------------------
        # Step 3: State Machine Workflow & Transitions
        # -------------------------------------------------------------
        print("[3/5] Testing Full State Machine Lifecycle & Transitions...")

        # 3.1 DRAFT -> SUBMITTED (by Agency)
        resp = await client.patch(
            f"/proposals/{draft_id}/status",
            json={"status": "submitted"},
            headers={"Authorization": f"Bearer {agency_token}"},
        )
        assert resp.status_code == 200
        sub_prop = resp.json()
        assert sub_prop["status"] == "submitted"
        assert sub_prop["submitted_at"] is not None
        print("  ✓ PATCH /proposals/{id}/status (draft -> submitted) -> 200 OK")

        # 3.2 Attempt edit on SUBMITTED proposal (should fail)
        resp = await client.put(
            f"/proposals/{draft_id}",
            json={"purpose": "Attempting to edit submitted proposal content."},
            headers={"Authorization": f"Bearer {agency_token}"},
        )
        assert resp.status_code == 400
        print("  ✓ PUT /proposals/{id} (Editing submitted proposal) -> 400 Bad Request")

        # 3.3 SUBMITTED -> UNDER_SCRUTINY (by District Authority)
        resp = await client.patch(
            f"/proposals/{draft_id}/status",
            json={"status": "under_scrutiny"},
            headers={"Authorization": f"Bearer {district_token}"},
        )
        assert resp.status_code == 200
        scrutiny_prop = resp.json()
        assert scrutiny_prop["status"] == "under_scrutiny"
        print("  ✓ PATCH /proposals/{id}/status (submitted -> under_scrutiny by District Authority) -> 200 OK")

        # 3.4 UNDER_SCRUTINY -> REVISION_REQUESTED without remarks (should fail)
        resp = await client.patch(
            f"/proposals/{draft_id}/status",
            json={"status": "revision_requested"},  # Missing remarks
            headers={"Authorization": f"Bearer {district_token}"},
        )
        assert resp.status_code == 400
        assert "Remarks" in resp.json()["detail"] or "remarks" in resp.json()["detail"]
        print("  ✓ PATCH /proposals/{id}/status (revision_requested without remarks) -> 400 Bad Request")

        # 3.5 UNDER_SCRUTINY -> REVISION_REQUESTED with remarks (by District Authority)
        resp = await client.patch(
            f"/proposals/{draft_id}/status",
            json={
                "status": "revision_requested",
                "remarks": "Please attach environmental clearance and detailed SIA survey report.",
            },
            headers={"Authorization": f"Bearer {district_token}"},
        )
        assert resp.status_code == 200
        rev_prop = resp.json()
        assert rev_prop["status"] == "revision_requested"
        assert "SIA survey" in rev_prop["remarks"]
        print("  ✓ PATCH /proposals/{id}/status (under_scrutiny -> revision_requested with remarks) -> 200 OK")

        # 3.6 Edit proposal while in REVISION_REQUESTED (by Agency creator)
        resp = await client.put(
            f"/proposals/{draft_id}",
            json={
                "purpose": "Revised purpose: 6-lane bypass road with full SIA survey and environmental clearance attached.",
            },
            headers={"Authorization": f"Bearer {agency_token}"},
        )
        assert resp.status_code == 200
        assert "SIA survey" in resp.json()["purpose"]
        print("  ✓ PUT /proposals/{id} (Agency editing in REVISION_REQUESTED) -> 200 OK")

        # 3.7 REVISION_REQUESTED -> SUBMITTED (Loop-back by Agency)
        resp = await client.patch(
            f"/proposals/{draft_id}/status",
            json={"status": "submitted"},
            headers={"Authorization": f"Bearer {agency_token}"},
        )
        assert resp.status_code == 200
        resubmitted_prop = resp.json()
        assert resubmitted_prop["status"] == "submitted"
        print("  ✓ PATCH /proposals/{id}/status (revision_requested -> submitted loop-back) -> 200 OK")

        # 3.8 SUBMITTED -> UNDER_SCRUTINY (by State Govt)
        resp = await client.patch(
            f"/proposals/{draft_id}/status",
            json={"status": "under_scrutiny"},
            headers={"Authorization": f"Bearer {state_token}"},
        )
        assert resp.status_code == 200
        print("  ✓ PATCH /proposals/{id}/status (submitted -> under_scrutiny by State Govt) -> 200 OK")

        # 3.9 UNDER_SCRUTINY -> APPROVED (by Central Ministry)
        resp = await client.patch(
            f"/proposals/{draft_id}/status",
            json={
                "status": "approved",
                "remarks": "Approved by Ministry of Rural Development after full scrutiny.",
            },
            headers={"Authorization": f"Bearer {central_token}"},
        )
        assert resp.status_code == 200
        approved_prop = resp.json()
        assert approved_prop["status"] == "approved"
        print("  ✓ PATCH /proposals/{id}/status (under_scrutiny -> approved by Central Ministry) -> 200 OK")

        # 3.10 Attempt transition on APPROVED proposal (terminal state -> should fail)
        resp = await client.patch(
            f"/proposals/{draft_id}/status",
            json={"status": "submitted"},
            headers={"Authorization": f"Bearer {agency_token}"},
        )
        assert resp.status_code == 400
        print("  ✓ PATCH /proposals/{id}/status (Transition from terminal APPROVED state) -> 400 Bad Request")

        # -------------------------------------------------------------
        # Step 4: Withdrawal Transition
        # -------------------------------------------------------------
        print("[4/5] Testing Proposal Withdrawal...")

        # 4.1 Create new draft proposal and withdraw it
        resp = await client.post(
            "/proposals",
            json={
                "project_id": project_id,
                "purpose": "Temporary test proposal to be withdrawn from draft state.",
                "status": "draft",
            },
            headers={"Authorization": f"Bearer {agency_token}"},
        )
        w_draft_id = resp.json()["id"]

        resp = await client.patch(
            f"/proposals/{w_draft_id}/status",
            json={"status": "withdrawn", "remarks": "Project scope changed by agency."},
            headers={"Authorization": f"Bearer {agency_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "withdrawn"
        print("  ✓ PATCH /proposals/{id}/status (draft -> withdrawn) -> 200 OK")

        # -------------------------------------------------------------
        # Step 5: Listing, Scoping, and Filtering
        # -------------------------------------------------------------
        print("[5/5] Testing Proposal Listing & Filtering...")

        # 5.1 List proposals as Central Ministry (sees all)
        resp = await client.get(
            "/proposals",
            headers={"Authorization": f"Bearer {central_token}"},
        )
        assert resp.status_code == 200
        list_data = resp.json()
        assert "items" in list_data
        assert list_data["total"] >= 5
        print(f"  ✓ GET /proposals (Central Ministry total: {list_data['total']}) -> 200 OK")

        # 5.2 Filter by status=approved
        resp = await client.get(
            "/proposals?status=approved",
            headers={"Authorization": f"Bearer {central_token}"},
        )
        assert resp.status_code == 200
        approved_items = resp.json()["items"]
        assert all(item["status"] == "approved" for item in approved_items)
        print(f"  ✓ GET /proposals?status=approved (Matching: {len(approved_items)}) -> 200 OK")

        # 5.3 Filter by project_id
        resp = await client.get(
            f"/proposals?project_id={project_id}",
            headers={"Authorization": f"Bearer {central_token}"},
        )
        assert resp.status_code == 200
        project_items = resp.json()["items"]
        assert all(item["project_id"] == project_id for item in project_items)
        print(f"  ✓ GET /proposals?project_id=... (Matching: {len(project_items)}) -> 200 OK")

        # 5.4 Fetch single proposal details
        resp = await client.get(
            f"/proposals/{draft_id}",
            headers={"Authorization": f"Bearer {central_token}"},
        )
        assert resp.status_code == 200
        single_prop = resp.json()
        assert single_prop["id"] == draft_id
        assert single_prop["project_name"] is not None
        print("  ✓ GET /proposals/{id} (Single proposal with project info) -> 200 OK")

    print()
    print("===========================================================")
    print("  ALL MODULE 3 PROPOSALS & WORKFLOW CHECKS PASSED ✓")
    print("===========================================================")


def main():
    asyncio.run(run_async_tests())


if __name__ == "__main__":
    main()
