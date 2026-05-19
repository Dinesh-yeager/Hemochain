from flask import Blueprint

from backend.utils.responses import success_response


health_bp = Blueprint("health", __name__)


@health_bp.get("/api/health")
def health():
    return success_response("Hemo Chain API is healthy")
