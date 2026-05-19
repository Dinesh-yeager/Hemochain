"""
HemoChain Private Blockchain Engine
====================================
A permissioned, MongoDB-backed private blockchain for healthcare verification.

Architecture:
- Blocks are stored in the `blockchain_blocks` MongoDB collection.
- Each block contains an index, timestamp, verification data, previous_hash, nonce, and hash.
- The genesis block is auto-created on first initialization.
- Proof-of-work uses a lightweight difficulty (2 leading zeros) since this is a private chain.
- Chain integrity can be validated at any time via `validate_chain()`.

This is NOT a crypto mining system. The proof-of-work exists solely
to ensure computational commitment to block creation, preventing trivial tampering.
"""

import json
from datetime import datetime, timezone

from backend.blockchain.utils.hash_utils import generate_block_hash
from backend.database.db import get_db


DIFFICULTY = 2  # Leading zeros required in block hash (lightweight for private chain)


def _blocks_collection():
    return get_db()["blockchain_blocks"]


def _utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# GENESIS BLOCK
# ---------------------------------------------------------------------------

def _create_genesis_block():
    """Create the first block in the chain if it doesn't exist."""
    col = _blocks_collection()
    if col.count_documents({}) > 0:
        return

    genesis = {
        "index": 0,
        "timestamp": _utc_now_iso(),
        "data": {"event_type": "genesis", "message": "HemoChain Private Blockchain Initialized"},
        "previous_hash": "0" * 64,
        "nonce": 0,
        "hash": None,
    }
    genesis["hash"] = generate_block_hash(
        genesis["index"], genesis["timestamp"], genesis["data"], genesis["previous_hash"], genesis["nonce"]
    )
    col.insert_one(genesis)


def initialize_chain():
    """Ensure the blockchain is initialized with a genesis block."""
    _create_genesis_block()


# ---------------------------------------------------------------------------
# BLOCK CREATION
# ---------------------------------------------------------------------------

def get_last_block():
    """Return the most recent block in the chain."""
    return _blocks_collection().find_one(sort=[("index", -1)])


def mine_block(data: dict) -> dict:
    """
    Create and persist a new block on the private chain.

    Steps:
    1. Retrieve the previous block.
    2. Increment the index.
    3. Run lightweight proof-of-work.
    4. Persist the block to MongoDB.
    5. Return the finalized block.
    """
    initialize_chain()
    last = get_last_block()

    new_index = last["index"] + 1
    timestamp = _utc_now_iso()
    previous_hash = last["hash"]
    nonce = 0

    # Lightweight proof-of-work (private chain: 2 leading zeros)
    while True:
        block_hash = generate_block_hash(new_index, timestamp, data, previous_hash, nonce)
        if block_hash[:DIFFICULTY] == "0" * DIFFICULTY:
            break
        nonce += 1

    block = {
        "index": new_index,
        "timestamp": timestamp,
        "data": data,
        "previous_hash": previous_hash,
        "nonce": nonce,
        "hash": block_hash,
    }

    _blocks_collection().insert_one(block)
    return {
        "block_index": new_index,
        "block_hash": block_hash,
        "previous_hash": previous_hash,
        "timestamp": timestamp,
        "nonce": nonce,
    }


# ---------------------------------------------------------------------------
# CHAIN VALIDATION
# ---------------------------------------------------------------------------

def validate_chain() -> dict:
    """
    Walk the entire chain and verify hash integrity.
    Returns a validation report with any tampered blocks flagged.
    """
    initialize_chain()
    blocks = list(_blocks_collection().find().sort("index", 1))
    total = len(blocks)
    tampered = []

    for i in range(1, total):
        current = blocks[i]
        previous = blocks[i - 1]

        # Verify previous_hash linkage
        if current["previous_hash"] != previous["hash"]:
            tampered.append({"block_index": current["index"], "issue": "previous_hash mismatch"})

        # Verify block hash integrity
        recalculated = generate_block_hash(
            current["index"], current["timestamp"], current["data"], current["previous_hash"], current["nonce"]
        )
        if recalculated != current["hash"]:
            tampered.append({"block_index": current["index"], "issue": "hash tampered"})

    return {
        "total_blocks": total,
        "chain_valid": len(tampered) == 0,
        "tampered_blocks": tampered,
    }


# ---------------------------------------------------------------------------
# CHAIN INFO
# ---------------------------------------------------------------------------

def get_chain_info() -> dict:
    """Return metadata about the current chain state."""
    initialize_chain()
    total = _blocks_collection().count_documents({})
    last = get_last_block()
    return {
        "total_blocks": total,
        "latest_block_index": last["index"] if last else 0,
        "latest_block_hash": last["hash"] if last else None,
        "chain_initialized": total > 0,
    }
