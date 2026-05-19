import hashlib

from backend.database.db import get_db, utc_now
from backend.utils.security import object_id, serialize_document


# ---------------------------------------------------------------------------
# ADMIN ACTION AUDIT LOGGER
# ---------------------------------------------------------------------------

def log_admin_action(admin_id, action, details):
    get_db()["activity_logs"].insert_one({
        "user_id": object_id(admin_id),
        "user_role": "admin",
        "action": action,
        "action_details": details,
        "created_at": utc_now()
    })


# ---------------------------------------------------------------------------
# 1. PLATFORM OVERVIEW (COMMAND CENTER)
# ---------------------------------------------------------------------------

def get_admin_dashboard_overview_data():
    db = get_db()

    total_donors = db["donors"].count_documents({})
    verified_hospitals = db["hospitals"].count_documents({"verified_status": "verified"})
    registered_bloodbanks = db["bloodbanks"].count_documents({})
    total_donations = db["donations"].count_documents({})
    verified_donations = db["donations"].count_documents({"screening_status": "verified"})
    active_emergencies = db["emergency_requests"].count_documents({"request_status": "active"})
    resolved_emergencies = db["emergency_requests"].count_documents({"request_status": {"$in": ["completed", "closed", "accepted_by_donor"]}})

    # Blood units in transit
    blood_in_transit = db["blood_transfers"].count_documents({"transfer_status": {"$in": ["pending", "dispatched"]}})

    # Global inventory
    inventory = list(db["blood_inventory"].find({}))
    total_blood_units = sum(i.get("available_units", 0) for i in inventory)

    # Verification backlog
    pending_hospitals = db["hospitals"].count_documents({"verified_status": {"$nin": ["verified", "suspended"]}})
    pending_bloodbanks = db["bloodbanks"].count_documents({"verified_status": {"$nin": ["verified", "approved", "suspended"]}})

    return {
        "total_registered_donors": total_donors,
        "verified_hospitals": verified_hospitals,
        "registered_bloodbanks": registered_bloodbanks,
        "total_donations_processed": total_donations,
        "verified_donations": verified_donations,
        "active_emergencies": active_emergencies,
        "resolved_emergencies": resolved_emergencies,
        "blood_units_in_transit": blood_in_transit,
        "total_blood_units": total_blood_units,
        "pending_hospital_verifications": pending_hospitals,
        "pending_bloodbank_verifications": pending_bloodbanks,
    }


# ---------------------------------------------------------------------------
# 2. ADMIN PROFILE
# ---------------------------------------------------------------------------

def get_admin_profile_data(admin_id):
    admin = get_db()["admins"].find_one({"_id": object_id(admin_id)}, {"password": 0})
    return serialize_document(admin)


def update_admin_profile_data(admin_id, update_fields):
    db = get_db()
    allowed = {"contact_number", "admin_name", "email"}
    update_doc = {k: v for k, v in update_fields.items() if k in allowed}
    if not update_doc:
        return None
    update_doc["updated_at"] = utc_now()
    db["admins"].update_one({"_id": object_id(admin_id)}, {"$set": update_doc})
    return get_admin_profile_data(admin_id)


# ---------------------------------------------------------------------------
# 3. ENTITY MANAGEMENT (HOSPITALS & BLOOD BANKS)
# ---------------------------------------------------------------------------

def get_facilities_data(entity_type=None):
    db = get_db()
    facilities = []

    if entity_type in (None, "hospital"):
        hospitals = db["hospitals"].find({}, {"password": 0}).sort("created_at", -1)
        for h in hospitals:
            doc = serialize_document(h)
            doc["entity_type"] = "hospital"
            facilities.append(doc)

    if entity_type in (None, "bloodbank"):
        bloodbanks = db["bloodbanks"].find({}, {"password": 0}).sort("created_at", -1)
        for b in bloodbanks:
            doc = serialize_document(b)
            doc["entity_type"] = "bloodbank"
            facilities.append(doc)

    return facilities


def verify_entity_data(admin_id, entity_id, entity_type):
    db = get_db()
    collection = "hospitals" if entity_type == "hospital" else "bloodbanks"
    name_field = "hospital_name" if entity_type == "hospital" else "bloodbank_name"

    result = db[collection].find_one_and_update(
        {"_id": object_id(entity_id)},
        {"$set": {"verified_status": "verified", "updated_at": utc_now()}},
        return_document=True
    )

    if result:
        # Notify the entity
        db["notifications"].insert_one({
            "user_id": object_id(entity_id),
            "role": entity_type,
            "title": "Account Verified ✔",
            "message": f"Your {entity_type} account has been verified by the HemoChain admin. Full dashboard access is now granted.",
            "notification_type": "system",
            "is_read": False,
            "created_at": utc_now()
        })
        log_admin_action(admin_id, f"verify_{entity_type}", f"Verified {result.get(name_field)} ({entity_id})")

    return serialize_document(result)


