"""KH: the wish list's routes under /api/kh/wishes (D72), for the user's household and with the planner add-on on."""

from fastapi import HTTPException, status
from pydantic import UUID4

from mealie.kh.notifications.events import notify_plan_created, notify_wish
from mealie.kh.wishes.schemas import WishOut, WishPlan
from mealie.kh.wishes.service import add_wish, drop_fulfilled, list_wishes, remove_wish
from mealie.repos.all_repositories import get_repositories
from mealie.routes._base import BaseCrudController, controller
from mealie.routes._base.routers import UserAPIRouter
from mealie.schema.meal_plan.new_meal import PlanEntryOut, PlanEntrySave
from mealie.services.event_bus_service.event_types import EventMealplanData, EventOperation, EventTypes

router = UserAPIRouter(prefix="/wishes")


@controller(router)
class KhWishController(BaseCrudController):
    """What the family wishes to eat."""

    def _group_recipe(self, recipe_id: UUID4):
        """The recipe if it belongs to the group (it may be another household's, like meal-plan entries allow)."""
        recipes = get_repositories(self.session, group_id=self.group_id, household_id=None).recipes
        if (recipe := recipes.get_one(recipe_id, "id")) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND)
        return recipe

    @router.get("", response_model=list[WishOut])
    def open_wishes(self) -> list[WishOut]:
        """The household's open wishes grouped by recipe, the longest wished first."""
        return list_wishes(self.session, self.household_id)

    @router.put("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
    def wish(self, recipe_id: UUID4) -> None:
        """The signed-in user wishes the recipe."""
        recipe = self._group_recipe(recipe_id)
        add_wish(self.session, self.group_id, self.household_id, self.user.id, recipe_id)
        notify_wish(self.user.id, self.household_id, recipe.name)  # D75

    @router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
    def unwish(self, recipe_id: UUID4) -> None:
        """The signed-in user takes back their own wish."""
        remove_wish(self.session, self.household_id, self.user.id, recipe_id)

    @router.post("/{recipe_id}/plan", response_model=PlanEntryOut, status_code=status.HTTP_201_CREATED)
    def plan(self, recipe_id: UUID4, data: WishPlan) -> PlanEntryOut:
        """Plans the recipe like Mealie's own create does (entry, event) and, with that, ends everybody's wish."""
        recipe = self._group_recipe(recipe_id)
        entry = PlanEntrySave(
            date=data.date,
            entry_type=data.entry_type,
            recipe_id=recipe_id,
            group_id=self.group_id,
            user_id=self.user.id,
        )
        result = self.repos.meals.create(entry)
        self.publish_event(
            event_type=EventTypes.mealplan_entry_created,
            document_data=EventMealplanData(
                operation=EventOperation.create,
                mealplan_id=result.id,
                recipe_id=recipe_id,
                recipe_name=recipe.name,
                recipe_slug=recipe.slug,
                date=data.date,
                end_date=None,
            ),
            group_id=self.group_id,
            household_id=self.household_id,
            message=f"{recipe.name}: {data.date.isoformat()}",
        )
        drop_fulfilled(self.session, self.household_id)
        notify_plan_created(self.user.id, self.household_id, recipe.name, data.date)  # D75
        return result
