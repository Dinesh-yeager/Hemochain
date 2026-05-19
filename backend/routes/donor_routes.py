from flask import Blueprint
from flask_jwt_extended import jwt_required

from backend.controllers.donor_controller import (
    accept_emergency,
    book_appointment,
    get_dashboard_stats,
    get_donations,
    get_emergency_requests,
    get_nearby_hospitals,
    get_notifications,
    get_profile,
    get_qr_verification,
    mark_notification_read,
    update_profile,
)
from backend.middleware.auth_middleware import role_required

donor_bp = Blueprint("donor", __name__, url_prefix="/api/donor")


# --- 1. Profile & Eligibility ---

@donor_bp.get("/profile")
@role_required("donor")
def profile():
    return get_profile()


@donor_bp.put("/update-profile")
@role_required("donor")
def update_profile_route():
    return update_profile()


# --- 2. Dashboard Stats ---

@donor_bp.get("/dashboard-stats")
@role_required("donor")
def dashboard_stats():
    return get_dashboard_stats()


# --- 3. Donation History ---

@donor_bp.get("/donations")
@role_required("donor")
def donations():
    return get_donations()


# --- 4. Smart Appointment Booking ---

@donor_bp.post("/book-appointment")
@role_required("donor")
def book_appointment_route():
    return book_appointment()


# --- 5. Emergency Response ---

@donor_bp.get("/emergency-requests")
@role_required("donor")
def emergency_requests():
    return get_emergency_requests()


@donor_bp.post("/accept-emergency/<request_id>")
@role_required("donor")
def accept_emergency_route(request_id):
    return accept_emergency(request_id)


# --- 6. Nearby Hospitals ---

@donor_bp.get("/nearby-hospitals")
@role_required("donor")
def nearby_hospitals():
    return get_nearby_hospitals()


# --- 7. Notifications ---

@donor_bp.get("/notifications")
@role_required("donor")
def notifications():
    return get_notifications()


@donor_bp.put("/mark-notification-read/<notification_id>")
@role_required("donor")
def mark_notification_read_route(notification_id):
    return mark_notification_read(notification_id)


# --- 8. QR Blockchain Verification ---

@donor_bp.get("/qr/<donation_id>")
@jwt_required()
def qr_verification(donation_id):
    return get_qr_verification(donation_id)
