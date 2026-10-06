from datetime import timedelta
import hashlib
import secrets
import uuid
from ..extensions import db


class SessionModel(db.Model):
    __tablename__ = "user_sessions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = db.Column(db.String(64), nullable=False, unique=True, index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    last_used_at = db.Column(db.DateTime(timezone=True), nullable=True)
    revoked_at = db.Column(db.DateTime(timezone=True), nullable=True)
    user = db.relationship("UserModel", backref=db.backref("sessions", lazy=True, cascade="all, delete-orphan"))

    @staticmethod
    def generate_token():
        return secrets.token_urlsafe(48)

    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def is_valid(self, now, idle_minutes=30):
        if self.revoked_at is not None:
            return False
        if self.expires_at <= now:
            return False
        if self.last_used_at is not None:
            idle_limit = (self.last_used_at + timedelta(minutes=idle_minutes))
            if idle_limit <= now:
                return False

        return True