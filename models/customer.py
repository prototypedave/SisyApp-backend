import uuid
from ..security.passwords import hash_password, verify_password
from ..extensions import db


class CustomerModel(db.Model):
    __tablename__ = "customers"

    id = db.Column(db.String(9), primary_key=True, default=lambda: str(uuid.uuid4().hex[:9]))
    first_name = db.Column(db.String(80), nullable=False,)
    last_name = db.Column(db.String(80), nullable=False,)
    email = db.Column(db.String(255), nullable=True, unique=True, index=True)
    mobile = db.Column(db.String(10), nullable=False, unique=True, index=True)
    salary = db.Column(db.Double, nullable=False)
    gender = db.Column(db.String(1), nullable=False)
    other_mobile = db.Column(db.String(10), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_owner = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    last_login_at = db.Column(db.DateTime(timezone=True), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    requests = db.Column(db.Integer, nullable=False, default=0)
    loan_limit = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    loan_balance = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    record = db.Column(db.Boolean, nullable=False, default=True)
    blacklisted = db.Column(db.Boolean, nullable=False, default=False, index=True)
    blacklisted_at = db.Column(db.DateTime(timezone=True), nullable=True)
    blacklist_reason = db.Column(db.String(500), nullable=True)
    archived = db.Column(db.Boolean, nullable=False, default=False, index=True)
    archived_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now(), onupdate=db.func.now())
    loans = db.relationship("LoanModel", back_populates="customer", lazy=True)
    

    def profile(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "gender": self.gender,
            "mobile": self.mobile,
            "other_mobile": self.other_mobile,
            "email": self.email,
            "salary": ( str(self.salary) if self.salary is not None else None ),
            "notes": self.notes,
            "requests": self.requests,
            "loan_limit": (str(self.loan_limit) if self.loan_limit is not None else "0.00"),
            "record": self.record,
            "blacklisted": self.blacklisted,
            "blacklisted_at": (self.blacklisted_at.isoformat() if self.blacklisted_at else None),
            "blacklist_reason": self.blacklist_reason,
            "archived": self.archived,
            "archived_at": (self.archived_at.isoformat() if self.archived_at else None),
            "created_at": (self.created_at.isoformat() if self.created_at else None),
            "updated_at": (self.updated_at.isoformat() if self.updated_at else None), 
        }

    def parse_loan(self, amount, interest):
        self.requests += 1
        self.loan_limit -= amount
        self.loan_balance += (amount + interest)
        
