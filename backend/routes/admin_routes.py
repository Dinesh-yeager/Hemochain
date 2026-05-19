from flask import Blueprint

from backend.controllers.admin_controller import (
    close_emergency,
    get_activity_logs,
    get_blockchain_logs,
    get_dashboard_overview,
    get_donors,
    get_facilities,
    get_global_emergencies,
    get_inventory,
    get_notifications,
    get_profile,
    get_reports,
    get_settings,
    mark_notification_read,
    suspend_donor,
    suspend_entity,
    update_profile,
    verify_entity,
)
from backend.middleware.auth_middleware import role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


# --- 1. Dashboard Overview ---

@admin_bp.get("/dashboard-overview")
@role_required("admin")
def dashboard_overview():
    return get_dashboard_overview()


# --- 2. Profile ---

@admin_bp.get("/profile")
@role_required("admin")
def profile():
    return get_profile()


@admin_bp.put("/update-profile")
@role_required("admin")
def update_profile_route():
    return update_profile()


# --- 3. Entity Management ---

@admin_bp.get("/facilities")
@role_required("admin")
def facilities():
    return get_facilities()


@admin_bp.post("/verify-entity/<entity_id>")
@role_required("admin")
def verify_entity_route(entity_id):
    return verify_entity(entity_id)


@admin_bp.post("/suspend-entity/<entity_id>")
@role_required("admin")
def suspend_entity_route(entity_id):
    return suspend_entity(entity_id)


# --- 4. Donor Governance ---

@admin_bp.get("/donors")
@role_required("admin")
def donors():
    return get_donors()


@admin_bp.post("/suspend-donor/<donor_id>")
@role_required("admin")
def suspend_donor_route(donor_id):
    return suspend_donor(donor_id)


# --- 5. Global Emergency Monitoring ---

@admin_bp.get("/global-emergencies")
@role_required("admin")
def global_emergencies():
    return get_global_emergencies()


@admin_bp.post("/close-emergency/<emergency_id>")
@role_required("admin")
def close_emergency_route(emergency_id):
    return close_emergency(emergency_id)


# --- 6. Blockchain Audit ---

@admin_bp.get("/blockchain-logs")
@role_required("admin")
def blockchain_logs():
    return get_blockchain_logs()


@admin_bp.get("/activity-logs")
@role_required("admin")
def activity_logs():
    return get_activity_logs()


# --- 7. Reports & Analytics ---

@admin_bp.get("/reports")
@role_required("admin")
def reports():
    return get_reports()


# --- 8. Global Inventory ---

@admin_bp.get("/inventory")
@role_required("admin")
def inventory():
    return get_inventory()


# --- 9. Notifications ---

@admin_bp.get("/notifications")
@role_required("admin")
def notifications():
    return get_notifications()


@admin_bp.put("/mark-notification-read/<notification_id>")
@role_required("admin")
def mark_notification_read_route(notification_id):
    return mark_notification_read(notification_id)


# --- 10. Settings ---

@admin_bp.get("/settings")
@role_required("admin")
def settings():
    return get_settings()
