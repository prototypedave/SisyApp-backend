from decimal import Decimal, ROUND_HALF_UP

from ..extensions import db

from ..models.company import CompanyModel
from ..models.business_settings import BusinessSettingsModel
from ..models.company_fund_adjustment import (
    CompanyFundAdjustmentModel,
)
from ..models.user import UserModel

from ..services.password_service import (
    hash_password,
    verify_password,
)
from ..services.session_service import (
    revoke_all_user_sessions,
)


CENT = Decimal("0.01")


def money(value):
    return Decimal(str(value)).quantize(
        CENT,
        rounding=ROUND_HALF_UP
    )


def get_company(company_id=None):
    if company_id is not None:
        company = db.session.get(
            CompanyModel,
            company_id
        )

        if not company:
            raise ValueError(
                "Company not found."
            )

        return company

    company = CompanyModel.query.first()

    if not company:
        raise ValueError(
            "Company has not been configured."
        )

    return company


def get_or_create_settings(company):
    settings = BusinessSettingsModel.query.filter_by(
        company_id=company.id
    ).first()

    if not settings:
        settings = BusinessSettingsModel(
            company_id=company.id
        )

        db.session.add(settings)
        db.session.flush()

    return settings


def get_settings(company_id=None):
    company = get_company(company_id)
    settings = get_or_create_settings(company)

    return {
        "company": {
            "id": company.id,
            "name": company.name,
            "initial_amount": str(
                money(company.initial_amount)
            ),
            "current_amount": str(
                money(company.current_amount)
            ),
        },
        "settings": {
            "currency": settings.currency,
            "default_interest_rate": str(
                settings.default_interest_rate
            ),
            "minimum_loan_amount": str(
                settings.minimum_loan_amount
            ),
            "maximum_loan_amount": (
                str(settings.maximum_loan_amount)
                if settings.maximum_loan_amount is not None
                else None
            ),
            "loan_grace_days": settings.loan_grace_days,
            "allow_partial_payments": (
                settings.allow_partial_payments
            ),
        },
    }


def update_business(
    company,
    name,
):
    name = str(name).strip()

    if not name:
        raise ValueError(
            "Business name is required."
        )

    if len(name) > 120:
        raise ValueError(
            "Business name cannot exceed 120 characters."
        )

    company.name = name

    return company


def update_operational_settings(
    company,
    currency=None,
    default_interest_rate=None,
    minimum_loan_amount=None,
    maximum_loan_amount=None,
    loan_grace_days=None,
    allow_partial_payments=None,
):
    settings = get_or_create_settings(company)

    if currency is not None:
        currency = str(currency).strip().upper()

        if not currency:
            raise ValueError(
                "Currency is required."
            )

        if len(currency) > 10:
            raise ValueError(
                "Currency is too long."
            )

        settings.currency = currency

    if default_interest_rate is not None:
        rate = Decimal(
            str(default_interest_rate)
        )

        if rate < 0:
            raise ValueError(
                "Interest rate cannot be negative."
            )

        if rate > 100:
            raise ValueError(
                "Interest rate cannot exceed 100%."
            )

        settings.default_interest_rate = rate

    if minimum_loan_amount is not None:
        minimum = money(
            minimum_loan_amount
        )

        if minimum < 0:
            raise ValueError(
                "Minimum loan amount cannot be negative."
            )

        settings.minimum_loan_amount = minimum

    if maximum_loan_amount is not None:
        maximum = money(
            maximum_loan_amount
        )

        if maximum <= 0:
            raise ValueError(
                "Maximum loan amount must be greater than zero."
            )

        if (
            settings.minimum_loan_amount
            and maximum < settings.minimum_loan_amount
        ):
            raise ValueError(
                "Maximum loan amount cannot be below the minimum."
            )

        settings.maximum_loan_amount = maximum

    if loan_grace_days is not None:
        grace_days = int(loan_grace_days)

        if grace_days < 0:
            raise ValueError(
                "Grace days cannot be negative."
            )

        if grace_days > 365:
            raise ValueError(
                "Grace period cannot exceed 365 days."
            )

        settings.loan_grace_days = grace_days

    if allow_partial_payments is not None:
        settings.allow_partial_payments = bool(
            allow_partial_payments
        )

    return settings


def change_owner_password(
    user,
    current_password,
    new_password,
):
    if not current_password:
        raise ValueError(
            "Current password is required."
        )

    if not new_password:
        raise ValueError(
            "New password is required."
        )

    if not verify_password(
        user.password_hash,
        current_password
    ):
        raise ValueError(
            "Current password is incorrect."
        )

    if len(new_password) < 12:
        raise ValueError(
            "New password must be at least 12 characters."
        )

    if current_password == new_password:
        raise ValueError(
            "New password must be different from the current password."
        )

    user.password_hash = hash_password(
        new_password
    )

    revoke_all_user_sessions(
        user.id
    )

    return user


def adjust_company_funds(
    company,
    user,
    adjustment_type,
    amount,
    reason,
):
    amount = money(amount)

    if amount <= 0:
        raise ValueError(
            "Amount must be greater than zero."
        )

    adjustment_type = str(
        adjustment_type
    ).strip().upper()

    if adjustment_type not in {
        "ADD",
        "REMOVE",
    }:
        raise ValueError(
            "Adjustment type must be ADD or REMOVE."
        )

    reason = str(reason or "").strip()

    if not reason:
        raise ValueError(
            "A reason is required for fund adjustments."
        )

    if len(reason) > 500:
        raise ValueError(
            "Reason cannot exceed 500 characters."
        )

    # Lock the company row so two simultaneous
    # adjustments cannot overwrite each other.
    company = (
        CompanyModel.query
        .filter_by(id=company.id)
        .with_for_update()
        .first()
    )

    if not company:
        raise ValueError(
            "Company not found."
        )

    balance_before = money(
        company.current_amount
    )

    if adjustment_type == "ADD":
        balance_after = money(
            balance_before + amount
        )

    else:
        if amount > balance_before:
            raise ValueError(
                "Cannot remove more funds than the company currently has."
            )

        balance_after = money(
            balance_before - amount
        )

    company.current_amount = balance_after

    adjustment = CompanyFundAdjustmentModel(
        company_id=company.id,
        user_id=user.id,
        adjustment_type=adjustment_type,
        amount=amount,
        balance_before=balance_before,
        balance_after=balance_after,
        reason=reason,
    )

    db.session.add(adjustment)
    db.session.flush()

    return adjustment