from datetime import datetime, timezone

from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt, get_jwt_identity
from pymongo.errors import DuplicateKeyError

from backend.database.db import get_db, utc_now
from backend.models.user_model import create_user, find_by_email, find_email_across_roles, find_by_id, public_user
from backend.utils.extensions import bcrypt
from backend.utils.responses import error_response, success_response
from backend.utils.security import sanitize_document
from backend.utils.validators import ROLE_REDIRECTS, validate_login_payload, validate_signup_payload


def signup_user(role, request):
    payload = sanitize_document(request.get_json(silent=True) or {})
    valid, message = validate_signup_payload(role, payload)
    if not valid:
        return error_response(message, 422)

    existing_role, _ = find_email_across_roles(payload["email"])
    if existing_role:
        return error_response("Email already exists", 409)

    password_hash = bcrypt.generate_password_hash(payload["password"]).decode("utf-8")
    payload.pop("confirm_password", None)
    payload.pop("password", None)

    try:
        user = create_user(role, payload, password_hash)
    except DuplicateKeyError:
        return error_response("Email already exists", 409)

    return success_response(
        "Signup successful",
        201,
        role=role,
        redirect="/login",
        user=public_user(user),
    )


def login_user(role, request):
    payload = sanitize_document(request.get_json(silent=True) or {})
    valid, message = validate_login_payload(payload)
    if not valid:
        return error_response(message, 422)

    user = find_by_email(role, payload["email"])
    invalid_message = "Invalid Admin Credentials" if role == "admin" else "Invalid credentials"
    if not user or not bcrypt.check_password_hash(user["password"], payload["password"]):
        return error_response(invalid_message, 401)

    login_time = datetime.now(timezone.utc).isoformat()
    claims = {"role": role, "login_time": login_time}
    access_token = create_access_token(identity=str(user["_id"]), additional_claims=claims)
    refresh_token = create_refresh_token(identity=str(user["_id"]), additional_claims=claims)

    return success_response(
        "Login successful",
        role=role,
        redirect=ROLE_REDIRECTS[role],
        token=access_token,
        refresh_token=refresh_token,
        login_time=login_time,
        user=public_user(user),
    )


def logout_user():
    jwt_payload = get_jwt()
    get_db()["jwt_blocklist"].insert_one({
        "jti": jwt_payload["jti"],
        "user_id": get_jwt_identity(),
        "type": jwt_payload.get("type", "access"),
        "revoked_at": utc_now(),
        "expires_at": datetime.fromtimestamp(jwt_payload["exp"], tz=timezone.utc),
    })
    return success_response("Logout successful", redirect="/login")


def refresh_access_token():
    user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get("role")
    user = find_by_id(role, user_id)
    if not user:
        return error_response("Unauthorized", 401)
    access_token = create_access_token(
        identity=user_id,
        additional_claims={"role": role, "login_time": claims.get("login_time")},
    )
    return success_response("Token refreshed", token=access_token, role=role, redirect=ROLE_REDIRECTS[role])
