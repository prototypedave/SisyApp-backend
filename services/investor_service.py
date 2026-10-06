from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy import select
from ..extensions import db
from ..models import (CompanyModel, InvestorModel, InvestorPaymentModel)
from flask import current_app


MONEY = Decimal("0.01")


def money(value):
    return Decimal(str(value)).quantize(MONEY, rounding=ROUND_HALF_UP)


def get_company(company_id):
    return db.session.get(CompanyModel, company_id)


def calculate_interest(principal, interest_rate):
    principal = money(principal)
    interest_rate = Decimal(str(interest_rate))
    return money(principal * interest_rate / Decimal("100"))


def create_loan(data):
    principal = money(data.get("principal"))
    interest_rate = Decimal(str(data.get("interest_rate")))
    if principal <= 0:
        raise ValueError("Loan amount must be greater than zero.")

    if interest_rate < 0:
        raise ValueError("Interest rate cannot be negative.")

    due_date = date.fromisoformat(str(data.get("due_date")))
    loan_date_value = data.get("loan_date")
    loan_date = date.fromisoformat(str(loan_date_value)) if loan_date_value else date.today()
    if not isinstance(due_date, date):
        raise ValueError("Invalid due date.")

    if loan_date is None:
        loan_date = date.today()

    if due_date < loan_date:
        raise ValueError("Due date cannot be before the loan date.")

    company_id = current_app.config.get("COMPANY_ID")
    company = get_company(company_id)
    
    if company is None:
        raise ValueError("Company account not found.")

    interest_amount = calculate_interest(principal, interest_rate)
    total_due = money(principal + interest_amount)
    loan = InvestorModel(
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        mobile=data.get("mobile"),
        email=data.get("email"),
        company_id=company.id,
        principal=principal,
        interest_rate=interest_rate,
        interest_amount=interest_amount,
        total_due=total_due,
        balance=total_due,
        loan_date=loan_date,
        due_date=due_date,
        status="ACTIVE",
    )
    company.receive_payment(principal)
    db.session.add(loan)
    db.session.flush()
    loan.loan_number = f"LN{loan.id:04d}"

    return loan


def get_loan(loan_id):
    return db.session.get(InvestorModel, loan_id)


def list_investments(page=1, per_page=20, status=None):
    query = InvestorModel.query
    if status:
        query = query.filter(InvestorModel.status == status.upper())

    query = query.order_by(InvestorModel.created_at.desc())

    return query.paginate(page=page, per_page=per_page, error_out=False)


def make_payment(loan, amount, payment_date, payment_method, payment_number, reference=None, notes=None):
    amount = money(amount)
    if amount <= 0:
        raise ValueError("Payment amount must be greater than zero.")

    if loan.status == "PAID":
        raise ValueError("This loan has already been fully paid.")

    if payment_date < loan.loan_date:
        raise ValueError("Payment date cannot be before the loan date.")

    if amount > loan.balance:
        raise ValueError("Payment cannot exceed the outstanding balance.")

    allowed_methods = {"M-Pesa", "Cash", "Bank"}

    if payment_method not in allowed_methods:
        raise ValueError("Invalid payment method.")
    
    previous_interest_paid = (db.session.query(db.func.coalesce(db.func.sum(InvestorPaymentModel.interest_amount), 0)).filter(InvestorPaymentModel.loan_id == loan.id).scalar())
    previous_interest_paid = money(previous_interest_paid)
    interest_remaining = money(loan.interest_amount - previous_interest_paid)
    paid_interest = min(amount, interest_remaining)
    paid_principal = money(amount - paid_interest)
    loan.apply_payment(amount, payment_date)
    payment = InvestorPaymentModel(
        loan_id=loan.id,
        company_id=loan.company_id,
        amount=amount,
        principal_amount=paid_principal,
        interest_amount=paid_interest,
        payment_method=payment_method,
        reference=(str(reference).strip() if reference else None),
        payment_date=payment_date,
        notes=(str(notes).strip() if notes else None),
        payment_number=payment_number
    )
    loan.company.reduce_funds(amount)
    db.session.add(payment)
    db.session.flush()
    payment.payment_number = f"PN{loan.id:06d}"

    return payment


def get_investor_payments(loan_id):
    return (InvestorPaymentModel.query.filter_by(loan_id=loan_id).order_by(InvestorPaymentModel.payment_date.asc(), InvestorPaymentModel.id.asc()).all())