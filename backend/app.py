import os
import sys
from pathlib import Path

# Ensure the project root is on sys.path so `backend.*` imports resolve
# regardless of whether we run from the project root or the backend/ folder.
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import get_jwt

from backend.config.settings import get_config
from backend.database.db import get_db, init_db
from backend.middleware.security_headers import register_security_headers
from backend.routes.admin_routes import admin_bp
from backend.routes.auth_routes import auth_bp
from backend.routes.blockchain_routes import blockchain_bp
from backend.routes.bloodbank_routes import bloodbank_bp
from backend.routes.dashboard_routes import dashboard_bp
from backend.routes.health_routes import health_bp
from backend.routes.donor_routes import donor_bp
from backend.routes.hospital_routes import hospital_bp
from backend.routes.page_routes import page_bp
from backend.utils.extensions import bcrypt, jwt
from backend.utils.responses import error_response


# Project root where frontend files live (index.html, auth.html, etc.)
_FRONTEND_DIR = str(Path(__file__).resolve().parent.parent)


def create_app():
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder=_FRONTEND_DIR,
        static_url_path="",
    )
    app.config.from_object(get_config())

    CORS(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    )

    bcrypt.init_app(app)
    jwt.init_app(app)
    init_db(app)
    register_security_headers(app)
    register_jwt_callbacks()

    app.register_blueprint(admin_bp)
    app.register_blueprint(blockchain_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(bloodbank_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(donor_bp)
    app.register_blueprint(hospital_bp)
    app.register_blueprint(page_bp)

    # Initialize blockchain on startup
    with app.app_context():
        from backend.blockchain.services.blockchain_service import init_blockchain
        init_blockchain()
    register_cli(app)

    # ── Serve frontend files directly from project root ──
    @app.route("/")
    def serve_index():
        return send_from_directory(_FRONTEND_DIR, "index.html")

    @app.errorhandler(404)
    def not_found(_):
        return error_response("Route not found", 404)

    @app.errorhandler(500)
    def server_error(_):
        return error_response("Internal server error", 500)

    return app


def register_jwt_callbacks():
    @jwt.token_in_blocklist_loader
    def is_token_revoked(_jwt_header, jwt_payload):
        return get_db()["jwt_blocklist"].find_one({"jti": jwt_payload["jti"]}) is not None

    @jwt.unauthorized_loader
    def missing_token(message):
        return error_response(message or "Unauthorized", 401)

    @jwt.invalid_token_loader
    def invalid_token(message):
        return error_response(message or "Invalid token", 422)

    @jwt.expired_token_loader
    def expired_token(_jwt_header, _jwt_payload):
        return error_response("Token has expired", 401)

    @jwt.revoked_token_loader
    def revoked_token(_jwt_header, _jwt_payload):
        return error_response("Token has been revoked", 401)


def register_cli(app):
    @app.cli.command("seed-admin")
    def seed_admin():
        from pymongo.errors import DuplicateKeyError
        from pymongo.errors import PyMongoError

        from backend.models.user_model import create_user, find_by_email

        email = os.getenv("ADMIN_EMAIL", "admin@hemochain.in")
        password = os.getenv("ADMIN_PASSWORD")
        admin_name = os.getenv("ADMIN_NAME", "Super Admin")

        if not password:
            raise RuntimeError("Set ADMIN_PASSWORD in the environment before seeding an admin.")

        try:
            if find_by_email("admin", email):
                print(f"Admin already exists: {email}")
                return
        except PyMongoError as exc:
            print("Could not connect to MongoDB while seeding admin.")
            print("Check MONGO_URI, database username, password, and Atlas Network Access.")
            print(f"MongoDB error: {exc}")
            return

        password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
        try:
            create_user("admin", {"admin_name": admin_name, "email": email}, password_hash)
        except DuplicateKeyError:
            print(f"Admin already exists: {email}")
            return
        except PyMongoError as exc:
            print("Could not create admin in MongoDB.")
            print("Check MONGO_URI, database username, password, and Atlas Network Access.")
            print(f"MongoDB error: {exc}")
            return

        print(f"Admin seeded: {email}")


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
