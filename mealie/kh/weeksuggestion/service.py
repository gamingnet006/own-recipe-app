"""KH: picks recipes for the week (D70): the household's wishes first (D72), then the ones the group cooks often and
the ones not cooked for long, then favorites never made, then anything else. Nothing made lately, nothing already
planned, nothing excluded."""

import random
from datetime import UTC, datetime, timedelta
from itertools import chain, zip_longest

import sqlalchemy as sa
from pydantic import UUID4
from sqlalchemy.orm import Session

from mealie.db.models.household.mealplan import GroupMealPlan
from mealie.db.models.recipe.recipe import RecipeModel
from mealie.db.models.users.user_to_recipe import UserToRecipe
from mealie.db.models.users.users import User
from mealie.kh.cooked.service import cooked_rows, made_counts
from mealie.kh.weeksuggestion.schemas import SuggestedRecipe
from mealie.kh.wishes.service import list_wishes

RECENTLY_MADE = timedelta(days=7)
PLANNED_AHEAD = timedelta(days=14)


def _blocked_ids(session: Session, group_id: UUID4, household_id: UUID4, exclude: list[UUID4]) -> set[UUID4]:
    """Recipes that must not be suggested: made in the last 7 days, planned by the household in the next 14 days, or
    asked to be left out."""
    today = datetime.now(UTC).date()
    planned = session.scalars(
        sa.select(GroupMealPlan.recipe_id)
        .join(User, User.id == GroupMealPlan.user_id)
        .where(
            GroupMealPlan.group_id == group_id,
            User.household_id == household_id,
            GroupMealPlan.recipe_id.is_not(None),
            GroupMealPlan.date <= today + PLANNED_AHEAD,
            sa.func.coalesce(GroupMealPlan.end_date, GroupMealPlan.date) >= today,
        )
    )
    recent = made_counts(session, group_id, datetime.now(UTC) - RECENTLY_MADE)
    return {*exclude, *planned, *recent}


def _never_made_favorites(session: Session, group_id: UUID4, user_id: UUID4) -> list[UUID4]:
    """The user's favorite recipes of the group that have no "made" event at all."""
    favorites = list(
        session.scalars(
            sa.select(UserToRecipe.recipe_id)
            .join(RecipeModel, RecipeModel.id == UserToRecipe.recipe_id)
            .where(
                UserToRecipe.user_id == user_id, UserToRecipe.is_favorite.is_(True), RecipeModel.group_id == group_id
            )
        )
    )
    made = made_counts(session, group_id, None, favorites)
    return [id_ for id_ in favorites if id_ not in made]


def suggest_week(
    session: Session,
    group_id: UUID4,
    household_id: UUID4,
    user_id: UUID4,
    days: int,
    exclude: list[UUID4],
    seed: int | None = None,
) -> list[SuggestedRecipe]:
    """DAYS distinct recipes of the group (fewer when it has fewer eligible ones). Wished recipes come first, the
    longest wished first; then "often" and "long ago" alternate,
    then come never-made favorites, then the rest in random order; SEED makes the shuffles repeatable."""
    rng = random.Random(seed)
    blocked = _blocked_ids(session, group_id, household_id, exclude)
    wished = [wish.recipe.id for wish in list_wishes(session, household_id)]
    rows = cooked_rows(session, group_id, household_id)
    cooked = [card.id for card in chain.from_iterable(zip_longest(rows.often, rows.long_ago)) if card]
    favorites = _never_made_favorites(session, group_id, user_id)
    rng.shuffle(favorites)
    rest = sorted(session.scalars(sa.select(RecipeModel.id).where(RecipeModel.group_id == group_id)))
    rng.shuffle(rest)

    picked: list[UUID4] = []
    for id_ in chain(wished, cooked, favorites, rest):
        if id_ not in blocked and id_ not in picked:
            picked.append(id_)
        if len(picked) == days:
            break
    recipes = {
        recipe.id: recipe for recipe in session.scalars(sa.select(RecipeModel).where(RecipeModel.id.in_(picked)))
    }
    return [
        SuggestedRecipe(id=id_, slug=recipes[id_].slug, name=recipes[id_].name, image=recipes[id_].image)
        for id_ in picked
    ]
