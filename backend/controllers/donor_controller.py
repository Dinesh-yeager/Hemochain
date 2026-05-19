from flask import request
from flask_jwt_extended import get_jwt_identity

from backend.models.donor_model import (
    accept_emergency_request_data,
    book_donation_appointment,
    get_donor_dashboard_stats_data,
    get_donor_donations_data,
    get_donor_notifications_data,
    get_donor_profile_data,
    get_emergency_requests_data,
    get_nearby_hospitals_data,
    get_qr_verification_data,
    mark_notification_read_data,
    update_donor_profile_data,
)
from backend.utils.responses import error_response, success_response
from backend.utils.security import sanitize_document


# ---------------------------------------------------------------------------
# 1. PROFILE & ELIGIBILITY
# ---------------------------------------------------------------------------

def get_profile():
    donor_id = get_jwt_identity()
    profile = get_donor_profile_data(donor_id)
    if not profile:
        return error_response("Profile not found", 404)
    return success_response("Profile retrieved successfully", data=profile)


def update_profile():
    donor_id = get_jwt_identity()
    payload = sanitize_document(request.get_json(silent=True) or {})
    updated = update_donor_profile_data(donor_id, payload)
    if not updated:
        return error_response("No valid fields provided for update", 400)
    return success_response("Profile updated successfully", data=updated)


# ---------------------------------------------------------------------------
# 2. LIVE DASHBOARD STATS
# ---------------------------------------------------------------------------

def get_dashboard_stats():
    donor_id = get_jwt_identity()
    stats = get_donor_dashboard_stats_data(donor_id)
    return success_response("Dashboard stats retrieved", data=stats)


# ---------------------------------------------------------------------------
# 3. DONATION HISTORY
# ---------------------------------------------------------------------------

def get_donations():
    donor_id = get_jwt_identity()
    donations = get_donor_donations_data(donor_id)
    return success_response("Donations retrieved successfully", data=donations)


# ---------------------------------------------------------------------------
# 4. SMART APPOINTMENT BOOKING
# ---------------------------------------------------------------------------

def book_appointment():
    donor_id = get_jwt_identity()
    payload = sanitize_document(request.get_json(silent=True) or {})
    hospital_id = payload.get("hospital_id")
    appt_date = payload.get("appointment_date")
    appt_time = payload.get("appointment_time")

    if not hospital_id or not appt_date or not appt_time:
        return error_response("hospital_id, appointment_date, and appointment_time are required", 422)

    # Eligibility enforcement
    profile = get_donor_profile_data(donor_id)
    if profile and not profile.get("eligible_to_donate", True):
        next_date = profile.get("next_eligible_date", "unknown")
        return error_response(
            f"You are currently not eligible to donate blood. Next eligible date: {next_date}", 400
        )

    appointment = book_donation_appointment(donor_id, hospital_id, appt_date, appt_time)
    return success_response("Appointment booked successfully", data=appointment)


# ---------------------------------------------------------------------------
# 5. EMERGENCY RESPONSE
# ---------------------------------------------------------------------------

def get_emergency_requests():
    donor_id = get_jwt_identity()
    # Fetch donor's blood group for smart filtering
    profile = get_donor_profile_data(donor_id)
    blood_group = profile.get("blood_group") if profile else None
    requests = get_emergency_requests_data(donor_blood_group=blood_group)
    return success_response("Emergency requests retrieved successfully", data=requests)


def accept_emergency(request_id):
    donor_id = get_jwt_identity()
    if not request_id:
        return error_response("request_id is required", 422)

    result = accept_emergency_request_data(donor_id, request_id)
    if not result:
        return error_response("Emergency request not found", 404)
    return success_response("Emergency request accepted successfully")


# ---------------------------------------------------------------------------
# 6. GEO-LOCATION & DISCOVERY
# ---------------------------------------------------------------------------

def get_nearby_hospitals():
    hospitals = get_nearby_hospitals_data()
    return success_response("Nearby hospitals retrieved successfully", data=hospitals)


# ---------------------------------------------------------------------------
# 7. NOTIFICATION CENTER
# ---------------------------------------------------------------------------

def get_notifications():
    donor_id = get_jwt_identity()
    notifications = get_donor_notifications_data(donor_id)
    return success_response("Notifications retrieved successfully", data=notifications)


def mark_notification_read(notification_id):
    donor_id = get_jwt_identity()
    result = mark_notification_read_data(donor_id, notification_id)
    if not result:
        return error_response("Notification not found", 404)
    return success_response("Notification marked as read", data=result)


# ---------------------------------------------------------------------------
# 8. QR BLOCKCHAIN VERIFICATION
# ---------------------------------------------------------------------------

def get_qr_verification(donation_id):
    data = get_qr_verification_data(donation_id)
    if not data:
        return error_response("Donation record not found", 404)
    return success_response("QR Verification data retrieved", data=data)
