from backend.database.db import get_db, utc_now
from backend.utils.security import object_id, serialize_document


# ---------------------------------------------------------------------------
# 1. DASHBOARD OVERVIEW (COMMAND CENTER)
# ---------------------------------------------------------------------------

def get_hospital_dashboard_overview_data(hospital_id):
    db = get_db()
    h_id = object_id(hospital_id)

    # Total available blood units across all groups
    inventory = list(db["blood_inventory"].find({"hospital_id": h_id}))
    total_blood_units = sum(item.get("available_units", 0) for item in inventory)

    # Low stock alerts
    low_stock_groups = [
        {"blood_group": i.get("blood_group"), "units": i.get("available_units"), "status": i.get("inventory_status")}
        for i in inventory if i.get("inventory_status") in ("low", "critical")
    ]

    active_emergencies = db["emergency_requests"].count_documents({"hospital_id": h_id, "request_status": "active"})
    pending_appointments = db["appointments"].count_documents({"hospital_id": h_id, "appointment_status": "pending"})
    incoming_transfers = db["blood_transfers"].count_documents({"destination_hospital": h_id, "transfer_status": {"$in": ["pending", "dispatched"]}})

    return {
        "total_blood_units": total_blood_units,
        "active_emergencies": active_emergencies,
        "pending_appointments": pending_appointments,
        "incoming_transfers": incoming_transfers,
        "low_stock_alerts": low_stock_groups,
    }


# ---------------------------------------------------------------------------
# 2. HOSPITAL PROFILE
# ---------------------------------------------------------------------------

def get_hospital_profile_data(hospital_id):
    db = get_db()
    hospital = db["hospitals"].find_one({"_id": object_id(hospital_id)}, {"password": 0})
    if not hospital:
        return None

    total_donations = db["donations"].count_documents({"hospital_id": object_id(hospital_id), "donation_status": "completed"})
    hospital["total_donations_received"] = total_donations
    return serialize_document(hospital)


def update_hospital_profile_data(hospital_id, update_fields):
    db = get_db()
    allowed = {"phone", "address", "emergency_contact", "profile_image", "location"}
    update_doc = {k: v for k, v in update_fields.items() if k in allowed}
    if not update_doc:
        return None
    update_doc["updated_at"] = utc_now()
    db["hospitals"].update_one({"_id": object_id(hospital_id)}, {"$set": update_doc})
    return get_hospital_profile_data(hospital_id)


# ---------------------------------------------------------------------------
# 3. BLOOD INVENTORY MANAGEMENT
# ---------------------------------------------------------------------------

def get_hospital_inventory_data(hospital_id):
    cursor = get_db()["blood_inventory"].find({"hospital_id": object_id(hospital_id)})
    return [serialize_document(i) for i in cursor]


def update_hospital_inventory_data(hospital_id, payload):
    db = get_db()
    blood_group = payload.get("blood_group")
    available_units = payload.get("available_units", 0)
    reserved_units = payload.get("reserved_units", 0)
    expiring_units = payload.get("expiring_units", 0)

    if not blood_group:
        return None

    # Smart Auto-Status Engine
    status = "healthy"
    if available_units < 5:
        status = "critical"
    elif available_units < 15:
        status = "low"

    update_doc = {
        "available_units": available_units,
        "reserved_units": reserved_units,
        "expiring_units": expiring_units,
        "inventory_status": status,
        "updated_at": utc_now()
    }

    result = db["blood_inventory"].find_one_and_update(
        {"hospital_id": object_id(hospital_id), "blood_group": blood_group},
        {"$set": update_doc},
        upsert=True,
        return_document=True
    )

    # Auto-notify hospital if stock is critical
    if status == "critical":
        db["notifications"].insert_one({
            "user_id": object_id(hospital_id),
            "role": "hospital",
            "title": f"Critical Stock Alert: {blood_group}",
            "message": f"Only {available_units} units of {blood_group} remaining. Immediate replenishment required.",
            "notification_type": "inventory",
            "is_read": False,
            "created_at": utc_now()
        })

    return serialize_document(result)


