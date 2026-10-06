from flask import (Blueprint, current_app, jsonify, request)
from ..extensions import db, limiter
from ..services.auth import (authenticate_user, create_session, get_session_from_token, revoke_session)


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

def get_bearer_token():
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        return None

    token = authorization[7:].strip()
    if not token:
        return None

    return token


def require_internal_service():
    configured_key = current_app.config.get("INTERNAL_API_KEY")
    if not configured_key:
        return False

    supplied_key = request.headers.get("X-Internal-API-Key")
    return supplied_key == configured_key


@auth_bp.post("/login")
@limiter.limit("5 per minute", methods=["POST"],)
def login():
    if not require_internal_service():
        return jsonify({"message": "Forbidden."}), 403

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"message": "Invalid request."}), 400

    email = data.get("email")
    password = data.get("password")
    if not isinstance(email, str):
        return jsonify({"message": "Invalid email or password."}), 401

    if not isinstance(password, str):
        return jsonify({"message": "Invalid email or password."}), 401

    user = authenticate_user(email, password)

    if user is None:
        return jsonify({"message": "Invalid email or password."}), 401

    try:
        session, token = create_session(user)
        user.last_login_at = (session.last_used_at)
        db.session.commit()

    except Exception:
        db.session.rollback()
        current_app.logger.exception("Authentication session creation failed.")
        return jsonify({"message": "Unable to complete login."}), 500

    return jsonify({
        "message": "Login successful.",
        "token": token,
        "user": user.profile(),
    }), 200


@auth_bp.post("/logout")
def logout():
    if not require_internal_service():
        return jsonify({"message": "Forbidden."}), 403

    token = get_bearer_token()
    if not token:
        return jsonify({"message": "Authentication required."}), 401

    try:
        revoked = revoke_session(token)
        db.session.commit()

    except Exception:
        db.session.rollback()
        current_app.logger.exception("Logout failed.")
        return jsonify({"message": "Unable to logout."}), 500

    if not revoked:
        return jsonify({"message": "Authentication required."}), 401

    return jsonify({"message": "Logout successful."}), 200


@auth_bp.get("/me")
def me():
    if not require_internal_service():
        return jsonify({"message": "Forbidden."}), 403
    token = get_bearer_token()
    current_app.logger.info(
        "Auth /me token present: %s",
        bool(token)
    )
    if not token:
        return jsonify({"message": "Authentication required."}), 401

    session = get_session_from_token(token)
    if session is None:
        return jsonify({"message": "Authentication required."}), 401

    user = session.user
    if user is None or not user.is_active:
        return jsonify({"message": "Authentication required."}), 401

    return jsonify({"user": user.profile()}), 200