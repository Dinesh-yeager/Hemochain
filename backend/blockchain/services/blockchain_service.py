"""
HemoChain Blockchain Service Layer
====================================
Central orchestrator that connects smart contracts with the application layer.
This is the single entry point for all blockchain operations.
"""

from backend.blockchain.chain import get_chain_info, validate_chain, initialize_chain
from backend.blockchain.contracts.donation_contract import (
    generate_qr_data,
    get_donation_verification,
    verify_donation,
)
from backend.blockchain.contracts.emergency_contract import (
    get_emergency_audit,
    log_emergency_acceptance,
    log_emergency_closure,
    log_emergency_creation,
)
from backend.blockchain.contracts.transfer_contract import (
    create_transfer_record,
    get_transfer_chain,
    verify_delivery,
)
from backend.database.db import get_db, utc_now
from backend.utils.security import object_id, serialize_document


# ---------------------------------------------------------------------------
# INITIALIZATION
# ---------------------------------------------------------------------------

def init_blockchain():
    """Initialize the blockchain on application startup."""
    initialize_chain()


# ---------------------------------------------------------------------------
# DONATION VERIFICATION
# ---------------------------------------------------------------------------

def blockchain_verify_donation(donation_id, bloodbank_id, donor_id, blood_group):
    """Full donation verification flow — called by blood bank model."""
    return verify_donation(donation_id, bloodbank_id, donor_id, blood_group)


def blockchain_get_donation_status(donation_id):
    """Get verification status for a specific donation."""
    return get_donation_verification(donation_id)


def blockchain_get_qr_data(donation_id):
    """Get QR-safe verification data."""
    return generate_qr_data(donation_id)


# ---------------------------------------------------------------------------
# TRANSFER VERIFICATION
# ---------------------------------------------------------------------------

def blockchain_log_transfer(transfer_id, source_id, destination_id, blood_group, units):
    """Log a blood transfer initiation on-chain."""
    return create_transfer_record(transfer_id, source_id, destination_id, blood_group, units)


def blockchain_verify_delivery(transfer_id, confirmed_by):
    """Verify delivery of a blood transfer on-chain."""
    return verify_delivery(transfer_id, confirmed_by)


def blockchain_get_transfer_custody(transfer_id):
    """Get chain-of-custody for a transfer."""
    return get_transfer_chain(transfer_id)


# ---------------------------------------------------------------------------
# EMERGENCY AUDIT
# ---------------------------------------------------------------------------

def blockchain_log_emergency(emergency_id, hospital_id, blood_group, urgency):
    """Log emergency creation on-chain."""
    return log_emergency_creation(emergency_id, hospital_id, blood_group, urgency)


def blockchain_log_emergency_accept(emergency_id, donor_id):
    """Log emergency acceptance on-chain."""
    return log_emergency_acceptance(emergency_id, donor_id)


def blockchain_log_emergency_close(emergency_id, closed_by, closer_role="admin"):
    """Log emergency closure on-chain."""
    return log_emergency_closure(emergency_id, closed_by, closer_role)


def blockchain_get_emergency_audit(emergency_id):
    """Get full audit trail for an emergency."""
    return get_emergency_audit(emergency_id)


# ---------------------------------------------------------------------------
# CHAIN MANAGEMENT
# ---------------------------------------------------------------------------

def blockchain_get_chain_info():
    """Get blockchain network status."""
    return get_chain_info()


def blockchain_validate_chain():
    """Validate entire chain integrity."""
    return validate_chain()


# ---------------------------------------------------------------------------
# ADMIN AUDIT QUERIES
# ---------------------------------------------------------------------------

def get_all_blockchain_logs(limit=100):
    """Return all blockchain logs for admin audit panel."""
    db = get_db()
    cursor = db["blockchain_logs"].find().sort("created_at", -1).limit(limit)
    logs = []
    for log in cursor:
        doc = serialize_document(log)
        doc["display"] = {
            "secure_hash": f"✔ {doc.get('secure_hash', 'N/A')[:16]}...",
            "verification_status": "✔ Blockchain Verification Complete",
            "record_type": "✔ Immutable Record",
        }
        logs.append(doc)
    return logs


def get_all_verification_events(limit=100):
    """Return all verification events for audit."""
    cursor = get_db()["verification_events"].find().sort("timestamp", -1).limit(limit)
    return [serialize_document(e) for e in cursor]


def get_all_audit_trails(limit=100):
    """Return all audit trails."""
    cursor = get_db()["audit_trails"].find().sort("created_at", -1).limit(limit)
    return [serialize_document(t) for t in cursor]


def get_all_transfer_chains(limit=50):
    """Return all chain-of-custody records."""
    cursor = get_db()["transfer_chain"].find().sort("created_at", -1).limit(limit)
    return [serialize_document(t) for t in cursor]
