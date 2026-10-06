from datetime import datetime, timedelta, timezone
from ..extensions import db
from ..models import SessionModel, UserModel
from flask import current_app
from ..security.passwords import password_needs_rehash


def get_current_utc():
    return datetime.now(timezone.utc)


def authenticate_user(email: str, password: str):
    if not email or not password:
        return None

    normalized_email = email.strip().lower()
    user = UserModel.query.filter_by(email=normalized_email).first()
    if user is None:
        return None

    if not user.is_active:
        return None

    if not user.check_password(password):
        return None

    if password_needs_rehash(user.password_hash):
        user.set_password(password)
        db.session.commit()

    return user


def create_session(user: UserModel):
    now = get_current_utc()
    duration_hours = current_app.config["SESSION_DURATION_HOURS"]

    token = SessionModel.generate_token()
    session = SessionModel(
        user_id=user.id,
        token_hash=SessionModel.hash_token(token),
        expires_at=now + timedelta(hours=duration_hours),
        last_used_at=now,
    )

    db.session.add(session)
    return session, token


def get_session_from_token(token: str, update_last_used=True):
    if not token:
        return None

    token_hash = (SessionModel.hash_token(token))
    session = (SessionModel.query.filter_by(token_hash=token_hash).first())
    if session is None:
        return None

    now = get_current_utc()
    idle_minutes = current_app.config["SESSION_IDLE_MINUTES"]

    if not session.is_valid(now, idle_minutes):
        return None

    if update_last_used:
        session.last_used_at = now
        db.session.commit()
    return session


def revoke_session(token: str):
    session = get_session_from_token(token, update_last_used=False,)
    if session is None:
        return False

    session.revoked_at = get_current_utc()
    return True