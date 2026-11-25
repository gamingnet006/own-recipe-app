"""KH: deleting an account without losing the family's recipes (D78): what a deleted user's rows become, who inherits
them, and the checks before a person deletes their own account."""

from dataclasses import dataclass

import sqlalchemy as sa
from fastapi import HTTPException, status
from pydantic import UUID4
from sqlalchemy.orm import Session

from mealie.db.models.household.mealplan import GroupMealPlan
from mealie.db.models.household.shopping_list import ShoppingList
from mealie.db.models.recipe import RecipeComment, RecipeModel, RecipeTimelineEvent
from mealie.db.models.users.user_to_recipe import UserToRecipe
from mealie.db.models.users.users import User
from mealie.kh.accounts.schemas import HeirOut
from mealie.kh.accounts.service import delete_links, person_of
from mealie.kh.allergens.service import delete_user_allergies
from mealie.kh.drafts.models import KhDraft
from mealie.kh.i18n.locale import DEFAULT_LOCALE, Locale
from mealie.kh.i18n.messages import say
from mealie.kh.navigation.service import delete_user_navigation
from mealie.kh.notes.models import KhRecipeNote
from mealie.kh.notices.models import KhNoticeRead
from mealie.kh.notifications.service import delete_user_notifications
from mealie.kh.onboarding.service import delete_user_rows
from mealie.kh.wishes.models import KhRecipeWish
from mealie.repos.all_repositories import get_repositories

# Everything that belongs to the family and not to the person: it moves to the heir. Tokens, password reset tokens,
# favorites/ratings and the KH settings tables are personal and deleted in _delete_personal instead.
_HANDED_OVER = (
    RecipeModel.user_id,
    ShoppingList.user_id,
    GroupMealPlan.user_id,
    RecipeComment.user_id,
    RecipeTimelineEvent.user_id,
    KhDraft.user_id,
    KhDraft.approved_by,
    KhRecipeNote.updated_by,
)

# What belongs to recipes of the whole group, not to the household: it may go to someone in another household.
_GROUP_WIDE = (RecipeComment.user_id, RecipeTimelineEvent.user_id)


@dataclass
class Owned:
    """How many recipes and shopping lists an account owns, and how many meal-plan entries."""

    recipes: int
    lists: int
    plans: int

    def __bool__(self) -> bool:
        return bool(self.recipes or self.lists or self.plans)


def owned_by(session: Session, user_id: UUID4) -> Owned:
    """What USER_ID owns that the family would lose."""

    def count(column) -> int:
        return session.scalar(sa.select(sa.func.count()).select_from(column.class_).where(column == user_id)) or 0

    return Owned(count(RecipeModel.user_id), count(ShoppingList.user_id), count(GroupMealPlan.user_id))


def default_heir(session: Session, user: User, group_wide: bool = False) -> User | None:
    """Another person of USER's household (of the whole group when GROUP_WIDE): an admin or household manager first,
    then the longest-standing account. Never an account of the same person (linked accounts), and None when nobody
    else lives there."""
    own = [account.id for account in person_of(session, user.id)]
    first = sa.case((sa.or_(User.admin.is_(True), User.can_manage_household.is_(True)), 0), else_=1)
    stmt = (
        sa.select(User)
        .where(User.group_id == user.group_id if group_wide else User.household_id == user.household_id)
        .where(User.id.not_in(own))
        .order_by(first, User.created_at, User.id)
    )
    return session.scalars(stmt).first()


def as_heir(user: User | None) -> HeirOut | None:
    """USER as the heir the dialogs show: the id and the name people know."""
    return HeirOut(id=user.id, name=user.full_name or user.username or "") if user else None


def admin_heir(
    session: Session, user_id: UUID4, transfer_to: UUID4 | None, locale: Locale = DEFAULT_LOCALE
) -> UUID4 | None:
    """The heir for an admin deleting USER_ID: the chosen TRANSFER_TO (422 unless it is another person of the same
    household), else the default heir. None only when the user owns nothing or is the last one of the group; otherwise
    409, so nothing is lost."""
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if transfer_to is not None:
        chosen = session.get(User, transfer_to)
        if chosen is None or chosen.id == user.id or chosen.household_id != user.household_id:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, say("heir_same_household", locale))
        return chosen.id
    heir = default_heir(session, user)
    # nobody left in the whole group (Mealie's teardown of a group): nothing can inherit, so it is deleted as before
    if heir is None and owned_by(session, user_id) and default_heir(session, user, group_wide=True):
        raise HTTPException(status.HTTP_409_CONFLICT, say("removal_alone", locale))
    return heir.id if heir else None


