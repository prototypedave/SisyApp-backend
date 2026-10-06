from flask import Blueprint, jsonify, request, g
from ..extensions import db
from ..security.auth import require_auth
from ..services.settings_service import (
    get_company,
    get_settings,
    update_business,
    update_operational_settings,
    change_owner_password,
    adjust_company_funds,
)

from ..services.settings_serializer import (
    serialize_fund_adjustment,
)

from ..models.company_fund_adjustment import (
    CompanyFundAdjustmentModel,
)


settings_bp = Blueprint(
    "settings",
    __name__,
    url_prefix="/settings",
)


def get_current_user():
    """
    Assumes @require_auth places the authenticated
    UserModel on flask.g.current_user.

    If your existing auth decorator uses a different
    g attribute, change only this function.
    """
    user = getattr(
        g,
        "current_user",
        None
    )

    if not user:
        raise ValueError(
            "Authentication required."
        )

    return user


@settings_bp.get("")
@require_auth
def settings():
    try:
        data = get_settings()

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
            "message": "Unable to load settings.",
        }), 500


@settings_bp.put("/business")
@require_auth
def update_business_settings():
    try:
        body = request.get_json(
            silent=True
        ) or {}

        company = get_company()

        update_business(
            company=company,
            name=body.get("name"),
        )

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Business details updated.",
            "data": get_settings(),
        }), 200

    except ValueError as error:
        db.session.rollback()

        return jsonify({
            "success": False,
            "message": str(error),
        }), 400

    except Exception:
        db.session.rollback()

        return jsonify({
            "success": False,
            "message": "Unable to update business details.",
        }), 500


@settings_bp.put("/operations")
@require_auth
def update_operations():
    try:
        body = request.get_json(
            silent=True
        ) or {}

        company = get_company()

        update_operational_settings(
            company=company,
            currency=body.get("currency"),
            default_interest_rate=body.get(
                "default_interest_rate"
            ),
            minimum_loan_amount=body.get(
                "minimum_loan_amount"
            ),
            maximum_loan_amount=body.get(
                "maximum_loan_amount"
            ),
            loan_grace_days=body.get(
                "loan_grace_days"
            ),
            allow_partial_payments=body.get(
                "allow_partial_payments"
            ),
        )

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Operational settings updated.",
            "data": get_settings(),
        }), 200

    except (ValueError, TypeError) as error:
        db.session.rollback()

        return jsonify({
            "success": False,
            "message": str(error),
        }), 400

    except Exception:
        db.session.rollback()

        return jsonify({
            "success": False,
            "message": "Unable to update settings.",
        }), 500


@settings_bp.put("/password")
@require_auth
def change_password():
    try:
        user = get_current_user()

        body = request.get_json(
            silent=True
        ) or {}

        current_password = body.get(
            "current_password"
        )

        new_password = body.get(
            "new_password"
        )

        confirm_password = body.get(
            "confirm_password"
        )

        if new_password != confirm_password:
            return jsonify({
                "success": False,
                "message": "New passwords do not match.",
            }), 400

        change_owner_password(
            user=user,
            current_password=current_password,
            new_password=new_password,
        )

        db.session.commit()

        return jsonify({
            "success": True,
            "message": (
                "Password changed successfully. "
                "Please sign in again."
            ),
        }), 200

    except ValueError as error:
        db.session.rollback()

        return jsonify({
            "success": False,
            "message": str(error),
        }), 400

    except Exception:
        db.session.rollback()

        return jsonify({
            "success": False,
            "message": "Unable to change password.",
        }), 500


@settings_bp.post("/funds")
@require_auth
def adjust_funds():
    try:
        user = get_current_user()

        body = request.get_json(
            silent=True
        ) or {}

        company = get_company()

        adjustment = adjust_company_funds(
            company=company,
            user=user,
            adjustment_type=body.get(
                "adjustment_type"
            ),
            amount=body.get("amount"),
            reason=body.get("reason"),
        )

        db.session.commit()

        return jsonify({
            "success": True,
            "message": (
                "Company funds updated."
            ),
            "data": serialize_fund_adjustment(
                adjustment
            ),
        }), 200

    except (ValueError, TypeError) as error:
        db.session.rollback()

        return jsonify({
            "success": False,
            "message": str(error),
        }), 400

    except Exception:
        db.session.rollback()

        return jsonify({
            "success": False,
            "message": "Unable to update company funds.",
        }), 500


@settings_bp.get("/funds")
@require_auth
def fund_history():
    try:
        limit = request.args.get(
            "limit",
            default=20,
            type=int
        )

        limit = max(
            1,
            min(limit, 100)
        )

        adjustments = (
            CompanyFundAdjustmentModel.query
            .order_by(
                CompanyFundAdjustmentModel.created_at.desc()
            )
            .limit(limit)
            .all()
        )

        return jsonify({
            "success": True,
            "data": [
                serialize_fund_adjustment(
                    adjustment
                )
                for adjustment in adjustments
            ],
        }), 200

    except Exception:
        return jsonify({
            "success": False,
            "message": "Unable to load fund history.",
        }), 500