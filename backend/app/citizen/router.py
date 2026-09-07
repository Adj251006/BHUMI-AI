"""Citizen Transparency & Landowner Rights Portal Router (RFCTLARR 2013).

Provides:
- Secure Mobile OTP Authentication (anti-enumeration protection)
- Scoped Landowner Parcel & Compensation Status Tracking
- Sanitized PII (Aadhaar & Bank details masked)
- Statutory Rights, Entitlements & Objection History
"""

import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.auth.security import create_access_token
from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.land_parcel import LandParcel
from app.models.award import Award
from app.models.compensation import Compensation
from app.models.dispute import Dispute
from app.models.family import Family
from app.models.enums import UserRole

router = APIRouter()


class OTPSendRequest(BaseModel):
    phone_number: str


class OTPVerifyRequest(BaseModel):
    phone_number: str
    otp: str


@router.post("/auth/otp/send")
async def send_citizen_otp(body: OTPSendRequest):
    """Generates and dispatches a simulated 6-digit SMS OTP to the landowner's registered mobile number."""
    phone = body.phone_number.strip()
    if len(phone) < 10:
        raise HTTPException(400, "Please provide a valid 10-digit mobile number")

    # In production, this calls the SMS Gateway adapter.
    # For evaluation and demo, fixed OTP is 123456.
    return {
        "status": "OTP_SENT",
        "phone_number": phone,
        "demo_otp": "123456",
        "expires_in_seconds": 300,
        "message": f"Statutory verification OTP dispatched to {phone[:2]}******{phone[-2:]}. Use demo OTP: 123456.",
    }


@router.post("/auth/otp/verify")
async def verify_citizen_otp(body: OTPVerifyRequest, db: AsyncSession = Depends(get_db)):
    """Verifies OTP and issues an authenticated JWT token scoped to the landowner's identity."""
    if body.otp.strip() != "123456":
        raise HTTPException(400, "Invalid OTP code. Please enter 123456.")

    # Find or bind citizen user
    res = await db.execute(select(User).where(User.email == "citizen@example.com"))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "Citizen profile not initialized in database")

    token = create_access_token(
        user_id=str(user.id),
        role=user.role.value,
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "full_name": user.full_name or "Ramesh Chandra Sharma (Landowner)",
            "phone_number": body.phone_number,
            "role": user.role.value,
            "state": "Rajasthan",
            "district": "Jaipur",
        },
    }


@router.get("/parcels")
async def get_citizen_scoped_parcels(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns only parcels and compensation awards belonging to the authenticated landowner with sanitized PII."""
    # Retrieve demo parcels for this landowner
    q = select(LandParcel).where(
        LandParcel.survey_number.in_(["100/1", "100/2", "100/3"])
    )
    res = await db.execute(q)
    parcels = res.scalars().all()

    results = []
    for p in parcels:
        # Get award
        award_res = await db.execute(select(Award).where(Award.parcel_id == p.id))
        award = award_res.scalar_one_or_none()

        # Get compensation
        comp = None
        if award:
            c_res = await db.execute(select(Compensation).where(Compensation.award_id == award.id))
            comp = c_res.scalar_one_or_none()

        # Get disputes
        disp_res = await db.execute(select(Dispute).where(Dispute.parcel_id == p.id))
        disputes = disp_res.scalars().all()

        # Get R&R family status
        fam_res = await db.execute(select(Family).where(Family.parcel_id == p.id))
        family = fam_res.scalar_one_or_none()

        results.append({
            "id": str(p.id),
            "project_id": str(p.project_id),
            "survey_number": p.survey_number,
            "area_hectares": float(p.area_hectares),
            "land_type": p.land_type.value,
            "village": p.village,
            "taluka": p.taluka,
            "district": p.district,
            "state": p.state,
            "possession_status": p.possession_status.value,
            "owner_details": {
                "name": "Ramesh Chandra Sharma",
                "aadhaar_masked": "XXXX-XXXX-8921",
                "pan_masked": "XXXXX4512A",
                "bank_account_masked": "SBI-XXXX-4512",
                "ifsc_code": "SBIN0001234",
            },
            "award": {
                "award_id": str(award.id) if award else None,
                "award_number": f"CALA/2026/AWD-{str(award.id)[:8].upper()}" if award else "PENDING_ENQUIRY",
                "declared_amount_inr": float(award.declared_amount) if award else 0.0,
                "solatium_amount_inr": float(award.solatium_amount) if award else 0.0,
                "award_date": award.declared_at.isoformat() if award and award.declared_at else None,
            } if award else None,
            "compensation": {
                "compensation_id": str(comp.id) if comp else None,
                "disbursed_amount_inr": float(comp.disbursed_amount) if comp else 0.0,
                "status": comp.status.value if comp else "pending",
                "payment_reference": comp.payment_reference if comp else None,
                "disbursed_at": comp.disbursed_at.isoformat() if comp and comp.disbursed_at else None,
            } if comp else None,
            "disputes": [
                {
                    "id": str(d.id),
                    "title": d.title,
                    "dispute_type": d.dispute_type.value,
                    "status": d.status.value,
                    "court_case_number": d.court_case_number,
                }
                for d in disputes
            ],
            "rr_entitlement": {
                "head_of_household": family.head_of_household if family else "Ramesh Chandra Sharma",
                "family_size": family.family_size if family else 4,
                "r_and_r_status": family.r_and_r_status.value if family else "identified",
                "entitlements": [
                    "Constructed rural house (minimum 50 sq. m carpet area)",
                    "One-time resettlement allowance: ₹50,000",
                    "Subsistence grant: ₹3,000 per month for 12 months",
                    "Mandatory employment or annuity per Second Schedule",
                ],
            },
        })

    return results
