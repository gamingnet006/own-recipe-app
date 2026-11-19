"""KH: accounts without e-mail (D53): placeholder addresses, the first-sign-in flag, mailed welcome and confirm links,
and the admin's "e-mail required" switch."""

import hashlib
import re
import secrets
from datetime import UTC, datetime, timedelta

import sqlalchemy as sa
from fastapi import HTTPException, status
from pydantic import UUID4
from sqlalchemy.orm import Session

from mealie.core.config import get_app_settings
from mealie.core.root_logger import get_logger
from mealie.core.security import hash_password
from mealie.db.models.users.users import User
from mealie.kh.accounts.models import KhAccountLink
from mealie.kh.features.settings import get_kh_settings
from mealie.kh.onboarding.mails import send_account_mail
from mealie.kh.onboarding.models import KhAccountSettings, KhAccountToken, KhUserOnboarding
from mealie.kh.onboarding.schemas import OnboardingStatus, WelcomeInfo

logger = get_logger()

PLACEHOLDER_DOMAIN = "no-email.invalid"
MIN_PASSWORD_LENGTH = 8
EMAIL_PATTERN = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def _fail(code: int, message: str) -> HTTPException:
    return HTTPException(code, detail=message)


def placeholder_email() -> str:
    """A unique address that stands for "no e-mail" in Mealie's required, unique e-mail column."""
    return f"{secrets.token_hex(8)}@{PLACEHOLDER_DOMAIN}"


def is_placeholder(email: str | None) -> bool:
    """True for D53 placeholders and D52 linked-account addresses: anything ending in .invalid."""
    return (email or "").strip().lower().endswith(".invalid")


def email_or_stored(session: Session, user_id: UUID4, email: str) -> str:
    """The submitted e-mail, or the stored one when it is blank, so an edit form that shows no address for a
    placeholder does not wipe it."""
    if email.strip():
        return email
    return session.execute(sa.select(User.email).where(User.id == user_id)).scalar_one_or_none() or email


def _onboarding_row(session: Session, user_id: UUID4) -> KhUserOnboarding | None:
    return session.execute(sa.select(KhUserOnboarding).where(KhUserOnboarding.user_id == user_id)).scalar_one_or_none()


def _row_for(session: Session, user_id: UUID4) -> KhUserOnboarding:
    """The user's onboarding row, created (not yet committed) when there is none."""
    row = _onboarding_row(session, user_id)
    if row is None:
        row = KhUserOnboarding(session=session, user_id=user_id, must_change_password=False)
        session.add(row)
    return row


def mark_new_user(session: Session, user_id: UUID4) -> None:
    """Makes the person choose their own password at the first sign-in."""
    _row_for(session, user_id).must_change_password = True
    session.commit()


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def issue_token(session: Session, user_id: UUID4, kind: str, email: str) -> str:
    """Stores a new link token for the user (older ones of the same kind are dropped) and returns the raw token,
    which only ever travels in the mail."""
    session.execute(sa.delete(KhAccountToken).where(KhAccountToken.user_id == user_id, KhAccountToken.kind == kind))
    token = secrets.token_urlsafe(32)
    session.add(KhAccountToken(session=session, user_id=user_id, kind=kind, token_hash=_hash(token), email=email))
    session.commit()
    return token


def use_token(session: Session, token: str, kind: str) -> KhAccountToken:
    """The stored token for this link; 400 when unknown or older than the link lifetime. The caller deletes it."""
    row = session.execute(
        sa.select(KhAccountToken).where(KhAccountToken.token_hash == _hash(token), KhAccountToken.kind == kind)
    ).scalar_one_or_none()
    lifetime = timedelta(hours=get_kh_settings().account_link_hours)
    if row is None or datetime.now(UTC) - row.created_at > lifetime:
        raise _fail(status.HTTP_400_BAD_REQUEST, "This link is invalid or has expired")
    return row


