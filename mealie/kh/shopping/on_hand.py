"""KH: "always in the house" for a food (D65): Mealie keeps it per household (households_to_ingredient_foods) and
reads it when recipe ingredients go onto a list; this sets or clears the household's link for any member."""

from pydantic import UUID4
from sqlalchemy.orm import Session

from mealie.db.models.household.household import Household
from mealie.db.models.recipe.ingredient import IngredientFoodModel


def set_on_hand(session: Session, group_id: UUID4, household_id: UUID4, food_id: UUID4, on_hand: bool) -> bool:
    """Marks the food as on hand for the household (or clears it); other households keep their own state.
    False, with nothing changed, when the food does not belong to the group."""
    food = session.get(IngredientFoodModel, food_id)
    household = session.get(Household, household_id)
    if food is None or household is None or food.group_id != group_id:
        return False
    linked = household in food.households_with_ingredient_food
    if on_hand and not linked:
        food.households_with_ingredient_food.append(household)
    elif not on_hand and linked:
        food.households_with_ingredient_food.remove(household)
    session.commit()
    return True
