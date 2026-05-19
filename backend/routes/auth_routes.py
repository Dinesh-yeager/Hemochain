from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from backend.controllers.auth_controller import login_user, logout_user, refresh_access_token, signup_user


auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/donor/signup")
def donor_signup():
    return signup_user("donor", request)


@auth_bp.post("/hospital/signup")
def hospital_signup():
    return signup_user("hospital", request)


@auth_bp.post("/bloodbank/signup")
def bloodbank_signup():
    return signup_user("bloodbank", request)


@auth_bp.post("/donor/login")
def donor_login():
    return login_user("donor", request)


@auth_bp.post("/hospital/login")
def hospital_login():
    return login_user("hospital", request)


@auth_bp.post("/bloodbank/login")
def bloodbank_login():
    return login_user("bloodbank", request)


@auth_bp.post("/admin/login")
def admin_login():
    return login_user("admin", request)


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    return refresh_access_token()


@auth_bp.post("/logout")
@jwt_required()
def logout():
    return logout_user()
