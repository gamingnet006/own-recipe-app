"""KH: tests of the nutrition per recipe (D44): hand-computed values, lines that cannot be counted, no servings,
values entered by hand, rounding, and the endpoint."""

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from mealie.kh.nutrition.bls import BlsFood, load_bls
from mealie.kh.nutrition.calculate import calculate
from mealie.kh.nutrition.mapping import load_aliases
from mealie.kh.nutrition.models import KhFoodNutrition
from mealie.schema.recipe.recipe import RecipeDraft
from mealie.schema.recipe.recipe_ingredient import IngredientFoodCreate, IngredientUnitCreate, RecipeIngredient
from mealie.schema.recipe.recipe_nutrition import Nutrition
from tests.kh.nutrition.helpers import new_food, new_recipe
from tests.utils.fixture_schemas import TestUser

FOODS = {name: IngredientFoodCreate(id=uuid4(), name=name) for name in ("Mehl", "Butter", "Eier", "Zucker", "Salz")}
UNIT_G = IngredientUnitCreate(name="Gramm", abbreviation="g")


def line(quantity: float | None, food: str | None, unit: IngredientUnitCreate | None = UNIT_G, note: str = ""):
    """An ingredient line with one of FOODS."""
    return RecipeIngredient(quantity=quantity, unit=unit, food=FOODS[food] if food else None, note=note)


def cake(servings: float = 4) -> RecipeDraft:
    """250 g Mehl, 200 g Butter, 3 Eier, 150 g Zucker: with the fixture table 3161 kcal in all."""
    lines = [line(250, "Mehl"), line(200, "Butter"), line(3, "Eier", None), line(150, "Zucker")]
    return RecipeDraft(name="Testkuchen", recipe_ingredient=lines, recipe_servings=servings)


def calc(recipe: RecipeDraft, mappings: dict | None = None):
    """calculate() with the fixture's table and aliases."""
    return calculate(recipe, mappings or {}, load_bls(), load_aliases())


def test_values_per_serving_are_estimated_until_confirmed(small_bls, session: Session) -> None:
    result = calc(cake())

    assert (result.per, result.servings, result.counted, result.total, result.missing) == ("serving", 4, 4, 4, [])
    assert result.estimated is True and result.manual is False
    # 250 g Mehl 340, 200 g Butter 740, 3 Eier = 165 g at 140, 150 g Zucker 400 kcal per 100 g, for 4 servings
    assert result.values.kcal == 790  # 3161 / 4 = 790.25, rounded to 10
    assert result.values.fat == 46  # (2.5 + 166 + 16.5 + 0) / 4 = 46.25 g, from 10 g whole
    assert result.values.salt == 0.2  # (0 + 0.04 + 0.5775 + 0) / 4 = 0.154, one decimal

    confirmed = {
        food.id: KhFoodNutrition(session=session, food_id=food.id, bls_code=code, confirmed=True)
        for food, code in zip(
            (FOODS["Mehl"], FOODS["Butter"], FOODS["Eier"], FOODS["Zucker"]),
            ("B100000", "B200000", "B400000", "B300000"),
            strict=True,
        )
    }
    assert calc(cake(), confirmed).estimated is False


def test_lines_without_amount_food_or_known_unit_are_listed_as_missing(small_bls) -> None:
    lines = [
        line(250, "Mehl"),
        line(None, None, None, note="Salz und Pfeffer"),
        RecipeIngredient(quantity=1, unit=IngredientUnitCreate(name="Bund"), note="Petersilie"),
        line(None, "Salz", None, note="etwas Öl"),
        RecipeIngredient(title="Für den Teig"),  # a section title is no line
    ]

    result = calc(RecipeDraft(name="Wenig", recipe_ingredient=lines, recipe_servings=2))

    assert (result.counted, result.total) == (1, 4)
    assert result.missing == [lines[1].display, lines[2].display, lines[3].display]
    assert "Salz und Pfeffer" in result.missing
    assert result.values.kcal == 430  # 250 g Mehl = 850 kcal, 2 servings, never a zero-calorie lie


def test_no_servings_gives_the_whole_recipe(small_bls) -> None:
    for servings in (0, None):
        recipe = cake()
        recipe.recipe_servings = servings or 0
        recipe.recipe_yield = "1 Springform"

        result = calc(recipe)

        assert (result.per, result.servings) == ("recipe", None)
        assert result.values.kcal == 3160


def test_a_food_mapped_to_no_entry_is_missing_not_suggested(small_bls, session: Session) -> None:
    mappings = {FOODS["Mehl"].id: KhFoodNutrition(session=session, food_id=FOODS["Mehl"].id, confirmed=True)}
    recipe = RecipeDraft(name="Nur Mehl", recipe_ingredient=[line(250, "Mehl")], recipe_servings=1)

    result = calc(recipe, mappings)

    assert (result.counted, result.total, result.values) == (0, 1, None)
    assert result.estimated is False


def test_values_entered_by_hand_are_shown_and_nothing_is_calculated(small_bls) -> None:
    recipe = cake()
    recipe.nutrition = Nutrition(
        calories="320 kcal", fat_content="12,5 g", sodium_content="400 mg", sugar_content="viel"
    )

    result = calc(recipe)

    assert result.manual is True and result.estimated is False and result.per == "serving"
    assert (result.values.kcal, result.values.fat, result.values.salt) == (320, 12.5, 1.0)
    assert result.values.sugar is None and result.values.protein is None  # no number, or not entered
    assert (result.counted, result.total, result.missing) == (0, 0, [])


def test_values_are_rounded_like_the_spec_says(session: Session) -> None:
    odd = BlsFood("X", "Test", 123.4, 12.6, 3.46, 0.04, None, 9.94, 10.4, 1.26)
    recipe = RecipeDraft(name="Rund", recipe_ingredient=[line(100, "Mehl")], recipe_servings=1)

    values = calculate(
        recipe, {FOODS["Mehl"].id: KhFoodNutrition(session=session, bls_code="X", confirmed=True)}, {"X": odd}, {}
    ).values

    assert (values.kcal, values.fat, values.saturated, values.carbs) == (120, 13, 3.5, 0.0)
    assert (values.sugar, values.protein, values.fiber, values.salt) == (None, 9.9, 10, 1.3)


def test_endpoint_returns_the_nutrition_of_any_recipe_of_the_group(
    small_bls, api_client: TestClient, unique_user: TestUser, h2_user: TestUser, g2_user: TestUser
) -> None:
    for name in ("Mehl", "Butter"):
        new_food(unique_user, name)
    recipe = new_recipe(
        api_client, unique_user, [(250, "g", "Mehl", ""), (100, "g", "Butter", ""), (1, "Prise", "Salz", "")], 2
    )
    url = f"/api/kh/recipes/{recipe['slug']}/nutrition"

    own = api_client.get(url, headers=unique_user.token)
    other_household = api_client.get(url, headers=h2_user.token)

    assert own.status_code == 200 and other_household.json() == own.json()
    body = own.json()
    assert body["per"] == "serving" and body["servings"] == 2
    assert (body["counted"], body["total"], body["estimated"], body["manual"]) == (2, 3, True, False)
    assert body["values"]["kcal"] == 800  # (250 g Mehl 340 + 100 g Butter 740) per 100 g = 1590 / 2 = 795
    assert len(body["missing"]) == 1
    assert api_client.get(url, headers=g2_user.token).status_code == 404
