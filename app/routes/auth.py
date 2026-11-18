from flask import Blueprint
from app.handlers.authLogin_handler import login, test_db_connection, protected_token, validatePass, logout, logger, validate_MFA_token

auth_bp = Blueprint("auth", __name__)

auth_bp.route("/login", methods=["POST"])(login)
auth_bp.route("/verify_token", methods=["GET"])(protected_token)
auth_bp.route("/confirmPass", methods=["POST"])(validatePass)
auth_bp.route("/testdb", methods=["GET"])(test_db_connection)
auth_bp.route("/mfa-callback", methods=["POST"])(validate_MFA_token)

auth_bp.route("/logout", methods=["POST"])(logout)
auth_bp.route("/action-logger", methods=["POST"])(logger)