def _drop_tokens(session: Session, user_id: UUID4, kind: str) -> None:
    """Deletes the user's open links of KIND, so a mail that reached the wrong person cannot be used later."""
    session.execute(sa.delete(KhAccountToken).where(KhAccountToken.user_id == user_id, KhAccountToken.kind == kind))


def _welcome_token(session: Session, token: str) -> KhAccountToken:
    """The welcome link's token while it still fits the account: the first password not yet chosen and the address
    the mail went to still the account's (400 otherwise, like an unknown link)."""
    row = use_token(session, token, "welcome")
    onboarding = _onboarding_row(session, row.user_id)
    user = session.get(User, row.user_id)
    if user is None or onboarding is None or not onboarding.must_change_password or user.email != row.email:
        raise _fail(status.HTTP_400_BAD_REQUEST, "This link is invalid or has expired")
    return row


def _email_required(session: Session) -> bool:
    return bool(session.execute(sa.select(KhAccountSettings.email_required)).scalars().first())


def status_of(session: Session, user: User) -> OnboardingStatus:
    """What the person still has to do. Without mail sending nobody is asked for an address."""
    row = _onboarding_row(session, user.id)
    linked = session.execute(sa.select(KhAccountLink.id).where(KhAccountLink.user_id == user.id)).first() is not None
    unverified = is_placeholder(user.email) or (row.verified_email if row else None) != user.email
    # admins are never asked: the one who turns the switch on must not be locked out by it
    needs_email = (
        _email_required(session) and get_app_settings().SMTP_ENABLE and not user.admin and not linked and unverified
    )
    pending = session.execute(
        sa.select(KhAccountToken.email).where(KhAccountToken.user_id == user.id, KhAccountToken.kind == "verify")
    ).scalar_one_or_none()
    return OnboardingStatus(
        must_change_password=bool(row and row.must_change_password),
        needs_email=needs_email,
        pending_email=pending,
        tour=bool(row and row.tour),
    )


def _check_password(password: str) -> str:
    if len(password.strip()) < MIN_PASSWORD_LENGTH:
        raise _fail(status.HTTP_400_BAD_REQUEST, f"The password needs at least {MIN_PASSWORD_LENGTH} characters")
    return password


def _store_password(session: Session, user_id: UUID4, password: str) -> None:
    """Hashes and saves the password; Mealie's update_password also ends every older session."""
    user = session.get(User, user_id)
    user.update_password(hash_password(_check_password(password)))  # type: ignore[union-attr]


def set_own_password(session: Session, user: User, password: str) -> None:
    """Lets a new person choose their password, once; 400 when nothing is required."""
    row = _onboarding_row(session, user.id)
    if row is None or not row.must_change_password:
        raise _fail(status.HTTP_400_BAD_REQUEST, "No password change is required")
    _store_password(session, user.id, password)
    row.must_change_password = False
    _drop_tokens(session, user.id, "welcome")
    session.commit()


def request_verification(session: Session, user: User, email: str, accept_language: str | None) -> None:
    """Mails a confirm link to the address; 400 for a bad address, 409 when another account has it, 503 when the
    mail cannot be sent."""
    address = email.strip().lower()
    if not EMAIL_PATTERN.fullmatch(address) or is_placeholder(address):
        raise _fail(status.HTTP_400_BAD_REQUEST, "This is not a valid e-mail address")
    if session.execute(sa.select(User.id).where(User.email == address, User.id != user.id)).first():
        raise _fail(status.HTTP_409_CONFLICT, "This e-mail address is already used by another account")
    if not get_app_settings().SMTP_ENABLE:
        raise _fail(status.HTTP_503_SERVICE_UNAVAILABLE, "Mail sending is not set up")
    token = issue_token(session, user.id, "verify", address)
    try:
        sent = send_account_mail("verify", address, token, accept_language)
    except Exception:
        logger.exception("failed to send the confirm e-mail")
        sent = False
    if not sent:
        _drop_tokens(session, user.id, "verify")
        session.commit()
        raise _fail(status.HTTP_503_SERVICE_UNAVAILABLE, "The mail could not be sent")


