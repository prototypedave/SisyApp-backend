import click
from flask import current_app
from ..extensions import db
from ..models.company import CompanyModel



def register_company_command(app):
    @app.cli.command("create-company")
    def create_company():
        click.echo()
        click.echo("SisyLoan Company Provisioning")
        click.echo("=" * 28)
        click.echo()
        existing_company = (db.session.query(CompanyModel).first())
        if existing_company:
            click.echo("Company has already been set")
            click.echo("Log in to access company")
            return

        company_name = click.prompt("company name").strip()
        initial_amount = click.prompt("Initial amount").strip()

        if not company_name:
            company_name = "Sisy Loan"

        if not initial_amount:
            click.echo("Amount cannot be empty")
            return

        company = CompanyModel(
            company_name=company_name,
            initial_amount=initial_amount,
            current_amount=initial_amount
        )

        try:
            db.session.add(company)
            db.session.commit()

    
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Company provisioning failed.")
            click.echo("Company provisioning failed.")
            return

        click.echo()
        click.echo("Company registered successfully.")
        click.echo()