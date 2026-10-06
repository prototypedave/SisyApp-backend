from datetime import date, timedelta
from decimal import Decimal
from flask import current_app
from sqlalchemy import func
from ..extensions import db

from ..models.company import CompanyModel
from ..models.customer import CustomerModel
from ..models.loan import LoanModel
from ..models.payment import PaymentModel, InvestorPaymentModel
from ..models.investor import InvestorModel



ZERO = Decimal("0.00")


def money(value):
    if value is None:
        return ZERO
    return Decimal(str(value)).quantize(
        Decimal("0.01")
    )


def get_company(company_id=None):
    if company_id is not None:
        company = db.session.get(CompanyModel, company_id)

        if not company:
            raise ValueError("Company not found.")

        return company

    configured_company_id = current_app.config.get("COMPANY_ID")

    if configured_company_id:
        company = db.session.get(
            CompanyModel,
            configured_company_id
        )

        if not company:
            raise ValueError("Configured company was not found.")
        return company

    companies = (
        CompanyModel.query.order_by(CompanyModel.id.asc()).limit(2).all()
    )

    if len(companies) == 1:
        return companies[0]

    if not companies:
        raise ValueError("No company has been configured.")

    raise ValueError(
        "Multiple companies exist. "
        "Configure COMPANY_ID.")


def parse_report_date(value, field_name):
    if not value:
        raise ValueError(f"{field_name} is required.")

    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"{field_name} must use YYYY-MM-DD format.")


def get_previous_period(start_date, end_date):
    period_length = (end_date - start_date).days + 1
    previous_end = (start_date - timedelta(days=1))
    previous_start = (previous_end - timedelta(days=period_length - 1))

    return previous_start, previous_end


