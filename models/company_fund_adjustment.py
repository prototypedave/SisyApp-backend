from ..extensions import db


class CompanyFundAdjustmentModel(db.Model):
    __tablename__ = "company_fund_adjustments"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    adjustment_type = db.Column(db.String(10), nullable=False)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    balance_before = db.Column(db.Numeric(14, 2), nullable=False)
    balance_after = db.Column(db.Numeric(14, 2), nullable=False)
    reason = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    company = db.relationship("CompanyModel", back_populates="fund_adjustments")
    user = db.relationship("UserModel")