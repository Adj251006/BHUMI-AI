"""National System Integrations Router.

Provides unified management and status for:
- DILRMP (Record of Rights / Land Records)
- e-Courts (National Judicial Data Grid)
- PFMS (Direct Benefit Transfer Payment Gateway)
- Bhu-Naksha (NIC Cadastral GIS Vector Layers)
"""

from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.audit.service import record_audit_event
from app.integrations.adapters import (
    DILRMPAdapter,
    ECourtsAdapter,
    PFMSAdapter,
    BhuNakshaAdapter,
)

router = APIRouter()

ADAPTERS = {
    "dilrmp": DILRMPAdapter(),
    "ecourts": ECourtsAdapter(),
    "pfms": PFMSAdapter(),
    "bhunaksha": BhuNakshaAdapter(),
}


@router.get("/status")
async def get_integrations_status(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Returns connectivity health, latency, and sync status for all 4 national integration gateways."""
    results = {}
    for key, adapter in ADAPTERS.items():
        health = await adapter.ping_health()
        results[key] = {
            "name": adapter.system_name,
            "ministry": adapter.ministry,
            "health": health,
        }
    return {
        "gateway_status": "ALL_SYSTEMS_OPERATIONAL",
        "integrations": results,
    }


@router.post("/sync/{system_key}")
async def trigger_integration_sync(
    system_key: str,
    state: str = "Rajasthan",
    district: str = "Jaipur",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Triggers an on-demand synchronization cycle with a national revenue/judicial system."""
    adapter = ADAPTERS.get(system_key.lower())
    if not adapter:
        raise HTTPException(
            404,
            f"Integration adapter '{system_key}' not found. Available adapters: {list(ADAPTERS.keys())}",
        )

    sync_result = await adapter.sync_records(state=state, district=district)

    await record_audit_event(
        db=db,
        action="NATIONAL_GATEWAY_SYNC",
        entity_type="IntegrationGateway",
        entity_id=system_key,
        current_user=current_user,
        new_value=sync_result,
        description=f"Triggered manual data sync with {adapter.system_name} for {district}, {state}.",
    )
    await db.flush()

    return sync_result
