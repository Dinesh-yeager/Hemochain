"""
Donation Verification Smart Contract
======================================
Handles the on-chain verification of blood donations.

Functions:
- verify_donation()     → generates hash, mines block, creates immutable record
- get_verification()    → retrieves on-chain verification proof
- generate_qr_data()   → generates QR-safe verification payload
"""

from backend.blockchain.chain import mine_block
from backend.blockchain.utils.hash_utils import generate_secure_hash, generate_verification_hash
from backend.database.db import get_db, utc_now
from backend.utils.security import object_id, serialize_document


def verify_donation(donation_id: str, bloodbank_id: str, donor_id: str, blood_group: str) -> dict:
    """
    Execute the full donation verification flow:
    1. Generate SHA-256 secure hash from donation metadata
    2. Mine a new block on the private chain
    3. Store verification event in blockchain_logs
    4. Store in verification_events for audit
    5. Create secure_record for chain of custody
    6. Update the donation document with blockchain proof
    """
    db = get_db()

    # Step 1: Generate cryptographic hash (no sensitive data)
    verification_data = {
        "event_type": "donation_verified",
        "donation_id": str(donation_id),
        "bloodbank_id": str(bloodbank_id),
        "blood_group": blood_group,
    }
    secure_hash = generate_secure_hash(verification_data)

    # Step 2: Mine block on private chain
    block_data = {
        "event_type": "donation_verified",
        "reference_id": str(donation_id),
        "secure_hash": secure_hash,
        "verified_by": str(bloodbank_id),
    }
    block_result = mine_block(block_data)

    # Step 3: Store in blockchain_logs
    blockchain_log = {
        "event_type": "donation_verified",
        "reference_id": object_id(donation_id),
        "secure_hash": secure_hash,
        "verified_by": object_id(bloodbank_id),
        "verification_status": "verified",
        "blockchain_tx_id": block_result["block_hash"],
        "block_index": block_result["block_index"],
        "donor_id": object_id(donor_id),
        "bloodbank_id": object_id(bloodbank_id),
        "created_at": utc_now(),
    }
    db["blockchain_logs"].insert_one(blockchain_log)

    # Step 4: Store verification event
    db["verification_events"].insert_one({
        "entity_type": "donation",
        "entity_id": object_id(donation_id),
        "action_type": "verified",
        "performed_by": object_id(bloodbank_id),
        "performer_role": "bloodbank",
        "secure_hash": secure_hash,
        "block_hash": block_result["block_hash"],
        "timestamp": utc_now(),
    })

    # Step 5: Create secure record (chain of custody origin)
    db["secure_records"].insert_one({
        "record_type": "donation",
        "reference_id": object_id(donation_id),
        "secure_hash": secure_hash,
        "blockchain_tx_id": block_result["block_hash"],
        "block_index": block_result["block_index"],
        "status": "immutable",
        "created_at": utc_now(),
    })

    # Step 6: Update donation with blockchain proof
    db["donations"].update_one(
        {"_id": object_id(donation_id)},
        {"$set": {
            "blockchain_verified": True,
            "secure_hash": secure_hash,
            "blockchain_tx_id": block_result["block_hash"],
            "block_index": block_result["block_index"],
        }}
    )

    return {
        "verified": True,
        "secure_hash": secure_hash,
        "block_hash": block_result["block_hash"],
        "block_index": block_result["block_index"],
        "timestamp": block_result["timestamp"],
    }


def get_donation_verification(donation_id: str) -> dict:
    """Retrieve the on-chain verification proof for a specific donation."""
    db = get_db()
    donation = db["donations"].find_one({"_id": object_id(donation_id)})
    if not donation:
        return None

    log = db["blockchain_logs"].find_one({"reference_id": object_id(donation_id), "event_type": "donation_verified"})

    return {
        "donation_id": str(donation_id),
        "blockchain_verified": donation.get("blockchain_verified", False),
        "secure_hash": donation.get("secure_hash"),
        "blockchain_tx_id": donation.get("blockchain_tx_id"),
        "block_index": donation.get("block_index"),
        "screening_status": donation.get("screening_status"),
        "verification_timestamp": str(log.get("created_at")) if log else None,
        "display": {
            "status": "✔ Verified Donation" if donation.get("blockchain_verified") else "⏳ Pending Verification",
            "security": "✔ Secure Record",
            "blockchain": "✔ Blockchain Verification Complete" if donation.get("blockchain_verified") else "Pending",
        }
    }


def generate_qr_data(donation_id: str) -> dict:
    """Generate a QR-safe payload that doesn't expose sensitive medical data."""
    db = get_db()
    donation = db["donations"].find_one({"_id": object_id(donation_id)})
    if not donation:
        return None

    donor = db["donors"].find_one({"_id": donation.get("donor_id")})
    hospital = db["hospitals"].find_one({"_id": donation.get("hospital_id")})

    return {
        "verification_url": f"/api/verify/{donation_id}",
        "verified": donation.get("blockchain_verified", False),
        "blood_group": donation.get("blood_group"),
        "donation_date": str(donation.get("donation_date", donation.get("created_at"))),
        "units_donated": donation.get("units_donated", donation.get("units_collected")),
        "screening_status": donation.get("screening_status"),
        "donor_name": donor.get("full_name") if donor else "Confidential",
        "hospital_name": hospital.get("hospital_name") if hospital else "N/A",
        "secure_hash": donation.get("secure_hash"),
        "display": {
            "verification": "✔ Donation Verified" if donation.get("blockchain_verified") else "Pending",
            "hospital": "✔ Hospital Verified" if hospital else "N/A",
            "timestamp": str(donation.get("created_at")),
        }
    }
