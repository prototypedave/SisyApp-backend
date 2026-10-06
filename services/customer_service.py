from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from sqlalchemy import or_

from ..extensions import db
from ..models import CustomerModel


def normalize_mobile(value):
    if value is None:
        return None

    value = str(value).strip()
    if not value:
        return None

    return value


def normalize_email(value):
    if value is None:
        return None

    value = str(value).strip().lower()
    return value or None


def validate_mobile(value):
    if not value:
        return False

    return (value.isdigit() and len(value) == 10)


def parse_decimal(value, field_name):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"{field_name} must be a valid number.")

    if amount < 0:
        raise ValueError(f"{field_name} cannot be negative.")

    return amount


def create_customer(data):
    first_name = str(data.get("first_name", "")).strip()
    last_name = str(data.get("last_name", "")).strip()
    mobile = normalize_mobile(data.get("mobile"))
    other_mobile = normalize_mobile(data.get("other_mobile"))
    email = normalize_email(data.get("email"))

    if not first_name:
        raise ValueError("First name is required.")

    if not last_name:
        raise ValueError("Last name is required.")

    if not validate_mobile(mobile):
        raise ValueError("Mobile number must contain exactly 10 digits.")

    if (other_mobile and not validate_mobile(other_mobile)):
        raise ValueError("Other mobile number must contain exactly 10 digits.")

    if (other_mobile and other_mobile == mobile):
        raise ValueError("Other mobile number must differ from the primary mobile number.")

    existing_mobile = (CustomerModel.query.filter_by(mobile=mobile).first())
    if existing_mobile:
        raise ValueError("A customer with this mobile number already exists.")

    if email:
        existing_email = (CustomerModel.query.filter_by(email=email).first())
        if existing_email:
            raise ValueError("A customer with this email already exists.")

    gender = data.get("gender")

    if gender:
        gender = str(gender).strip().upper()
        if gender not in {"M", "F"}:
            raise ValueError("Gender must be M or F.")

    salary = data.get("salary")
    if salary in (None, ""):
        salary = None
    else:
        salary = parse_decimal(salary, "Salary")

    loan_limit = salary * Decimal("0.3") if salary is not None else Decimal("0.00")
    loan_limit = parse_decimal(
        loan_limit,
        "Loan limit"
    )

    customer = CustomerModel(
        first_name=first_name,
        last_name=last_name,
        gender=gender,
        mobile=mobile,
        other_mobile=other_mobile,
        email=email,
        salary=salary,
        notes=str(data.get("notes", "")).strip() or None,
        loan_limit=loan_limit,
        requests=0,
        record=True,
        blacklisted=False,
        archived=False,
    )

    db.session.add(customer)
    db.session.flush()

    return customer


def get_customer(customer_id):
    return (
        CustomerModel.query.filter_by(id=customer_id).first())


def list_customers(search=None, page=1, per_page=20, include_archived=False):
    query = CustomerModel.query
    if not include_archived:
        query = query.filter(CustomerModel.archived.is_(False))

    search = (search.strip() if search else None)
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                CustomerModel.id.ilike(pattern),
                CustomerModel.first_name.ilike(pattern),
                CustomerModel.last_name.ilike(pattern),
                CustomerModel.mobile.ilike(pattern),
                CustomerModel.other_mobile.ilike(pattern),
                CustomerModel.email.ilike(pattern),
            )
        )

    query = query.order_by(
        CustomerModel.created_at.desc()
    )

    return query.paginate(page=page, per_page=per_page, error_out=False)


def update_customer(customer, data):
    if customer.archived:
        raise ValueError("Archived customers cannot be edited.")

    if "first_name" in data:
        first_name = str(data["first_name"]).strip()
        if not first_name:
            raise ValueError("First name is required.")

        customer.first_name = first_name

    if "last_name" in data:
        last_name = str(data["last_name"]).strip()

        if not last_name:
            raise ValueError("Last name is required.")

        customer.last_name = last_name

    if "gender" in data:
        gender = data["gender"]

        if gender:
            gender = str(gender).strip().upper()
            if gender not in {"M", "F"}:
                raise ValueError("Gender must be M or F.")

        customer.gender = gender

    if "mobile" in data:
        mobile = normalize_mobile(data["mobile"])
        if not validate_mobile(mobile):
            raise ValueError("Mobile number must contain exactly 10 digits.")

        existing = (
            CustomerModel.query.filter(
                CustomerModel.mobile == mobile,
                CustomerModel.id != customer.id
            ).first())

        if existing:
            raise ValueError("A customer with this mobile number already exists.")

        customer.mobile = mobile

    if "other_mobile" in data:
        other_mobile = normalize_mobile(data["other_mobile"])

        if (other_mobile and not validate_mobile(other_mobile)):
            raise ValueError("Other mobile number must contain exactly 10 digits.")

        if (other_mobile and other_mobile == customer.mobile):
            raise ValueError("Other mobile number must differ from the primary mobile number.")

        customer.other_mobile = other_mobile

    if "email" in data:
        email = normalize_email(data["email"])
        if email:
            existing = (
                CustomerModel.query.filter(
                    CustomerModel.email == email,
                    CustomerModel.id != customer.id
                ).first()
            )

            if existing:
                raise ValueError("A customer with this email already exists.")

        customer.email = email

    if "salary" in data:
        salary = data["salary"]

        if salary in (None, ""):
            customer.salary = None
        else:
            customer.salary = parse_decimal(salary, "Salary")
            existing_loan_balance = (CustomerModel.query.filter_by(id=customer.id).first().loan_balance)
            loan_limit = customer.salary * Decimal("0.3") + existing_loan_balance  
            customer.loan_limit = parse_decimal(str(loan_limit), "Loan limit")

    if "notes" in data:
        customer.notes = (
            str(data["notes"]).strip()
            or None
        )

    return customer


def archive_customer(customer):
    if customer.archived:
        raise ValueError("Customer is already archived.")

    customer.archived = True
    customer.archived_at = datetime.now(timezone.utc)
    return customer


def blacklist_customer(customer, reason):
    if customer.archived:
        raise ValueError("Archived customers cannot be blacklisted.")
    reason = (
        str(reason).strip() if reason else "")

    if not reason:
        raise ValueError("A blacklist reason is required.")

    customer.blacklisted = True
    customer.blacklisted_at = datetime.now(timezone.utc)
    customer.blacklist_reason = reason

    return customer


def unblacklist_customer(customer):
    customer.blacklisted = False
    customer.blacklisted_at = None
    customer.blacklist_reason = None

    return customer