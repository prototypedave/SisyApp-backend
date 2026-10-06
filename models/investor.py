from ..extensions import db


class InvestorModel(db.Model):
    __tablename__ = "investors"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False, index=True)
    first_name = db.Column(db.String(80), nullable=False,)
    last_name = db.Column(db.String(80), nullable=False,)
    email = db.Column(db.String(255), nullable=True, index=True)
    mobile = db.Column(db.String(10), nullable=False, index=True)
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
    payments = db.relationship("InvestorPaymentModel", back_populates="investor", lazy=True)
    company = db.relationship("CompanyModel", back_populates="investors")

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