def get_overview_report(company, start_date, end_date):
    loans_issued = (
        db.session.query(func.count(LoanModel.id))
        .filter(
            LoanModel.company_id == company.id,
            LoanModel.loan_date >= start_date,
            LoanModel.loan_date <= end_date,
        )
        .scalar()
        or 0
    )

    principal_issued = money(
        db.session.query(func.coalesce(func.sum(
                    LoanModel.principal
                ),
                0
            )
        )
        .filter(
            LoanModel.company_id == company.id,
            LoanModel.loan_date >= start_date,
            LoanModel.loan_date <= end_date,
        )
        .scalar()
    )

    interest_expected = money(
        db.session.query(
            func.coalesce(
                func.sum(
                    LoanModel.interest_amount
                ),
                0
            )
        )
        .filter(
            LoanModel.company_id == company.id,
            LoanModel.loan_date >= start_date,
            LoanModel.loan_date <= end_date,
        )
        .scalar()
    )

    collections = money(
        db.session.query(
            func.coalesce(
                func.sum(
                    PaymentModel.amount
                ),
                0
            )
        )
        .filter(
            PaymentModel.company_id == company.id,
            PaymentModel.payment_date >= start_date,
            PaymentModel.payment_date <= end_date,
        )
        .scalar()
    )

    interest_collected = money(
        db.session.query(
            func.coalesce(
                func.sum(
                    PaymentModel.interest_amount
                ),
                0
            )
        )
        .filter(
            PaymentModel.company_id == company.id,
            PaymentModel.payment_date >= start_date,
            PaymentModel.payment_date <= end_date,
        )
        .scalar()
    )

    principal_collected = money(
        db.session.query(
            func.coalesce(
                func.sum(
                    PaymentModel.principal_amount
                ),
                0
            )
        )
        .filter(
            PaymentModel.company_id == company.id,
            PaymentModel.payment_date >= start_date,
            PaymentModel.payment_date <= end_date,
        )
        .scalar()
    )
    outstanding = money(
        db.session.query(
            func.coalesce(
                func.sum(
                    LoanModel.balance
                ),
                0
            )
        )
        .filter(
            LoanModel.company_id == company.id,
            LoanModel.status == "ACTIVE",
        )
        .scalar()
    )

    active_loans = (
        db.session.query(
            func.count(LoanModel.id)
        )
        .filter(
            LoanModel.company_id == company.id,
            LoanModel.status == "ACTIVE",
        )
        .scalar()
        or 0
    )

    completed_loans = (
        db.session.query(
            func.count(LoanModel.id)
        )
        .filter(
            LoanModel.company_id == company.id,
            LoanModel.status == "PAID",
        )
        .scalar()
        or 0
    )

    overdue_loans = (
        db.session.query(
            func.count(LoanModel.id)
        )
        .filter(
            LoanModel.company_id == company.id,
            LoanModel.status == "ACTIVE",
            LoanModel.due_date < date.today(),
        )
        .scalar()
        or 0
    )

    overdue_amount = money(
        db.session.query(
            func.coalesce(
                func.sum(
                    LoanModel.balance
                ),
                0
            )
        )
        .filter(
            LoanModel.company_id == company.id,
            LoanModel.status == "ACTIVE",
            LoanModel.due_date < date.today(),
        )
        .scalar()
    )

    total_customers = (
        db.session.query(
            func.count(CustomerModel.id)
        )
        .scalar()
        or 0
    )

    active_borrowers = (
        db.session.query(
            func.count(
                func.distinct(
                    LoanModel.customer_id
                )
            )
        )
        .filter(
            LoanModel.company_id == company.id,
            LoanModel.status == "ACTIVE",
        )
        .scalar()
        or 0
    )

    investor_capital = money(
        db.session.query(
            func.coalesce(
                func.sum(
                    InvestorModel.principal
                ),
                0
            )
        )
        .filter(
            InvestorModel.company_id == company.id
        )
        .scalar()
    )

    investor_balance = money(
        db.session.query(
            func.coalesce(
                func.sum(
                    InvestorModel.balance
                ),
                0
            )
        )
        .filter(
            InvestorModel.company_id == company.id,
            InvestorModel.status == "ACTIVE",
        )
        .scalar()
    )

    investor_returns_paid = money(
        db.session.query(
            func.coalesce(
                func.sum(
                    InvestorPaymentModel.interest_amount
                ),
                0
            )
        )
        .filter(
            InvestorPaymentModel.company_id == company.id,
            InvestorPaymentModel.payment_date >= start_date,
            InvestorPaymentModel.payment_date <= end_date,
        )
        .scalar()
    )

    return {
        "loans_issued": loans_issued,
        "principal_issued": str(principal_issued),
        "interest_expected": str(interest_expected),

        "collections": str(collections),
        "principal_collected": str(
            principal_collected
        ),
        "interest_collected": str(
            interest_collected
        ),

        "outstanding": str(outstanding),
        "active_loans": active_loans,
        "completed_loans": completed_loans,
        "overdue_loans": overdue_loans,
        "overdue_amount": str(
            overdue_amount
        ),

        "total_customers": total_customers,
        "active_borrowers": active_borrowers,

        "investor_capital": str(
            investor_capital
        ),
        "investor_balance": str(
            investor_balance
        ),
        "investor_returns_paid": str(
            investor_returns_paid
        ),
    }


def get_loans_report(company, start_date, end_date):
    issued_query = (LoanModel.query
        .filter(
            LoanModel.company_id == company.id,
            LoanModel.loan_date >= start_date,
            LoanModel.loan_date <= end_date,
        )
    )

    issued_count = (issued_query.with_entities(
            func.count(LoanModel.id)
        )
        .scalar()
        or 0
    )

    principal_issued = money(issued_query.with_entities(
            func.coalesce(
                func.sum(
                    LoanModel.principal
                ),
                0
            )
        )
        .scalar()
    )

    interest_issued = money(issued_query.with_entities(
            func.coalesce(
                func.sum(
                    LoanModel.interest_amount
                ),
                0
            )
        )
        .scalar()
    )

    active_count = (LoanModel.query
        .filter(
            LoanModel.company_id == company.id,
            LoanModel.status == "ACTIVE",
        )
        .count()
    )

    paid_count = (LoanModel.query
        .filter(
            LoanModel.company_id == company.id,
            LoanModel.status == "PAID",
        )
        .count()
    )

    overdue_query = (LoanModel.query
        .filter(
            LoanModel.company_id == company.id,
            LoanModel.status == "ACTIVE",
            LoanModel.due_date < date.today(),
        )
    )

    overdue_count = (overdue_query
        .with_entities(
            func.count(LoanModel.id)
        )
        .scalar()
        or 0
    )

    overdue_balance = money(overdue_query
        .with_entities(
            func.coalesce(
                func.sum(
                    LoanModel.balance
                ),
                0
            )
        )
        .scalar()
    )

    outstanding_balance = money(db.session.query(
            func.coalesce(
                func.sum(
                    LoanModel.balance
                ),
                0
            )
        )
        .filter(
            LoanModel.company_id == company.id,
            LoanModel.status == "ACTIVE",
        )
        .scalar()
    )

    average_loan = (
        principal_issued /
        issued_count
        if issued_count
        else ZERO
    )

    return {
        "issued_count": issued_count,
        "principal_issued": str(
            principal_issued
        ),
        "interest_expected": str(
            interest_issued
        ),
        "average_loan": str(
            money(average_loan)
        ),
        "active_count": active_count,
        "paid_count": paid_count,
        "overdue_count": overdue_count,
        "overdue_balance": str(
            overdue_balance
        ),
        "outstanding_balance": str(
            outstanding_balance
        ),
    }


