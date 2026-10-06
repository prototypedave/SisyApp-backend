from ..extensions import db


class PaymentModel(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey("loans.id"), nullable=False, index=True)
    payment_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False, index=True)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    principal_amount = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    interest_amount = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    payment_method = db.Column(db.String(20), nullable=False, default="M-Pesa")
    reference = db.Column(db.String(100), nullable=True)
    payment_date = db.Column(db.Date, nullable=False, server_default=db.func.current_date())
    notes = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())

    loan = db.relationship("LoanModel", back_populates="payments")
    company = db.relationship("CompanyModel", back_populates="payments")

    __table_args__ = (
        db.Index("ix_payments_company_payment_date", "company_id", "payment_date"),
        )


class InvestorPaymentModel(db.Model):
    __tablename__ = "investor_payments"

    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey("investors.id"), nullable=False, index=True)
    payment_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False, index=True)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    principal_amount = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    interest_amount = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    payment_method = db.Column(db.String(20), nullable=False, default="M-Pesa")
    reference = db.Column(db.String(100), nullable=True)
    payment_date = db.Column(db.Date, nullable=False, server_default=db.func.current_date())
    notes = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())

    investor = db.relationship("InvestorModel", back_populates="payments")
    company = db.relationship("CompanyModel", back_populates="investor_payments")