def _delete_personal(session: Session, user_id: UUID4) -> None:
    """Deletes the rows that belong to the person alone; SQLite in Mealie skips cascades, so each table is named."""
    for rating in session.scalars(sa.select(UserToRecipe).where(UserToRecipe.user_id == user_id)).all():
        session.delete(rating)  # one by one: the recipe's rating is recalculated on every delete
    session.commit()
    session.execute(sa.delete(KhRecipeWish).where(KhRecipeWish.user_id == user_id))
    session.execute(sa.delete(KhNoticeRead).where(KhNoticeRead.user_id == user_id))
    session.commit()
    delete_links(session, user_id)
    delete_user_allergies(session, user_id)
    delete_user_rows(session, user_id)
    delete_user_navigation(session, user_id)
    delete_user_notifications(session, user_id)


def _hand_over(session: Session, columns: tuple, user_id: UUID4, heir_id: UUID4) -> None:
    """Points every row of COLUMNS that belongs to USER_ID at HEIR_ID, in one commit."""
    for column in columns:
        session.execute(
            sa.update(column.class_).where(column == user_id).values({column.key: heir_id}),
            execution_options={"synchronize_session": False},
        )
    session.commit()


def transfer_and_delete(session: Session, user_id: UUID4, heir_id: UUID4 | None) -> None:
    """Moves the family's rows of USER_ID to HEIR_ID, deletes the personal ones, then the user. HEIR_ID must live in
    the user's household; it may only be None when the user owns nothing. The move is one commit, so a failure
    later never loses recipes; the deletion can simply be run again."""
    user = session.get(User, user_id)
    if user is None:
        raise ValueError("User not found")
    if heir_id is None:
        # Comments and timeline events belong to recipes of the whole group, so they go to a group-wide heir; the
        # family's own rows need a household heir unless nobody is left in the group (Mealie's group teardown).
        group_heir = default_heir(session, user, group_wide=True)
        if group_heir is None:
            pass
        elif owned_by(session, user_id):
            raise ValueError("The user owns recipes, lists or plans, so an heir is needed")
        else:
            _hand_over(session, _GROUP_WIDE, user_id, group_heir.id)
    else:
        heir = session.get(User, heir_id)
        if heir is None or heir.id == user_id or heir.household_id != user.household_id:
            raise ValueError("The heir must be another person of the same household")
        _hand_over(session, _HANDED_OVER, user_id, heir_id)
    session.expire_all()
    _delete_personal(session, user_id)
    get_repositories(session, group_id=None, household_id=None).users.delete(user_id)  # tokens, directory, the row


@dataclass
class OwnDeletion:
    """What deleting the signed-in person's own accounts needs: for each account its heir, and a blocking reason."""

    heirs: dict[UUID4, UUID4 | None]
    owned: Owned
    blocked: str | None


def _blocked_reason(
    session: Session, user: User, person: list[User], heirs: dict[UUID4, UUID4 | None], locale: Locale
) -> str | None:
    """Why the person cannot delete themselves, or None: the last admin of a group, or an account that has nobody to
    leave its recipes to."""
    ids = {account.id for account in person}
    for account in person:
        if account.admin and not session.scalar(
            sa.select(User.id).where(User.group_id == account.group_id, User.admin.is_(True), User.id.not_in(ids))
        ):
            return say("removal_last_admin", locale)
    for account in person:
        if heirs[account.id] is None:
            if account.id == user.id:
                return say("removal_last_person", locale)
            return say("removal_no_heir", locale, household=account.household.name)
    return None


def plan_own_deletion(session: Session, user: User, locale: Locale = DEFAULT_LOCALE) -> OwnDeletion:
    """Heirs, totals and the blocking reason for USER deleting themselves with all their linked accounts."""
    person = person_of(session, user.id)
    heirs = {}
    owned = Owned(0, 0, 0)
    for account in person:
        heir = default_heir(session, account)
        heirs[account.id] = heir.id if heir else None
        mine = owned_by(session, account.id)
        owned = Owned(owned.recipes + mine.recipes, owned.lists + mine.lists, owned.plans + mine.plans)
    return OwnDeletion(heirs, owned, _blocked_reason(session, user, person, heirs, locale))


def delete_own_accounts(session: Session, user: User, locale: Locale = DEFAULT_LOCALE) -> None:
    """Deletes USER and their linked accounts, each with its own household's heir; the primary account goes last, so
    the links of the others are gone by then. Raises ValueError when the deletion is blocked."""
    plan = plan_own_deletion(session, user, locale)
    if plan.blocked:
        raise ValueError(plan.blocked)
    for account in reversed(person_of(session, user.id)):
        transfer_and_delete(session, account.id, plan.heirs[account.id])