def get_collections_report(company, start_date, end_date):
    payment_query = (
        PaymentModel.query
        .filter(
            PaymentModel.company_id == company.id,
            PaymentModel.payment_date >= start_date,
            PaymentModel.payment_date <= end_date,
        )
    )

    payment_count = (
        payment_query
        .with_entities(
            func.count(PaymentModel.id)
        )
        .scalar()
        or 0
    )

    total_collected = money(
        payment_query
        .with_entities(
            func.coalesce(
                func.sum(
                    PaymentModel.amount
                ),
                0
            )
        )
        .scalar()
    )

    principal_collected = money(
        payment_query
        .with_entities(
            func.coalesce(
                func.sum(
                    PaymentModel.principal_amount
                ),
                0
            )
        )
        .scalar()
    )

    interest_collected = money(
        payment_query
        .with_entities(
            func.coalesce(
                func.sum(
                    PaymentModel.interest_amount
                ),
                0
            )
        )
        .scalar()
    )

    outstanding = money(
        db.session.query(
            func.coalesce(
                func.sum(
                    LoanModel.balance
                ),
                0
            )
        )
        .filter(
            LoanModel.company_id == company.id,
            LoanModel.status == "ACTIVE",
        )
        .scalar()
    )

    expected_interest = money(
        db.session.query(
            func.coalesce(
                func.sum(
                    LoanModel.interest_amount
                ),
                0
            )
        )
        .filter(
            LoanModel.company_id == company.id,
            LoanModel.loan_date <= end_date,
            LoanModel.status.in_(
                ["ACTIVE", "PAID"]
            ),
        )
        .scalar()
    )

    collection_rate = ZERO

    if expected_interest + outstanding > ZERO:
        collection_rate = (
            total_collected /
            (
                expected_interest +
                outstanding
            )
        ) * Decimal("100")

    return {
        "payment_count": payment_count,
        "total_collected": str(
            total_collected
        ),
        "principal_collected": str(
            principal_collected
        ),
        "interest_collected": str(
            interest_collected
        ),
        "outstanding": str(
            outstanding
        ),
        "collection_rate": str(
            money(collection_rate)
        ),
    }


def get_customers_report(company):
    total_customers = (
        db.session.query(
            func.count(CustomerModel.id)
        )
        .scalar()
        or 0
    )

    active_borrowers = (
        db.session.query(
            func.count(
                func.distinct(
                    LoanModel.customer_id
                )
            )
        )
        .filter(
            LoanModel.company_id == company.id,
            LoanModel.status == "ACTIVE",
        )
        .scalar()
        or 0
    )

    customers_with_loans = (
        db.session.query(
            func.count(
                func.distinct(
                    LoanModel.customer_id
                )
            )
        )
        .filter(
            LoanModel.company_id == company.id
        )
        .scalar()
        or 0
    )

    completed_borrowers = (
        db.session.query(
            func.count(
                func.distinct(
                    LoanModel.customer_id
                )
            )
        )
        .filter(
            LoanModel.company_id == company.id,
            LoanModel.status == "PAID",
        )
        .scalar()
        or 0
    )

    return {
        "total_customers": total_customers,
        "active_borrowers": active_borrowers,
        "customers_with_loans": customers_with_loans,
        "completed_borrowers": completed_borrowers,
    }


