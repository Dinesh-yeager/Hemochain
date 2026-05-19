from flask import Blueprint
from flask_jwt_extended import jwt_required

from backend.controllers.blockchain_controller import (
    get_audit_trails,
    get_blockchain_logs,
    get_chain_info,
    get_emergency_audit_trail,
    get_transfer_chains,
    get_transfer_custody,
    get_verification_events,
    get_verification_status,
    public_verify,
    validate_chain,
    verify_donation,
    verify_transfer_delivery,
)
from backend.middleware.auth_middleware import role_required

blockchain_bp = Blueprint("blockchain", __name__, url_prefix="/api/blockchain")


# --- PUBLIC: QR Verification (no auth) ---

@blockchain_bp.get("/verify/<record_id>")
def public_verification(record_id):
    return public_verify(record_id)


# --- Donation Verification (bloodbank) ---

@blockchain_bp.post("/verify-donation")
@role_required("bloodbank")
def verify_donation_route():
    return verify_donation()


# --- Verification Status (any authenticated user) ---

@blockchain_bp.get("/status/<record_id>")
@jwt_required()
def verification_status(record_id):
    return get_verification_status(record_id)


# --- Transfer Verification ---

@blockchain_bp.post("/verify-transfer/<transfer_id>")
@jwt_required()
def verify_transfer_route(transfer_id):
    return verify_transfer_delivery(transfer_id)


@blockchain_bp.get("/transfer-chain/<transfer_id>")
@jwt_required()
def transfer_custody(transfer_id):
    return get_transfer_custody(transfer_id)


# --- Emergency Audit ---

@blockchain_bp.get("/emergency-audit/<emergency_id>")
@jwt_required()
def emergency_audit(emergency_id):
    return get_emergency_audit_trail(emergency_id)


# --- Chain Management (admin only) ---

@blockchain_bp.get("/chain-info")
@role_required("admin")
def chain_info():
    return get_chain_info()


@blockchain_bp.get("/validate-chain")
@role_required("admin")
def chain_validation():
    return validate_chain()


# --- Admin Audit Panel ---

@blockchain_bp.get("/logs")
@role_required("admin")
def blockchain_logs():
    return get_blockchain_logs()


@blockchain_bp.get("/verification-events")
@role_required("admin")
def verification_events():
    return get_verification_events()


@blockchain_bp.get("/audit-trails")
@role_required("admin")
def audit_trails():
    return get_audit_trails()


@blockchain_bp.get("/transfer-chains")
@role_required("admin")
def transfer_chains():
    return get_transfer_chains()
