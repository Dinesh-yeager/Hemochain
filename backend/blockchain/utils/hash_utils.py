"""
SHA-256 Cryptographic Hashing Utilities
=======================================
Generates tamper-proof hashes for all healthcare verification events.
No sensitive medical data is stored on-chain — only verification metadata.
"""

import hashlib
import json
from datetime import datetime, timezone


def generate_secure_hash(data: dict) -> str:
    """Generate a deterministic SHA-256 hash from a dictionary of verification data."""
    # Sort keys for deterministic hashing
    canonical = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def generate_block_hash(index: int, timestamp: str, data: dict, previous_hash: str, nonce: int) -> str:
    """Generate the hash of a block in the chain."""
    block_string = f"{index}{timestamp}{json.dumps(data, sort_keys=True, default=str)}{previous_hash}{nonce}"
    return hashlib.sha256(block_string.encode("utf-8")).hexdigest()


def generate_verification_hash(event_type: str, reference_id: str, verifier_id: str) -> str:
    """Generate a verification-specific hash for audit trails."""
    payload = {
        "event_type": event_type,
        "reference_id": str(reference_id),
        "verifier_id": str(verifier_id),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return generate_secure_hash(payload)


def generate_transfer_hash(source: str, destination: str, blood_group: str, units: int) -> str:
    """Generate a chain-of-custody hash for blood transfers."""
    payload = {
        "source": str(source),
        "destination": str(destination),
        "blood_group": blood_group,
        "units": units,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return generate_secure_hash(payload)


def verify_hash_integrity(data: dict, expected_hash: str) -> bool:
    """Verify that a stored hash matches the recalculated hash for tamper detection."""
    return generate_secure_hash(data) == expected_hash
