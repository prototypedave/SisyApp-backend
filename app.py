from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from flask_migrate import Migrate
from .config import Config
from .extensions import db, limiter
from .models import UserModel, CompanyModel
from .cli.owner import register_owner_command
from .cli.sessions import register_session_commands
from .cli.company import register_company_command
from .routes import auth_bp
from .routes.protected import protected_bp
from .routes.customers import customers_bp
from .routes.loans import loans_bp
from .routes.dashboard import dashboard_bp
from .routes.investors import investors_bp
from .routes.reports import reports_bp
from .routes.settings import settings_bp


migrate = Migrate()


def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    register_owner_command(app)
    register_session_commands(app)
    register_company_command(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(protected_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(loans_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(investors_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(settings_bp)
    return app


app = create_app()
with app.app_context():
    db.create_all()
    #db.session.add(CompanyModel(initial_amount=200000))
    #db.session.commit()
    print("Database tables created successfully.")

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
    )

    