import os
import sys
from pathlib import Path

# Ensure backend imports resolve
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from backend.app import create_app
from backend.database.db import get_db, utc_now, REQUIRED_COLLECTIONS
from backend.utils.extensions import bcrypt
from backend.utils.security import normalize_email

app = create_app()


def seed_mock_users():
    with app.app_context():
        db = get_db()
        password = "asdfghjkl"
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        # ── STEP 1: Wipe all existing data ──
        print("🗑️  Wiping all existing data...")
        all_collections = list(REQUIRED_COLLECTIONS) + [
            "jwt_blocklist",
            "blockchain_blocks",
        ]
        for col_name in all_collections:
            count = db[col_name].count_documents({})
            db[col_name].delete_many({})
            if count > 0:
                print(f"   Cleared {col_name}: {count} documents removed")
        print("   ✅ Database wiped clean.\n")

        # ── STEP 2: Seed exactly 1 of each role ──
        users = [
            {
                "collection": "donors",
                "role": "donor",
                "data": {
                    "full_name": "Mock Donor",
                    "email": normalize_email("donor@gmail.com"),
                    "phone": "1234567890",
                    "blood_group": "O+",
                    "gender": "male",
                    "age": 25,
                    "address": "123 Donor St, New York",
                    "location": "New York",
                    "password": hashed_password,
                    "role": "donor",
                    "eligible_to_donate": True,
                    "verification_status": "verified",
                    "last_donation_date": None,
                    "profile_image": None,
                    "created_at": utc_now(),
                    "updated_at": utc_now()
                }
            },
            {
                "collection": "hospitals",
                "role": "hospital",
                "data": {
                    "hospital_name": "Mock Hospital",
                    "email": normalize_email("hospital@gmail.com"),
                    "registration_id": "HOSP-001",
                    "phone": "1234567890",
                    "address": "123 Hospital St",
                    "location": "New York",
                    "password": hashed_password,
                    "role": "hospital",
                    "verified_status": "verified",
                    "created_at": utc_now(),
                    "updated_at": utc_now()
                }
            },
            {
                "collection": "bloodbanks",
                "role": "bloodbank",
                "data": {
                    "bloodbank_name": "Mock Blood Bank",
                    "email": normalize_email("bloodbank@gmail.com"),
                    "registration_id": "BB-001",
                    "storage_capacity": 5000,
                    "phone": "1234567890",
                    "address": "456 BloodBank Ave",
                    "location": "New York",
                    "password": hashed_password,
                    "role": "bloodbank",
                    "verified_status": "verified",
                    "created_at": utc_now(),
                    "updated_at": utc_now()
                }
            },
            {
                "collection": "admins",
                "role": "admin",
                "data": {
                    "admin_name": "Mock Admin",
                    "email": normalize_email("admin@gmail.com"),
                    "password": hashed_password,
                    "role": "super_admin",
                    "access_level": 1,
                    "created_at": utc_now(),
                    "updated_at": utc_now()
                }
            }
        ]

        print("🌱 Seeding fresh users...")
        for u in users:
            db[u["collection"]].insert_one(u["data"])
            email = u["data"]["email"]
            print(f"   [+] Created {u['role'].title()}: {email} (Password: {password})")

        print(f"\n✅ Database reset complete!")
        print(f"   • 1 Donor    → donor@gmail.com")
        print(f"   • 1 Hospital → hospital@gmail.com")
        print(f"   • 1 BloodBank→ bloodbank@gmail.com")
        print(f"   • 1 Admin    → admin@gmail.com")
        print(f"   • Password   → {password}")


if __name__ == "__main__":
    seed_mock_users()
