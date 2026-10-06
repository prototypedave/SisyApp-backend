from datetime import datetime, timezone
import click
from ..extensions import db
from ..models import SessionModel


def register_session_commands(app):
    @app.cli.command("cleanup-sessions")
    def cleanup_sessions():
        now = datetime.now(timezone.utc)
        deleted = (SessionModel.query.filter((SessionModel.expires_at<= now) | (SessionModel.revoked_at != None)).delete(synchronize_session=False))
        db.session.commit()
        click.echo(f"Removed {deleted} expired/revoked sessions.")