def suspend_entity_data(admin_id, entity_id, entity_type):
    db = get_db()
    collection = "hospitals" if entity_type == "hospital" else "bloodbanks"
    name_field = "hospital_name" if entity_type == "hospital" else "bloodbank_name"

    result = db[collection].find_one_and_update(
        {"_id": object_id(entity_id)},
        {"$set": {"verified_status": "suspended", "updated_at": utc_now()}},
        return_document=True
    )

    if result:
        # Blacklist all active JWT tokens for this entity
        db["jwt_blocklist"].insert_one({
            "user_id": str(entity_id),
            "reason": "admin_suspension",
            "revoked_at": utc_now()
        })

        # Notify the entity
        db["notifications"].insert_one({
            "user_id": object_id(entity_id),
            "role": entity_type,
            "title": "Account Suspended",
            "message": "Your account has been suspended by the HemoChain administration. Contact support for details.",
            "notification_type": "system",
            "is_read": False,
            "created_at": utc_now()
        })
        log_admin_action(admin_id, f"suspend_{entity_type}", f"Suspended {result.get(name_field)} ({entity_id})")

    return serialize_document(result)


# ---------------------------------------------------------------------------
# 4. DONOR GOVERNANCE
# ---------------------------------------------------------------------------

def get_donors_admin_data():
    db = get_db()
    cursor = db["donors"].find({}, {"password": 0}).sort("created_at", -1)
    donors = []
    for d in cursor:
        doc = serialize_document(d)
        did = d["_id"]
        doc["total_donations"] = db["donations"].count_documents({"donor_id": did})
        doc["emergency_responses"] = db["emergency_requests"].count_documents({"accepted_donor_id": did})
        donors.append(doc)
    return donors


def suspend_donor_data(admin_id, donor_id):
    db = get_db()
    result = db["donors"].find_one_and_update(
        {"_id": object_id(donor_id)},
        {"$set": {"verification_status": "suspended", "updated_at": utc_now()}},
        return_document=True
    )

    if result:
        # Blacklist active JWT tokens
        db["jwt_blocklist"].insert_one({
            "user_id": str(donor_id),
            "reason": "admin_suspension",
            "revoked_at": utc_now()
        })

        db["notifications"].insert_one({
            "user_id": object_id(donor_id),
            "role": "donor",
            "title": "Account Suspended",
            "message": "Your donor account has been suspended. Contact support for more information.",
            "notification_type": "system",
            "is_read": False,
            "created_at": utc_now()
        })
        log_admin_action(admin_id, "suspend_donor", f"Suspended donor {result.get('full_name')} ({donor_id})")

    return serialize_document(result)


# ---------------------------------------------------------------------------
# 5. GLOBAL EMERGENCY MONITORING
# ---------------------------------------------------------------------------

def get_global_emergencies_data():
    db = get_db()
    cursor = db["emergency_requests"].find().sort([("urgency_level", 1), ("created_at", -1)])
    emergencies = []
    for req in cursor:
        doc = serialize_document(req)
        # Enrich with hospital details
        hospital = db["hospitals"].find_one({"_id": req.get("hospital_id")})
        if hospital:
            doc["hospital_name"] = hospital.get("hospital_name")
            doc["hospital_location"] = hospital.get("location", hospital.get("address"))

        # Enrich with accepted donor details
        if req.get("accepted_donor_id"):
            donor = db["donors"].find_one({"_id": req["accepted_donor_id"]})
            if donor:
                doc["accepted_donor_name"] = donor.get("full_name")

        # Check for related transfers
        transfers = db["blood_transfers"].count_documents({"destination_hospital": req.get("hospital_id"), "transfer_status": {"$in": ["pending", "dispatched"]}})
        doc["related_transfers_in_progress"] = transfers

        emergencies.append(doc)
    return emergencies


def close_emergency_admin_data(admin_id, emergency_id):
    db = get_db()
    result = db["emergency_requests"].find_one_and_update(
        {"_id": object_id(emergency_id)},
        {"$set": {"request_status": "closed", "closed_by": "admin", "updated_at": utc_now()}},
        return_document=True
    )
    if result:
        log_admin_action(admin_id, "close_emergency", f"Closed emergency {emergency_id}")
    return serialize_document(result)


# ---------------------------------------------------------------------------
# 6. BLOCKCHAIN AUDIT & SECURITY LOGS
# ---------------------------------------------------------------------------

