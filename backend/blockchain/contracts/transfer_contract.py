"""
Blood Transfer Verification Smart Contract
============================================
Handles chain-of-custody tracking for blood unit movements.

Functions:
- create_transfer_record()   → logs transfer initiation on-chain
- verify_delivery()          → marks delivery as immutable
- get_transfer_chain()       → returns full custody chain
"""

from backend.blockchain.chain import mine_block
from backend.blockchain.utils.hash_utils import generate_transfer_hash, generate_secure_hash
from backend.database.db import get_db, utc_now
from backend.utils.security import object_id, serialize_document


def create_transfer_record(transfer_id: str, source_id: str, destination_id: str, blood_group: str, units: int) -> dict:
    """
    Log a blood transfer initiation on the private blockchain.
    Creates an immutable chain-of-custody record.
    """
    db = get_db()

    secure_hash = generate_transfer_hash(source_id, destination_id, blood_group, units)

    block_data = {
        "event_type": "transfer_initiated",
        "reference_id": str(transfer_id),
        "source": str(source_id),
        "destination": str(destination_id),
        "secure_hash": secure_hash,
    }
    block_result = mine_block(block_data)

    # Store in blockchain_logs
    db["blockchain_logs"].insert_one({
        "event_type": "transfer_initiated",
        "reference_id": object_id(transfer_id),
        "secure_hash": secure_hash,
        "verified_by": object_id(source_id),
        "verification_status": "initiated",
        "blockchain_tx_id": block_result["block_hash"],
        "block_index": block_result["block_index"],
        "created_at": utc_now(),
    })

    # Store in transfer_chain for custody tracking
    db["transfer_chain"].insert_one({
        "blood_unit_id": object_id(transfer_id),
        "source": object_id(source_id),
        "destination": object_id(destination_id),
        "blood_group": blood_group,
        "units": units,
        "transfer_status": "initiated",
        "secure_hash": secure_hash,
        "blockchain_tx_id": block_result["block_hash"],
        "block_index": block_result["block_index"],
        "created_at": utc_now(),
    })

    # Store verification event
    db["verification_events"].insert_one({
        "entity_type": "transfer",
        "entity_id": object_id(transfer_id),
        "action_type": "initiated",
        "performed_by": object_id(source_id),
        "performer_role": "bloodbank",
        "secure_hash": secure_hash,
        "block_hash": block_result["block_hash"],
        "timestamp": utc_now(),
    })

    return {
        "recorded": True,
        "secure_hash": secure_hash,
        "block_hash": block_result["block_hash"],
        "block_index": block_result["block_index"],
    }


def verify_delivery(transfer_id: str, confirmed_by: str) -> dict:
    """Mark a blood delivery as immutably verified on-chain."""
    db = get_db()

    delivery_data = {
        "event_type": "transfer_delivered",
        "transfer_id": str(transfer_id),
        "confirmed_by": str(confirmed_by),
    }
    secure_hash = generate_secure_hash(delivery_data)

    block_data = {
        "event_type": "transfer_delivered",
        "reference_id": str(transfer_id),
        "secure_hash": secure_hash,
        "confirmed_by": str(confirmed_by),
    }
    block_result = mine_block(block_data)

    # Update transfer_chain
    db["transfer_chain"].update_one(
        {"blood_unit_id": object_id(transfer_id)},
        {"$set": {
            "transfer_status": "delivered",
            "delivery_hash": secure_hash,
            "delivery_block_hash": block_result["block_hash"],
            "delivered_at": utc_now(),
        }}
    )

    # Log delivery verification
    db["blockchain_logs"].insert_one({
        "event_type": "transfer_delivered",
        "reference_id": object_id(transfer_id),
        "secure_hash": secure_hash,
        "verified_by": object_id(confirmed_by),
        "verification_status": "delivered",
        "blockchain_tx_id": block_result["block_hash"],
        "block_index": block_result["block_index"],
        "created_at": utc_now(),
    })

    db["verification_events"].insert_one({
        "entity_type": "transfer",
        "entity_id": object_id(transfer_id),
        "action_type": "delivered",
        "performed_by": object_id(confirmed_by),
        "performer_role": "hospital",
        "secure_hash": secure_hash,
        "block_hash": block_result["block_hash"],
        "timestamp": utc_now(),
    })

    return {
        "verified": True,
        "secure_hash": secure_hash,
        "block_hash": block_result["block_hash"],
        "block_index": block_result["block_index"],
    }


def get_transfer_chain(transfer_id: str) -> dict:
    """Return the full chain-of-custody for a blood transfer."""
    db = get_db()
    record = db["transfer_chain"].find_one({"blood_unit_id": object_id(transfer_id)})
    if not record:
        return None

    # Enrich with facility names
    source = db["bloodbanks"].find_one({"_id": record.get("source")})
    destination = db["hospitals"].find_one({"_id": record.get("destination")})

    return {
        "transfer_id": str(transfer_id),
        "source_name": source.get("bloodbank_name") if source else "Unknown",
        "destination_name": destination.get("hospital_name") if destination else "Unknown",
        "blood_group": record.get("blood_group"),
        "units": record.get("units"),
        "transfer_status": record.get("transfer_status"),
        "initiation_hash": record.get("secure_hash"),
        "delivery_hash": record.get("delivery_hash"),
        "created_at": str(record.get("created_at")),
        "delivered_at": str(record.get("delivered_at")) if record.get("delivered_at") else None,
    }