def get_investors_report(company, start_date, end_date):
    investor_count = (
        InvestorModel.query
        .filter(
            InvestorModel.company_id == company.id
        )
        .count()
    )

    active_investors = (
        InvestorModel.query
        .filter(
            InvestorModel.company_id == company.id,
            InvestorModel.status == "ACTIVE",
        )
        .count()
    )

    total_principal = money(
        db.session.query(
            func.coalesce(
                func.sum(
                    InvestorModel.principal
                ),
                0
            )
        )
        .filter(
            InvestorModel.company_id == company.id
        )
        .scalar()
    )

    outstanding_balance = money(
        db.session.query(
            func.coalesce(
                func.sum(
                    InvestorModel.balance
                ),
                0
            )
        )
        .filter(
            InvestorModel.company_id == company.id,
            InvestorModel.status == "ACTIVE",
        )
        .scalar()
    )

    total_due = money(
        db.session.query(
            func.coalesce(
                func.sum(
                    InvestorModel.total_due
                ),
                0
            )
        )
        .filter(
            InvestorModel.company_id == company.id,
            InvestorModel.status == "ACTIVE",
        )
        .scalar()
    )

    returns_paid = money(
        db.session.query(
            func.coalesce(
                func.sum(
                    InvestorPaymentModel.interest_amount
                ),
                0
            )
        )
        .filter(
            InvestorPaymentModel.company_id == company.id,
            InvestorPaymentModel.payment_date >= start_date,
            InvestorPaymentModel.payment_date <= end_date,
        )
        .scalar()
    )

    principal_paid = money(
        db.session.query(
            func.coalesce(
                func.sum(
                    InvestorPaymentModel.principal_amount
                ),
                0
            )
        )
        .filter(
            InvestorPaymentModel.company_id == company.id,
            InvestorPaymentModel.payment_date >= start_date,
            InvestorPaymentModel.payment_date <= end_date,
        )
        .scalar()
    )

    total_paid = money(
        db.session.query(
            func.coalesce(
                func.sum(
                    InvestorPaymentModel.amount
                ),
                0
            )
        )
        .filter(
            InvestorPaymentModel.company_id == company.id,
            InvestorPaymentModel.payment_date >= start_date,
            InvestorPaymentModel.payment_date <= end_date,
        )
        .scalar()
    )

    return {
        "investor_count": investor_count,
        "active_investors": active_investors,
        "total_principal": str(
            total_principal
        ),
        "outstanding_balance": str(
            outstanding_balance
        ),
        "total_due": str(
            total_due
        ),
        "returns_paid": str(
            returns_paid
        ),
        "principal_paid": str(
            principal_paid
        ),
        "total_paid": str(
            total_paid
        ),
    }


def get_reports(start_date, end_date, company_id=None):
    if end_date < start_date:
        raise ValueError(
            "Report end date cannot be before start date."
        )

    company = get_company(
        company_id
    )

    previous_start, previous_end = (
        get_previous_period(
            start_date,
            end_date
        )
    )

    overview = get_overview_report(
        company,
        start_date,
        end_date
    )

    previous_overview = get_overview_report(
        company,
        previous_start,
        previous_end
    )

    loans = get_loans_report(
        company,
        start_date,
        end_date
    )

    collections = get_collections_report(
        company,
        start_date,
        end_date
    )

    customers = get_customers_report(
        company
    )

    investors = get_investors_report(
        company,
        start_date,
        end_date
    )

    return {
        "company": {
            "id": company.id,
            "name": company.name,
        },

        "period": {
            "from": start_date.isoformat(),
            "to": end_date.isoformat(),
            "previous_from": previous_start.isoformat(),
            "previous_to": previous_end.isoformat(),
        },

        "overview": overview,

        "comparison": {
            "previous": previous_overview,
        },

        "loans": loans,

        "collections": collections,

        "customers": customers,

        "investors": investors,
    }