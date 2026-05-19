from flask import request
from flask_jwt_extended import get_jwt_identity

from backend.models.bloodbank_model import (
    approve_hospital_request_data,
    create_emergency_dispatch_data,
    get_blood_transfers_data,
    get_bloodbank_dashboard_overview_data,
    get_bloodbank_inventory_data,
    get_bloodbank_notifications_data,
    get_bloodbank_profile_data,
    get_bloodbank_reports_data,
    get_donor_records_data,
    get_hospital_requests_data,
    get_incoming_donations_data,
    mark_bloodbank_notification_read_data,
    reject_hospital_request_data,
    update_bloodbank_inventory_data,
    update_bloodbank_profile_data,
    update_donation_verification_data,
    update_transfer_status_data,
)
from backend.utils.responses import error_response, success_response
from backend.utils.security import sanitize_document


# ---------------------------------------------------------------------------
# 1. DASHBOARD OVERVIEW
# ---------------------------------------------------------------------------

def get_dashboard_overview():
    bb_id = get_jwt_identity()
    overview = get_bloodbank_dashboard_overview_data(bb_id)
    return success_response("Dashboard overview retrieved", data=overview)


# ---------------------------------------------------------------------------
# 2. PROFILE
# ---------------------------------------------------------------------------

def get_profile():
    bb_id = get_jwt_identity()
    profile = get_bloodbank_profile_data(bb_id)
    if not profile:
        return error_response("Profile not found", 404)
    return success_response("Profile retrieved successfully", data=profile)


def update_profile():
    bb_id = get_jwt_identity()
    payload = sanitize_document(request.get_json(silent=True) or {})
    updated = update_bloodbank_profile_data(bb_id, payload)
    if not updated:
        return error_response("No valid fields provided for update", 400)
    return success_response("Profile updated successfully", data=updated)


# ---------------------------------------------------------------------------
# 3. BLOOD INVENTORY
# ---------------------------------------------------------------------------

def get_inventory():
    bb_id = get_jwt_identity()
    inventory = get_bloodbank_inventory_data(bb_id)
    return success_response("Inventory retrieved successfully", data=inventory)


def update_inventory():
    bb_id = get_jwt_identity()
    payload = sanitize_document(request.get_json(silent=True) or {})
    if "blood_group" not in payload:
        return error_response("blood_group is required", 422)
    updated = update_bloodbank_inventory_data(bb_id, payload)
    if not updated:
        return error_response("Failed to update inventory", 400)
    return success_response("Inventory updated successfully", data=updated)


# ---------------------------------------------------------------------------
# 4. HOSPITAL REQUESTS
# ---------------------------------------------------------------------------

def get_hospital_requests():
    bb_id = get_jwt_identity()
    reqs = get_hospital_requests_data(bb_id)
    return success_response("Hospital requests retrieved", data=reqs)


def approve_request(request_id):
    bb_id = get_jwt_identity()
    if not request_id:
        return error_response("request_id is required", 422)
    result = approve_hospital_request_data(bb_id, request_id)
    if not result:
        return error_response("Request not found or already processed", 404)
    return success_response("Request approved, transfer created", data=result)


def reject_request(request_id):
    bb_id = get_jwt_identity()
    if not request_id:
        return error_response("request_id is required", 422)
    result = reject_hospital_request_data(bb_id, request_id)
    if not result:
        return error_response("Request not found or already processed", 404)
    return success_response("Request rejected", data=result)


# ---------------------------------------------------------------------------
# 5. BLOOD TRANSFERS & LOGISTICS
# ---------------------------------------------------------------------------

def get_transfers():
    bb_id = get_jwt_identity()
    transfers = get_blood_transfers_data(bb_id)
    return success_response("Blood transfers retrieved", data=transfers)


def update_transfer_status(transfer_id):
    bb_id = get_jwt_identity()
    payload = sanitize_document(request.get_json(silent=True) or {})
    status = payload.get("status")
    if status not in ("pending", "dispatched", "delivered"):
        return error_response("Invalid status. Must be pending, dispatched, or delivered.", 422)
    result = update_transfer_status_data(bb_id, transfer_id, status)
    if not result:
        return error_response("Transfer record not found", 404)
    return success_response("Transfer status updated", data=result)


def emergency_dispatch():
    bb_id = get_jwt_identity()
    payload = sanitize_document(request.get_json(silent=True) or {})
    result = create_emergency_dispatch_data(bb_id, payload)
    if not result:
        return error_response("hospital_id, blood_group, and units_transferred are required", 422)
    return success_response("Emergency dispatch initiated", data=result)


# ---------------------------------------------------------------------------
# 6. DONATION & BLOCKCHAIN VERIFICATION
# ---------------------------------------------------------------------------

def get_donations():
    bb_id = get_jwt_identity()
    donations = get_incoming_donations_data(bb_id)
    return success_response("Incoming donations retrieved", data=donations)


def verify_donation(donation_id):
    bb_id = get_jwt_identity()
    payload = sanitize_document(request.get_json(silent=True) or {})
    status = payload.get("status")
    if status not in ("verified", "testing", "rejected"):
        return error_response("Invalid status. Must be verified, testing, or rejected.", 422)
    result = update_donation_verification_data(bb_id, donation_id, status)
    if not result:
        return error_response("Donation record not found", 404)
    return success_response("Donation screening updated", data=result)


# ---------------------------------------------------------------------------
# 7. DONOR DIRECTORY
# ---------------------------------------------------------------------------

def get_donors():
    blood_group = request.args.get("blood_group")
    eligible_only = request.args.get("eligible_only", "false").lower() == "true"
    donors = get_donor_records_data(blood_group, eligible_only)
    return success_response("Donor records retrieved", data=donors)


# ---------------------------------------------------------------------------
# 8. NOTIFICATIONS
# ---------------------------------------------------------------------------

def get_notifications():
    bb_id = get_jwt_identity()
    notifications = get_bloodbank_notifications_data(bb_id)
    return success_response("Notifications retrieved", data=notifications)


def mark_notification_read(notification_id):
    bb_id = get_jwt_identity()
    result = mark_bloodbank_notification_read_data(bb_id, notification_id)
    if not result:
        return error_response("Notification not found", 404)
    return success_response("Notification marked as read", data=result)


# ---------------------------------------------------------------------------
# 9. REPORTS & ANALYTICS
# ---------------------------------------------------------------------------

def get_reports():
    bb_id = get_jwt_identity()
    reports = get_bloodbank_reports_data(bb_id)
    return success_response("Reports generated successfully", data=reports)
