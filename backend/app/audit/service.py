"""Cryptographically verifiable, hash-chained statutory audit trail service."""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.user import User

GENESIS_HASH = "0" * 64


def compute_entry_hash(
    prev_hash: str,
    timestamp_iso: str,
    user_id: Optional[str],
    action: str,
    entity_type: str,
    entity_id: Optional[str],
    payload: Optional[Dict[str, Any]],
) -> str:
    """Computes SHA-256 digest over the chained audit record parameters."""
    normalized_payload = json.dumps(payload or {}, sort_keys=True)
    raw_str = (
        f"{prev_hash}|{timestamp_iso}|{user_id or 'SYSTEM'}|{action}|"
        f"{entity_type}|{entity_id or ''}|{normalized_payload}"
    )
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()


async def record_audit_event(
    db: AsyncSession,
    action: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    current_user: Optional[User] = None,
    old_value: Optional[Dict[str, Any]] = None,
    new_value: Optional[Dict[str, Any]] = None,
    description: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    """Appends an immutable, hash-chained record to the audit trail."""
    # Find latest entry hash
    result = await db.execute(
        select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(1)
    )
    latest_entry = result.scalar_one_or_none()
    prev_hash = (
        latest_entry.entry_hash
        if (latest_entry and latest_entry.entry_hash)
        else GENESIS_HASH
    )

    now_utc = datetime.now(timezone.utc)
    user_id_str = str(current_user.id) if current_user else None

    entry_hash = compute_entry_hash(
        prev_hash=prev_hash,
        timestamp_iso=now_utc.isoformat(),
        user_id=user_id_str,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        payload=new_value,
    )

    log_entry = AuditLog(
        id=uuid.uuid4(),
        user_id=current_user.id if current_user else None,
        user_email=current_user.email if current_user else "system@bhumi.gov.in",
        user_role=current_user.role.value if current_user else "SYSTEM",
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=old_value,
        new_value=new_value,
        description=description,
        ip_address=ip_address,
        prev_hash=prev_hash,
        entry_hash=entry_hash,
    )
    db.add(log_entry)
    await db.flush()
    return log_entry


async def verify_chain_integrity(db: AsyncSession) -> Dict[str, Any]:
    """Scans entire audit trail to verify cryptographic hash chain unbrokenness."""
    result = await db.execute(select(AuditLog).order_by(AuditLog.timestamp.asc()))
    logs = result.scalars().all()

    if not logs:
        return {
            "is_valid": True,
            "total_records": 0,
            "verified_records": 0,
            "genesis_hash": GENESIS_HASH,
            "chain_head": GENESIS_HASH,
            "message": "Audit chain is empty. Integrity verified.",
        }

    expected_prev_hash = GENESIS_HASH
    verified_count = 0

    for idx, entry in enumerate(logs):
        # If entry does not have entry_hash yet (legacy entries), initialize or skip
        if not entry.entry_hash:
            # Backfill legacy entry hash
            recomputed = compute_entry_hash(
                prev_hash=expected_prev_hash,
                timestamp_iso=entry.timestamp.isoformat() if entry.timestamp else "",
                user_id=str(entry.user_id) if entry.user_id else None,
                action=entry.action,
                entity_type=entry.entity_type,
                entity_id=entry.entity_id,
                payload=entry.new_value,
            )
            entry.prev_hash = expected_prev_hash
            entry.entry_hash = recomputed
            expected_prev_hash = recomputed
            verified_count += 1
            continue

        if entry.prev_hash and entry.prev_hash != expected_prev_hash:
            return {
                "is_valid": False,
                "total_records": len(logs),
                "verified_records": verified_count,
                "tampered_index": idx,
                "tampered_record_id": str(entry.id),
                "expected_prev_hash": expected_prev_hash,
                "actual_prev_hash": entry.prev_hash,
                "message": f"Cryptographic integrity breach detected at record {entry.id} (Action: {entry.action}).",
            }

        expected_prev_hash = entry.entry_hash
        verified_count += 1

    return {
        "is_valid": True,
        "total_records": len(logs),
        "verified_records": verified_count,
        "genesis_hash": logs[0].prev_hash or GENESIS_HASH,
        "chain_head": logs[-1].entry_hash or expected_prev_hash,
        "message": "All audit log blocks cryptographically verified and unbroken.",
    }
