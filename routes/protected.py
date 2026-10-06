from flask import Blueprint, g, jsonify
from ..security.auth import require_auth


protected_bp = Blueprint("protected", __name__, url_prefix="/protected",)

@protected_bp.get("/test")
@require_auth
def protected_test():
    user = g.current_user
    return jsonify({
        "message": "Authentication successful.",
        "user": user.profile(),
}), 200