from decimal import Decimal

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, jsonify, request
from flask_cors import CORS
from extensions import db, ma
from models.kjf import ClientModel, LoanModel, CompanyModel, PaymentModel, ActivityLogModel
from schemas import ClientSchema
from datetime import date, datetime, timedelta
from loans import assign_loan, repay_loan
from util import time_since

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/postgres'
    db.init_app(app)
    ma.init_app(app)
    CORS(app)

    with app.app_context():
        db.drop_all()
        db.create_all()
        db.session.add(CompanyModel(initial_amount=1000000, current_amount=1000000, rate=0.2, cost=0.3, id=7685))
        db.session.commit()

    return app

app = create_app()
client_schema = ClientSchema()        
clients_schema = ClientSchema(many=True)


@app.route('/customers', methods=['GET'])
def get_users():
    users = ClientModel.query.all()
    return jsonify([user.profile() for user in users]), 200


@app.route('/customers/<id>', methods=['GET'])
def get_user(id):
    user = ClientModel.query.get(id)
    if not user:
        return jsonify({"message":"User not found"}), 404
    return jsonify({"customer": user.profile()}), 200


@app.route('/customer/loans/<id>', methods=['GET'])
def get_client_loans(id):
    user = db.session.get(ClientModel, id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    loans = LoanModel.query.filter_by(client_id=id).all()
    return jsonify([ loan.get_loan_details() for loan in loans]), 200


@app.route('/customer/payments/<id>', methods=['GET'])
def get_client_payments(id):
    user = db.session.get(ClientModel, id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    payments = PaymentModel.query.filter_by(client_id=id).all()
    return jsonify([ payment.get_payment_details() for payment in payments]), 200


@app.route('/customers/summary', methods=['GET'])
def get_customer_summary():
    clients = ClientModel.query.all()
    if not clients:
        return jsonify({"message": "Failed to retrieve customers summary"}), 404
    
    blacklisted, overdue_clients, active_clients = 0, 0, 0
    total_clients = len(clients)
    for client in clients:
        if client.status == "Active":
            active_clients += 1
        if client.status == "Overdue":
            overdue_clients += 1
        if client.status == "Blacklisted":
            blacklisted += 1

    return jsonify({"total_customers": total_clients, "active_borrowers": active_clients, "overdue_customers": overdue_clients, "blacklisted": blacklisted}), 200


@app.route('/add_client_loan', methods=['POST'])
def request_loan():
    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400
    comp = db.session.get(CompanyModel, 7685) #change to env to call the company ID
    client = ClientModel.query.filter_by(id=data['client_id']).first()
    if not client or not comp:
        return jsonify({"message": "Client not found"}), 404
    msg, status_code = assign_loan(data, client, comp)
    return jsonify({"message": msg}), status_code


@app.route('/loan-payment', methods=['POST'])
def loan_payment():
    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400
    client = db.session.get(ClientModel, data["client_id"])
    if not client:
        return jsonify({"message": "Client not found"}), 404
    msg, status_code = repay_loan(data, client)
    return jsonify({"message": msg}), status_code


@app.route("/customers/lookup", methods=["GET"])
def lookup_customer():
    mobile = request.args.get("mobile", "").strip()
    if not mobile:
        return jsonify({"message": "Mobile number is required."}), 400

    customer = (ClientModel.query.filter_by(mobile=mobile).first())
    if not customer:
        return jsonify({"message": "No customer found with that mobile number."}), 404

    active_loans = [loan for loan in customer.loans if not loan.paid and (loan.balance or Decimal("0")) > 0]
    outstanding = sum((loan.balance or Decimal("0") for loan in active_loans),Decimal("0"))

    loans = [
        {
            "id": loan.id,
            "client_id": loan.client_id,
            "amount": str(loan.amount),
            "interest": str(loan.interest),
            "balance": str(loan.balance),
            "pay_date": (loan.pay_date.isoformat() if loan.pay_date else None),
            "created_at": (loan.created_at.isoformat() if loan.created_at else None),
            "paid": loan.paid,
        }
        for loan in active_loans
    ]

    return jsonify({"customer": customer.profile(), "summary": { "active_loans": len(active_loans), "outstanding": str(outstanding),}, "loans": loans,}), 200


@app.route("/payment/summary", methods=["GET"])
def payment_summary():
    try:
        today = date.today()
        month_start = today.replace(day=1)
        if today.month == 12:
            next_month = date(today.year + 1, 1, 1)
        else:
            next_month = date(today.year, today.month + 1, 1)

        month_payments = (PaymentModel.query.filter(
                PaymentModel.date >= month_start,
                PaymentModel.date < next_month,
            ).all()
        )

        collected_this_month = sum((payment.amount or Decimal("0")) for payment in month_payments)
        total_transactions = len(month_payments)
        today_payments = ( PaymentModel.query.filter( PaymentModel.date == today).all())
        collected_today = sum((payment.amount or Decimal("0")) for payment in today_payments)
        transactions_today = len(today_payments)
        expected_loans = (LoanModel.query.filter(
                LoanModel.pay_date >= month_start,
                LoanModel.pay_date < next_month,
                LoanModel.paid.is_(False),
                LoanModel.balance > 0,
            ).all()
        )

        expected_this_month = sum((loan.balance or Decimal("0")) for loan in expected_loans)

        return jsonify({
            "collected_this_month": float(collected_this_month),
            "collected_today": float(collected_today),
            "expected_this_month": float(expected_this_month),
            "total_transactions": total_transactions,
            "transactions_today": transactions_today,
        }), 200

    except Exception as error:
        print( f"Payment summary error: {error}")
        return jsonify({"message": "Unable to load payment summary."}), 500


@app.route('/payments', methods=['GET'])
def get_payments():
    payments = PaymentModel.query.all()
    payment_list = []
    for payment in payments:
        payment_list.append(payment.get_payment_details())

    return jsonify(payment_list), 200


@app.route('/payments/<id>', methods=['GET'])
def get_client_payment(id):
    payment = db.session.get(PaymentModel, id)
    if not payment:
        return jsonify({"message": "Payment not found, Please check payment ref and try again"}), 404
    loan = db.session.get(LoanModel, payment.loan_id)
    client = db.session.get(ClientModel, payment.client_id)

    if not loan and not client:
        return jsonify({"message": "Internal server error"}), 503

    payment_history = PaymentModel.query.filter_by(loan_id=loan.id).all()

    return jsonify({
        "payment": payment.get_payment_details(),
        "loan": loan.get_loan_details(),
        "customer": client.profile(),
        "payment_history": [pay.get_payment_details() for pay in payment_history]
    }), 200


@app.route('/loans', methods=['GET'])
def get_loans():
    loans = LoanModel.query.all()
    loan_list = []
    for loan in loans:
        loan_list.append(loan.get_loan_details())

    return jsonify(loan_list), 200


@app.route('/loan/<id>', methods=['GET'])
def get_loan_by_id(id):
    loan = db.session.get(LoanModel, id)
    if not loan:
        return jsonify({"message": "Loan not found, Please check loan ref and try again"}), 404
    payment_history = PaymentModel.query.filter_by(loan_id=id).all()
    client = db.session.get(ClientModel, loan.client_id)

    if not client:
        return jsonify({"message": "Internal server error"}), 503

    return jsonify({
        "loan": loan.get_loan_details(),
        "customer": client.profile(),
        "payment_history": [pay.get_payment_details() for pay in payment_history]
    }), 200


@app.route("/loans/summary", methods=["GET"])
def loan_summary():
    try:
        today = date.today()
        loans = LoanModel.query.all()

        overdue, due_today, outstanding, active_loans = 0, 0, 0, 0

        for loan in loans:
            if not loan.paid:
                if (loan.pay_date + timedelta(5)) < today:
                    overdue += 1
                else:
                    active_loans += 1

                if loan.pay_date == today:
                    due_today += 1

                outstanding += loan.balance

        return jsonify({
            "active_loans": active_loans,
            "outstanding": float(outstanding),
            "due_today": due_today,
            "overdue": overdue,
        }), 200

    except Exception as error:
        print( f"Loan summary error: {error}")
        return jsonify({"message": "Unable to load loan summary."}), 500


def decimal_to_float(value): 
    if value is None: 
        return 0.0 
    return float(value) 

def parse_report_date(value, fallback): 
    if not value: 
        return fallback 
    try: 
        return datetime.strptime( value, "%Y-%m-%d" ).date() 
    except ValueError: 
        return fallback 
    
    
@app.route("/reports/<report_type>", methods=["GET"]) 
def get_report(report_type): 
    try: 
        allowed_reports = { "portfolio", } 
        if report_type not in allowed_reports: 
            return jsonify({ "message": "Unsupported report type." }), 400 
        today = date.today() 
        default_from = today.replace(day=1) 
        default_to = today 
        from_date = parse_report_date( request.args.get("from"), default_from ) 
        to_date = parse_report_date( request.args.get("to"), default_to ) 
        if from_date > to_date: 
            return jsonify({ "message": "The start date cannot be after the end date." }), 400 
        
        to_date_exclusive = to_date + timedelta(days=1) 
        loans = ( LoanModel.query .filter( LoanModel.created_at >= from_date, LoanModel.created_at < to_date_exclusive ) .all() ) 
        total_loans = len(loans) 
        active_loans = sum( 1 for loan in loans if not loan.paid and (loan.balance or Decimal("0")) > 0 ) 
        completed_loans = sum( 1 for loan in loans if loan.paid ) 
        overdue_loans = [ loan for loan in loans if not loan.paid and (loan.balance or Decimal("0")) > 0 and loan.pay_date and loan.pay_date < today ] 
        overdue_count = len(overdue_loans) 
        issued = sum( ( loan.amount or Decimal("0") ) for loan in loans ) 
        interest_earned = sum( ( loan.interest or Decimal("0") ) for loan in loans ) 
        payments = ( PaymentModel.query .filter( PaymentModel.date >= from_date, PaymentModel.date < to_date_exclusive ) .all() ) 
        collected = sum( ( payment.amount or Decimal("0") ) for payment in payments ) 
        outstanding = sum( ( loan.balance or Decimal("0") ) for loan in loans if not loan.paid ) 
        if issued > 0: 
            collection_rate = ( collected / issued ) * Decimal("100") 
        else: collection_rate = Decimal("0") 
        
        trend = [] 
        current_month = from_date.replace(day=1)
        if current_month.month == 12: 
            next_month = date( current_month.year + 1, 1, 1 ) 
        else: 
            next_month = date( current_month.year, current_month.month + 1, 1 ) 
        
        month_loans = [ loan for loan in loans if loan.created_at and current_month <= loan.created_at < next_month ] 
        month_issued = sum( ( loan.amount or Decimal("0") ) for loan in month_loans ) 
        month_payments = [ payment for payment in payments if payment.date and current_month <= payment.date < next_month ] 
        month_collected = sum( ( payment.amount or Decimal("0") ) for payment in month_payments ) 
        month_outstanding = sum( ( loan.balance or Decimal("0") ) for loan in month_loans if not loan.paid ) 
        trend.append({ 
            "month": current_month.strftime("%b"), 
            "issued": decimal_to_float( month_issued ), 
            "collected": decimal_to_float( month_collected ), 
            "outstanding": decimal_to_float( month_outstanding ), 
        }) 
        current_month = next_month  
        overdue_data = [] 
        for loan in overdue_loans: 
            client = loan.client 
            if not client: 
                continue 
            days_overdue = ( today - loan.pay_date ).days 
            client_name = ( f"{client.first_name} " f"{client.middle_name or ''} " f"{client.last_name}" ).strip() 
            overdue_data.append({ 
                "id": str(loan.id), 
                "client": client_name, 
                "client_id": client.id, 
                "mobile": client.mobile, 
                "due_date": ( loan.pay_date.isoformat() if loan.pay_date else None ), 
                "days_overdue": days_overdue, 
                "balance": str( loan.balance or Decimal("0") ), 
            })  
            overdue_data.sort( key=lambda item: ( item["days_overdue"], float(item["balance"]) ), reverse=True ) 
        
        return jsonify({ 
            "summary": { 
                "issued": str(issued), 
                "collected": str(collected), 
                "outstanding": str(outstanding), 
                "interest_earned": str( interest_earned ), 
                "total_loans": total_loans, 
                "active_loans": active_loans, 
                "completed_loans": completed_loans, 
                "overdue_loans": overdue_count, 
                "collection_rate": round( float(collection_rate), 2 ), 
            }, 
            "trend": trend, 
            "overdue_loans": overdue_data, 
        }), 200 
    except Exception as error: 
        db.session.rollback() 
        print( f"Report error: {error}" ) 
        return jsonify({ "message": "Unable to generate report." }), 500


from sqlalchemy import func

@app.route("/dashboard/summary", methods=["GET"])
def dashboard_summary():

    try:
        today = date.today()
        month_start = today.replace(day=1)
        total_amount_issued = (db.session.query(func.coalesce(func.sum(LoanModel.amount), 0)).scalar())
        outstanding_balance = (
            db.session.query(
                func.coalesce(
                    func.sum(LoanModel.balance),
                    0
                )
            )
            .filter(
                LoanModel.paid.is_(False),
                LoanModel.balance > 0
            )
            .scalar()
        )

        overdue_loans = (
            db.session.query(
                func.count(LoanModel.id)
            )
            .filter(
                LoanModel.paid.is_(False),
                LoanModel.balance > 0,
                LoanModel.pay_date < today
            )
            .scalar()
        )

        collected_this_month = (
            db.session.query(
                func.coalesce(
                    func.sum(PaymentModel.amount),
                    0
                )
            )
            .filter(
                PaymentModel.date >= month_start,
                PaymentModel.date <= today
            )
            .scalar()
        )

        return jsonify({

            "total_amount_issued": str(total_amount_issued or Decimal("0")),
            "collected_this_month": str(collected_this_month or Decimal("0")),
            "outstanding_balance": str(outstanding_balance or Decimal("0")),
            "overdue_loans": int(overdue_loans or 0),
        }), 200

    except Exception as error:
        db.session.rollback()
        print(f"Dashboard summary error: {error}")

        return jsonify({"message": "Unable to load dashboard summary."}), 500


@app.route("/dashboard/portfolio", methods=["GET"])
def dashboard_portfolio():
    try:
        try:
            months = int(request.args.get("months", 6))
        except ValueError:
            months = 6

        if months not in (6, 12):
            months = 6
        today = date.today()
        current_month = today.replace(day=1)
        month_list = []
        year = current_month.year
        month = current_month.month

        for _ in range(months):
            month_list.append(date(year, month, 1))
            month -= 1
            if month == 0:
                month = 12
                year -= 1
        
        month_list.reverse()
        chart_data = []

        for month_start in month_list:
            if month_start.month == 12:
                next_month = date(month_start.year + 1, 1, 1)
            else:
                next_month = date(month_start.year, month_start.month + 1, 1)

            issued = (db.session.query(func.coalesce(func.sum(LoanModel.amount), 0))
                .filter(
                    LoanModel.created_at >= month_start,
                    LoanModel.created_at < next_month
                )
                .scalar()
            )

            repayments = (db.session.query(func.coalesce(func.sum(PaymentModel.amount), 0))
                .filter(
                    PaymentModel.date >= month_start,
                    PaymentModel.date < next_month
                )
                .scalar()
            )

            outstanding = (db.session.query(func.coalesce(func.sum(LoanModel.balance), 0))
                .filter(
                    LoanModel.created_at < next_month,
                    LoanModel.paid.is_(False),
                    LoanModel.balance > 0
                )
                .scalar()
            )

            chart_data.append({
                "month": month_start.strftime("%b"),
                "issued": float(issued or Decimal("0")),
                "repayments": float(repayments or Decimal("0")),
                "outstanding": float(outstanding or Decimal("0")),
            })

        current_month_data = (chart_data[-1] if chart_data else {
                "issued": 0,
                "repayments": 0,
                "outstanding": 0,
            }
        )

        return jsonify({
            "data": chart_data,
            "summary": {
                "issued": current_month_data["issued"],
                "repayments": current_month_data["repayments"],
                "outstanding": current_month_data["outstanding"],
            },

        }), 200

    except Exception as error:
        db.session.rollback()
        print( f"Portfolio chart error: {error}")
        return jsonify({
            "message": "Unable to load portfolio data."
        }), 500






@app.route('/add_client', methods=['POST']) 
def add_client():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No input data provided"}), 400
    
    errors = client_schema.validate(json_data)
    if errors:
        return jsonify({"message": "Validation errors", "errors": errors}), 422
    
    errors = client_schema.validate(json_data)
    if errors:
        return jsonify({"message": "Validation errors", "errors": errors}), 422
        
    data = client_schema.load(json_data)
    new_client = ClientModel()
    msg, status_code = new_client.__newclient__(data)
    return jsonify({"message": msg, "user": new_client.profile()}), status_code


@app.route('/pay_loan', methods=['POST'])
def pay_loan():
    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400
    
    client = ClientModel.query.filter_by(mobile=data['mobile']).first()
    if not client:
        return jsonify({"message": "Client not found"}), 404
        
    msg, status_code = repay_loan(data, client)
    return jsonify({"message": msg}), status_code


@app.route('/recent_loans', methods=['GET'])
def recent_loans():
    three_days_ago = date.today() - timedelta(days=3)
    recent_loans = (
        LoanModel.query
        .filter(
            LoanModel.created_at >= three_days_ago,
            LoanModel.paid.is_(False)
        )
        .order_by(LoanModel.pay_date.desc())
        .all()
    )

    loans_list = []

    for loan in recent_loans:
        loans_list.append(loan.get_loan_details())

    return jsonify(loans_list)


@app.route('/all_recent_loans', methods=['GET'])
def all_recent_loans():
    latest_10 = (LoanModel.query.order_by(LoanModel.pay_date.desc()).limit(10).all())
    loans_list = []
    for loan in latest_10:
        loans_list.append(loan.get_loan_details())
    return jsonify(loans_list)


@app.route('/actionable_loans', methods=['GET'])
def get_actionable_loans():
    two_days_from_now = date.today() + timedelta(days=2)
    action_loans = (
        LoanModel.query
        .filter(
            LoanModel.pay_date >= two_days_from_now,
            LoanModel.paid.is_(False)
        )
        .order_by(LoanModel.pay_date.desc())
        .all()
    )
    loans_list = []
    for loan in action_loans:
        loans_list.append(loan.get_loan_details())

    return jsonify(loans_list)


@app.route('/clients_list', methods=['GET'])
def get_new_clients():
    clients = ClientModel.query.all()
    client_list = []
    for client in clients:
        client_list.append(client.profile())

    return jsonify(client_list)





@app.route('/send_reminder/<int:id>', methods=['POST'])
def send_reminder(id):
    loan = LoanModel.query.get(id)
    if not loan:
        return jsonify({"message": "Loan not found"}), 404

    # Here you would implement the logic to send a reminder, e.g., via email or SMS.
    # For demonstration purposes, we'll just return a success message.
    return jsonify({"message": f"Reminder sent for loan ID {id}"}), 200


@app.route('/blacklist_client/<int:id>', methods=['PATCH'])
def blacklist_client(id):
    loan = LoanModel.query.get(id)
    if not loan:
        return jsonify({"message": "Loan not found"}), 404
    
    client = ClientModel.query.get(loan.client_id)
    if not client:
        return jsonify({"message": "Client not found"}), 404

    client.record = False
    db.session.commit()

    return jsonify({"message": "Client blacklisted successfully"}), 200


@app.route('/logs', methods=['GET'])
def get_logs():

    today = datetime.now().date()

    start_of_day = datetime.combine(today, datetime.min.time())
    start_of_tomorrow = start_of_day + timedelta(days=1)

    logs = (
        ActivityLogModel.query
        .filter(
            ActivityLogModel.timestamp >= start_of_day,
            ActivityLogModel.timestamp < start_of_tomorrow
        )
        .order_by(ActivityLogModel.timestamp.desc())
        .all()
    )

    log_list = []

    for log in logs:
        log_list.append({
            "id": log.id,
            "title": log.action,
            "description": log.description,
            "type": log.table_name,
            "time": time_since(log.timestamp)
        })

    return jsonify(log_list), 200


@app.route('/defaulted_loans', methods=['GET'])
def defaulted_loans():
    today = date.today()
    defaulted_loans = (
        LoanModel.query
        .filter(
            (LoanModel.pay_date + timedelta(days=7)) > today,
            LoanModel.paid.is_(False)
        )
        .order_by(LoanModel.pay_date.desc())
        .all()
    )

    loans_list = []

    for loan in defaulted_loans:
        loans_list.append(loan.get_loan_details())

    return jsonify(loans_list)


@app.route('/pro_clients', methods=['GET'])
def pro_clients():
    today = date.today()
    pro_clients = (
        ClientModel.query
        .filter(
            ClientModel.record.is_(True),
            ClientModel.requests > 0
        )
        .all()
    )

    clients_list = []

    for client in pro_clients:
        clients_list.append(client.profile())

    return jsonify(clients_list)
            


@app.route('/get_client/<client_id>', methods=['GET'])
def get_client(client_id):
    client = ClientModel.query.get(client_id)
    if not client:
        return jsonify({"message": "Client not found"}), 404
    
    return jsonify({"client": client.profile()}), 200


@app.route('/update_client/<client_id>', methods=['PATCH'])
def update_client(client_id):
    data = request.get_json()

    if not data:
        return jsonify({"message": "No data provided"}), 400
    
    client = ClientModel.query.get(client_id)

    if not client:
        return jsonify({"message": "Client not found"}), 404

    for key, value in data.items():
        if hasattr(client, key):
            setattr(client, key, value)

    db.session.commit()

    return jsonify({
        "message": "Client updated successfully",
        "client": client.profile()
    }), 201

@app.route('/delete_client/<client_id>', methods=['DELETE'])
def delete_client(client_id):
    client = ClientModel.query.get(client_id)
    if not client:
        return jsonify({"message": "Client not found"}), 404
    
    db.session.delete(client)
    db.session.commit()
    
    return jsonify({"message": "Client deleted successfully"}), 200





@app.route('/client_history/<client_id>', methods=['GET']) 
def client_loan_history(client_id):
    client = ClientModel.query.get(client_id)
    if not client:
        return jsonify({"message": "Client not found"}), 404
    
    loans = LoanModel.query.filter_by(client_id=client_id).all()
    loan_history = []
    for loan in loans:
        loan_history.append({
            "amount": str(loan.amount),
            "interest": str(loan.interest),
            "pay_date": loan.pay_date.strftime("%Y-%m-%d"),
            "balance": str(loan.balance),
            "paid": loan.paid
        })
    
    return jsonify({"client": client.profile(), "loan_history": loan_history}), 200


@app.route("/payment_history/<client_id>", methods=['GET'])
def payment_history(client_id):
    client = ClientModel.query.get(client_id)
    if not client:
        return jsonify({"message": "Client not found"}), 404
    
    payments = PaymentModel.query.filter_by(client_id=client_id).all()
    payment_history = []
    for payment in payments:
        payment_history.append({
            "amount": str(payment.amount),
            "date": payment.date.strftime("%Y-%m-%d"),
            "company": payment.company.id
        })
    
    return jsonify({"client": client.profile(), "payment_history": payment_history}), 200


@app.route("/loan_status/<client_id>", methods=['GET'])
def loan_status(client_id):
    client = ClientModel.query.get(client_id)
    if not client:
        return jsonify({"message": "Client not found"}), 404
    
    loan = LoanModel.query.filter_by(client_id=client_id, paid=False).first()
    if not loan:
        return jsonify({"message": "No active loan found for this client"}), 404
    
    return jsonify({
        "amount": str(loan.balance),
        "pay_date": loan.pay_date.strftime("%Y-%m-%d"),
    }), 200


@app.route('/current_amount', methods=['GET'])
def current_amount():
    company = CompanyModel.query.get(7685)
    if not company:
        return jsonify({"message": "Company not found"}), 404
    
    return jsonify({"current_amount": str(company.current_amount)}), 200


@app.route('/amount_out', methods=['GET'])
def amount_out():    
    loans = LoanModel.query.filter_by(paid=False).all()
    total_out = 0
    for loan in loans:
        if loan.balance > loan.interest:
            total_out += (loan.balance - loan.interest)
    return jsonify({"amount_out": str(total_out)}), 200


@app.route('/expected_interest', methods=['GET'])
def expected_interest():
    loans = LoanModel.query.filter_by(paid=False).all()
    total_interest = 0
    for loan in loans:
        if loan.balance > loan.interest:
            total_interest += loan.interest
        else:
            total_interest += loan.balance

    return jsonify({"expected_interest": str(total_interest)}), 200


@app.route('/interest_made', methods=['GET'])
def interest_made():
    loans = LoanModel.query.filter_by(paid=True).all()
    total_interest = 0
    for loan in loans:
        total_interest += loan.interest
    return jsonify({"interest_made": str(total_interest)}), 200


@app.route('/interest_paid_period', methods=['POST'])
def interest_paid_period():
    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400
    start_date = datetime.now() - timedelta(days=data['days'])
    loans = LoanModel.query.filter_by(paid=True).filter(LoanModel.completion_date >= start_date).all()
    total_interest = sum(loan.interest for loan in loans)
    return jsonify({"interest_paid_period": str(total_interest)}), 200

@app.route('/overdue_loans', methods=['GET'])
def overdue_loans():
    today = datetime.now()
    loans = LoanModel.query.filter_by(paid=False).filter(LoanModel.pay_date < today).all()
    total_overdue = 0
    overdue_list = []
    for loan in loans:
        if loan.balance > loan.interest:
            total_overdue += (loan.balance - loan.interest)
        overdue_list.append({
            "client": loan.client.profile(),
            "amount": str(loan.amount),
            "pay_date": loan.pay_date.strftime("%Y-%m-%d"),
            "balance": str(loan.balance)
        })
    return jsonify({"overdue_loans": overdue_list, "total_overdue": str(total_overdue)}), 200
        

# Route: Fetch all users


  
if __name__ == '__main__':
    app.run(debug=True)