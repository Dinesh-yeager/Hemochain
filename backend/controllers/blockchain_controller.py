from flask import request
from flask_jwt_extended import get_jwt, get_jwt_identity

from backend.blockchain.services.blockchain_service import (
    blockchain_get_chain_info,
    blockchain_get_donation_status,
    blockchain_get_emergency_audit,
    blockchain_get_qr_data,
    blockchain_get_transfer_custody,
    blockchain_validate_chain,
    blockchain_verify_delivery,
    blockchain_verify_donation,
    get_all_audit_trails,
    get_all_blockchain_logs,
    get_all_transfer_chains,
    get_all_verification_events,
)
from backend.utils.responses import error_response, success_response
from backend.utils.security import sanitize_document


# ---------------------------------------------------------------------------
# PUBLIC: QR VERIFICATION (no auth required)
# ---------------------------------------------------------------------------

def public_verify(record_id):
    """Public QR scan endpoint — no sensitive data exposed."""
    data = blockchain_get_qr_data(record_id)
    if not data:
        return error_response("Record not found", 404)
    return success_response("Verification retrieved", data=data)


# ---------------------------------------------------------------------------
# DONATION VERIFICATION (bloodbank role)
# ---------------------------------------------------------------------------

def verify_donation():
    payload = sanitize_document(request.get_json(silent=True) or {})
    donation_id = payload.get("donation_id")
    donor_id = payload.get("donor_id")
    blood_group = payload.get("blood_group")
    bloodbank_id = get_jwt_identity()

    if not all([donation_id, donor_id, blood_group]):
        return error_response("donation_id, donor_id, and blood_group are required", 422)

    result = blockchain_verify_donation(donation_id, bloodbank_id, donor_id, blood_group)
    return success_response("Donation verified on blockchain", data=result)


# ---------------------------------------------------------------------------
# VERIFICATION STATUS (role-based)
# ---------------------------------------------------------------------------

def get_verification_status(record_id):
    """Get blockchain verification status for a donation."""
    data = blockchain_get_donation_status(record_id)
    if not data:
        return error_response("Record not found", 404)
    return success_response("Verification status retrieved", data=data)


# ---------------------------------------------------------------------------
# TRANSFER VERIFICATION
# ---------------------------------------------------------------------------

def verify_transfer_delivery(transfer_id):
    confirmed_by = get_jwt_identity()
    result = blockchain_verify_delivery(transfer_id, confirmed_by)
    return success_response("Delivery verified on blockchain", data=result)


def get_transfer_custody(transfer_id):
    data = blockchain_get_transfer_custody(transfer_id)
    if not data:
        return error_response("Transfer record not found", 404)
    return success_response("Chain of custody retrieved", data=data)


# ---------------------------------------------------------------------------
# EMERGENCY AUDIT
# ---------------------------------------------------------------------------

def get_emergency_audit_trail(emergency_id):
    data = blockchain_get_emergency_audit(emergency_id)
    return success_response("Emergency audit trail retrieved", data=data)


# ---------------------------------------------------------------------------
# CHAIN MANAGEMENT (admin only)
# ---------------------------------------------------------------------------

def get_chain_info():
    info = blockchain_get_chain_info()
    return success_response("Blockchain info retrieved", data=info)


def validate_chain():
    result = blockchain_validate_chain()
    return success_response("Chain validation complete", data=result)


# ---------------------------------------------------------------------------
# ADMIN AUDIT PANEL
# ---------------------------------------------------------------------------

def get_blockchain_logs():
    logs = get_all_blockchain_logs()
    return success_response("Blockchain logs retrieved", data=logs)


def get_verification_events():
    events = get_all_verification_events()
    return success_response("Verification events retrieved", data=events)


def get_audit_trails():
    trails = get_all_audit_trails()
    return success_response("Audit trails retrieved", data=trails)


def get_transfer_chains():
    chains = get_all_transfer_chains()
    return success_response("Transfer chains retrieved", data=chains)
