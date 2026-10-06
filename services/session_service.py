from datetime import datetime, timezone

from ..extensions import db
from ..models.session import SessionModel


def revoke_all_user_sessions(user_id):
    now = datetime.now(timezone.utc)

    (
        SessionModel.query
        .filter(
            SessionModel.user_id == user_id,
            SessionModel.revoked_at.is_(None),
        )
        .update(
            {
                SessionModel.revoked_at: now,
            },
            synchronize_session=False,
        )
    )

    db.session.flush()