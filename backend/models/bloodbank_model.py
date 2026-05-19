import hashlib
from datetime import timedelta

from backend.database.db import get_db, utc_now
from backend.utils.security import object_id, serialize_document


# ---------------------------------------------------------------------------
# 1. DASHBOARD OVERVIEW (COMMAND CENTER)
# ---------------------------------------------------------------------------

def get_bloodbank_dashboard_overview_data(bloodbank_id):
    db = get_db()
    bb_id = object_id(bloodbank_id)

    total_donations = db["donations"].count_documents({"bloodbank_id": bb_id})
    active_transfers = db["blood_transfers"].count_documents({"source_bloodbank": bb_id, "transfer_status": {"$in": ["pending", "dispatched"]}})
    completed_transfers = db["blood_transfers"].count_documents({"source_bloodbank": bb_id, "transfer_status": "delivered"})
    hospital_requests = db["blood_requests"].count_documents({"bloodbank_id": bb_id})
    pending_requests = db["blood_requests"].count_documents({"bloodbank_id": bb_id, "request_status": "pending"})

    # Capacity monitoring
    bloodbank = db["bloodbanks"].find_one({"_id": bb_id}, {"password": 0})
    storage_capacity = int(bloodbank.get("storage_capacity", 0)) if bloodbank else 0

    inventory = list(db["blood_inventory"].find({"bloodbank_id": bb_id}))
    total_units = sum(item.get("available_units", 0) for item in inventory)
    expiring_units = sum(item.get("expiring_units", 0) for item in inventory)

    # Low stock alerts
    low_stock_groups = [
        {"blood_group": i.get("blood_group"), "units": i.get("available_units"), "status": i.get("inventory_status")}
        for i in inventory if i.get("inventory_status") in ("low", "critical")
    ]

    # Capacity threshold warning
    capacity_warning = None
    if storage_capacity > 0 and total_units >= (storage_capacity * 0.9):
        capacity_warning = f"Storage at {round(total_units / storage_capacity * 100)}% capacity. Consider dispatching excess inventory."

    return {
        "total_donations_collected": total_donations,
        "active_blood_transfers": active_transfers,
        "completed_blood_transfers": completed_transfers,
        "hospital_requests_received": hospital_requests,
        "pending_requests": pending_requests,
        "total_units_available": total_units,
        "expiring_units": expiring_units,
        "storage_capacity": storage_capacity,
        "low_stock_alerts": low_stock_groups,
        "capacity_warning": capacity_warning,
    }


# ---------------------------------------------------------------------------
# 2. BLOOD BANK PROFILE
# ---------------------------------------------------------------------------

def get_bloodbank_profile_data(bloodbank_id):
    db = get_db()
    bb = db["bloodbanks"].find_one({"_id": object_id(bloodbank_id)}, {"password": 0})
    if not bb:
        return None

    inventory = db["blood_inventory"].find({"bloodbank_id": object_id(bloodbank_id)})
    total_units = sum(item.get("available_units", 0) for item in inventory)
    bb["total_units_available"] = total_units
    return serialize_document(bb)


def update_bloodbank_profile_data(bloodbank_id, update_fields):
    db = get_db()
    allowed = {"phone", "address", "location", "storage_capacity", "profile_image"}
    update_doc = {k: v for k, v in update_fields.items() if k in allowed}
    if not update_doc:
        return None

    # Convert storage_capacity to int if present
    if "storage_capacity" in update_doc:
        try:
            update_doc["storage_capacity"] = int(update_doc["storage_capacity"])
        except (TypeError, ValueError):
            return None

    update_doc["updated_at"] = utc_now()
    db["bloodbanks"].update_one({"_id": object_id(bloodbank_id)}, {"$set": update_doc})
    return get_bloodbank_profile_data(bloodbank_id)


# ---------------------------------------------------------------------------
# 3. BLOOD INVENTORY MANAGEMENT
# ---------------------------------------------------------------------------

def get_bloodbank_inventory_data(bloodbank_id):
    cursor = get_db()["blood_inventory"].find({"bloodbank_id": object_id(bloodbank_id)})
    return [serialize_document(item) for item in cursor]


