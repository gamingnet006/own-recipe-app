"""KH: substitution hints and recipe variants (D44). A rule says: an ingredient text with MATCH that has ALLERGEN can
be replaced by REPLACEMENT. A household's own rules come before the standard ones in data/substitutions.json."""

import json
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import sqlalchemy as sa
from pydantic import UUID4

from mealie.db.models.recipe import IngredientFoodModel
from mealie.kh.allergens.rules import ALLERGENS, allergens_of_line, line_text, text_has
from mealie.kh.allergens.schemas import AllergenHit, LineSubstitution
from mealie.repos.all_repositories import AllRepositories
from mealie.schema.recipe.recipe import Recipe
from mealie.schema.recipe.recipe_ingredient import IngredientFood, RecipeIngredient, SaveIngredientFood
from mealie.schema.recipe.request_helpers import RecipeDuplicate
from mealie.services.recipe.recipe_service import RecipeService

SUBSTITUTIONS_JSON = Path(__file__).parent / "data" / "substitutions.json"

# The allergens as the family says them, for the name of a variant.
ALLERGEN_NAMES_DE = {
    "gluten": "Gluten",
    "crustaceans": "Krebstiere",
    "eggs": "Eier",
    "fish": "Fisch",
    "peanuts": "Erdnüsse",
    "soy": "Soja",
    "milk": "Milch",
    "nuts": "Nüsse",
    "celery": "Sellerie",
    "mustard": "Senf",
    "sesame": "Sesam",
    "sulphites": "Sulfite",
    "lupin": "Lupine",
    "molluscs": "Weichtiere",
}


@dataclass(frozen=True)
class Substitution:
    """One rule; own says it is a household's own."""

    match: str
    replacement: str
    allergen: str
    own: bool


@cache
def standard_rules() -> list[Substitution]:
    """The shipped rules, most specific word first (Paniermehl before Mehl), as written in the file."""
    return [Substitution(**rule, own=False) for rule in json.loads(SUBSTITUTIONS_JSON.read_text(encoding="utf-8"))]


def _plan(recipe: Recipe, allergens: list[str], own_rules: list[Substitution]) -> list[tuple[int, LineSubstitution]]:
    """For each line (by index) and each of ALLERGENS the line has: the first rule that fits, own rules first."""
    rules = [*own_rules, *standard_rules()]
    plan = []
    for index, line in enumerate(recipe.recipe_ingredient):
        shown, text = line_text(line)
        found = allergens_of_line(text)
        for allergen in (a for a in allergens if a in found):
            rule = next((r for r in rules if r.allergen == allergen and text_has(text, r.match)), None)
            if rule:
                plan.append((index, LineSubstitution(line=shown, allergen=allergen, replacement=rule.replacement)))
    return plan


def substitutions_for(recipe: Recipe, hits: list[AllergenHit], own_rules: list[Substitution]) -> list[LineSubstitution]:
    """A hint per ingredient line and allergen of the recipe (one a correction took out is left out)."""
    allergens = [hit.allergen for hit in hits if hit.corrected is not False]
    return [sub for _, sub in _plan(recipe, allergens, own_rules)]


def _food_named(repos: AllRepositories, group_id: UUID4, name: str) -> IngredientFood:
    """The group's food with this name (case does not matter), created when there is none."""
    food_id = repos.session.execute(
        sa.select(IngredientFoodModel.id).where(
            IngredientFoodModel.group_id == group_id, sa.func.lower(IngredientFoodModel.name) == name.lower()
        )
    ).scalar()
    foods = repos.ingredient_foods
    return (food_id and foods.get_one(food_id)) or foods.create(SaveIngredientFood(name=name, group_id=group_id))


def save_variant(
    service: RecipeService,
    repos: AllRepositories,
    recipe: Recipe,
    hits: list[AllergenHit],
    allergens: list[str],
    own_rules: list[Substitution],
) -> Recipe:
    """Saves a copy of RECIPE named "<Name> (ohne <allergens>)" whose lines with one of ALLERGENS use the replacement
    food; quantity and unit stay. A line without a food carries its text in the note, so the note is replaced.
    ValueError when no line can be replaced. The original is not touched."""
    present = [hit.allergen for hit in hits if hit.corrected is not False and hit.allergen in allergens]
    plan: dict[int, LineSubstitution] = {}
    for index, sub in _plan(recipe, present, own_rules):
        plan.setdefault(index, sub)  # one replacement per line
    if not plan:
        raise ValueError("No ingredient line can be replaced")

    replaced = {sub.allergen for sub in plan.values()}
    names = ", ".join(ALLERGEN_NAMES_DE[a] for a in ALLERGENS if a in replaced)
    new = service.duplicate_one(recipe.slug, RecipeDuplicate(name=f"{recipe.name} (ohne {names})"))
    lines = list(new.recipe_ingredient)
    for index, sub in plan.items():
        lines[index] = _replaced(lines[index], sub.replacement, repos, recipe.group_id)
    new.recipe_ingredient = lines
    return service.update_one(new.slug, new)


def _replaced(line: RecipeIngredient, replacement: str, repos: AllRepositories, group_id: UUID4) -> RecipeIngredient:
    """LINE with the replacement food (or note, for a line without a food) and its display text made anew."""
    if line.food:
        change = {"food": _food_named(repos, group_id, replacement).model_dump()}
    else:
        change = {"note": replacement}
    return RecipeIngredient.model_validate({**line.model_dump(), **change, "display": ""})
