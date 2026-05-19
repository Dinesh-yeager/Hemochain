from flask import Blueprint

from backend.controllers.bloodbank_controller import (
    approve_request,
    emergency_dispatch,
    get_dashboard_overview,
    get_donations,
    get_donors,
    get_hospital_requests,
    get_inventory,
    get_notifications,
    get_profile,
    get_reports,
    get_transfers,
    mark_notification_read,
    reject_request,
    update_inventory,
    update_profile,
    update_transfer_status,
    verify_donation,
)
from backend.middleware.auth_middleware import role_required

bloodbank_bp = Blueprint("bloodbank", __name__, url_prefix="/api/bloodbank")


# --- 1. Dashboard Overview ---

@bloodbank_bp.get("/dashboard-overview")
@role_required("bloodbank")
def dashboard_overview():
    return get_dashboard_overview()


# --- 2. Profile ---

@bloodbank_bp.get("/profile")
@role_required("bloodbank")
def profile():
    return get_profile()


@bloodbank_bp.put("/update-profile")
@role_required("bloodbank")
def update_profile_route():
    return update_profile()


# --- 3. Blood Inventory ---

@bloodbank_bp.get("/inventory")
@role_required("bloodbank")
def inventory():
    return get_inventory()


@bloodbank_bp.post("/update-inventory")
@role_required("bloodbank")
def update_inventory_route():
    return update_inventory()


# --- 4. Hospital Requests ---

@bloodbank_bp.get("/hospital-requests")
@role_required("bloodbank")
def hospital_requests():
    return get_hospital_requests()


@bloodbank_bp.post("/approve-request/<request_id>")
@role_required("bloodbank")
def approve_request_route(request_id):
    return approve_request(request_id)


@bloodbank_bp.post("/reject-request/<request_id>")
@role_required("bloodbank")
def reject_request_route(request_id):
    return reject_request(request_id)


# --- 5. Blood Transfers & Logistics ---

@bloodbank_bp.get("/transfers")
@role_required("bloodbank")
def transfers():
    return get_transfers()


@bloodbank_bp.post("/update-transfer-status/<transfer_id>")
@role_required("bloodbank")
def update_transfer_status_route(transfer_id):
    return update_transfer_status(transfer_id)


@bloodbank_bp.post("/emergency-dispatch")
@role_required("bloodbank")
def emergency_dispatch_route():
    return emergency_dispatch()


# --- 6. Donation & Blockchain Verification ---

@bloodbank_bp.get("/donations")
@role_required("bloodbank")
def donations():
    return get_donations()


@bloodbank_bp.post("/update-screening-status/<donation_id>")
@role_required("bloodbank")
def verify_donation_route(donation_id):
    return verify_donation(donation_id)


# --- 7. Donor Directory ---

@bloodbank_bp.get("/donors")
@role_required("bloodbank")
def donors():
    return get_donors()


# --- 8. Notifications ---

@bloodbank_bp.get("/notifications")
@role_required("bloodbank")
def notifications():
    return get_notifications()


@bloodbank_bp.put("/mark-notification-read/<notification_id>")
@role_required("bloodbank")
def mark_notification_read_route(notification_id):
    return mark_notification_read(notification_id)


# --- 9. Reports & Analytics ---

@bloodbank_bp.get("/reports")
@role_required("bloodbank")
def reports():
    return get_reports()
