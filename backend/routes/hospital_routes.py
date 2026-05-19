from flask import Blueprint

from backend.controllers.hospital_controller import (
    approve_appointment,
    cancel_appointment,
    create_emergency,
    get_appointments,
    get_dashboard_overview,
    get_donors,
    get_emergency_requests,
    get_inventory,
    get_nearby_donors,
    get_notifications,
    get_profile,
    get_reports,
    mark_notification_read,
    request_blood,
    update_inventory,
    update_profile,
)
from backend.middleware.auth_middleware import role_required

hospital_bp = Blueprint("hospital", __name__, url_prefix="/api/hospital")


# --- 1. Dashboard Overview ---

@hospital_bp.get("/dashboard-overview")
@role_required("hospital")
def dashboard_overview():
    return get_dashboard_overview()


# --- 2. Profile ---

@hospital_bp.get("/profile")
@role_required("hospital")
def profile():
    return get_profile()


@hospital_bp.put("/update-profile")
@role_required("hospital")
def update_profile_route():
    return update_profile()


# --- 3. Blood Inventory ---

@hospital_bp.get("/inventory")
@role_required("hospital")
def inventory():
    return get_inventory()


@hospital_bp.post("/update-inventory")
@role_required("hospital")
def update_inventory_route():
    return update_inventory()


# --- 4. Emergency Response ---

@hospital_bp.post("/create-emergency")
@role_required("hospital")
def create_emergency_route():
    return create_emergency()


@hospital_bp.get("/emergency-requests")
@role_required("hospital")
def emergency_requests():
    return get_emergency_requests()


# --- 5. Appointments & Donors ---

@hospital_bp.get("/appointments")
@role_required("hospital")
def appointments():
    return get_appointments()


@hospital_bp.post("/approve-appointment/<appointment_id>")
@role_required("hospital")
def approve_appointment_route(appointment_id):
    return approve_appointment(appointment_id)


@hospital_bp.post("/cancel-appointment/<appointment_id>")
@role_required("hospital")
def cancel_appointment_route(appointment_id):
    return cancel_appointment(appointment_id)


@hospital_bp.get("/donors")
@role_required("hospital")
def donors():
    return get_donors()


@hospital_bp.get("/nearby-donors")
@role_required("hospital")
def nearby_donors():
    return get_nearby_donors()


# --- 6. Blood Bank Requests ---

@hospital_bp.post("/request-blood")
@role_required("hospital")
def request_blood_route():
    return request_blood()


# --- 7. Notifications ---

@hospital_bp.get("/notifications")
@role_required("hospital")
def notifications():
    return get_notifications()


@hospital_bp.put("/mark-notification-read/<notification_id>")
@role_required("hospital")
def mark_notification_read_route(notification_id):
    return mark_notification_read(notification_id)


# --- 8. Reports & Analytics ---

@hospital_bp.get("/reports")
@role_required("hospital")
def reports():
    return get_reports()
