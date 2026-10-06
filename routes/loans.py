from datetime import date
from flask import (Blueprint, jsonify, request)
from ..extensions import db
from ..security.auth import require_auth
from ..services.loan_serializer import serialize_loan, serialize_payment
from ..services.loan_service import (create_loan, get_loan, get_loan_payments, list_loans, make_payment)


loans_bp = Blueprint("loans", __name__, url_prefix="/loans")


@loans_bp.get("")
@require_auth
def loans():
    try:
        page = max(int(request.args.get("page", 1)), 1)
        per_page = min(
            max(int(request.args.get("per_page", 20)), 1), 100)

    except ValueError:
        return jsonify({"message": "Invalid pagination values."}), 400

    pagination = list_loans(
        page=page,
        per_page=per_page,
        status=request.args.get("status"),
        customer_id=request.args.get("customer_id"),
    )

    return jsonify({
        "loans": [serialize_loan(loan) for loan in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        }
    }), 200


@loans_bp.post("")
@require_auth
def create():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"message": "Invalid request body."}), 400

    try:
        customer_id = str(data.get("customer_id", "")).strip()
        principal = data.get("principal")
        interest_rate = data.get("interest_rate")
        due_date = date.fromisoformat(str(data.get("due_date")))
        loan_date_value = data.get("loan_date")
        loan_date = (date.fromisoformat(str(loan_date_value)) if loan_date_value else date.today())
        loan = create_loan(
            customer_id=customer_id,
            company_id=1,
            principal=principal,
            interest_rate=interest_rate,
            due_date=due_date,
            loan_date=loan_date,
        )

        db.session.commit()

        return jsonify({
            "message": "Loan created successfully.",
            "loan": serialize_loan(loan, include_payments=True)}), 201

    except ValueError as exc:
        db.session.rollback()
        return jsonify({"message": str(exc)}), 400

    except TypeError:
        db.session.rollback()
        return jsonify({"message": "Invalid loan data."}), 400

    except Exception:
        db.session.rollback()
        raise


@loans_bp.get("/<int:loan_id>")
@require_auth
def get(loan_id):
    loan = get_loan(loan_id)
    if loan is None:
        return jsonify({"message": "Loan not found."}), 404

    return jsonify(serialize_loan(loan, include_payments=True)), 200


@loans_bp.post("/<int:loan_id>/payments")
@require_auth
def payment(loan_id):
    loan = get_loan(loan_id)

    if loan is None:
        return jsonify({"message": "Loan not found."}), 404

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"message": "Invalid request body."}), 400
        
    try:
        amount = data.get("amount")
        payment_date = date.fromisoformat(str(data.get("payment_date")))
        payment_method = str(data.get("payment_method", "M-Pesa")).strip()
        payment_record = make_payment(
            loan=loan,
            amount=amount,
            payment_date=payment_date,
            payment_method=payment_method,
            reference=data.get("reference"),
            notes=data.get("notes"),
            payment_number=data.get("payment_number")
        )

        db.session.commit()
        return jsonify({
            "message": "Payment recorded successfully.",
            "payment": {
                "id": payment_record.id,
                "amount": str(payment_record.amount),
                "principal_amount": str(payment_record.principal_amount),
                "interest_amount": str(payment_record.interest_amount),
                "payment_method": payment_record.payment_method,
                "payment_date": payment_record.payment_date.isoformat(),
            },
            "loan": serialize_loan(loan, include_payments=True)}), 201

    except ValueError as exc:
        db.session.rollback()
        return jsonify({"message": str(exc)}), 400

    except TypeError:
        db.session.rollback()

        return jsonify({"message": "Invalid payment data."}), 400

    except Exception:
        db.session.rollback()
        raise


@loans_bp.get("/<int:loan_id>/payments")
@require_auth
def payments(loan_id):
    loan = get_loan(loan_id)
    if loan is None:
        return jsonify({"message": "Loan not found."}), 404

    records = get_loan_payments(loan_id)
    return jsonify({
        "payments": [serialize_payment(payment) for payment in records]
    }), 200