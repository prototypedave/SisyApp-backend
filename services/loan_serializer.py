def serialize_payment(payment):
    return {
        "id": payment.id,
        "loan_id": payment.loan_id,
        "payment_number": payment.payment_number, 
        "company_id": payment.company_id,
        "amount": str(payment.amount),
        "principal_amount": str(payment.principal_amount),
        "interest_amount": str(payment.interest_amount),
        "payment_method": payment.payment_method,
        "reference": payment.reference,
        "payment_date": (payment.payment_date.isoformat() if payment.payment_date else None),
        "notes": payment.notes,
        "created_at": (payment.created_at.isoformat() if payment.created_at else None),
    }


def serialize_loan(loan, include_payments=False):
    data = {
        "id": loan.id,
        "loan_number": loan.loan_number,
        "customer_id": loan.customer_id,
        "customer": {
            "id": loan.customer.id,
            "first_name": loan.customer.first_name,
            "last_name": loan.customer.last_name,
            "mobile": loan.customer.mobile,
        },
        "company_id": loan.company_id,
        "principal": str(loan.principal),
        "interest_rate": str(loan.interest_rate),
        "interest_amount": str(loan.interest_amount),
        "total_due": str(loan.total_due),
        "balance": str(loan.balance),
        "loan_date": (loan.loan_date.isoformat() if loan.loan_date else None),
        "due_date": (loan.due_date.isoformat() if loan.due_date else None),
        "status": loan.status,
        "completion_date": (loan.completion_date.isoformat() if loan.completion_date else None),
        "created_at": (loan.created_at.isoformat() if loan.created_at else None),
    }

    if include_payments:
        data["payments"] = [serialize_payment(payment) for payment in loan.payments]

    return data


def serialize_investor(loan, include_payments=False):
    data = {
        "id": loan.id,
        "first_name": loan.first_name,
        "last_name": loan.last_name,
        "mobile": loan.mobile,
        "company_id": loan.company_id,
        "principal": str(loan.principal),
        "interest_rate": str(loan.interest_rate),
        "interest_amount": str(loan.interest_amount),
        "total_due": str(loan.total_due),
        "balance": str(loan.balance),
        "loan_date": (loan.loan_date.isoformat() if loan.loan_date else None),
        "due_date": (loan.due_date.isoformat() if loan.due_date else None),
        "status": loan.status,
        "completion_date": (loan.completion_date.isoformat() if loan.completion_date else None),
        "created_at": (loan.created_at.isoformat() if loan.created_at else None),
    }

    if include_payments:
        data["payments"] = [serialize_payment(payment) for payment in loan.payments]

    return data