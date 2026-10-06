from ..security import (
    hash_password,
    verify_password,
    password_needs_rehash,
    validate_password,
)


def test_password_is_hashed():
    password = "SisyLoanAdmin2026!"
    password_hash = hash_password(password)
    assert password_hash != password
    assert password_hash.startswith("$argon2id$")


def test_correct_password_is_verified():
    password = "SisyLoanAdmin2026!"
    password_hash = hash_password(password)
    assert verify_password(password_hash, password)


def test_wrong_password_is_rejected():
    password_hash = hash_password("SisyLoanAdmin2026!")
    assert not verify_password(password_hash, "WrongPassword2026!")


def test_same_password_generates_different_hashes():
    password = "SisyLoanAdmin2026!"
    first_hash = hash_password(password)
    second_hash = hash_password(password)
    assert first_hash != second_hash


def test_invalid_hash_is_rejected():
    assert not verify_password("invalid-hash", "SisyLoanAdmin2026!")


def test_empty_password_is_rejected():
    try:
        hash_password("")
    except ValueError:
        assert True
    else:
        assert False


def test_password_policy_rejects_short_password():
    valid, error = validate_password("Short1!")
    assert not valid
    assert error is not None


def test_password_policy_accepts_strong_password():
    valid, error = validate_password("SisyLoanAdmin2026!")
    assert valid
    assert error is None


def test_password_needs_rehash_returns_boolean():
    password_hash = hash_password("SisyLoanAdmin2026!")
    result = password_needs_rehash(password_hash)

    assert isinstance(result, bool)