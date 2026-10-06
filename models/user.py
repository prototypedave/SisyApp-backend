import uuid
from ..security.passwords import hash_password, verify_password
from ..extensions import db


class UserModel(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    first_name = db.Column(db.String(80), nullable=False,)
    last_name = db.Column(db.String(80), nullable=False,)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    phone = db.Column(db.String(20), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_owner = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    last_login_at = db.Column(db.DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<UserModel {self.email}>"

    def set_password(self, password: str) -> None:
        self.password_hash = hash_password(password)

    def check_password(self, password: str) -> bool:
        return verify_password(self.password_hash, password)

    def profile(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "is_active": self.is_active,
            "created_at": (self.created_at.isoformat() if self.created_at else None),
            "last_login_at": (self.last_login_at.isoformat() if self.last_login_at else None),
        }