def validate_password(password: str) -> tuple[bool, str | None]:
    if not isinstance(password, str):
        return False, "Password must be a string."

    if len(password) < 12:
        return False, "Password must contain at least 12 characters."

    if len(password) > 128:
        return False, "Password must not exceed 128 characters."

    if password.isspace():
        return False, "Password cannot contain only whitespace."

    if not any(character.isupper() for character in password):
        return False, "Password must contain an uppercase letter."

    if not any(character.islower() for character in password):
        return False, "Password must contain a lowercase letter."

    if not any(character.isdigit() for character in password):
        return False, "Password must contain a number."

    if not any(not character.isalnum() for character in password):
        return False, "Password must contain a special character."

    return True, None