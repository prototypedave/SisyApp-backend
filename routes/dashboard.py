from flask import Blueprint, jsonify
from ..security.auth import require_auth
from ..services.dashboard_service import get_dashboard_summary


dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.get("")
@require_auth
def dashboard():
    try:
        data = get_dashboard_summary()
        return jsonify({
            "success": True,
            "data": data,
        }), 200

    except ValueError as error:
        return jsonify({
            "success": False,
            "message": str(error),
        }), 400

    except Exception:
        return jsonify({
            "success": False,
            "message": ("Unable to load dashboard."),
        }), 500