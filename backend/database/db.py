from datetime import datetime, timezone

from pymongo import ASCENDING, MongoClient
from pymongo.errors import PyMongoError


client = None
db = None


REQUIRED_COLLECTIONS = (
    "donors",
    "hospitals",
    "bloodbanks",
    "admins",
    "emergency_requests",
    "donations",
    "notifications",
    "appointments",
    "blood_inventory",
    "blood_requests",
    "hospital_requests",
    "blood_transfers",
    "reports",
    "activity_logs",
    "blockchain_logs",
    "blockchain_blocks",
    "verification_events",
    "audit_trails",
    "transfer_chain",
    "secure_records",
)


def init_db(app):
    global client, db
    client = MongoClient(
        app.config["MONGO_URI"],
        serverSelectionTimeoutMS=app.config["MONGO_TIMEOUT_MS"],
        connectTimeoutMS=app.config["MONGO_TIMEOUT_MS"],
    )
    db = client[app.config["MONGO_DB_NAME"]]

    try:
        client.admin.command("ping")
        app.logger.info("MongoDB connection established.")
    except PyMongoError as exc:
        app.logger.warning("MongoDB ping failed: %s", exc)
        return

    if app.config.get("AUTO_CREATE_INDEXES", True):
        create_indexes()


def get_db():
    if db is None:
        raise RuntimeError("Database has not been initialized. Call init_db(app) first.")
    return db


def create_indexes():
    database = get_db()
    for collection in ("donors", "hospitals", "bloodbanks", "admins"):
        database[collection].create_index([("email", ASCENDING)], unique=True)
        database[collection].create_index([("role", ASCENDING)])

    database["emergency_requests"].create_index([("status", ASCENDING), ("created_at", ASCENDING)])
    database["donations"].create_index([("donor_id", ASCENDING), ("created_at", ASCENDING)])
    database["notifications"].create_index([("user_id", ASCENDING), ("created_at", ASCENDING)])
    database["appointments"].create_index([("donor_id", ASCENDING), ("appointment_date", ASCENDING)])
    database["blood_inventory"].create_index([("hospital_id", ASCENDING), ("blood_group", ASCENDING)], unique=True)
    database["blood_inventory"].create_index([("bloodbank_id", ASCENDING), ("blood_group", ASCENDING)], unique=True)
    database["hospital_requests"].create_index([("request_status", ASCENDING), ("created_at", ASCENDING)])
    database["blood_transfers"].create_index([("transfer_status", ASCENDING), ("created_at", ASCENDING)])
    database["activity_logs"].create_index([("created_at", ASCENDING)])
    database["blockchain_logs"].create_index([("created_at", ASCENDING)])
    database["blockchain_logs"].create_index([("event_type", ASCENDING)])
    database["blockchain_logs"].create_index([("reference_id", ASCENDING)])
    database["blockchain_blocks"].create_index([("index", ASCENDING)], unique=True)
    database["blockchain_blocks"].create_index([("hash", ASCENDING)])
    database["verification_events"].create_index([("entity_id", ASCENDING)])
    database["verification_events"].create_index([("timestamp", ASCENDING)])
    database["audit_trails"].create_index([("reference_id", ASCENDING)])
    database["audit_trails"].create_index([("created_at", ASCENDING)])
    database["transfer_chain"].create_index([("blood_unit_id", ASCENDING)])
    database["transfer_chain"].create_index([("created_at", ASCENDING)])
    database["secure_records"].create_index([("reference_id", ASCENDING)])
    database["secure_records"].create_index([("blockchain_tx_id", ASCENDING)])
    database["jwt_blocklist"].create_index([("jti", ASCENDING)], unique=True)
    database["jwt_blocklist"].create_index([("expires_at", ASCENDING)], expireAfterSeconds=0)


def utc_now():
    return datetime.now(timezone.utc)