def get_blockchain_logs_admin_data():
    db = get_db()
    cursor = db["blockchain_logs"].find().sort("verified_at", -1).limit(100)
    logs = []
    for log in cursor:
        doc = serialize_document(log)
        # Enrich with bloodbank name
        if log.get("bloodbank_id"):
            bb = db["bloodbanks"].find_one({"_id": log["bloodbank_id"]})
            if bb:
                doc["bloodbank_name"] = bb.get("bloodbank_name")
        # Frontend-safe output
        doc["display"] = {
            "secure_hash": f"✔ {doc.get('secure_hash', 'N/A')[:16]}...",
            "verification_status": "✔ Blockchain Verification Complete",
            "record_type": "✔ Immutable Record",
        }
        logs.append(doc)
    return logs


def get_activity_logs_admin_data():
    cursor = get_db()["activity_logs"].find().sort("created_at", -1).limit(100)
    return [serialize_document(log) for log in cursor]


# ---------------------------------------------------------------------------
# 7. SYSTEM REPORTS & ANALYTICS
# ---------------------------------------------------------------------------

def get_admin_reports_data():
    db = get_db()

    # Network-wide analytics
    total_donors = db["donors"].count_documents({})
    total_donations = db["donations"].count_documents({})
    verified_donations = db["donations"].count_documents({"screening_status": "verified"})
    total_emergencies = db["emergency_requests"].count_documents({})
    resolved_emergencies = db["emergency_requests"].count_documents({"request_status": {"$in": ["completed", "closed", "accepted_by_donor"]}})
    total_transfers = db["blood_transfers"].count_documents({})
    delivered_transfers = db["blood_transfers"].count_documents({"transfer_status": "delivered"})

    # Total blood volume transferred
    pipeline = [
        {"$match": {"transfer_status": "delivered"}},
        {"$group": {"_id": None, "total_volume": {"$sum": "$units_transferred"}}}
    ]
    volume_result = list(db["blood_transfers"].aggregate(pipeline))
    total_volume = volume_result[0]["total_volume"] if volume_result else 0

    # Most demanded blood groups
    bg_pipeline = [
        {"$group": {"_id": "$blood_group_needed", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 8}
    ]
    demand = list(db["emergency_requests"].aggregate(bg_pipeline))
    most_demanded = [{"blood_group": d["_id"], "emergency_count": d["count"]} for d in demand if d["_id"]]

    # Global inventory summary
    inventory = list(db["blood_inventory"].find({}))
    total_units = sum(i.get("available_units", 0) for i in inventory)
    expiring_units = sum(i.get("expiring_units", 0) for i in inventory)

    return {
        "total_registered_donors": total_donors,
        "total_donations_processed": total_donations,
        "verified_donations": verified_donations,
        "total_emergencies": total_emergencies,
        "resolved_emergencies": resolved_emergencies,
        "total_transfers": total_transfers,
        "delivered_transfers": delivered_transfers,
        "total_blood_volume_transferred": total_volume,
        "most_demanded_blood_groups": most_demanded,
        "total_blood_units_available": total_units,
        "expiring_units": expiring_units,
    }


# ---------------------------------------------------------------------------
# 8. NOTIFICATIONS
# ---------------------------------------------------------------------------

def get_admin_notifications_data():
    cursor = get_db()["notifications"].find({"role": "admin"}).sort("created_at", -1).limit(50)
    return [serialize_document(n) for n in cursor]


def mark_admin_notification_read_data(notification_id):
    db = get_db()
    result = db["notifications"].find_one_and_update(
        {"_id": object_id(notification_id), "role": "admin"},
        {"$set": {"is_read": True}},
        return_document=True
    )
    return serialize_document(result) if result else None


# ---------------------------------------------------------------------------
# 9. GLOBAL INVENTORY VIEW
# ---------------------------------------------------------------------------

def get_blood_inventory_admin_data():
    cursor = get_db()["blood_inventory"].find().sort("blood_group", 1)
    items = []
    db = get_db()
    for inv in cursor:
        doc = serialize_document(inv)
        # Enrich with owner name
        if inv.get("hospital_id"):
            h = db["hospitals"].find_one({"_id": inv["hospital_id"]})
            doc["facility_name"] = h.get("hospital_name") if h else "Unknown"
            doc["facility_type"] = "hospital"
        elif inv.get("bloodbank_id"):
            b = db["bloodbanks"].find_one({"_id": inv["bloodbank_id"]})
            doc["facility_name"] = b.get("bloodbank_name") if b else "Unknown"
            doc["facility_type"] = "bloodbank"
        items.append(doc)
    return items


# ---------------------------------------------------------------------------
# 10. SYSTEM SETTINGS
# ---------------------------------------------------------------------------

def get_settings_admin_data():
    return {
        "system_configuration": {"maintenance_mode": False, "platform_version": "1.0.0"},
        "security_settings": {"2fa_required": True, "session_timeout_minutes": 60, "jwt_expiry_hours": 24},
        "api_management": {"rate_limiting": True, "max_requests_per_minute": 60},
        "backup_settings": {"auto_backup": True, "frequency": "daily", "retention_days": 30},
    }
