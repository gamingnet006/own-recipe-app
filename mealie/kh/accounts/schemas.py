"""KH: the data of switching households (D52)."""

from pydantic import UUID4

from mealie.schema._mealie import MealieModel


class AccountOut(MealieModel):
    """One account of a person, with where it lives."""

    user_id: UUID4
    full_name: str
    household_id: UUID4
    household: str
    group: str
    group_slug: str
    current: bool = False


class PersonOut(MealieModel):
    """A person (primary account) with all accounts, the primary one first."""

    user_id: UUID4
    full_name: str
    accounts: list[AccountOut]


class SwitchIn(MealieModel):
    user_id: UUID4


class LinkIn(MealieModel):
    """Gives PERSON an account in HOUSEHOLD."""

    user_id: UUID4
    household_id: UUID4


class HeirOut(MealieModel):
    """The person who takes over the recipes and lists of a deleted account."""

    id: UUID4
    name: str


class DeletePreviewOut(MealieModel):
    """What deleting the own account would do; BLOCKED is the German reason it is not possible, else None."""

    heir: HeirOut | None
    recipes: int
    lists: int
    blocked: str | None


class DeleteIn(MealieModel):
    """CONFIRM must be the username, so the account is not deleted by a stray click."""

    confirm: str