# ---------------------------------------------------------------------------
# 4. EMERGENCY RESPONSE CENTER
# ---------------------------------------------------------------------------

def create_emergency_request_data(hospital_id, payload):
    db = get_db()
    hospital = db["hospitals"].find_one({"_id": object_id(hospital_id)})
    if not hospital:
        return None

    blood_group = payload.get("blood_group_needed")
    units = payload.get("units_required")

    req = {
        "hospital_id": object_id(hospital_id),
        "hospital_name": hospital.get("hospital_name"),
        "blood_group_needed": blood_group,
        "units_required": units,
        "urgency_level": payload.get("urgency_level", "urgent"),
        "patient_condition": payload.get("patient_condition", ""),
        "location": hospital.get("location", hospital.get("address")),
        "contact_number": payload.get("contact_number", hospital.get("phone")),
        "request_status": "active",
        "accepted_donor_id": None,
        "created_at": utc_now()
    }

    result = db["emergency_requests"].insert_one(req)
    req["_id"] = result.inserted_id

    # Automated Donor Radar — notify eligible matching donors
    donors = db["donors"].find({"blood_group": blood_group, "eligible_to_donate": {"$ne": False}})
    for donor in donors:
        db["notifications"].insert_one({
            "user_id": donor["_id"],
            "role": "donor",
            "title": f"🚨 Emergency: {blood_group} Needed",
            "message": f"{hospital.get('hospital_name')} urgently needs {units} units of {blood_group}. Please respond immediately.",
            "notification_type": "emergency_alert",
            "is_read": False,
            "created_at": utc_now()
        })

    # Notify nearby blood banks
    bloodbanks = db["bloodbanks"].find({})
    for bb in bloodbanks:
        db["notifications"].insert_one({
            "user_id": bb["_id"],
            "role": "bloodbank",
            "title": f"Hospital Emergency: {blood_group}",
            "message": f"{hospital.get('hospital_name')} has declared an emergency for {units} units of {blood_group}.",
            "notification_type": "emergency_alert",
            "is_read": False,
            "created_at": utc_now()
        })

    return serialize_document(req)


def get_hospital_emergency_requests_data(hospital_id):
    cursor = get_db()["emergency_requests"].find({"hospital_id": object_id(hospital_id)}).sort("created_at", -1)
    return [serialize_document(r) for r in cursor]


# ---------------------------------------------------------------------------
# 5. APPOINTMENT & DONOR MANAGEMENT
# ---------------------------------------------------------------------------

def get_hospital_appointments_data(hospital_id):
    db = get_db()
    cursor = db["appointments"].find({"hospital_id": object_id(hospital_id)}).sort("appointment_date", 1)
    appointments = []
    for appt in cursor:
        donor = db["donors"].find_one({"_id": appt.get("donor_id")})
        appt_doc = serialize_document(appt)
        if donor:
            appt_doc["donor_name"] = donor.get("full_name")
            appt_doc["donor_phone"] = donor.get("phone")
            appt_doc["blood_group"] = appt.get("blood_group") or donor.get("blood_group")
        appointments.append(appt_doc)
    return appointments


def update_appointment_status_data(hospital_id, appointment_id, status):
    db = get_db()
    result = db["appointments"].find_one_and_update(
        {"_id": object_id(appointment_id), "hospital_id": object_id(hospital_id)},
        {"$set": {"appointment_status": status, "updated_at": utc_now()}},
        return_document=True
    )
    if result:
        status_label = "approved" if status == "confirmed" else status
        db["notifications"].insert_one({
            "user_id": result.get("donor_id"),
            "role": "donor",
            "title": f"Appointment {status_label.title()}",
            "message": f"Your appointment on {result.get('appointment_date')} has been {status_label} by the hospital.",
            "notification_type": "appointment",
            "is_read": False,
            "created_at": utc_now()
        })
    return serialize_document(result)


def get_donors_list_data():
    cursor = get_db()["donors"].find({}, {"password": 0})
    return [serialize_document(d) for d in cursor]


