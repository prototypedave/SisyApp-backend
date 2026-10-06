from datetime import date
from decimal import Decimal
from datetime import date, timedelta
from flask import current_app
from sqlalchemy import func, or_
from ..extensions import db
from ..models.company import CompanyModel
from ..models.customer import CustomerModel
from ..models.loan import LoanModel
from ..models.payment import PaymentModel


ZERO = Decimal("0.00")


def money(value):
    if value is None:
        return ZERO
    return Decimal(str(value)).quantize(
        Decimal("0.01")
    )


def get_dashboard_company(company_id=None):
    if company_id is not None:
        company = db.session.get(CompanyModel, company_id)
        if not company:
            raise ValueError("Company not found.")
        return company

    configured_company_id = current_app.config.get("COMPANY_ID")

    if configured_company_id:
        company = db.session.get(
            CompanyModel, configured_company_id)

        if not company:
            raise ValueError("Configured company was not found.")
        return company

    companies = (CompanyModel.query.order_by(CompanyModel.id.asc()).limit(2).all())
    if len(companies) == 1:
        return companies[0]

    if not companies:
        raise ValueError("No company has been configured.")

    raise ValueError(
        "Multiple companies exist. "
        "Configure COMPANY_ID."
    )


def get_month_boundaries(today):
    month_start = today.replace(day=1)
    if today.month == 12:
        next_month = date(today.year + 1,1,1)
    else:
        next_month = date(today.year,today.month + 1,1)
    return month_start, next_month


def query_active_loan(company):
    active_loan_query = (LoanModel.query.filter(
            LoanModel.company_id == company.id,
            LoanModel.status == "ACTIVE"
        )
    )

    active_loan_count = (active_loan_query.with_entities(
        func.count(LoanModel.id)).scalar() or 0
    )

    outstanding_amount = money(active_loan_query.with_entities(
        func.coalesce(
            func.sum(LoanModel.balance), 0
        )).scalar()
    )

    return active_loan_count, outstanding_amount


def query_outstanding_loan(company, today):
    overdue_query = (LoanModel.query.filter(
            LoanModel.company_id == company.id,
            LoanModel.status == "ACTIVE",
            LoanModel.due_date < today
        )
    )
    
    overdue_loan_count = (overdue_query.with_entities(
        func.count(LoanModel.id)).scalar() or 0
    )
    
    overdue_amount = money(overdue_query.with_entities(
            func.coalesce(
                func.sum(LoanModel.balance), 0
            )
        ).scalar()
    )

    return overdue_loan_count, overdue_amount


def query_due_today(company, today):
    due_today_query = (LoanModel.query.filter(
            LoanModel.company_id == company.id,
            LoanModel.status == "ACTIVE",
            LoanModel.due_date == today
        )
    )
    
    due_today_loan_count = (due_today_query.with_entities(
        func.count(LoanModel.id)).scalar() or 0
    )
    
    due_today_amount = money(due_today_query.with_entities(
        func.coalesce(
            func.sum(LoanModel.balance), 0)).scalar()
    )

    return due_today_loan_count, due_today_amount


def query_collections_for_the_month(company, month_start, next_month):
    collection_filter = (
        PaymentModel.company_id == company.id,
        PaymentModel.payment_date >= month_start,
        PaymentModel.payment_date < next_month,
    )
    
    collected_this_month = money(db.session.query(
        func.coalesce(
            func.sum(PaymentModel.amount), 0
        )).filter(*collection_filter).scalar()
    )
    
    principal_collected_this_month = money(db.session.query(
        func.coalesce(
            func.sum(PaymentModel.principal_amount), 0
        )).filter(*collection_filter).scalar()
    )
    
    interest_collected_this_month = money(db.session.query(
        func.coalesce(
            func.sum(PaymentModel.interest_amount), 0
        )).filter(*collection_filter).scalar()
    )

    return collected_this_month, principal_collected_this_month, interest_collected_this_month


