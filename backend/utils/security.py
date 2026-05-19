from bson import ObjectId


def normalize_email(email):
    return str(email or "").strip().lower()


def sanitize_document(payload):
    sanitized = {}
    for key, value in (payload or {}).items():
        if not isinstance(key, str) or key.startswith("$") or "." in key:
            continue
        sanitized[key] = value.strip() if isinstance(value, str) else value
    return sanitized


def object_id(value):
    try:
        return ObjectId(value)
    except Exception:
        return None


def serialize_document(document):
    if not document:
        return None
    clean = {}
    for key, value in document.items():
        if key == "password":
            continue
        if isinstance(value, ObjectId):
            clean[key] = str(value)
        else:
            clean[key] = value
    return clean
