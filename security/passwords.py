from argon2 import PasswordHasher
from argon2.exceptions import (InvalidHashError, VerificationError, VerifyMismatchError)

_password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    if not isinstance(password, str):
        raise TypeError("Password must be a string.")
    if not password:
        raise ValueError("Password cannot be empty.")
    return _password_hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    if not password_hash or not isinstance(password_hash, str):
        return False

    if not isinstance(password, str):
        return False

    try:
        return _password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def password_needs_rehash(password_hash: str) -> bool:
    if not password_hash:
        return False
    try:
        return _password_hasher.check_needs_rehash(password_hash)
    except (VerificationError, InvalidHashError):
        return False