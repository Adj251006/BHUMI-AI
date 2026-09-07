"""External Communication Gateway (SMS & Email Dispatcher) for Landowners and Stakeholders."""

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# In-memory simulated outbox for live UI display and verification
NOTIFICATION_OUTBOX: List[Dict[str, Any]] = [
    {
        "id": "sms-001",
        "channel": "SMS",
        "recipient": "+91-98765-43210",
        "recipient_name": "Ramesh Chandra Sharma (Landowner)",
        "message": "Govt of Rajasthan / MoRD: Your Section 11 preliminary land notice for Survey 100/1 has been published. File objections within 60 days. Portal: https://bhumi.gov.in/citizen",
        "status": "DELIVERED",
        "gateway_ref": "SMS-AIRTEL-982143",
        "dispatched_at": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "email-001",
        "channel": "EMAIL",
        "recipient": "jaipur@gov.in",
        "recipient_name": "District Collector, Jaipur",
        "message": "Statutory Alert: Section 19 declaration for Delhi-Jaipur Highway has reached 320 elapsed days. Statutory lapse threshold is 365 days. Immediate review required.",
        "status": "DELIVERED",
        "gateway_ref": "NIC-SMTP-48190",
        "dispatched_at": datetime.now(timezone.utc).isoformat(),
    },
]


def dispatch_sms(recipient_phone: str, message: str, recipient_name: str = "Landowner") -> Dict[str, Any]:
    """Simulates external SMS dispatch via National Telecom Gateway (CDAC/NIC SMS Gateway)."""
    receipt = {
        "id": f"sms-{len(NOTIFICATION_OUTBOX) + 1}",
        "channel": "SMS",
        "recipient": recipient_phone,
        "recipient_name": recipient_name,
        "message": message,
        "status": "DELIVERED",
        "gateway_ref": f"NIC-SMS-{hashlib.md5(message.encode()).hexdigest()[:8].upper()}",
        "dispatched_at": datetime.now(timezone.utc).isoformat(),
    }
    NOTIFICATION_OUTBOX.insert(0, receipt)
    logger.info(f"[SMS GATEWAY] Dispatched to {recipient_phone}: {message[:60]}...")
    return receipt


def dispatch_email(recipient_email: str, subject: str, body: str, recipient_name: str = "Officer") -> Dict[str, Any]:
    """Simulates external government email delivery via NIC Mail Server."""
    receipt = {
        "id": f"email-{len(NOTIFICATION_OUTBOX) + 1}",
        "channel": "EMAIL",
        "recipient": recipient_email,
        "recipient_name": recipient_name,
        "subject": subject,
        "message": body,
        "status": "DELIVERED",
        "gateway_ref": f"NIC-MAIL-{hashlib.md5(body.encode()).hexdigest()[:8].upper()}",
        "dispatched_at": datetime.now(timezone.utc).isoformat(),
    }
    NOTIFICATION_OUTBOX.insert(0, receipt)
    logger.info(f"[EMAIL GATEWAY] Dispatched to {recipient_email}: {subject}")
    return receipt
