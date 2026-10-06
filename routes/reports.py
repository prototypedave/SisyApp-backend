from datetime import date
from flask import Blueprint, jsonify, request
from ..security.auth import require_auth
from ..services.report_service import (
    get_reports,
    parse_report_date,
)


reports_bp = Blueprint("reports",__name__,url_prefix="/reports")


@reports_bp.get("")
@require_auth
def reports():
    try:
        today = date.today()
        default_start = today.replace(day=1)
        start_date = parse_report_date(
            request.args.get("from"),
            "from"
        ) if request.args.get("from") else default_start

        end_date = parse_report_date(
            request.args.get("to"),
            "to"
        ) if request.args.get("to") else today

        data = get_reports(
            start_date=start_date,
            end_date=end_date,
        )

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
            "message": "Unable to generate report.",
        }), 500