from flask import Blueprint, jsonify, request

from ..extensions import db
from ..security.auth import require_auth
from ..services.customer_service import (
    archive_customer,
    blacklist_customer,
    create_customer,
    get_customer,
    list_customers,
    unblacklist_customer,
    update_customer,
)


customers_bp = Blueprint("customers", __name__, url_prefix="/customers")


@customers_bp.get("")
@require_auth
def customers():
    search = request.args.get("search", "")
    try:
        page = max(int(request.args.get("page", 1)), 1)
        per_page = min(max(int(request.args.get("per_page", 20)), 1), 100)

    except ValueError:
        return jsonify({"message": "Invalid pagination values."}), 400

    include_archived = (request.args.get("include_archived", "false").lower() == "true")
    pagination = list_customers(search=search, page=page, per_page=per_page, include_archived=include_archived)

    return jsonify({
        "customers": [customer.profile() for customer in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        }}), 200


@customers_bp.post("")
@require_auth
def create():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"message": "Invalid request body."}), 400

    try:
        customer = create_customer(data)
        db.session.commit()
        return jsonify({
            "message": "Customer created successfully.",
            "customer": customer.profile()
        }), 201

    except ValueError as exc:
        db.session.rollback()
        return jsonify({"message": str(exc)}), 400

    except Exception:
        db.session.rollback()
        raise


@customers_bp.get("/<string:customer_id>")
@require_auth
def get(customer_id):
    customer = get_customer(customer_id)
    if customer is None:
        return jsonify({"message": "Customer not found."}), 404

    return jsonify(customer.profile()), 200


@customers_bp.patch("/<string:customer_id>")
@require_auth
def update(customer_id):
    customer = get_customer(customer_id)
    if customer is None:
        return jsonify({"message": "Customer not found."}), 404

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"message": "Invalid request body."}), 400

    try:
        update_customer(customer, data)
        db.session.commit()
        return jsonify({
            "message": "Customer updated successfully.",
            "customer": customer.profile()
        }), 200

    except ValueError as exc:
        db.session.rollback()
        return jsonify({"message": str(exc)}), 400

    except Exception:
        db.session.rollback()
        raise


@customers_bp.post("/<string:customer_id>/archive")
@require_auth
def archive(customer_id):
    customer = get_customer(customer_id)

    if customer is None:
        return jsonify({"message": "Customer not found."}), 404

    try:
        archive_customer(customer)
        db.session.commit()
        return jsonify({
            "message": "Customer archived successfully.",
            "customer": customer.profile()
        }), 200

    except ValueError as exc:
        db.session.rollback()
        return jsonify({"message": str(exc)}), 400

    except Exception:
        db.session.rollback()
        raise


@customers_bp.post("/<string:customer_id>/blacklist")
@require_auth
def blacklist(customer_id):
    customer = get_customer(customer_id)
    if customer is None:
        return jsonify({"message": "Customer not found."}), 404

    data = request.get_json(silent=True) or {}

    try:
        blacklist_customer(customer, data.get("reason"))
        db.session.commit()
        return jsonify({
            "message": "Customer blacklisted successfully.",
            "customer": customer.profile()
        }), 200

    except ValueError as exc:
        db.session.rollback()

        return jsonify({"message": str(exc)}), 400

    except Exception:
        db.session.rollback()
        raise


@customers_bp.post("/<string:customer_id>/unblacklist")
@require_auth
def unblacklist(customer_id):
    customer = get_customer(customer_id)

    if customer is None:
        return jsonify({"message": "Customer not found."}), 404

    try:
        unblacklist_customer(customer)
        db.session.commit()
        return jsonify({
            "message": "Customer removed from blacklist.",
            "customer": customer.profile()
        }), 200

    except Exception:
        db.session.rollback()
        raise