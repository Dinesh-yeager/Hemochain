from flask import request
from flask_jwt_extended import get_jwt_identity

from backend.models.admin_model import (
    close_emergency_admin_data,
    get_activity_logs_admin_data,
    get_admin_dashboard_overview_data,
    get_admin_notifications_data,
    get_admin_profile_data,
    get_admin_reports_data,
    get_blood_inventory_admin_data,
    get_blockchain_logs_admin_data,
    get_donors_admin_data,
    get_facilities_data,
    get_global_emergencies_data,
    get_settings_admin_data,
    mark_admin_notification_read_data,
    suspend_donor_data,
    suspend_entity_data,
    update_admin_profile_data,
    verify_entity_data,
)
from backend.utils.responses import error_response, success_response
from backend.utils.security import sanitize_document


# ---------------------------------------------------------------------------
# 1. DASHBOARD OVERVIEW
# ---------------------------------------------------------------------------

def get_dashboard_overview():
    overview = get_admin_dashboard_overview_data()
    return success_response("Dashboard overview retrieved", data=overview)


# ---------------------------------------------------------------------------
# 2. PROFILE
# ---------------------------------------------------------------------------

def get_profile():
    admin_id = get_jwt_identity()
    profile = get_admin_profile_data(admin_id)
    if not profile:
        return error_response("Profile not found", 404)
    return success_response("Profile retrieved successfully", data=profile)


def update_profile():
    admin_id = get_jwt_identity()
    payload = sanitize_document(request.get_json(silent=True) or {})
    updated = update_admin_profile_data(admin_id, payload)
    if not updated:
        return error_response("No valid fields provided for update", 400)
    return success_response("Profile updated successfully", data=updated)


# ---------------------------------------------------------------------------
# 3. ENTITY MANAGEMENT
# ---------------------------------------------------------------------------

def get_facilities():
    entity_type = request.args.get("type")  # "hospital" or "bloodbank" or None for all
    facilities = get_facilities_data(entity_type)
    return success_response("Facilities retrieved", data=facilities)


def verify_entity(entity_id):
    admin_id = get_jwt_identity()
    payload = sanitize_document(request.get_json(silent=True) or {})
    entity_type = payload.get("entity_type")
    if entity_type not in ("hospital", "bloodbank"):
        return error_response("entity_type must be 'hospital' or 'bloodbank'", 422)
    result = verify_entity_data(admin_id, entity_id, entity_type)
    if not result:
        return error_response("Entity not found", 404)
    return success_response(f"{entity_type.title()} verified successfully", data=result)


def suspend_entity(entity_id):
    admin_id = get_jwt_identity()
    payload = sanitize_document(request.get_json(silent=True) or {})
    entity_type = payload.get("entity_type")
    if entity_type not in ("hospital", "bloodbank"):
        return error_response("entity_type must be 'hospital' or 'bloodbank'", 422)
    result = suspend_entity_data(admin_id, entity_id, entity_type)
    if not result:
        return error_response("Entity not found", 404)
    return success_response(f"{entity_type.title()} suspended successfully", data=result)


# ---------------------------------------------------------------------------
# 4. DONOR GOVERNANCE
# ---------------------------------------------------------------------------

def get_donors():
    donors = get_donors_admin_data()
    return success_response("Donors retrieved", data=donors)


def suspend_donor(donor_id):
    admin_id = get_jwt_identity()
    result = suspend_donor_data(admin_id, donor_id)
    if not result:
        return error_response("Donor not found", 404)
    return success_response("Donor suspended successfully", data=result)


# ---------------------------------------------------------------------------
# 5. GLOBAL EMERGENCY MONITORING
# ---------------------------------------------------------------------------

def get_global_emergencies():
    emergencies = get_global_emergencies_data()
    return success_response("Global emergencies retrieved", data=emergencies)


def close_emergency(emergency_id):
    admin_id = get_jwt_identity()
    result = close_emergency_admin_data(admin_id, emergency_id)
    if not result:
        return error_response("Emergency not found", 404)
    return success_response("Emergency closed successfully", data=result)


# ---------------------------------------------------------------------------
# 6. BLOCKCHAIN AUDIT
# ---------------------------------------------------------------------------

def get_blockchain_logs():
    logs = get_blockchain_logs_admin_data()
    return success_response("Blockchain logs retrieved", data=logs)


def get_activity_logs():
    logs = get_activity_logs_admin_data()
    return success_response("Activity logs retrieved", data=logs)


# ---------------------------------------------------------------------------
# 7. REPORTS & ANALYTICS
# ---------------------------------------------------------------------------

def get_reports():
    reports = get_admin_reports_data()
    return success_response("Reports generated successfully", data=reports)


# ---------------------------------------------------------------------------
# 8. GLOBAL INVENTORY
# ---------------------------------------------------------------------------

def get_inventory():
    inventory = get_blood_inventory_admin_data()
    return success_response("Global inventory retrieved", data=inventory)


# ---------------------------------------------------------------------------
# 9. NOTIFICATIONS
# ---------------------------------------------------------------------------

def get_notifications():
    notifications = get_admin_notifications_data()
    return success_response("Notifications retrieved", data=notifications)


def mark_notification_read(notification_id):
    result = mark_admin_notification_read_data(notification_id)
    if not result:
        return error_response("Notification not found", 404)
    return success_response("Notification marked as read", data=result)


# ---------------------------------------------------------------------------
# 10. SETTINGS
# ---------------------------------------------------------------------------

def get_settings():
    settings = get_settings_admin_data()
    return success_response("Settings retrieved", data=settings)
