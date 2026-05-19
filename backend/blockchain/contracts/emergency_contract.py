"""
Emergency Response Audit Smart Contract
========================================
Creates immutable audit trails for emergency blood requests.

Functions:
- log_emergency_creation()   → records emergency declaration on-chain
- log_emergency_acceptance() → records donor acceptance on-chain
- log_emergency_closure()    → records emergency resolution on-chain
- get_emergency_audit()      → returns full audit trail
"""

from backend.blockchain.chain import mine_block
from backend.blockchain.utils.hash_utils import generate_secure_hash
from backend.database.db import get_db, utc_now
from backend.utils.security import object_id, serialize_document


def log_emergency_creation(emergency_id: str, hospital_id: str, blood_group: str, urgency: str) -> dict:
    """Record an emergency declaration as an immutable audit event."""
    db = get_db()

    event_data = {
        "event_type": "emergency_created",
        "emergency_id": str(emergency_id),
        "hospital_id": str(hospital_id),
        "blood_group": blood_group,
        "urgency_level": urgency,
    }
    secure_hash = generate_secure_hash(event_data)

    block_result = mine_block({
        "event_type": "emergency_created",
        "reference_id": str(emergency_id),
        "secure_hash": secure_hash,
        "initiated_by": str(hospital_id),
    })

    # Blockchain log
    db["blockchain_logs"].insert_one({
        "event_type": "emergency_created",
        "reference_id": object_id(emergency_id),
        "secure_hash": secure_hash,
        "verified_by": object_id(hospital_id),
        "verification_status": "active",
        "blockchain_tx_id": block_result["block_hash"],
        "block_index": block_result["block_index"],
        "created_at": utc_now(),
    })

    # Audit trail
    db["audit_trails"].insert_one({
        "event_name": "emergency_created",
        "event_description": f"Emergency for {blood_group} declared with {urgency} urgency",
        "initiated_by": object_id(hospital_id),
        "initiator_role": "hospital",
        "reference_id": object_id(emergency_id),
        "secure_hash": secure_hash,
        "block_hash": block_result["block_hash"],
        "created_at": utc_now(),
    })

    return {"recorded": True, "secure_hash": secure_hash, "block_hash": block_result["block_hash"]}


def log_emergency_acceptance(emergency_id: str, donor_id: str) -> dict:
    """Record a donor's acceptance of an emergency on-chain."""
    db = get_db()

    event_data = {
        "event_type": "emergency_accepted",
        "emergency_id": str(emergency_id),
        "donor_id": str(donor_id),
    }
    secure_hash = generate_secure_hash(event_data)

    block_result = mine_block({
        "event_type": "emergency_accepted",
        "reference_id": str(emergency_id),
        "secure_hash": secure_hash,
        "accepted_by": str(donor_id),
    })

    db["blockchain_logs"].insert_one({
        "event_type": "emergency_accepted",
        "reference_id": object_id(emergency_id),
        "secure_hash": secure_hash,
        "verified_by": object_id(donor_id),
        "verification_status": "accepted",
        "blockchain_tx_id": block_result["block_hash"],
        "block_index": block_result["block_index"],
        "created_at": utc_now(),
    })

    db["audit_trails"].insert_one({
        "event_name": "emergency_accepted",
        "event_description": f"Donor accepted emergency request",
        "initiated_by": object_id(donor_id),
        "initiator_role": "donor",
        "reference_id": object_id(emergency_id),
        "secure_hash": secure_hash,
        "block_hash": block_result["block_hash"],
        "created_at": utc_now(),
    })

    return {"recorded": True, "secure_hash": secure_hash, "block_hash": block_result["block_hash"]}


def log_emergency_closure(emergency_id: str, closed_by: str, closer_role: str = "admin") -> dict:
    """Record an emergency closure as an immutable event."""
    db = get_db()

    event_data = {
        "event_type": "emergency_closed",
        "emergency_id": str(emergency_id),
        "closed_by": str(closed_by),
    }
    secure_hash = generate_secure_hash(event_data)

    block_result = mine_block({
        "event_type": "emergency_closed",
        "reference_id": str(emergency_id),
        "secure_hash": secure_hash,
        "closed_by": str(closed_by),
    })

    db["blockchain_logs"].insert_one({
        "event_type": "emergency_closed",
        "reference_id": object_id(emergency_id),
        "secure_hash": secure_hash,
        "verified_by": object_id(closed_by),
        "verification_status": "closed",
        "blockchain_tx_id": block_result["block_hash"],
        "block_index": block_result["block_index"],
        "created_at": utc_now(),
    })

    db["audit_trails"].insert_one({
        "event_name": "emergency_closed",
        "event_description": f"Emergency request closed",
        "initiated_by": object_id(closed_by),
        "initiator_role": closer_role,
        "reference_id": object_id(emergency_id),
        "secure_hash": secure_hash,
        "block_hash": block_result["block_hash"],
        "created_at": utc_now(),
    })

    return {"recorded": True, "secure_hash": secure_hash, "block_hash": block_result["block_hash"]}


def get_emergency_audit(emergency_id: str) -> dict:
    """Return the full immutable audit trail for an emergency."""
    db = get_db()
    trails = list(db["audit_trails"].find({"reference_id": object_id(emergency_id)}).sort("created_at", 1))

    return {
        "emergency_id": str(emergency_id),
        "total_events": len(trails),
        "audit_trail": [
            {
                "event": t.get("event_name"),
                "description": t.get("event_description"),
                "role": t.get("initiator_role"),
                "secure_hash": t.get("secure_hash"),
                "block_hash": t.get("block_hash"),
                "timestamp": str(t.get("created_at")),
            }
            for t in trails
        ],
    }
