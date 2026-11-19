"""KH: which recipes a household cooks often and which it has not cooked for long (D67). A "made" event is what
Mealie's "I made this" dialog and the daily meal-plan task write into the recipe timeline."""

from datetime import UTC, datetime, timedelta

import sqlalchemy as sa
from pydantic import UUID4
from sqlalchemy.orm import Session

from mealie.db.models.household.household_to_recipe import HouseholdToRecipe
from mealie.db.models.recipe.recipe import RecipeModel
from mealie.db.models.recipe.recipe_timeline import RecipeTimelineEvent
from mealie.kh.cooked.schemas import CookedOut, CookedRecipe

ROW_SIZE = 8
OFTEN_WINDOW = timedelta(days=365)
OFTEN_MIN_COUNT = 2
LONG_AGO_AFTER = timedelta(days=30)

# The dialog stores a translated subject ("<user> made this"), so the German and English endings are listed; the
# meal-plan task stores the key "recipe.made-this-for-<meal>|<user>" as an info event.
MADE_BY_DIALOG = sa.and_(
    RecipeTimelineEvent.event_type == "comment",
    sa.or_(RecipeTimelineEvent.subject.like("% made this"), RecipeTimelineEvent.subject.like("% hat's gemacht")),
)
MADE_BY_MEAL_PLAN = sa.and_(
    RecipeTimelineEvent.event_type == "info", RecipeTimelineEvent.subject.like("recipe.made-this-%")
)


def made_counts(session: Session, group_id: UUID4, since: datetime | None, only: list[UUID4] | None = None) -> dict:
    """Made events per recipe id of the group, from SINCE on (all time when None), for the recipes ONLY when given."""
    query = (
        sa.select(RecipeTimelineEvent.recipe_id, sa.func.count())
        .join(RecipeModel, RecipeModel.id == RecipeTimelineEvent.recipe_id)
        .where(RecipeModel.group_id == group_id, sa.or_(MADE_BY_DIALOG, MADE_BY_MEAL_PLAN))
        .group_by(RecipeTimelineEvent.recipe_id)
    )
    if since:
        query = query.where(RecipeTimelineEvent.timestamp >= since)
    if only is not None:
        query = query.where(RecipeTimelineEvent.recipe_id.in_(only))
    return dict(session.execute(query).all())


def cooked_rows(session: Session, group_id: UUID4, household_id: UUID4) -> CookedOut:
    """The group's recipes made most often in the last 365 days (at least twice) and the ones the household made at
    least once, last more than 30 days ago, the oldest first; eight each."""
    now = datetime.now(UTC)
    counts = made_counts(session, group_id, now - OFTEN_WINDOW)
    top = sorted((item for item in counts.items() if item[1] >= OFTEN_MIN_COUNT), key=lambda item: -item[1])[:ROW_SIZE]
    last_made = {
        row.recipe_id: row.last_made
        for row in session.scalars(
            sa.select(HouseholdToRecipe).where(
                HouseholdToRecipe.household_id == household_id, HouseholdToRecipe.last_made.is_not(None)
            )
        )
    }
    old = sorted((id_ for id_, at in last_made.items() if at < now - LONG_AGO_AFTER), key=lambda id_: last_made[id_])
    old = old[:ROW_SIZE]
    all_time = made_counts(session, group_id, None, old)
    return CookedOut(
        often=_cards(session, group_id, [id_ for id_, _ in top], counts, last_made),
        long_ago=_cards(session, group_id, old, all_time, last_made),
    )


def _cards(session: Session, group_id: UUID4, ids: list[UUID4], counts: dict, last_made: dict) -> list[CookedRecipe]:
    """The recipes of the group with these ids, in the order of IDS (those of other groups drop out)."""
    recipes = {
        recipe.id: recipe
        for recipe in session.scalars(
            sa.select(RecipeModel).where(RecipeModel.id.in_(ids), RecipeModel.group_id == group_id)
        )
    }
    return [
        CookedRecipe(
            id=id_,
            slug=recipes[id_].slug,
            name=recipes[id_].name,
            image=recipes[id_].image,
            count=counts.get(id_, 0),
            last_made=last_made.get(id_),
        )
        for id_ in ids
        if id_ in recipes
    ]