def confirm_email(session: Session, token: str) -> None:
    """Sets the account's e-mail to the confirmed address (409 when someone took it meanwhile)."""
    row = use_token(session, token, "verify")
    if session.execute(sa.select(User.id).where(User.email == row.email, User.id != row.user_id)).first():
        raise _fail(status.HTTP_409_CONFLICT, "This e-mail address is already used by another account")
    session.get(User, row.user_id).email = row.email  # type: ignore[union-attr]
    _row_for(session, row.user_id).verified_email = row.email
    session.delete(row)
    session.commit()


def welcome_info(session: Session, token: str) -> WelcomeInfo:
    """Username and name for the welcome page; the link stays valid."""
    user = session.get(User, _welcome_token(session, token).user_id)
    return WelcomeInfo(username=user.username, full_name=user.full_name or "")  # type: ignore[union-attr]


def accept_welcome(session: Session, token: str, password: str) -> None:
    """Sets the chosen password; following the link proves the address, so it counts as confirmed."""
    row = _welcome_token(session, token)
    _store_password(session, row.user_id, password)
    onboarding = _row_for(session, row.user_id)
    onboarding.must_change_password = False
    onboarding.verified_email = row.email
    session.delete(row)
    session.commit()


def after_admin_create(
    session: Session, user_id: UUID4, email: str, username: str, accept_language: str | None
) -> None:
    """Marks an admin-created account for its first sign-in and mails a welcome link when it has a real address and
    mail works; a failed mail is logged and never fails the creation."""
    mark_new_user(session, user_id)
    if is_placeholder(email) or not get_app_settings().SMTP_ENABLE:
        return
    try:
        token = issue_token(session, user_id, "welcome", email)
        if not send_account_mail("welcome", email, token, accept_language, username):
            logger.error("the welcome e-mail was not accepted by the mail server")
    except Exception:
        logger.exception("failed to send the welcome e-mail")


def after_password_reset(session: Session, user_id: UUID4) -> None:
    """A reset through Mealie's link means the person chose a password, so the first-sign-in step is done."""
    row = _onboarding_row(session, user_id)
    if row is not None and row.must_change_password:
        row.must_change_password = False
    _drop_tokens(session, user_id, "welcome")
    session.commit()


def set_tour(session: Session, user_id: UUID4, tour: bool) -> None:
    """Sets or clears the first-sign-in tour of a user (D59); 404 for an unknown user. Commits."""
    if session.get(User, user_id) is None:
        raise _fail(status.HTTP_404_NOT_FOUND, "User not found")
    _row_for(session, user_id).tour = tour
    session.commit()


def delete_user_rows(session: Session, user_id: UUID4) -> None:
    """Deletes a deleted user's onboarding row and tokens; SQLite in Mealie skips cascades. Commits."""
    session.execute(sa.delete(KhUserOnboarding).where(KhUserOnboarding.user_id == user_id))
    session.execute(sa.delete(KhAccountToken).where(KhAccountToken.user_id == user_id))
    session.commit()


def get_email_required(session: Session) -> bool:
    """The admin switch "e-mail required"."""
    return _email_required(session)


def set_email_required(session: Session, value: bool) -> None:
    """Saves the switch; turning it on needs working mail, otherwise nobody could confirm an address (400)."""
    if value and not get_app_settings().SMTP_ENABLE:
        raise _fail(status.HTTP_400_BAD_REQUEST, "Mail sending is not set up")
    row = session.execute(sa.select(KhAccountSettings)).scalars().first()
    if row is None:
        row = KhAccountSettings(session=session, email_required=value)
        session.add(row)
    row.email_required = value
    session.commit()
