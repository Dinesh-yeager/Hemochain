from backend.database.db import get_db, utc_now
from backend.utils.security import object_id, serialize_document


def create_notification(user_id, role, title, message, category="system"):
    document = {
        "user_id": object_id(user_id) if user_id else None,
        "role": role,
        "title": title,
        "message": message,
        "category": category,
        "read": False,
        "created_at": utc_now(),
    }
    get_db()["notifications"].insert_one(document)
    return document


def list_notifications(user_id=None, role=None, limit=20):
    query = {}
    if user_id:
        query["user_id"] = object_id(user_id)
    if role:
        query["$or"] = [{"role": role}, {"role": "all"}]
    cursor = get_db()["notifications"].find(query).sort("created_at", -1).limit(limit)
    return [serialize_document(item) for item in cursor]


def list_emergency_requests(limit=20):
    cursor = get_db()["emergency_requests"].find({}).sort("created_at", -1).limit(limit)
    return [serialize_document(item) for item in cursor]
