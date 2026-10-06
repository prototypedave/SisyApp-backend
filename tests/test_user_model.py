from ..app import app
from ..extensions import db
from ..models import UserModel
from datetime import datetime


with app.app_context():
    user = UserModel(
        first_name="Sisy",
        last_name="Admin",
        email="admin@example.com",
        phone="0712345678",
        password_hash="TEMPORARY_VALUE",
        last_login_at=datetime.now()
    )

    db.session.add(user)
    db.session.commit()

    print("User created:")
    print(user.profile())