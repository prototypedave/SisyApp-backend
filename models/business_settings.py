from ..extensions import db


class BusinessSettingsModel(db.Model):
    __tablename__ = "business_settings"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False, unique=True, index=True)
    currency = db.Column(db.String(10),nullable=False, default="KES")
    default_interest_rate = db.Column(db.Numeric(8, 4), nullable=False, default=10)
    minimum_loan_amount = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    maximum_loan_amount = db.Column(db.Numeric(14, 2), nullable=True)
    loan_grace_days = db.Column(db.Integer, nullable=False, default=0)
    allow_partial_payments = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now(), onupdate=db.func.now())
    company = db.relationship("CompanyModel", back_populates="settings")