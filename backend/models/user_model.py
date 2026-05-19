from backend.database.db import get_db, utc_now
from backend.utils.security import normalize_email, object_id, serialize_document
from backend.utils.validators import PUBLIC_FIELDS, ROLE_COLLECTIONS, SIGNUP_FIELDS


def collection_for(role):
    return get_db()[ROLE_COLLECTIONS[role]]


def find_by_email(role, email):
    return collection_for(role).find_one({"email": normalize_email(email)})


def find_email_across_roles(email):
    normalized = normalize_email(email)
    for role in ROLE_COLLECTIONS:
        user = get_db()[ROLE_COLLECTIONS[role]].find_one({"email": normalized})
        if user:
            return role, user
    return None, None


def find_by_id(role, user_id):
    oid = object_id(user_id)
    if not oid:
        return None
    return collection_for(role).find_one({"_id": oid})


def create_user(role, payload, password_hash):
    allowed = set(PUBLIC_FIELDS[role]) | set(SIGNUP_FIELDS[role]) | {"registration_id", "address", "password", "created_at", "updated_at"}
    document = {key: value for key, value in payload.items() if key in allowed}
    document["email"] = normalize_email(document["email"])
    document["password"] = password_hash
    document["role"] = role
    document["created_at"] = utc_now()
    document["updated_at"] = utc_now()
    result = collection_for(role).insert_one(document)
    document["_id"] = result.inserted_id
    return document


def public_user(document):
    return serialize_document(document)
