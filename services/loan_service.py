from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy import select
from ..extensions import db
from ..models import (CompanyModel, CustomerModel, LoanModel, PaymentModel)


MONEY = Decimal("0.01")


def money(value):
    return Decimal(str(value)).quantize(MONEY, rounding=ROUND_HALF_UP)


def get_company(company_id):
    return db.session.get(CompanyModel, company_id)


def calculate_interest(principal, interest_rate):
    print(interest_rate)
    principal = money(principal)
    interest_rate = Decimal(str(interest_rate))
    return money(principal * interest_rate / Decimal("100"))


def create_loan(customer_id, company_id, principal, interest_rate, due_date, loan_date=None):
    principal = money(principal)
    interest_rate = Decimal(str(interest_rate))
    if principal <= 0:
        raise ValueError("Loan amount must be greater than zero.")

    if interest_rate < 0:
        raise ValueError("Interest rate cannot be negative.")

    if not isinstance(due_date, date):
        raise ValueError("Invalid due date.")

    if loan_date is None:
        loan_date = date.today()

    if due_date < loan_date:
        raise ValueError("Due date cannot be before the loan date.")

    customer = db.session.get(CustomerModel, customer_id)
    if customer is None:
        raise ValueError("Customer not found.")

    if customer.archived:
        raise ValueError("Archived customers cannot receive a loan.")

    if customer.blacklisted:
        raise ValueError("Blacklisted customers cannot receive a loan.")

    loan_limit = money(customer.loan_limit or 0)

    if principal > loan_limit:
        raise ValueError("Loan amount exceeds the customer's loan limit.")

    company = get_company(company_id)
    #company.receive_payment(company.initial_amount)
    if company is None:
        raise ValueError("Company account not found.")

    if not company.can_issue_loan(principal):
        raise ValueError("Insufficient company funds.")

    interest_amount = calculate_interest(principal, interest_rate)
    total_due = money(principal + interest_amount)
    loan = LoanModel(
        customer_id=customer.id,
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
    company.reduce_funds(principal)
    customer.parse_loan(principal, interest_amount)
    db.session.add(loan)
    db.session.flush()
    loan.loan_number = f"LN{loan.id:04d}"

    return loan


def get_loan(loan_id):
    return db.session.get(LoanModel, loan_id)


def list_loans(page=1, per_page=20, status=None, customer_id=None):
    query = LoanModel.query
    if status:
        query = query.filter(LoanModel.status == status.upper())

    if customer_id:
        query = query.filter(LoanModel.customer_id == customer_id)

    query = query.order_by(LoanModel.created_at.desc())

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
    
    previous_interest_paid = (db.session.query(db.func.coalesce(db.func.sum(PaymentModel.interest_amount), 0)).filter(PaymentModel.loan_id == loan.id).scalar())
    previous_interest_paid = money(previous_interest_paid)
    interest_remaining = money(loan.interest_amount - previous_interest_paid)
    paid_interest = min(amount, interest_remaining)
    paid_principal = money(amount - paid_interest)
    loan.apply_payment(amount, payment_date)
    payment = PaymentModel(
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
    loan.company.receive_payment(amount)
    db.session.add(payment)
    db.session.flush()
    payment.payment_number = f"PN{loan.id:06d}"

    return payment


def get_loan_payments(loan_id):
    return (PaymentModel.query.filter_by(loan_id=loan_id).order_by(PaymentModel.payment_date.asc(), PaymentModel.id.asc()).all())