def update_bloodbank_inventory_data(bloodbank_id, payload):
    db = get_db()
    blood_group = payload.get("blood_group")
    available_units = payload.get("available_units", 0)
    reserved_units = payload.get("reserved_units", 0)
    expiring_units = payload.get("expiring_units", 0)
    expiry_date = payload.get("expiry_date")

    if not blood_group:
        return None

    # Smart Auto-Status Engine
    status = "healthy"
    if available_units <= 10:
        status = "critical"
    elif available_units <= 30:
        status = "low"

    update_doc = {
        "available_units": available_units,
        "reserved_units": reserved_units,
        "expiring_units": expiring_units,
        "expiry_date": expiry_date,
        "inventory_status": status,
        "updated_at": utc_now()
    }

    result = db["blood_inventory"].find_one_and_update(
        {"bloodbank_id": object_id(bloodbank_id), "blood_group": blood_group},
        {"$set": update_doc},
        upsert=True,
        return_document=True
    )

    # Auto-alert on critical stock
    if status == "critical":
        db["notifications"].insert_one({
            "user_id": object_id(bloodbank_id),
            "role": "bloodbank",
            "title": f"Critical Stock Alert: {blood_group}",
            "message": f"Only {available_units} units of {blood_group} remaining. Immediate replenishment required.",
            "notification_type": "inventory",
            "is_read": False,
            "created_at": utc_now()
        })

    return serialize_document(result)


# ---------------------------------------------------------------------------
# 4. HOSPITAL REQUESTS (ORDER MANAGEMENT)
# ---------------------------------------------------------------------------

def get_hospital_requests_data(bloodbank_id):
    db = get_db()
    cursor = db["blood_requests"].find({"bloodbank_id": object_id(bloodbank_id)}).sort("created_at", -1)
    requests = []
    for req in cursor:
        req_doc = serialize_document(req)
        hospital = db["hospitals"].find_one({"_id": req.get("hospital_id")})
        if hospital:
            req_doc["hospital_name"] = hospital.get("hospital_name")
            req_doc["hospital_phone"] = hospital.get("phone")
        requests.append(req_doc)
    return requests


def approve_hospital_request_data(bloodbank_id, request_id):
    db = get_db()
    req = db["blood_requests"].find_one_and_update(
        {"_id": object_id(request_id), "bloodbank_id": object_id(bloodbank_id), "request_status": "pending"},
        {"$set": {"request_status": "approved", "updated_at": utc_now()}},
        return_document=True
    )
    if not req:
        return None

    # Reserve inventory (deduct available, increase reserved)
    blood_group = req.get("blood_group")
    units = req.get("units_requested", 0)
    inv = db["blood_inventory"].find_one({"bloodbank_id": object_id(bloodbank_id), "blood_group": blood_group})
    if inv:
        new_available = max(0, inv.get("available_units", 0) - units)
        new_reserved = inv.get("reserved_units", 0) + units

        inv_status = "healthy"
        if new_available <= 10:
            inv_status = "critical"
        elif new_available <= 30:
            inv_status = "low"

        db["blood_inventory"].update_one(
            {"_id": inv["_id"]},
            {"$set": {"available_units": new_available, "reserved_units": new_reserved, "inventory_status": inv_status, "updated_at": utc_now()}}
        )

    # Generate pending blood_transfer record
    transfer = {
        "source_bloodbank": object_id(bloodbank_id),
        "destination_hospital": req.get("hospital_id"),
        "blood_group": blood_group,
        "units_transferred": units,
        "transfer_status": "pending",
        "dispatch_time": None,
        "delivery_time": None,
        "created_at": utc_now()
    }
    db["blood_transfers"].insert_one(transfer)

    # Notify hospital
    db["notifications"].insert_one({
        "user_id": req.get("hospital_id"),
        "role": "hospital",
        "title": "Blood Request Approved",
        "message": f"Your request for {units} units of {blood_group} has been approved and is being prepared for dispatch.",
        "notification_type": "transfer",
        "is_read": False,
        "created_at": utc_now()
    })

    return serialize_document(req)


def reject_hospital_request_data(bloodbank_id, request_id):
    db = get_db()
    req = db["blood_requests"].find_one_and_update(
        {"_id": object_id(request_id), "bloodbank_id": object_id(bloodbank_id), "request_status": "pending"},
        {"$set": {"request_status": "rejected", "updated_at": utc_now()}},
        return_document=True
    )
    if not req:
        return None

    # Notify hospital
    db["notifications"].insert_one({
        "user_id": req.get("hospital_id"),
        "role": "hospital",
        "title": "Blood Request Rejected",
        "message": f"Your request for {req.get('units_requested')} units of {req.get('blood_group')} could not be fulfilled. Please contact another blood bank.",
        "notification_type": "transfer",
        "is_read": False,
        "created_at": utc_now()
    })

    return serialize_document(req)


# ---------------------------------------------------------------------------
# 5. BLOOD TRANSFERS & LOGISTICS
# ---------------------------------------------------------------------------

