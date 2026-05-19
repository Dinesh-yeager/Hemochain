from datetime import datetime, timedelta, timezone

from backend.database.db import get_db, utc_now
from backend.utils.security import object_id, serialize_document


# ---------------------------------------------------------------------------
# 1. SMART ELIGIBILITY ENGINE
# ---------------------------------------------------------------------------

def calculate_eligibility(last_donation_date):
    """Return (eligible: bool, next_eligible_date: str|None)."""
    if not last_donation_date:
        return True, None
    if isinstance(last_donation_date, str):
        try:
            last_donation_date = datetime.fromisoformat(last_donation_date)
        except ValueError:
            return True, None

    next_eligible = last_donation_date + timedelta(days=90)
    now = datetime.now(timezone.utc)
    return now >= next_eligible, next_eligible.isoformat()


# ---------------------------------------------------------------------------
# 2. PROFILE DATA
# ---------------------------------------------------------------------------

def get_donor_profile_data(donor_id):
    db = get_db()
    donor = db["donors"].find_one({"_id": object_id(donor_id)})
    if not donor:
        return None

    # Eligibility calculation (runs every fetch)
    last_donation = donor.get("last_donation_date")
    eligible, next_date = calculate_eligibility(last_donation)
    donor["eligible_to_donate"] = eligible
    donor["next_eligible_date"] = next_date

    # Live donation metrics
    did = object_id(donor_id)
    donor["total_donations"] = db["donations"].count_documents({"donor_id": did})
    donor["completed_donations"] = db["donations"].count_documents({"donor_id": did, "screening_status": "verified"})
    donor["emergency_responses"] = db["emergency_requests"].count_documents({"accepted_donor_id": did})

    return serialize_document(donor)


def update_donor_profile_data(donor_id, update_fields):
    db = get_db()

    # Allowed fields to update (no admin approval required)
    allowed = {"phone", "address", "profile_image", "email", "gender", "age"}
    update_doc = {k: v for k, v in update_fields.items() if k in allowed}

    if not update_doc:
        return None

    update_doc["updated_at"] = utc_now()
    db["donors"].update_one(
        {"_id": object_id(donor_id)},
        {"$set": update_doc}
    )
    return get_donor_profile_data(donor_id)


# ---------------------------------------------------------------------------
# 3. DASHBOARD STATS (live metrics endpoint)
# ---------------------------------------------------------------------------

def get_donor_dashboard_stats_data(donor_id):
    db = get_db()
    did = object_id(donor_id)

    total = db["donations"].count_documents({"donor_id": did})
    completed = db["donations"].count_documents({"donor_id": did, "screening_status": "verified"})
    emergency_responses = db["emergency_requests"].count_documents({"accepted_donor_id": did})
    pending_appointments = db["appointments"].count_documents({"donor_id": did, "appointment_status": "pending"})
    unread_notifications = db["notifications"].count_documents({"user_id": did, "is_read": {"$ne": True}})

    return {
        "total_donations": total,
        "completed_donations": completed,
        "emergency_responses": emergency_responses,
        "pending_appointments": pending_appointments,
        "unread_notifications": unread_notifications,
    }


# ---------------------------------------------------------------------------
# 4. DONATION HISTORY
# ---------------------------------------------------------------------------

def get_donor_donations_data(donor_id):
    cursor = get_db()["donations"].find({"donor_id": object_id(donor_id)}).sort("created_at", -1)
    return [serialize_document(d) for d in cursor]


# ---------------------------------------------------------------------------
# 5. SMART APPOINTMENT BOOKING
# ---------------------------------------------------------------------------

def book_donation_appointment(donor_id, hospital_id, appt_date, appt_time):
    db = get_db()

    # Resolve hospital name & donor blood_group for richer records
    hospital = db["hospitals"].find_one({"_id": object_id(hospital_id)})
    donor = db["donors"].find_one({"_id": object_id(donor_id)})
    hospital_name = hospital.get("hospital_name", "Unknown") if hospital else "Unknown"
    blood_group = donor.get("blood_group", "Unknown") if donor else "Unknown"

    appointment = {
        "donor_id": object_id(donor_id),
        "hospital_id": object_id(hospital_id),
        "hospital_name": hospital_name,
        "blood_group": blood_group,
        "appointment_date": appt_date,
        "appointment_time": appt_time,
        "appointment_status": "pending",
        "created_at": utc_now()
    }
    result = db["appointments"].insert_one(appointment)
    appointment["_id"] = result.inserted_id

    # Notify donor
    db["notifications"].insert_one({
        "user_id": object_id(donor_id),
        "role": "donor",
        "title": "Appointment Booked",
        "message": f"Your donation appointment is confirmed for {appt_date} at {hospital_name}.",
        "notification_type": "appointment",
        "is_read": False,
        "created_at": utc_now()
    })

    # Notify hospital
    if hospital:
        db["notifications"].insert_one({
            "user_id": object_id(hospital_id),
            "role": "hospital",
            "title": "New Appointment Request",
            "message": f"A donor has booked a blood donation appointment for {appt_date}.",
            "notification_type": "appointment",
            "is_read": False,
            "created_at": utc_now()
        })

    return serialize_document(appointment)


