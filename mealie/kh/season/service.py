"""KH: finds the group's recipes that use a food in season (D80). The calendar lives in the frontend
(kh/app/lib/season.ts); it sends the food names, so this module only does the matching."""

import re

import sqlalchemy as sa
from pydantic import UUID4
from sqlalchemy.orm import Session

from mealie.db.models.recipe import IngredientFoodModel, RecipeIngredientModel
from mealie.db.models.recipe.recipe import RecipeModel
from mealie.kh.season.schemas import SeasonOut, SeasonRecipe

ROW_SIZE = 8


def _matcher(terms: list[str]) -> re.Pattern[str]:
    """A pattern for the terms as whole words, so "Lauch" does not match "Knoblauch" but "Rote Bete" matches."""
    words = "|".join(re.escape(term) for term in sorted(terms, key=len, reverse=True))
    return re.compile(rf"(?<!\w)(?:{words})(?!\w)", re.IGNORECASE)


def season_recipes(session: Session, group_id: UUID4, terms: list[str]) -> SeasonOut:
    """The group's recipes with an ingredient whose food (name or plural) contains one of TERMS as a word; the ones
    with the most matching foods first, then by name, at most eight."""
    terms = [term.strip() for term in terms if term.strip()]
    if not terms:
        return SeasonOut(recipes=[])
    match = _matcher(terms)
    rows = session.execute(
        sa.select(RecipeIngredientModel.recipe_id, IngredientFoodModel.name, IngredientFoodModel.plural_name)
        .join(IngredientFoodModel, IngredientFoodModel.id == RecipeIngredientModel.food_id)
        .join(RecipeModel, RecipeModel.id == RecipeIngredientModel.recipe_id)
        .where(RecipeModel.group_id == group_id)
    ).all()
    found: dict[UUID4, dict[str, None]] = {}  # recipe id -> its matching foods, in order of appearance
    for recipe_id, name, plural in rows:
        hit = next((value for value in (name, plural) if value and match.search(value)), None)
        if hit:
            found.setdefault(recipe_id, {})[name or hit] = None
    recipes = {
        recipe.id: recipe for recipe in session.scalars(sa.select(RecipeModel).where(RecipeModel.id.in_(list(found))))
    }
    best = sorted(recipes.values(), key=lambda recipe: (-len(found[recipe.id]), recipe.name.casefold()))[:ROW_SIZE]
    return SeasonOut(
        recipes=[
            SeasonRecipe(id=r.id, slug=r.slug, name=r.name, image=r.image, food=next(iter(found[r.id]))) for r in best
        ]
    )