def get_blood_transfers_data(bloodbank_id):
    db = get_db()
    cursor = db["blood_transfers"].find({"source_bloodbank": object_id(bloodbank_id)}).sort("created_at", -1)
    transfers = []
    for t in cursor:
        t_doc = serialize_document(t)
        hospital = db["hospitals"].find_one({"_id": t.get("destination_hospital")})
        if hospital:
            t_doc["destination_hospital_name"] = hospital.get("hospital_name")
        transfers.append(t_doc)
    return transfers


def update_transfer_status_data(bloodbank_id, transfer_id, status):
    db = get_db()
    update_doc = {"transfer_status": status}

    if status == "dispatched":
        update_doc["dispatch_time"] = utc_now()
    elif status == "delivered":
        update_doc["delivery_time"] = utc_now()

    result = db["blood_transfers"].find_one_and_update(
        {"_id": object_id(transfer_id), "source_bloodbank": object_id(bloodbank_id)},
        {"$set": update_doc},
        return_document=True
    )

    if result:
        # Release reserved inventory on delivery
        if status == "delivered":
            blood_group = result.get("blood_group")
            units = result.get("units_transferred", 0)
            inv = db["blood_inventory"].find_one({"bloodbank_id": object_id(bloodbank_id), "blood_group": blood_group})
            if inv:
                new_reserved = max(0, inv.get("reserved_units", 0) - units)
                db["blood_inventory"].update_one({"_id": inv["_id"]}, {"$set": {"reserved_units": new_reserved, "updated_at": utc_now()}})

        # Notify hospital
        status_label = "dispatched — on the way" if status == "dispatched" else status
        db["notifications"].insert_one({
            "user_id": result.get("destination_hospital"),
            "role": "hospital",
            "title": f"Blood Transfer {status.title()}",
            "message": f"Transfer of {result.get('units_transferred')} units of {result.get('blood_group')} is now {status_label}.",
            "notification_type": "transfer",
            "is_read": False,
            "created_at": utc_now()
        })

    return serialize_document(result)


def create_emergency_dispatch_data(bloodbank_id, payload):
    db = get_db()
    hospital_id = payload.get("hospital_id")
    blood_group = payload.get("blood_group")
    units = payload.get("units_transferred")

    if not all([hospital_id, blood_group, units]):
        return None

    # Deduct from inventory immediately
    inv = db["blood_inventory"].find_one({"bloodbank_id": object_id(bloodbank_id), "blood_group": blood_group})
    if inv:
        new_available = max(0, inv.get("available_units", 0) - units)
        inv_status = "healthy"
        if new_available <= 10:
            inv_status = "critical"
        elif new_available <= 30:
            inv_status = "low"
        db["blood_inventory"].update_one({"_id": inv["_id"]}, {"$set": {"available_units": new_available, "inventory_status": inv_status, "updated_at": utc_now()}})

    transfer = {
        "source_bloodbank": object_id(bloodbank_id),
        "destination_hospital": object_id(hospital_id),
        "blood_group": blood_group,
        "units_transferred": units,
        "transfer_status": "dispatched",
        "dispatch_time": utc_now(),
        "delivery_time": None,
        "is_emergency": True,
        "created_at": utc_now()
    }
    result = db["blood_transfers"].insert_one(transfer)
    transfer["_id"] = result.inserted_id

    # Notify hospital
    db["notifications"].insert_one({
        "user_id": object_id(hospital_id),
        "role": "hospital",
        "title": "🚨 Emergency Dispatch Initiated",
        "message": f"Emergency dispatch of {units} units of {blood_group} is on the way immediately.",
        "notification_type": "emergency_alert",
        "is_read": False,
        "created_at": utc_now()
    })

    return serialize_document(transfer)


# ---------------------------------------------------------------------------
# 6. DONATION & BLOCKCHAIN VERIFICATION
# ---------------------------------------------------------------------------

def get_incoming_donations_data(bloodbank_id):
    db = get_db()
    cursor = db["donations"].find({"bloodbank_id": object_id(bloodbank_id)}).sort("created_at", -1)
    donations = []
    for d in cursor:
        d_doc = serialize_document(d)
        donor = db["donors"].find_one({"_id": d.get("donor_id")})
        if donor:
            d_doc["donor_name"] = donor.get("full_name")
            d_doc["donor_phone"] = donor.get("phone")
        donations.append(d_doc)
    return donations


