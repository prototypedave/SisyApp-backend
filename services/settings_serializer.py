def serialize_fund_adjustment(adjustment):
    user = adjustment.user

    return {
        "id": adjustment.id,
        "company_id": adjustment.company_id,
        "user_id": adjustment.user_id,
        "user": {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
        } if user else None,
        "adjustment_type": adjustment.adjustment_type,
        "amount": str(adjustment.amount),
        "balance_before": str(
            adjustment.balance_before
        ),
        "balance_after": str(
            adjustment.balance_after
        ),
        "reason": adjustment.reason,
        "created_at": (
            adjustment.created_at.isoformat()
            if adjustment.created_at
            else None
        ),
    }