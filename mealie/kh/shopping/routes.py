"""KH: the shopping page's routes under /api/kh/shopping (D60). Mealie's own POST /api/foods and /api/units need the
permission to organize, which a normal family member lacks; these two let every signed-in member of the group
write down an item, and only ever make a food or one of four standard units."""

from fastapi import HTTPException, status

from mealie.kh.notifications.events import notify_items_added
from mealie.kh.shopping.on_hand import set_on_hand
from mealie.kh.shopping.schemas import AddByVoiceIn, AddByVoiceOut, EnsureFoodIn, EnsureUnitIn, OnHandIn
from mealie.kh.shopping.service import ensure_food, ensure_unit
from mealie.kh.shopping.voice import add_to_list, parse_articles, pick_list, plan_additions, spoken_summary
from mealie.repos.all_repositories import get_repositories
from mealie.routes._base import BaseUserController, controller
from mealie.routes._base.routers import UserAPIRouter
from mealie.schema.household.group_shopping_list import ShoppingListCreate, ShoppingListOut
from mealie.schema.recipe.recipe_ingredient import IngredientFoodOut, IngredientUnitOut
from mealie.schema.response import ErrorResponse
from mealie.services.household_services.shopping_lists import ShoppingListService

router = UserAPIRouter(prefix="/shopping")
FIRST_LIST_NAME = "Einkaufsliste"


@controller(router)
class KhShoppingController(BaseUserController):
    """Foods and units for members who may not organize."""

    @router.post("/ensure-food", response_model=IngredientFoodOut)
    def food(self, data: EnsureFoodIn) -> IngredientFoodOut:
        """The group's food of this name (ignoring case and singular or plural), made when there is none, for any
        member, also without the permission to organize. A label must belong to the user's group (422 otherwise)."""
        repos = get_repositories(self.session, group_id=self.group_id, household_id=None)
        if data.label_id and repos.group_multi_purpose_labels.get_one(data.label_id) is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, ErrorResponse.respond("Unknown label"))
        return ensure_food(repos, data.name, data.label_id)

    @router.post("/ensure-unit", response_model=IngredientUnitOut)
    def unit(self, data: EnsureUnitIn) -> IngredientUnitOut:
        """The group's unit g, kg, ml or l (found by abbreviation or name, ignoring case), made when missing, for
        any member, also without the permission to organize; any other abbreviation is refused with 422."""
        repos = get_repositories(self.session, group_id=self.group_id, household_id=None)
        return ensure_unit(repos, data.abbreviation)

    @router.post("/add", response_model=AddByVoiceOut)
    def add(self, data: AddByVoiceIn) -> AddByVoiceOut:
        """Puts the articles in a said or typed text ("Milch und 2 Butter") on the named list or the household list
        updated last (D64, for the Siri Shortcut, which signs in with an API key); a store at the end of the text
        ("... bei Rewe") picks the list when it matches one (D87). An open article gets the amount,
        a ticked-off one is put back. Without any list the first one is made; 404 for an unknown list name, 422
        when no article is understood."""
        lists = self.repos.group_shopping_lists.get_all()
        # D87: the stores said ("bei Rewe") pick the lists; a list given explicitly wins for everything
        groups = plan_additions(data.text, [] if data.list else [entry.name or "" for entry in lists])
        if not groups:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, ErrorResponse.respond("Ich habe keinen Artikel verstanden.")
            )
        group_repos = get_repositories(self.session, group_id=self.group_id, household_id=None)
        # all or nothing: every list is found and every article understood before anything is written
        targets = [self._existing_list(lists, list_name or data.list) for list_name, _ in groups]
        try:
            parsed = [parse_articles(group_repos, articles) for _, articles in groups]
        except ValueError:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, ErrorResponse.respond("Ich habe keinen Artikel verstanden.")
            ) from None
        results: list[tuple[str, list[str]]] = []
        for target, lines in zip(targets, parsed, strict=True):
            shopping_list = target or self._make_first_list()
            names = add_to_list(self.repos, group_repos, shopping_list, lines)
            notify_items_added(self.user.id, self.household_id, shopping_list.id, names)  # D75
            results.append((shopping_list.name or FIRST_LIST_NAME, names))
        return AddByVoiceOut(message=spoken_summary(results))

    def _existing_list(self, lists: list[ShoppingListOut], name: str | None) -> ShoppingListOut | None:
        """The list called NAME, else the one updated last; None for a family without any list and no name (the
        first one is made when writing), 404 for a name that no list has."""
        shopping_list = pick_list(lists, name)
        if shopping_list is None and (lists or name):
            raise HTTPException(status.HTTP_404_NOT_FOUND, ErrorResponse.respond(f"Die Liste {name} gibt es nicht."))
        return shopping_list

    def _make_first_list(self) -> ShoppingListOut:
        """A new family's first "Hey Siri" makes the list "Einkaufsliste" instead of failing."""
        return ShoppingListService(self.repos).create_one_list(ShoppingListCreate(name=FIRST_LIST_NAME), self.user.id)

    @router.post("/on-hand", response_model=IngredientFoodOut)
    def on_hand(self, data: OnHandIn) -> IngredientFoodOut:
        """Marks a food of the group as always in the house for the user's household, or clears it (D65), for any
        member, also without the permission to organize. Other households keep their own state; a food of another
        group is 404."""
        if not set_on_hand(self.session, self.group_id, self.household_id, data.food_id, data.on_hand):
            raise HTTPException(status.HTTP_404_NOT_FOUND, ErrorResponse.respond("Unknown food"))
        group_repos = get_repositories(self.session, group_id=self.group_id, household_id=None)
        return group_repos.ingredient_foods.get_one(data.food_id)  # type: ignore[return-value]  # found just above
