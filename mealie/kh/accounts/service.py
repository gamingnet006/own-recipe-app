"""KH: switching households (D52): a person's accounts, creating a linked account, and copying the primary
account's permissions before a switch."""

import secrets

import sqlalchemy as sa
from fastapi import HTTPException, status
from pydantic import UUID4
from sqlalchemy.orm import Session

from mealie.core.security import security
from mealie.db.models.household import Household
from mealie.db.models.users.users import User
from mealie.kh.accounts.models import KhAccountLink
from mealie.kh.accounts.schemas import AccountOut, PersonOut
from mealie.kh.allergens.models import KhUserAllergies
from mealie.repos.all_repositories import AllRepositories
from mealie.routes.users._helpers import permission_attrs
from mealie.schema.user.user import UserIn


def _primary_id(session: Session, user_id: UUID4) -> UUID4:
    """The person's primary account: the one linked accounts point to, or the account itself."""
    primary = session.execute(sa.select(KhAccountLink.primary_user_id).where(KhAccountLink.user_id == user_id))
    return primary.scalar_one_or_none() or user_id


def _person_users(session: Session, primary_id: UUID4) -> list[User]:
    """All accounts of the person, the primary one first."""
    linked = sa.select(KhAccountLink.user_id).where(KhAccountLink.primary_user_id == primary_id)
    users = session.execute(sa.select(User).where(sa.or_(User.id == primary_id, User.id.in_(linked)))).scalars().all()
    return sorted(users, key=lambda user: user.id != primary_id)


def _account(user: User, current_id: UUID4 | None = None) -> AccountOut:
    return AccountOut(
        user_id=user.id,
        full_name=user.full_name or "",
        household_id=user.household_id,
        household=user.household.name,
        group=user.group.name,
        group_slug=user.group.slug,
        current=user.id == current_id,
    )


def accounts_of(session: Session, user_id: UUID4) -> list[AccountOut]:
    """The accounts of USER's person; empty when the person has only one, which hides the switch."""
    users = _person_users(session, _primary_id(session, user_id))
    return [_account(user, user_id) for user in users] if len(users) > 1 else []


def all_people(session: Session) -> list[PersonOut]:
    """Every person (every account that is not linked) with all their accounts, for the admin page."""
    linked = sa.select(KhAccountLink.user_id)
    primaries = session.execute(sa.select(User).where(User.id.not_in(linked)).order_by(User.full_name)).scalars()
    return [
        PersonOut(
            user_id=p.id, full_name=p.full_name or "", accounts=[_account(u) for u in _person_users(session, p.id)]
        )
        for p in primaries
    ]


def _strip_rights(user: User) -> None:
    """Takes every permission from an account that is no longer linked, so copied rights cannot outlive the link."""
    for name in permission_attrs:
        setattr(user, name, False)


def sync_linked_rights(session: Session, primary_id: UUID4) -> None:
    """Copies the primary's permissions onto all its linked accounts, so they are the same in every household; runs
    when the admin changes the primary and before a switch. Does nothing for an account that is no primary. Commits."""
    users = _person_users(session, primary_id)
    for user in users[1:]:
        for name in permission_attrs:
            setattr(user, name, getattr(users[0], name))
    session.commit()


def delete_links(session: Session, user_id: UUID4) -> None:
    """Deletes the links a deleted user is part of, on either side, and takes the rights from the accounts that were
    linked to it; SQLite in Mealie checks no foreign keys, so the cascade is not enough. Commits."""
    for user in _person_users(session, user_id):
        if user.id != user_id:
            _strip_rights(user)
    session.execute(
        sa.delete(KhAccountLink).where(
            sa.or_(KhAccountLink.user_id == user_id, KhAccountLink.primary_user_id == user_id)
        )
    )
    session.commit()


def _fail(code: int, message: str) -> HTTPException:
    return HTTPException(code, detail=message)


def _free_username(session: Session, base: str) -> str:
    """BASE, or BASE-2, BASE-3 ... the first that is not taken."""
    taken = set(session.execute(sa.select(User.username).where(User.username.like(f"{base}%"))).scalars())
    return next(name for name in (base, *(f"{base}-{n}" for n in range(2, len(taken) + 3))) if name not in taken)


def link_account(repos: AllRepositories, primary_id: UUID4, household_id: UUID4) -> AccountOut:
    """Creates the person's account in HOUSEHOLD with the primary's permissions and allergies, and links it."""
    session = repos.session
    primary = session.get(User, primary_id)
    household = session.get(Household, household_id)
    if primary is None or household is None:
        raise _fail(status.HTTP_404_NOT_FOUND, "Person or household not found")
    if _primary_id(session, primary_id) != primary_id:
        raise _fail(status.HTTP_400_BAD_REQUEST, "A linked account cannot get linked accounts of its own")
    if any(user.household_id == household_id for user in _person_users(session, primary_id)):
        raise _fail(status.HTTP_400_BAD_REQUEST, "The person already has an account in this household")

    # The e-mail is only a placeholder for the unique column: nobody can sign in with the random password
    created = repos.users.create(
        UserIn(
            username=_free_username(session, f"{primary.username}-{household.slug}"),
            full_name=f"{primary.full_name} ({household.name})",
            email=f"{secrets.token_hex(8)}@linked-account.invalid",
            password=security.hash_password(secrets.token_urlsafe(32)),
            group=household.group.name,
            household=household.name,
            **{name: getattr(primary, name) for name in permission_attrs},
        ).model_dump()  # validated as UserIn, handed over as a dict like Mealie's own sign-in providers do
    )
    session.add(KhAccountLink(session=session, primary_user_id=primary_id, user_id=created.id))
    allergies = session.execute(
        sa.select(KhUserAllergies).where(KhUserAllergies.user_id == primary_id)
    ).scalar_one_or_none()
    if allergies is not None:
        session.add(KhUserAllergies(session=session, user_id=created.id, allergens=list(allergies.allergens)))
    session.commit()
    return _account(session.get(User, created.id))  # type: ignore[arg-type]


def unlink_account(session: Session, user_id: UUID4) -> None:
    """Dissolves the link and takes the account's rights; the account and its recipes stay."""
    link = session.execute(sa.select(KhAccountLink).where(KhAccountLink.user_id == user_id)).scalar_one_or_none()
    if link is None:
        raise _fail(status.HTTP_404_NOT_FOUND, "This account is not linked")
    _strip_rights(session.get(User, user_id))  # type: ignore[arg-type]
    session.delete(link)
    session.commit()


def prepare_switch(session: Session, current_id: UUID4, target_id: UUID4) -> None:
    """Checks that TARGET belongs to the current account's person (404 otherwise, which does not reveal whether the
    account exists) and copies the primary's permissions onto it, so they stay the same in every household."""
    primary_id = _primary_id(session, current_id)
    users = {user.id: user for user in _person_users(session, primary_id)}
    if target_id not in users:
        raise _fail(status.HTTP_404_NOT_FOUND, "Account not found")
    sync_linked_rights(session, primary_id)