def get_nearby_donors_data(blood_group=None):
    query = {"eligible_to_donate": {"$ne": False}}
    if blood_group:
        query["blood_group"] = blood_group
    cursor = get_db()["donors"].find(query, {"password": 0}).limit(50)
    return [serialize_document(d) for d in cursor]


# ---------------------------------------------------------------------------
# 6. BLOOD BANK REQUESTS (TRANSFERS)
# ---------------------------------------------------------------------------

def create_blood_request_data(hospital_id, payload):
    db = get_db()
    hospital = db["hospitals"].find_one({"_id": object_id(hospital_id)})
    hospital_name = hospital.get("hospital_name", "Unknown") if hospital else "Unknown"

    req = {
        "hospital_id": object_id(hospital_id),
        "hospital_name": hospital_name,
        "blood_group": payload.get("blood_group"),
        "units_requested": payload.get("units_requested"),
        "request_priority": payload.get("request_priority", "normal"),
        "request_status": "pending",
        "bloodbank_id": object_id(payload.get("bloodbank_id")) if payload.get("bloodbank_id") else None,
        "created_at": utc_now()
    }
    result = db["blood_requests"].insert_one(req)
    req["_id"] = result.inserted_id

    # Notify blood bank
    if req.get("bloodbank_id"):
        db["notifications"].insert_one({
            "user_id": req["bloodbank_id"],
            "role": "bloodbank",
            "title": "New Blood Request",
            "message": f"{hospital_name} has requested {req['units_requested']} units of {req['blood_group']}.",
            "notification_type": "transfer",
            "is_read": False,
            "created_at": utc_now()
        })

    return serialize_document(req)


# ---------------------------------------------------------------------------
# 7. NOTIFICATION CENTER
# ---------------------------------------------------------------------------

def get_hospital_notifications_data(hospital_id):
    cursor = get_db()["notifications"].find({"user_id": object_id(hospital_id)}).sort("created_at", -1).limit(50)
    return [serialize_document(n) for n in cursor]


def mark_hospital_notification_read_data(hospital_id, notification_id):
    db = get_db()
    result = db["notifications"].find_one_and_update(
        {"_id": object_id(notification_id), "user_id": object_id(hospital_id)},
        {"$set": {"is_read": True}},
        return_document=True
    )
    return serialize_document(result) if result else None


# ---------------------------------------------------------------------------
# 8. REPORTS & ANALYTICS
# ---------------------------------------------------------------------------

def get_hospital_reports_data(hospital_id):
    db = get_db()
    h_id = object_id(hospital_id)

    total_donations = db["donations"].count_documents({"hospital_id": h_id})
    completed_donations = db["donations"].count_documents({"hospital_id": h_id, "donation_status": "completed"})
    total_emergencies = db["emergency_requests"].count_documents({"hospital_id": h_id})
    active_emergencies = db["emergency_requests"].count_documents({"hospital_id": h_id, "request_status": "active"})
    resolved_emergencies = db["emergency_requests"].count_documents({"hospital_id": h_id, "request_status": {"$in": ["completed", "closed", "accepted_by_donor"]}})
    blood_requests_sent = db["blood_requests"].count_documents({"hospital_id": h_id})
    transfers_received = db["blood_transfers"].count_documents({"destination_hospital": h_id, "transfer_status": "delivered"})

    # Inventory summary
    inventory = list(db["blood_inventory"].find({"hospital_id": h_id}))
    total_units = sum(i.get("available_units", 0) for i in inventory)
    expiring_units = sum(i.get("expiring_units", 0) for i in inventory)

    return {
        "total_donations_processed": total_donations,
        "completed_donations": completed_donations,
        "total_emergencies_raised": total_emergencies,
        "active_emergencies": active_emergencies,
        "resolved_emergencies": resolved_emergencies,
        "blood_requests_sent": blood_requests_sent,
        "transfers_received": transfers_received,
        "total_blood_units": total_units,
        "expiring_units": expiring_units,
    }
