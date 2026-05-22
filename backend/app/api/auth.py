"""
Authentication endpoints for the NexGenIQ API.

Implements registration and the OAuth2 password-flow token endpoint
(Phase 3 Part 3C Section 3.4 / 3.6).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models import User
from app.services.audit import record_event
from app.schemas import (
    PasswordResetQuestionRequest,
    PasswordResetQuestionResponse,
    PasswordResetRequest,
    Token,
    UserCreate,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])

_VALID_ROLES = {
    "producer", "researcher", "breeder", "assoc_admin", "site_admin",
}


def _normalise_answer(answer: str) -> str:
    """Normalise a security-question answer before hashing or comparing.

    Answers are matched case-insensitively and ignoring surrounding
    whitespace, so "Big Horn" and "  big horn " count as the same answer.
    """
    return answer.strip().lower()


@router.post("/register", response_model=UserOut, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    """Create a new user account.

    Raises
    ------
    HTTPException 409
        If the email is already registered.
    HTTPException 422
        If the requested role is not recognised.
    """
    if payload.role not in _VALID_ROLES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown role {payload.role!r}.",
        )

    existing = (
        db.query(User).filter(User.email == payload.email).one_or_none()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    # The security answer, if given, is bcrypt-hashed exactly like a
    # password -- it is never stored in plain text. The question text is
    # stored as-is so it can be shown back during a reset.
    answer = payload.security_answer.strip()
    question = payload.security_question.strip()
    answer_hash = (
        hash_password(_normalise_answer(answer))
        if answer and question
        else None
    )

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
        security_question=question or None,
        security_answer_hash=answer_hash,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    record_event(
        db, event_type="register",
        summary=f"New {user.role} account created.",
        user=user,
    )
    return user


@router.post("/token", response_model=Token)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    """Exchange email + password for a JWT access token.

    Uses the OAuth2 password-flow form (``username`` carries the email).
    """
    user = (
        db.query(User).filter(User.email == form.username).one_or_none()
    )
    if user is None or not verify_password(
        form.password, user.password_hash
    ):
        record_event(
            db, event_type="login_failed",
            summary="Failed sign-in: wrong email or password.",
            user_email=form.username,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        record_event(
            db, event_type="login_failed",
            summary="Failed sign-in: account is disabled.",
            user=user,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is disabled.",
        )

    record_event(
        db, event_type="login", summary="Signed in.", user=user,
    )
    token = create_access_token(subject=user.id, role=user.role)
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    """Return the currently authenticated user."""
    return user


@router.post(
    "/password-reset/question",
    response_model=PasswordResetQuestionResponse,
)
def password_reset_question(
    payload: PasswordResetQuestionRequest,
    db: Session = Depends(get_db),
) -> PasswordResetQuestionResponse:
    """Step 1 of a password reset: return the account's security question.

    Self-service password reset has no email step; instead the user must
    answer the security question they set at registration. This endpoint
    returns that question (never the answer) so the UI can show it.

    If the account does not exist, or exists but has no security question
    on file (older accounts), ``has_question`` is false and a plain
    message explains the situation. The answer is never returned.
    """
    user = (
        db.query(User).filter(User.email == payload.email).one_or_none()
    )
    if user is None or not user.is_active:
        return PasswordResetQuestionResponse(
            has_question=False,
            message=(
                "If an account exists for that email, its security "
                "question will be shown. If nothing appears, the email "
                "may not be registered."
            ),
        )
    if not user.security_question or not user.security_answer_hash:
        return PasswordResetQuestionResponse(
            has_question=False,
            message=(
                "This account has no security question on file, so it "
                "cannot be reset this way. Please contact an "
                "administrator to reset the password."
            ),
        )
    return PasswordResetQuestionResponse(
        has_question=True,
        question=user.security_question,
    )


@router.post("/password-reset/confirm", status_code=204)
def password_reset_confirm(
    payload: PasswordResetRequest,
    db: Session = Depends(get_db),
) -> None:
    """Step 2 of a password reset: verify the answer and set a new password.

    The submitted security answer is normalised and checked against the
    stored bcrypt hash. On a match the password is replaced; otherwise a
    401 is returned. The error message is deliberately generic so the
    endpoint does not reveal whether the email or the answer was wrong.
    """
    user = (
        db.query(User).filter(User.email == payload.email).one_or_none()
    )
    answer_ok = (
        user is not None
        and user.is_active
        and user.security_answer_hash is not None
        and verify_password(
            _normalise_answer(payload.security_answer),
            user.security_answer_hash,
        )
    )
    if not user or not answer_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="That security answer did not match.",
        )

    user.password_hash = hash_password(payload.new_password)
    db.add(user)
    db.commit()

    record_event(
        db, event_type="password_reset",
        summary="Password reset via security question.",
        user=user,
    )
