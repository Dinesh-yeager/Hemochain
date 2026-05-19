from flask_jwt_extended import get_jwt, get_jwt_identity

from backend.models.activity_model import list_emergency_requests, list_notifications
from backend.models.user_model import find_by_id, public_user
from backend.utils.blockchain import verification_snapshot
from backend.utils.responses import error_response, success_response


def profile_response():
    role = get_jwt().get("role")
    user = find_by_id(role, get_jwt_identity())
    if not user:
        return error_response("User not found", 404)
    return success_response("Profile loaded", role=role, user=public_user(user))


def dashboard_response(expected_role):
    claims = get_jwt()
    role = claims.get("role")
    user = find_by_id(role, get_jwt_identity())
    if not user:
        return error_response("User not found", 404)

    payload = {
        "role": role,
        "user": public_user(user),
        "notifications": list_notifications(get_jwt_identity(), role, limit=10),
        "verification": verification_snapshot(),
    }

    if expected_role in ("hospital", "bloodbank", "admin"):
        payload["emergency_requests"] = list_emergency_requests(limit=10)

    return success_response(f"{expected_role.title()} dashboard loaded", **payload)


def blockchain_verification_response():
    return success_response("Verification status loaded", verification=verification_snapshot())
