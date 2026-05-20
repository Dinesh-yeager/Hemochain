"""
HemoChain — Complete Database Seed Script
==========================================
Clears ALL existing data and seeds clean, realistic demo accounts
for the Chennai-based Hemo Chain platform.

Usage:
    python backend/seed.py          (from project root)
    python seed.py                  (from backend/)

Login Credentials (all accounts):
    Password: asdfghjkl

    admin@gmail.com      → /admin-dashboard
    donor@gmail.com      → /donor-dashboard
    hospital@gmail.com   → /hospital-dashboard
    bloodbank@gmail.com  → /bloodbank-dashboard
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ── Ensure imports resolve from project root ──
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from backend.app import create_app
from backend.database.db import get_db, utc_now, REQUIRED_COLLECTIONS
from backend.utils.extensions import bcrypt
from backend.utils.security import normalize_email

app = create_app()

# ── All collections to wipe ──
COLLECTIONS_TO_CLEAR = list(REQUIRED_COLLECTIONS) + [
    "jwt_blocklist",
    "blockchain_blocks",
    "reports",
]


def seed():
    with app.app_context():
        db = get_db()

        # Shared password for all accounts
        password = "asdfghjkl"
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        now = utc_now()

        # ================================================================
        # STEP 1 — Clear all existing data
        # ================================================================
        print("\n🗑️  Clearing all existing data...")
        for col_name in COLLECTIONS_TO_CLEAR:
            count = db[col_name].count_documents({})
            if count > 0:
                db[col_name].delete_many({})
                print(f"   Cleared {col_name}: {count} documents removed")
        print("   ✔ Existing data cleared\n")

        # ================================================================
        # STEP 2 — Seed Admin
        # ================================================================
        admin_doc = {
            "admin_name": "HemoChain Super Admin",
            "email": normalize_email("admin@gmail.com"),
            "password": hashed_password,
            "role": "admin",
            "access_level": "super_admin",
            "contact_number": "+91 9876543210",
            "created_at": now,
            "updated_at": now,
        }
        admin_result = db["admins"].insert_one(admin_doc)
        admin_id = admin_result.inserted_id
        print("   ✔ Admin seeded: admin@gmail.com")

        # ================================================================
        # STEP 3 — Seed Donor
        # ================================================================
        donor_doc = {
            "full_name": "Dinesh Kumar",
            "email": normalize_email("donor@gmail.com"),
            "phone": "+91 9123456780",
            "blood_group": "O+",
            "gender": "Male",
            "age": 21,
            "location": "Chennai",
            "address": "Anna Nagar, Chennai",
            "password": hashed_password,
            "eligible_to_donate": True,
            "total_donations": 3,
            "verification_status": "verified",
            "last_donation_date": "2025-12-01",
            "next_eligible_date": "2026-03-01",
            "role": "donor",
            "profile_image": None,
            "emergency_responses": 1,
            "created_at": now,
            "updated_at": now,
        }
        donor_result = db["donors"].insert_one(donor_doc)
        donor_id = donor_result.inserted_id
        print("   ✔ Donor seeded: donor@gmail.com")

        # ================================================================
        # STEP 4 — Seed Hospital
        # ================================================================
        hospital_doc = {
            "hospital_name": "Apollo Hospitals Chennai",
            "email": normalize_email("hospital@gmail.com"),
            "registration_id": "HOSP-CHN-001",
            "phone": "+91 9444444444",
            "address": "Greams Road, Chennai",
            "location": "Chennai",
            "emergency_contact": "+91 9555555555",
            "password": hashed_password,
            "verified_status": "verified",
            "suspension_status": False,
            "role": "hospital",
            "created_at": now,
            "updated_at": now,
        }
        hospital_result = db["hospitals"].insert_one(hospital_doc)
        hospital_id = hospital_result.inserted_id
        print("   ✔ Hospital seeded: hospital@gmail.com")

        # ================================================================
        # STEP 5 — Seed Blood Bank
        # ================================================================
        bloodbank_doc = {
            "bloodbank_name": "Chennai Central Blood Bank",
            "email": normalize_email("bloodbank@gmail.com"),
            "registration_id": "BB-CHN-001",
            "phone": "+91 9333333333",
            "address": "T Nagar, Chennai",
            "location": "Chennai",
            "storage_capacity": 1500,
            "password": hashed_password,
            "verified_status": "verified",
            "suspension_status": False,
            "role": "bloodbank",
            "created_at": now,
            "updated_at": now,
        }
        bloodbank_result = db["bloodbanks"].insert_one(bloodbank_doc)
        bloodbank_id = bloodbank_result.inserted_id
        print("   ✔ Blood bank seeded: bloodbank@gmail.com")

        # ================================================================
        # STEP 6 — Seed Blood Inventory
        # ================================================================
        inventory_items = [
            {"blood_group": "A+",  "available_units": 50, "facility_name": "Chennai Central Blood Bank"},
            {"blood_group": "B+",  "available_units": 35, "facility_name": "Chennai Central Blood Bank"},
            {"blood_group": "O+",  "available_units": 80, "facility_name": "Chennai Central Blood Bank"},
            {"blood_group": "AB+", "available_units": 20, "facility_name": "Chennai Central Blood Bank"},
        ]
        for item in inventory_items:
            item["bloodbank_id"] = bloodbank_id
            item["hospital_id"] = hospital_id
            item["inventory_status"] = "healthy" if item["available_units"] >= 30 else "low"
            item["last_updated"] = now
            item["created_at"] = now
        db["blood_inventory"].insert_many(inventory_items)
        print("   ✔ Inventory seeded: A+, B+, O+, AB+")

        # ================================================================
        # STEP 7 — Seed Emergency Request
        # ================================================================
        emergency_doc = {
            "hospital_id": hospital_id,
            "hospital_name": "Apollo Hospitals Chennai",
            "blood_group_needed": "O+",
            "units_needed": 3,
            "units_required": 3,
            "urgency_level": "critical",
            "request_status": "active",
            "location": "Chennai",
            "contact_number": "+91 9444444444",
            "created_at": now,
            "updated_at": now,
        }
        db["emergency_requests"].insert_one(emergency_doc)
        print("   ✔ Emergency request seeded: O+ critical")

        # ================================================================
        # STEP 8 — Seed Notifications
        # ================================================================
        notifications = [
            # ── Donor notifications ──
            {
                "user_id": donor_id,
                "role": "donor",
                "title": "Emergency Blood Request Nearby",
                "message": "Apollo Hospitals Chennai urgently needs O+ blood. You are a match!",
                "notification_type": "emergency_alert",
                "is_read": False,
                "created_at": now - timedelta(minutes=15),
            },
            {
                "user_id": donor_id,
                "role": "donor",
                "title": "Appointment Approved",
                "message": "Your blood donation appointment at Apollo Hospitals Chennai has been confirmed for next Monday.",
                "notification_type": "appointment",
                "is_read": False,
                "created_at": now - timedelta(hours=2),
            },
            {
                "user_id": donor_id,
                "role": "donor",
                "title": "Donation Milestone Reached",
                "message": "Congratulations! You have completed 3 successful donations. Thank you for saving lives!",
                "notification_type": "donation_update",
                "is_read": True,
                "created_at": now - timedelta(days=1),
            },
            # ── Hospital notifications ──
            {
                "user_id": hospital_id,
                "role": "hospital",
                "title": "Donor Accepted Emergency Request",
                "message": "A verified donor has accepted your critical O+ blood request. ETA: 30 minutes.",
                "notification_type": "emergency_alert",
                "is_read": False,
                "created_at": now - timedelta(minutes=10),
            },
            {
                "user_id": hospital_id,
                "role": "hospital",
                "title": "Inventory Low Alert",
                "message": "AB+ blood stock is running low (20 units). Consider placing a request to nearby blood banks.",
                "notification_type": "system",
                "is_read": False,
                "created_at": now - timedelta(hours=3),
            },
            {
                "user_id": hospital_id,
                "role": "hospital",
                "title": "New Appointment Request",
                "message": "A donor has booked a blood donation appointment for next Monday.",
                "notification_type": "appointment",
                "is_read": True,
                "created_at": now - timedelta(hours=6),
            },
            # ── Blood Bank notifications ──
            {
                "user_id": bloodbank_id,
                "role": "bloodbank",
                "title": "Blood Transfer Request",
                "message": "Apollo Hospitals Chennai has requested 3 units of O+ blood. Review and approve.",
                "notification_type": "system",
                "is_read": False,
                "created_at": now - timedelta(minutes=30),
            },
            {
                "user_id": bloodbank_id,
                "role": "bloodbank",
                "title": "Inventory Low Alert",
                "message": "AB+ stock is critically low at 20 units. Schedule donor drives or place inter-bank requests.",
                "notification_type": "system",
                "is_read": False,
                "created_at": now - timedelta(hours=4),
            },
            {
                "user_id": bloodbank_id,
                "role": "bloodbank",
                "title": "Blockchain Verification Complete",
                "message": "Transfer #TXN-2026-0519 has been verified and recorded on the blockchain.",
                "notification_type": "donation_update",
                "is_read": True,
                "created_at": now - timedelta(days=1),
            },
            # ── Admin notifications ──
            {
                "user_id": admin_id,
                "role": "admin",
                "title": "Critical Emergency Alert",
                "message": "Apollo Hospitals Chennai has raised a critical O+ blood emergency. 3 units required.",
                "notification_type": "emergency_alert",
                "is_read": False,
                "created_at": now - timedelta(minutes=20),
            },
            {
                "user_id": admin_id,
                "role": "admin",
                "title": "New Hospital Registered",
                "message": "Apollo Hospitals Chennai has been registered and verified on the platform.",
                "notification_type": "system",
                "is_read": False,
                "created_at": now - timedelta(hours=5),
            },
            {
                "user_id": admin_id,
                "role": "admin",
                "title": "Platform Security Update",
                "message": "All JWT tokens and blockchain records have been audited. No anomalies detected.",
                "notification_type": "system",
                "is_read": True,
                "created_at": now - timedelta(days=1),
            },
        ]
        db["notifications"].insert_many(notifications)
        print("   ✔ Notifications seeded: 12 notifications across all dashboards")

        # ================================================================
        # STEP 9 — Seed sample donation record
        # ================================================================
        donation_doc = {
            "donor_id": donor_id,
            "hospital_id": hospital_id,
            "hospital_name": "Apollo Hospitals Chennai",
            "blood_group": "O+",
            "units_donated": 1,
            "donation_date": "2025-12-01",
            "screening_status": "verified",
            "blockchain_verified": True,
            "created_at": now - timedelta(days=170),
        }
        db["donations"].insert_one(donation_doc)
        print("   ✔ Sample donation record seeded")

        # ================================================================
        # DONE
        # ================================================================
        print("\n" + "=" * 55)
        print("  ✔ Database seeding completed successfully")
        print("=" * 55)
        print(f"\n  📋 Login Credentials (Password: {password})")
        print("  ─────────────────────────────────────────")
        print("  Admin      → admin@gmail.com       → /admin-dashboard")
        print("  Donor      → donor@gmail.com       → /donor-dashboard")
        print("  Hospital   → hospital@gmail.com    → /hospital-dashboard")
        print("  Blood Bank → bloodbank@gmail.com   → /bloodbank-dashboard")
        print()


if __name__ == "__main__":
    seed()