def get_dashboard_summary(company_id=None):
    company = get_dashboard_company(company_id)
    today = date.today()
    month_start, next_month = (get_month_boundaries(today))

    active_loan_count, outstanding_amount = query_active_loan(company)
    overdue_loan_count, overdue_amount = query_outstanding_loan(company, today)
    due_today_loan_count, due_today_amount = query_due_today(company, today)
    collected_this_month, principal_collected_this_month, interest_collected_this_month = query_collections_for_the_month(company, month_start, next_month)

    loans_issued_filter = (
        LoanModel.company_id == company.id,
        LoanModel.loan_date >= month_start,
        LoanModel.loan_date < next_month,
    )

    loans_issued_this_month = money(db.session.query(
        func.coalesce(
            func.sum(LoanModel.principal), 0))
        .filter(*loans_issued_filter)
        .scalar()
    )

    loan_count_this_month = (db.session.query(
        func.count(LoanModel.id)).filter(*loans_issued_filter).scalar()
        or 0
    )

    customer_count = (db.session.query(
        func.count(CustomerModel.id)).scalar()
        or 0
    )

    active_customer_count = (db.session.query(
        func.count(
            func.distinct(LoanModel.customer_id)
        )).filter(
            LoanModel.company_id == company.id,
            LoanModel.status == "ACTIVE"
        ).scalar()
        or 0
    )

    recent_loans = (LoanModel.query.filter(
            LoanModel.company_id == company.id
        ).order_by(
            LoanModel.created_at.desc()
        ).limit(5).all()
    )

    recent_loan_data = []

    for loan in recent_loans:
        customer = loan.customer
        recent_loan_data.append({
            "type": "LOAN",
            "id": loan.id,
            "created_at": (loan.created_at.isoformat() if loan.created_at else None),
            "amount": str(money(loan.principal)),
            "status": loan.status,
            "customer": {
                "id": (customer.id if customer else None),
                "first_name": (customer.first_name if customer else None),
                "last_name": (customer.last_name if customer else None),
            }
        })

    recent_payments = (PaymentModel.query.filter(
            PaymentModel.company_id == company.id
        ).order_by(
            PaymentModel.created_at.desc()
        ).limit(5).all()
    )

    recent_payment_data = []

    for payment in recent_payments:
        loan = payment.loan

        customer = (loan.customer if loan else None)
        recent_payment_data.append({
            "type": "PAYMENT",
            "id": payment.id,
            "created_at": (payment.created_at.isoformat() if payment.created_at else None),
            "amount": str(money(payment.amount)),
            "payment_method": payment.payment_method,
            "reference": payment.reference,
            "loan_id": payment.loan_id,
            "customer": {
                "id": (customer.id if customer else None),
                "first_name": (customer.first_name if customer else None),
                "last_name": (customer.last_name if customer else None),
            }
        })

    activity = (recent_loan_data + recent_payment_data)
    activity.sort(key=lambda item: ( item["created_at"] or "" ),
        reverse=True
    )

    activity = activity[:8]

    return {
        "company": {
            "id": company.id,
            "name": company.name,
        },

        "financial": {
            "available_funds": str(money(company.current_amount)),
            "initial_funds": str(money(company.initial_amount)),
            "outstanding": str(outstanding_amount),
            "overdue_amount": str(overdue_amount),
            "due_today_amount": str(due_today_amount),
            "collected_this_month": str(collected_this_month),
            "principal_collected_this_month": str(principal_collected_this_month),
            "interest_collected_this_month": str(interest_collected_this_month),
            "loans_issued_this_month": str(loans_issued_this_month),
        },

        "loans": {
            "active": active_loan_count,
            "overdue": overdue_loan_count,
            "due_today": due_today_loan_count,
            "issued_this_month": loan_count_this_month,
        },

        "customers": {
            "total": customer_count,
            "active_borrowers": (active_customer_count),
        },

        "activity": activity,
        "attention": {
            "overdue_loans": overdue_loan_count,
            "due_today_loans": (due_today_loan_count),
        },

        "period": {
            "today": today.isoformat(),
            "month_start": (month_start.isoformat()),
            "month_end": ( next_month - timedelta(days=1)).isoformat(),
        },
    }