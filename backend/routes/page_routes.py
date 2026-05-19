from flask import Blueprint, redirect

from backend.middleware.auth_middleware import role_required


page_bp = Blueprint("pages", __name__)


@page_bp.get("/login")
def login_page():
    return redirect("/auth.html")


@page_bp.get("/signup")
def signup_page():
    return redirect("/auth.html")


@page_bp.get("/admin")
def admin_page():
    return redirect("/admin/index.html")


@page_bp.get("/donor-dashboard")
@role_required("donor")
def donor_dashboard_page():
    return redirect("/dashboard.html")


@page_bp.get("/hospital-dashboard")
@role_required("hospital")
def hospital_dashboard_page():
    return redirect("/hospital.html")


@page_bp.get("/bloodbank-dashboard")
@role_required("bloodbank")
def bloodbank_dashboard_page():
    return redirect("/bloodbank.html")


@page_bp.get("/admin-dashboard")
@role_required("admin")
def admin_dashboard_page():
    return redirect("/admin/dashboard.html")