# ---------------------------------------------------------------------------
# 6. REAL-TIME EMERGENCY RESPONSE
# ---------------------------------------------------------------------------

def get_emergency_requests_data(donor_blood_group=None):
    db = get_db()
    query = {"request_status": {"$nin": ["completed", "closed", "accepted_by_donor"]}}

    # Filter emergencies matching the donor's blood group
    if donor_blood_group:
        query["blood_group_needed"] = donor_blood_group

    cursor = db["emergency_requests"].find(query).sort([
        ("urgency_level", 1),   # critical first
        ("created_at", -1)
    ])
    return [serialize_document(r) for r in cursor]


def accept_emergency_request_data(donor_id, request_id):
    db = get_db()
    req = db["emergency_requests"].find_one({"_id": object_id(request_id)})
    if not req:
        return None

    # Assign donor to the emergency
    db["emergency_requests"].update_one(
        {"_id": object_id(request_id)},
        {"$set": {
            "request_status": "accepted_by_donor",
            "accepted_donor_id": object_id(donor_id)
        }}
    )

    # Notify hospital immediately
    db["notifications"].insert_one({
        "user_id": req.get("hospital_id"),
        "role": "hospital",
        "title": "Emergency Request Accepted",
        "message": "A donor has accepted your emergency blood request.",
        "notification_type": "emergency_alert",
        "is_read": False,
        "created_at": utc_now()
    })

    # Notify donor confirmation
    db["notifications"].insert_one({
        "user_id": object_id(donor_id),
        "role": "donor",
        "title": "Emergency Accepted",
        "message": f"You accepted an emergency request. Please proceed to the hospital immediately.",
        "notification_type": "emergency_alert",
        "is_read": False,
        "created_at": utc_now()
    })

    return True


# ---------------------------------------------------------------------------
# 7. NOTIFICATION CENTER
# ---------------------------------------------------------------------------

def get_donor_notifications_data(donor_id):
    cursor = get_db()["notifications"].find(
        {"user_id": object_id(donor_id)}
    ).sort("created_at", -1).limit(50)
    return [serialize_document(n) for n in cursor]


def mark_notification_read_data(donor_id, notification_id):
    db = get_db()
    result = db["notifications"].find_one_and_update(
        {"_id": object_id(notification_id), "user_id": object_id(donor_id)},
        {"$set": {"is_read": True}},
        return_document=True
    )
    return serialize_document(result) if result else None


# ---------------------------------------------------------------------------
# 8. GEO-LOCATION & DISCOVERY
# ---------------------------------------------------------------------------

def get_nearby_hospitals_data():
    cursor = get_db()["hospitals"].find(
        {"verified_status": "verified"},
        {"password": 0}
    ).limit(50)
    return [serialize_document(h) for h in cursor]


# ---------------------------------------------------------------------------
# 9. QR BLOCKCHAIN VERIFICATION
# ---------------------------------------------------------------------------

def get_qr_verification_data(donation_id):
    db = get_db()
    donation = db["donations"].find_one({"_id": object_id(donation_id)})
    if not donation:
        return None

    donor = db["donors"].find_one({"_id": donation.get("donor_id")})
    hospital = db["hospitals"].find_one({"_id": donation.get("hospital_id")})

    # Only expose safe, non-medical fields
    return {
        "verified": donation.get("blockchain_verified", False),
        "donation_date": donation.get("donation_date"),
        "blood_group": donation.get("blood_group"),
        "units_donated": donation.get("units_donated"),
        "screening_status": donation.get("screening_status"),
        "donor_name": donor.get("full_name") if donor else "Unknown",
        "hospital_name": hospital.get("hospital_name") if hospital else "Unknown",
        "verification_status": "✔ Verified Donation" if donation.get("blockchain_verified") else "Pending Verification",
        "secure_record": "✔ Secure Record",
    }
