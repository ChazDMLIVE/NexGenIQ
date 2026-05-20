"""
Authentication and password security for the NexGenIQ backend.

Implements password hashing (bcrypt) and JWT access tokens (OAuth2 password
flow), per NexGenIQ Phase 3 Part 3C Section 3.6.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

_settings = get_settings()

# bcrypt is a deliberately slow, salted password hash.
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Return a salted bcrypt hash of ``plain_password``."""
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Return ``True`` if ``plain_password`` matches the stored hash."""
    return _pwd_context.verify(plain_password, password_hash)


def create_access_token(
    subject: str,
    *,
    role: str,
    expires_minutes: int | None = None,
) -> str:
    """Create a signed JWT access token.

    Parameters
    ----------
    subject:
        The token subject — the user's id, placed in the ``sub`` claim.
    role:
        The user's role, placed in a ``role`` claim so authorisation checks
        do not need a database round-trip.
    expires_minutes:
        Token lifetime; defaults to the configured value.

    Returns
    -------
    str
        The encoded JWT.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or _settings.access_token_expire_minutes
    )
    claims = {"sub": subject, "role": role, "exp": expire}
    return jwt.encode(
        claims, _settings.jwt_secret, algorithm=_settings.jwt_algorithm
    )


def decode_access_token(token: str) -> dict | None:
    """Decode and verify a JWT.

    Returns
    -------
    dict | None
        The token claims if the token is valid and unexpired; ``None`` if
        the signature is invalid or the token has expired.
    """
    try:
        return jwt.decode(
            token,
            _settings.jwt_secret,
            algorithms=[_settings.jwt_algorithm],
        )
    except JWTError:
        return None
