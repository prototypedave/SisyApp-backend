from ..app import app
from ..models import UserModel


with app.app_context():
    user = UserModel.query.first()

    if not user:
        print("No user exists.")
        raise SystemExit(1)

    correct_password = input("Enter the owner's password: ")
    wrong_password = "DefinitelyWrongPassword123!"

    print()
    print("Correct password:", user.check_password(correct_password),)
    print("Wrong password:", user.check_password(wrong_password),)