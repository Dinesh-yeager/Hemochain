from flask import request
from flask_jwt_extended import get_jwt_identity

from backend.models.hospital_model import (
    create_blood_request_data,
    create_emergency_request_data,
    get_donors_list_data,
    get_hospital_appointments_data,
    get_hospital_dashboard_overview_data,
    get_hospital_emergency_requests_data,
    get_hospital_inventory_data,
    get_hospital_notifications_data,
    get_hospital_profile_data,
    get_hospital_reports_data,
    get_nearby_donors_data,
    mark_hospital_notification_read_data,
    update_appointment_status_data,
    update_hospital_inventory_data,
    update_hospital_profile_data,
)
from backend.utils.responses import error_response, success_response
from backend.utils.security import sanitize_document


# ---------------------------------------------------------------------------
# 1. DASHBOARD OVERVIEW
# ---------------------------------------------------------------------------

def get_dashboard_overview():
    hospital_id = get_jwt_identity()
    overview = get_hospital_dashboard_overview_data(hospital_id)
    return success_response("Dashboard overview retrieved", data=overview)


# ---------------------------------------------------------------------------
# 2. PROFILE
# ---------------------------------------------------------------------------

def get_profile():
    hospital_id = get_jwt_identity()
    profile = get_hospital_profile_data(hospital_id)
    if not profile:
        return error_response("Profile not found", 404)
    return success_response("Profile retrieved successfully", data=profile)


def update_profile():
    hospital_id = get_jwt_identity()
    payload = sanitize_document(request.get_json(silent=True) or {})
    updated = update_hospital_profile_data(hospital_id, payload)
    if not updated:
        return error_response("No valid fields provided for update", 400)
    return success_response("Profile updated successfully", data=updated)


# ---------------------------------------------------------------------------
# 3. BLOOD INVENTORY
# ---------------------------------------------------------------------------

def get_inventory():
    hospital_id = get_jwt_identity()
    inventory = get_hospital_inventory_data(hospital_id)
    return success_response("Inventory retrieved successfully", data=inventory)


def update_inventory():
    hospital_id = get_jwt_identity()
    payload = sanitize_document(request.get_json(silent=True) or {})
    if "blood_group" not in payload:
        return error_response("blood_group is required", 422)
    updated = update_hospital_inventory_data(hospital_id, payload)
    if not updated:
        return error_response("Failed to update inventory", 400)
    return success_response("Inventory updated successfully", data=updated)


# ---------------------------------------------------------------------------
# 4. EMERGENCY RESPONSE
# ---------------------------------------------------------------------------

def create_emergency():
    hospital_id = get_jwt_identity()
    payload = sanitize_document(request.get_json(silent=True) or {})
    if not payload.get("blood_group_needed") or not payload.get("units_required"):
        return error_response("blood_group_needed and units_required are required", 422)
    req = create_emergency_request_data(hospital_id, payload)
    if not req:
        return error_response("Hospital not found", 404)
    return success_response("Emergency request created and donors notified", data=req)


def get_emergency_requests():
    hospital_id = get_jwt_identity()
    reqs = get_hospital_emergency_requests_data(hospital_id)
    return success_response("Emergency requests retrieved", data=reqs)


# ---------------------------------------------------------------------------
# 5. APPOINTMENTS & DONORS
# ---------------------------------------------------------------------------

def get_appointments():
    hospital_id = get_jwt_identity()
    appointments = get_hospital_appointments_data(hospital_id)
    return success_response("Appointments retrieved", data=appointments)


def approve_appointment(appointment_id):
    hospital_id = get_jwt_identity()
    if not appointment_id:
        return error_response("appointment_id is required", 422)
    result = update_appointment_status_data(hospital_id, appointment_id, "confirmed")
    if not result:
        return error_response("Appointment not found", 404)
    return success_response("Appointment approved", data=result)


def cancel_appointment(appointment_id):
    hospital_id = get_jwt_identity()
    if not appointment_id:
        return error_response("appointment_id is required", 422)
    result = update_appointment_status_data(hospital_id, appointment_id, "cancelled")
    if not result:
        return error_response("Appointment not found", 404)
    return success_response("Appointment cancelled", data=result)


def get_donors():
    donors = get_donors_list_data()
    return success_response("Donors list retrieved", data=donors)


def get_nearby_donors():
    blood_group = request.args.get("blood_group")
    donors = get_nearby_donors_data(blood_group)
    return success_response("Nearby donors retrieved", data=donors)


# ---------------------------------------------------------------------------
# 6. BLOOD BANK REQUESTS
# ---------------------------------------------------------------------------

def request_blood():
    hospital_id = get_jwt_identity()
    payload = sanitize_document(request.get_json(silent=True) or {})
    if not payload.get("blood_group") or not payload.get("units_requested"):
        return error_response("blood_group and units_requested are required", 422)
    req = create_blood_request_data(hospital_id, payload)
    return success_response("Blood request sent to blood bank", data=req)


# ---------------------------------------------------------------------------
# 7. NOTIFICATIONS
# ---------------------------------------------------------------------------

def get_notifications():
    hospital_id = get_jwt_identity()
    notifications = get_hospital_notifications_data(hospital_id)
    return success_response("Notifications retrieved", data=notifications)


def mark_notification_read(notification_id):
    hospital_id = get_jwt_identity()
    result = mark_hospital_notification_read_data(hospital_id, notification_id)
    if not result:
        return error_response("Notification not found", 404)
    return success_response("Notification marked as read", data=result)


# ---------------------------------------------------------------------------
# 8. REPORTS & ANALYTICS
# ---------------------------------------------------------------------------

def get_reports():
    hospital_id = get_jwt_identity()
    reports = get_hospital_reports_data(hospital_id)
    return success_response("Reports generated successfully", data=reports)
