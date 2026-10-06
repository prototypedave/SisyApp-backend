from decimal import Decimal, InvalidOperation
from datetime import datetime
from flask import request, jsonify
from extensions import db
from models.kjf import LoanModel


def assign_loan(data, client, comp):
    try:
        amount = Decimal(data['amount'])

        if amount <= 0:
            return "Loan amount must be greater than zero", 400

    except (KeyError, InvalidOperation):
        return "Invalid loan amount", 400

    try:
        pay_date = datetime.strptime(
            data['pay_date'],
            '%Y-%m-%d'
        ).date()

    except (KeyError, ValueError):
        return "Invalid payment date", 400

    new_loan = LoanModel(
        client=client,
        company=comp,
        amount=amount
    )

    success, message = new_loan.assign_loan(pay_date)

    if not success:
        return message, 400

    return message, 201


def repay_loan(data, client):
    try:
        amount = Decimal(data['amount'])
        if amount <= 0:
            return "Payment amount must be greater than zero", 400
    except (KeyError, InvalidOperation):
        return "Invalid payment amount", 400
    try:
        payment_date = datetime.strptime(
            data['pay_date'],
            '%Y-%m-%d'
        ).date()
    except (KeyError, ValueError):
        return "Invalid payment date", 400
    
    loan = db.session.get(LoanModel, data["loan_id"])
    if not loan:
        return "No active loan found for this client", 404
    
    if payment_date < loan.created_at:
        return (f"Payment date cannot be before loan " 
                f"{loan.id} creation date", 400)

    
    msg, status_code = loan.repay_loan(amount, payment_date, data["method"])
    try:
        db.session.commit()
        return msg, status_code
    except Exception as e:
        db.session.rollback()
        return "Unable to save payment", 500

   
