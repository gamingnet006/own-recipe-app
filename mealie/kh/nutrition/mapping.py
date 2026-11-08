"""KH: which BLS entry a food means (D44): our suggestion, a person's confirmation, and the list the mapping page
shows. One mapping per Mealie food, for the whole group."""

import json
from functools import cache, lru_cache
from pathlib import Path

import sqlalchemy as sa
from pydantic import UUID4
from sqlalchemy.orm import Session

from mealie.db.models.recipe import IngredientFoodModel, RecipeIngredientModel
from mealie.kh.amounts.parse import stem
from mealie.kh.nutrition.bls import BlsFood, load_bls
from mealie.kh.nutrition.grams import name_stems
from mealie.kh.nutrition.models import KhFoodNutrition
from mealie.kh.nutrition.schemas import FoodMappingIn, FoodMappingOut
from mealie.schema.recipe.recipe_ingredient import IngredientFood

ALIASES_JSON = Path(__file__).parent / "data" / "aliases.json"
MIN_PREFIX_STEM = 4  # a shorter stem ("rot", "ei") would match far too many BLS names


@lru_cache
def _aliases(path: Path) -> dict[str, str]:
    """The alias file at PATH with its food names reduced to stems. Cached per path."""
    return {stem(name): code for name, code in json.loads(path.read_text(encoding="utf-8")).items()}


def load_aliases(path: Path | None = None) -> dict[str, str]:
    """The common foods' BLS codes by food stem, from PATH or the shipped file."""
    return _aliases(path or ALIASES_JSON)


@cache
def _normalized(name: str) -> str:
    """A BLS name as Mealie normalizes names, so "Möhre" meets the stem "mohr". Cached: the table has 7000 names."""
    return IngredientFoodModel.normalize(name)


def suggest_code(food_name: str, foods: dict[str, BlsFood], aliases: dict[str, str]) -> str | None:
    """A BLS code for FOOD_NAME: the alias of its stem (or of one of its words) if the table has that code, else the
    shortest BLS name that starts with the stem. None if nothing fits."""
    stems = name_stems(food_name)
    for key in stems:
        if aliases.get(key) in foods:
            return aliases[key]
    for key in (k for k in stems if len(k) >= MIN_PREFIX_STEM):
        hits = [food for food in foods.values() if _normalized(food.name).startswith(key)]
        if hits:
            return min(hits, key=lambda food: len(food.name)).code
    return None


def resolve_code(
    food_name: str, row: KhFoodNutrition | None, foods: dict[str, BlsFood], aliases: dict[str, str]
) -> tuple[str | None, bool]:
    """The BLS code to use for a food and whether it is only our suggestion. A confirmed row is final, also when it
    says "no fitting entry" (None); otherwise the row's code, or else our suggestion, counts as a suggestion."""
    if row is not None and row.confirmed:
        return row.bls_code, False
    code = row.bls_code if row is not None and row.bls_code else suggest_code(food_name, foods, aliases)
    return code, code is not None


def _mapping_out(food_id: UUID4, name: str, row: KhFoodNutrition | None, recipe_count: int) -> FoodMappingOut:
    """The page's view of one food, from its stored row (if any) and the number of recipes that use it."""
    foods = load_bls()
    code, suggested = resolve_code(name, row, foods, load_aliases())
    return FoodMappingOut(
        food_id=str(food_id),
        food_name=name,
        bls_code=code,
        bls_name=foods[code].name if code in foods else None,
        confirmed=row is not None and row.confirmed,
        suggested=suggested,
        piece_grams=row.piece_grams if row is not None else None,
        recipe_count=recipe_count,
    )


def _row_of(session: Session, food_id: UUID4) -> KhFoodNutrition | None:
    """The food's stored mapping, if it has one."""
    return session.execute(sa.select(KhFoodNutrition).where(KhFoodNutrition.food_id == food_id)).scalar_one_or_none()


def food_mapping(session: Session, food: IngredientFood) -> FoodMappingOut:
    """The mapping of one food of the caller's group."""
    count = session.execute(
        sa.select(sa.func.count(sa.distinct(RecipeIngredientModel.recipe_id))).where(
            RecipeIngredientModel.food_id == food.id
        )
    ).scalar_one()
    return _mapping_out(food.id, food.name, _row_of(session, food.id), count)


def list_mappings(session: Session, group_id: UUID4) -> list[FoodMappingOut]:
    """The mappings of all foods of the group that at least one recipe uses: unconfirmed first, then by name."""
    used = session.execute(
        sa.select(
            IngredientFoodModel.id,
            IngredientFoodModel.name,
            sa.func.count(sa.distinct(RecipeIngredientModel.recipe_id)),
        )
        .join(RecipeIngredientModel, RecipeIngredientModel.food_id == IngredientFoodModel.id)
        .where(IngredientFoodModel.group_id == group_id, RecipeIngredientModel.recipe_id.is_not(None))
        .group_by(IngredientFoodModel.id, IngredientFoodModel.name)
    ).all()
    rows = {
        row.food_id: row
        for row in session.execute(
            sa.select(KhFoodNutrition).where(KhFoodNutrition.food_id.in_([food_id for food_id, _, _ in used]))
        ).scalars()
    }
    out = [_mapping_out(food_id, name, rows.get(food_id), count) for food_id, name, count in used]
    return sorted(out, key=lambda mapping: (mapping.confirmed, mapping.food_name.lower()))


def save_mapping(session: Session, food_id: UUID4, data: FoodMappingIn) -> None:
    """Creates or replaces the food's mapping. Commits."""
    row = _row_of(session, food_id)
    if row is None:
        row = KhFoodNutrition(session=session, food_id=food_id)
        session.add(row)
    row.bls_code, row.confirmed, row.piece_grams = data.bls_code, data.confirmed, data.piece_grams
    session.commit()


def delete_food_mappings(session: Session, food_ids: list[UUID4]) -> None:
    """Deletes the mappings of deleted or merged foods; SQLite in Mealie checks no foreign keys, so the cascade is not
    enough. Commits."""
    session.execute(sa.delete(KhFoodNutrition).where(KhFoodNutrition.food_id.in_(food_ids)))
    session.commit()
