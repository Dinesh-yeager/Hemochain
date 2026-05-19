import re


ROLE_COLLECTIONS = {
    "donor": "donors",
    "hospital": "hospitals",
    "bloodbank": "bloodbanks",
    "admin": "admins",
}

ROLE_REDIRECTS = {
    "donor": "/donor-dashboard",
    "hospital": "/hospital-dashboard",
    "bloodbank": "/bloodbank-dashboard",
    "admin": "/admin-dashboard",
}

SIGNUP_FIELDS = {
    "donor": ("full_name", "email", "phone", "blood_group", "gender", "age", "location", "password"),
    "hospital": ("hospital_name", "email", "registration_id", "phone", "address", "password"),
    "bloodbank": ("bloodbank_name", "email", "registration_id", "storage_capacity", "location", "password"),
    "admin": ("admin_name", "email", "password"),
}

PUBLIC_FIELDS = {
    "donor": ("full_name", "email", "phone", "blood_group", "gender", "age", "location", "role"),
    "hospital": ("hospital_name", "email", "registration_id", "phone", "address", "role"),
    "bloodbank": ("bloodbank_name", "email", "registration_id", "storage_capacity", "location", "role"),
    "admin": ("admin_name", "email", "role"),
}

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_role(role):
    return role in ROLE_COLLECTIONS


def validate_email(email):
    return bool(EMAIL_RE.match(str(email or "").strip()))


def validate_password(password):
    password = str(password or "")
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number"
    return True, ""


def validate_signup_payload(role, payload):
    missing = [field for field in SIGNUP_FIELDS[role] if not payload.get(field)]
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"

    if not validate_email(payload.get("email")):
        return False, "Invalid email address"

    password_ok, password_message = validate_password(payload.get("password"))
    if not password_ok:
        return False, password_message

    if payload.get("confirm_password") is not None and payload["confirm_password"] != payload["password"]:
        return False, "Passwords do not match"

    if role == "bloodbank":
        try:
            capacity = int(payload.get("storage_capacity"))
            if capacity <= 0:
                return False, "Storage capacity must be greater than zero"
        except (TypeError, ValueError):
            return False, "Storage capacity must be a valid number"

    return True, ""


def validate_login_payload(payload):
    if not payload.get("email") or not payload.get("password"):
        return False, "Email and password are required"
    if not validate_email(payload.get("email")):
        return False, "Invalid email address"
    return True, ""
