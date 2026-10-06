from ..extensions import db


class LoanModel(db.Model):
    __tablename__ = "loans"

    id = db.Column(db.Integer, primary_key=True)
    loan_number = db.Column(db.String(20), unique=True, nullable=True, index=True)
    customer_id = db.Column(db.String(36), db.ForeignKey("customers.id"), nullable=False, index=True)
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False, index=True)
    principal = db.Column(db.Numeric(14, 2), nullable=False)
    interest_rate = db.Column(db.Numeric(8, 4), nullable=False)
    interest_amount = db.Column(db.Numeric(14, 2), nullable=False)
    total_due = db.Column(db.Numeric(14, 2), nullable=False)
    balance = db.Column(db.Numeric(14, 2), nullable=False)
    loan_date = db.Column(db.Date, nullable=False, server_default=db.func.current_date())
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="ACTIVE", index=True)
    completion_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    updated_at = db.Column( db.DateTime(timezone=True), nullable=False, server_default=db.func.now(), onupdate=db.func.now())

    customer = db.relationship("CustomerModel", back_populates="loans")
    company = db.relationship("CompanyModel", back_populates="loans")
    payments = db.relationship("PaymentModel", back_populates="loan", lazy=True)

    __table_args__ = (
        db.Index("ix_loans_company_status", "company_id", "status"),
        db.Index("ix_loans_company_due_date", "company_id", "due_date"),
        db.Index("ix_loans_company_loan_date", "company_id", "loan_date"),
    )

    @property
    def paid(self):
        return self.status == "PAID"

    def apply_payment(self, amount, payment_date):
        if amount <= 0:
            raise ValueError("Payment amount must be greater than zero.")

        if self.status == "PAID":
            raise ValueError("This loan has already been fully paid.")

        if amount > self.balance:
            raise ValueError("Payment cannot exceed the outstanding balance.")

        self.balance -= amount

        if self.balance == 0:
            self.status = "PAID"
            self.completion_date = payment_date

        return self