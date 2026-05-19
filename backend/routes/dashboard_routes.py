from flask import Blueprint
from flask_jwt_extended import jwt_required

from backend.controllers.dashboard_controller import (
    blockchain_verification_response,
    dashboard_response,
    profile_response,
)
from backend.middleware.auth_middleware import role_required


dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


@dashboard_bp.get("/me")
@jwt_required()
def me():
    return profile_response()


@dashboard_bp.get("/donor")
@role_required("donor")
def donor_dashboard():
    return dashboard_response("donor")


@dashboard_bp.get("/hospital")
@role_required("hospital")
def hospital_dashboard():
    return dashboard_response("hospital")


@dashboard_bp.get("/bloodbank")
@role_required("bloodbank")
def bloodbank_dashboard():
    return dashboard_response("bloodbank")


@dashboard_bp.get("/admin")
@role_required("admin")
def admin_dashboard():
    return dashboard_response("admin")


@dashboard_bp.get("/blockchain-verification")
@role_required("admin", "hospital", "bloodbank")
def blockchain_verification():
    return blockchain_verification_response()
