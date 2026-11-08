"""KH: "Ich vertrage nicht" (D44): a user's list of allergens and the warnings it gives a household's recipes."""

import sqlalchemy as sa
from pydantic import UUID4
from sqlalchemy.orm import Session

from mealie.db.models.users.users import User
from mealie.kh.allergens.models import KhUserAllergies
from mealie.kh.allergens.schemas import AllergenHit, AllergenWarning


def load_allergies(session: Session, user_id: UUID4) -> list[str]:
    """The allergens the user cannot have (empty when never set)."""
    row = session.execute(sa.select(KhUserAllergies).where(KhUserAllergies.user_id == user_id)).scalar_one_or_none()
    return list(row.allergens) if row else []


def save_allergies(session: Session, user_id: UUID4, allergens: list[str]) -> None:
    """Stores the user's list, replacing the old one. Commits."""
    row = session.execute(sa.select(KhUserAllergies).where(KhUserAllergies.user_id == user_id)).scalar_one_or_none()
    if row is None:
        session.add(KhUserAllergies(session=session, user_id=user_id, allergens=allergens))
    else:
        row.allergens = allergens
    session.commit()


def household_members(session: Session, household_id: UUID4) -> list[tuple[str, set[str]]]:
    """The members of the household with a non-empty list, as (full name, allergens), by name."""
    rows = session.execute(
        sa.select(User.full_name, User.username, KhUserAllergies.allergens)
        .join(KhUserAllergies, KhUserAllergies.user_id == User.id)
        .where(User.household_id == household_id)
    ).all()
    return sorted((full_name or username, set(allergens)) for full_name, username, allergens in rows if allergens)


def warnings_for(members: list[tuple[str, set[str]]], hits: list[AllergenHit]) -> list[AllergenWarning]:
    """For each allergen the recipe has (a correction False takes it out), the members who cannot have it."""
    warnings = []
    for hit in hits:
        if hit.corrected is False:
            continue
        names = [name for name, allergens in members if hit.allergen in allergens]
        if names:
            warnings.append(AllergenWarning(allergen=hit.allergen, names=names))
    return warnings


def household_warnings(session: Session, household_id: UUID4, hits: list[AllergenHit]) -> list[AllergenWarning]:
    """The warnings of HITS for one household; only its own members are named."""
    return warnings_for(household_members(session, household_id), hits)