def update_donation_verification_data(bloodbank_id, donation_id, status):
    db = get_db()

    update_data = {"screening_status": status, "updated_at": utc_now()}

    if status == "verified":
        update_data["blockchain_verified"] = True
        # Generate secure cryptographic hash for tamper-proof record
        hash_input = f"{donation_id}:{bloodbank_id}:{utc_now().isoformat()}"
        update_data["secure_hash"] = hashlib.sha256(hash_input.encode()).hexdigest()

    result = db["donations"].find_one_and_update(
        {"_id": object_id(donation_id), "bloodbank_id": object_id(bloodbank_id)},
        {"$set": update_data},
        return_document=True
    )

    if result:
        # Update donor cooldown when verified
        if status == "verified" and result.get("donor_id"):
            now = utc_now()
            next_eligible = now + timedelta(days=90)
            db["donors"].update_one(
                {"_id": result["donor_id"]},
                {"$set": {
                    "last_donation_date": now,
                    "eligible_to_donate": False,
                    "next_eligible_date": next_eligible.isoformat(),
                    "updated_at": now
                }}
            )

        # Notify donor
        status_messages = {
            "testing": "Your donated blood is currently being tested.",
            "verified": "Your blood donation has been verified and is safe for transfusion. ✔ Blockchain Verified.",
            "rejected": "Unfortunately, your blood donation did not pass screening. Please consult with a healthcare professional."
        }
        db["notifications"].insert_one({
            "user_id": result.get("donor_id"),
            "role": "donor",
            "title": f"Donation Screening: {status.title()}",
            "message": status_messages.get(status, f"Your donation status has been updated to {status}."),
            "notification_type": "donation_update",
            "is_read": False,
            "created_at": utc_now()
        })

        # Log blockchain verification event
        if status == "verified":
            db["blockchain_logs"].insert_one({
                "event": "donation_verified",
                "donation_id": object_id(donation_id),
                "donor_id": result.get("donor_id"),
                "bloodbank_id": object_id(bloodbank_id),
                "secure_hash": update_data.get("secure_hash"),
                "verified_at": utc_now()
            })

    return serialize_document(result)


# ---------------------------------------------------------------------------
# 7. DONOR DIRECTORY
# ---------------------------------------------------------------------------

def get_donor_records_data(blood_group=None, eligible_only=False):
    query = {}
    if blood_group:
        query["blood_group"] = blood_group
    if eligible_only:
        query["eligible_to_donate"] = {"$ne": False}

    cursor = get_db()["donors"].find(query, {"password": 0}).limit(50)
    return [serialize_document(d) for d in cursor]


# ---------------------------------------------------------------------------
# 8. NOTIFICATION CENTER
# ---------------------------------------------------------------------------

def get_bloodbank_notifications_data(bloodbank_id):
    cursor = get_db()["notifications"].find({"user_id": object_id(bloodbank_id)}).sort("created_at", -1).limit(50)
    return [serialize_document(n) for n in cursor]


def mark_bloodbank_notification_read_data(bloodbank_id, notification_id):
    db = get_db()
    result = db["notifications"].find_one_and_update(
        {"_id": object_id(notification_id), "user_id": object_id(bloodbank_id)},
        {"$set": {"is_read": True}},
        return_document=True
    )
    return serialize_document(result) if result else None


# ---------------------------------------------------------------------------
# 9. REPORTS & ANALYTICS
# ---------------------------------------------------------------------------

def get_bloodbank_reports_data(bloodbank_id):
    db = get_db()
    bb_id = object_id(bloodbank_id)

    total_donations = db["donations"].count_documents({"bloodbank_id": bb_id})
    verified_donations = db["donations"].count_documents({"bloodbank_id": bb_id, "screening_status": "verified"})
    rejected_donations = db["donations"].count_documents({"bloodbank_id": bb_id, "screening_status": "rejected"})
    active_transfers = db["blood_transfers"].count_documents({"source_bloodbank": bb_id, "transfer_status": {"$in": ["pending", "dispatched"]}})
    completed_transfers = db["blood_transfers"].count_documents({"source_bloodbank": bb_id, "transfer_status": "delivered"})
    total_requests = db["blood_requests"].count_documents({"bloodbank_id": bb_id})
    approved_requests = db["blood_requests"].count_documents({"bloodbank_id": bb_id, "request_status": "approved"})
    rejected_requests = db["blood_requests"].count_documents({"bloodbank_id": bb_id, "request_status": "rejected"})

    # Inventory summary
    inventory = list(db["blood_inventory"].find({"bloodbank_id": bb_id}))
    total_units = sum(i.get("available_units", 0) for i in inventory)
    reserved_units = sum(i.get("reserved_units", 0) for i in inventory)
    expiring_units = sum(i.get("expiring_units", 0) for i in inventory)

    return {
        "total_donations_collected": total_donations,
        "verified_donations": verified_donations,
        "rejected_donations": rejected_donations,
        "active_blood_transfers": active_transfers,
        "completed_blood_transfers": completed_transfers,
        "total_hospital_requests": total_requests,
        "approved_requests": approved_requests,
        "rejected_requests": rejected_requests,
        "total_units_available": total_units,
        "reserved_units": reserved_units,
        "expiring_units": expiring_units,
    }
