"""
Shared FastAPI dependencies for the NexGenIQ API.

Provides the current-user dependency used to protect endpoints.
Reference: NexGenIQ Phase 3 Part 3C Section 3.6.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models import User

_settings = get_settings()

# The tokenUrl is where clients exchange credentials for a token; it also
# tells the OpenAPI docs how to authorise interactive requests.
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{_settings.api_v1_prefix}/auth/token"
)

_credentials_error = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials.",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the authenticated user from the bearer token.

    Raises
    ------
    HTTPException 401
        If the token is missing, invalid, expired, or names a user who no
        longer exists or is inactive.
    """
    claims = decode_access_token(token)
    if claims is None or "sub" not in claims:
        raise _credentials_error

    user = db.get(User, claims["sub"])
    if user is None or not user.is_active:
        raise _credentials_error
    return user


def require_role(*allowed_roles: str):
    """Build a dependency that requires the user to hold one of the roles.

    Example
    -------
    ``Depends(require_role("site_admin"))`` restricts an endpoint to site
    administrators. Roles are a default for the UI but still gate
    privileged API actions (Phase 3 Part 3C Section 3.6).
    """

    def _checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"This action requires one of: "
                    f"{', '.join(allowed_roles)}."
                ),
            )
        return user

    return _checker
