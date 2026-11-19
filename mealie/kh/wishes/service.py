"""KH: the household wish list (D72): wishing, taking a wish back, listing the open wishes, and planning a wished
recipe. A wish is fulfilled, and deleted for everybody, as soon as the household has a meal-plan entry for the recipe
today or later."""

from datetime import UTC, datetime

import sqlalchemy as sa
from pydantic import UUID4
from sqlalchemy.orm import Session

from mealie.db.models.household.mealplan import GroupMealPlan
from mealie.db.models.recipe.recipe import RecipeModel
from mealie.db.models.users.users import User
from mealie.kh.wishes.models import KhRecipeWish
from mealie.kh.wishes.schemas import WishOut, WishPerson, WishRecipe


def drop_fulfilled(session: Session, household_id: UUID4) -> None:
    """Deletes the household's wishes for recipes it has planned for today or later (week entries count until they
    end)."""
    today = datetime.now(UTC).date()
    planned = (
        sa.select(GroupMealPlan.recipe_id)
        .join(User, User.id == GroupMealPlan.user_id)
        .where(
            User.household_id == household_id,
            GroupMealPlan.recipe_id.is_not(None),
            sa.func.coalesce(GroupMealPlan.end_date, GroupMealPlan.date) >= today,
        )
    )
    session.execute(
        sa.delete(KhRecipeWish).where(KhRecipeWish.household_id == household_id, KhRecipeWish.recipe_id.in_(planned))
    )
    session.commit()


def list_wishes(session: Session, household_id: UUID4) -> list[WishOut]:
    """The household's open wishes grouped by recipe, the longest wished first."""
    drop_fulfilled(session, household_id)
    # inner joins: on SQLite, which does not enforce the CASCADE, a wish of a deleted user or recipe stays unseen
    rows = session.execute(
        sa.select(KhRecipeWish, RecipeModel, User.full_name, User.username)
        .join(User, User.id == KhRecipeWish.user_id)
        .join(RecipeModel, RecipeModel.id == KhRecipeWish.recipe_id)
        .where(KhRecipeWish.household_id == household_id)
        .order_by(KhRecipeWish.created_at, KhRecipeWish.id)
    ).all()
    by_recipe: dict[UUID4, WishOut] = {}
    for wish, recipe, full_name, username in rows:
        if wish.recipe_id not in by_recipe:
            card = WishRecipe(id=recipe.id, slug=recipe.slug, name=recipe.name, image=recipe.image)
            by_recipe[wish.recipe_id] = WishOut(recipe=card, people=[], since=wish.created_at)
        by_recipe[wish.recipe_id].people.append(WishPerson(id=wish.user_id, name=full_name or username))
    return list(by_recipe.values())


def add_wish(session: Session, group_id: UUID4, household_id: UUID4, user_id: UUID4, recipe_id: UUID4) -> None:
    """The user wishes the recipe (a second wish of the same person changes nothing)."""
    exists = session.scalar(
        sa.select(KhRecipeWish.id).where(
            KhRecipeWish.household_id == household_id,
            KhRecipeWish.recipe_id == recipe_id,
            KhRecipeWish.user_id == user_id,
        )
    )
    if not exists:
        session.add(
            KhRecipeWish(
                session=session, group_id=group_id, household_id=household_id, recipe_id=recipe_id, user_id=user_id
            )
        )
        session.commit()


def remove_wish(session: Session, household_id: UUID4, user_id: UUID4, recipe_id: UUID4) -> None:
    """Takes back the user's own wish; the wishes of others stay."""
    session.execute(
        sa.delete(KhRecipeWish).where(
            KhRecipeWish.household_id == household_id,
            KhRecipeWish.recipe_id == recipe_id,
            KhRecipeWish.user_id == user_id,
        )
    )
    session.commit()
