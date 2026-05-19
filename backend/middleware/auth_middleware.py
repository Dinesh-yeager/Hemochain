from functools import wraps

from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request

from backend.models.user_model import find_by_id
from backend.utils.responses import error_response


def role_required(*allowed_roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            role = claims.get("role")
            if role not in allowed_roles:
                return error_response("Unauthorized", 401)
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def current_user():
    claims = get_jwt()
    role = claims.get("role")
    user_id = get_jwt_identity()
    if not role or not user_id:
        return None
    return find_by_id(role, user_id)
