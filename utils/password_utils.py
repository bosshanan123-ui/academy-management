"""
utils/password_utils.py
Password hashing helpers using werkzeug.
"""
from werkzeug.security import generate_password_hash, check_password_hash


def hash_password(password: str) -> str:
    """Return a secure hash of the given password."""
    return generate_password_hash(password, method="pbkdf2:sha256")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a stored hash."""
    try:
        return check_password_hash(password_hash, password)
    except Exception:
        return False