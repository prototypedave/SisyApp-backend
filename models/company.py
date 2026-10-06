from ..extensions import db


class CompanyModel(db.Model):
    __tablename__ = "company"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, default="SisyLoan")
    initial_amount = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    current_amount = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now(), onupdate=db.func.now())

    loans = db.relationship("LoanModel", back_populates="company", lazy=True)
    payments = db.relationship("PaymentModel", back_populates="company", lazy=True)
    investors = db.relationship("InvestorModel", back_populates="company", lazy=True)
    investor_payments = db.relationship("InvestorPaymentModel", back_populates="company", lazy=True)
    settings = db.relationship("BusinessSettingsModel", back_populates="company", uselist=False, cascade="all, delete-orphan")
    fund_adjustments = db.relationship("CompanyFundAdjustmentModel", back_populates="company", lazy=True)

    def available_funds(self):
        return self.current_amount

    def can_issue_loan(self, amount):
        return self.current_amount >= amount

    def reduce_funds(self, amount):
        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")

        if self.current_amount < amount:
            raise ValueError("Insufficient company funds.")

        self.current_amount -= amount

    def receive_payment(self, amount):
        if amount <= 0:
            raise ValueError("Payment amount must be greater than zero.")

        self.current_amount += amount