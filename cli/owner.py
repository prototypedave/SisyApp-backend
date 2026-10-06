import getpass
import uuid
import click
from flask import current_app
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..models.user import UserModel
from ..security.validation import validate_password


def register_owner_command(app):
    @app.cli.command("create-owner")
    def create_owner():
        click.echo()
        click.echo("SisyLoan Owner Provisioning")
        click.echo("=" * 28)
        click.echo()
        existing_owner = (db.session.query(UserModel).filter(UserModel.is_owner.is_(True)).first())
        if existing_owner:
            click.echo("An owner account already exists.")
            click.echo("Owner provisioning has been refused.")
            return

        first_name = click.prompt("First name").strip()
        last_name = click.prompt("Last name").strip()
        email = click.prompt("Email").strip().lower()
        phone = click.prompt("Phone").strip()

        if not first_name:
            click.echo("First name cannot be empty.")
            return

        if not last_name:
            click.echo("Last name cannot be empty.")
            return

        if not email:
            click.echo("Email cannot be empty.")
            return

        if not phone:
            click.echo("Phone cannot be empty.")
            return

        password = getpass.getpass("Password: ")
        password_confirmation = getpass.getpass("Confirm password: ")

        if password != password_confirmation:
            click.echo("Passwords do not match.")
            return

        valid, error = validate_password(password)

        if not valid:
            click.echo(error)
            return

        owner = UserModel(
            id=str(uuid.uuid4()),
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            is_active=True,
            is_owner=True,
        )

        owner.set_password(password)
        try:
            db.session.add(owner)
            db.session.commit()

        except IntegrityError:
            db.session.rollback()

            click.echo(
                "Owner provisioning failed because "
                "the email or phone already exists."
            )
            return

        except Exception:
            db.session.rollback()
            current_app.logger.exception("Owner provisioning failed.")
            click.echo("Owner provisioning failed.")
            return

        click.echo()
        click.echo("Owner account created successfully.")
        click.echo()