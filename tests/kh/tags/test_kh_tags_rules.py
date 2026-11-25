"""KH: tests for the rule-based tag suggestions (pure functions, self-written ingredient lines)."""

import pytest

from mealie.kh.tags.rules import suggested_keys
from mealie.kh.tags.starter import STARTER_TAGS, starter_key
from mealie.schema.recipe.recipe import RecipeDraft
from mealie.schema.recipe.recipe_ingredient import RecipeIngredient


def recipe(*lines: str, total: int | None = None, prep: int | None = None, cook: int | None = None) -> RecipeDraft:
    return RecipeDraft(
        recipe_ingredient=[RecipeIngredient(note=line) for line in lines],
        total_time_seconds=total,
        prep_time_seconds=prep,
        perform_time_seconds=cook,
    )


@pytest.mark.parametrize(
    ("lines", "keys"),
    [
        (["200 g Mehl", "1 Zwiebel", "Olivenöl"], {"vegetarian", "vegan"}),
        (["200 g Mehl", "3 Eier"], {"vegetarian"}),
        (["200 g Hackfleisch", "1 Zwiebel"], {"meat"}),
        (["2 Fleischtomaten", "Salz"], {"vegetarian", "vegan"}),
        (["4 Hühnereier", "Butter"], {"vegetarian"}),
        (["400 g Lachsfilet", "1 Zitrone"], {"fish"}),
        (["Zitronenrinde", "Zucker"], {"vegetarian", "vegan"}),
        (["100 g Speck", "200 g Garnelen"], {"meat", "fish"}),
        (["1 EL Honig", "Haferflocken"], {"vegetarian"}),
        ([], set()),
        (["2 eggs", "200 ml milk", "200 g flour"], {"vegetarian"}),
        (["200 g salmon fillet", "1 lemon"], {"fish"}),
        (["1 can tuna"], {"fish"}),
        (["400 g mince", "1 onion"], {"meat"}),
        (["4 chicken thighs"], {"meat"}),
        (["1 lemon rind", "1 bunch parsley"], {"vegetarian", "vegan"}),
        (["100 g coconut meat", "1 beefsteak tomato"], {"vegetarian", "vegan"}),
        (["200 g Fruchtfleisch", "Kürbisfleisch"], {"vegetarian", "vegan"}),
        (["veganes Hack", "Sojahack", "Fleischersatz"], {"vegetarian", "vegan"}),
        (["200 g plant-based mince", "vegan sausage"], {"vegetarian", "vegan"}),
        (["Entenbrust", "Gänsekeule"], {"meat"}),
        (["500 g Weizenteig"], {"vegetarian", "vegan"}),
        (["Steak vom Rind", "Gulasch", "Mett", "Roastbeef", "Gyros", "Kassler", "Reh", "Hirsch"], {"meat"}),
        (["Pancetta"], {"meat"}),
        (["Prosciutto"], {"meat"}),
        (["Mortadella", "Leberkäse"], {"meat"}),
        (["2 steaks", "100 g veal", "1 duck breast", "200 g venison", "50 g lard", "2 sheets gelatin"], {"meat"}),
        (["Steakgewürz", "1 tsp steak seasoning"], {"vegetarian", "vegan"}),
        (["1 cup wild rice", "1 head lamb's lettuce"], {"vegetarian", "vegan"}),
    ],
)
def test_diet_tags(lines: list[str], keys: set[str]) -> None:
    assert suggested_keys(recipe(*lines)) == keys


def test_quick_uses_total_else_prep_plus_cooking() -> None:
    assert suggested_keys(recipe(total=30 * 60)) == {"quick"}
    assert suggested_keys(recipe(total=31 * 60)) == set()
    assert suggested_keys(recipe(prep=10 * 60, cook=15 * 60)) == {"quick"}
    assert suggested_keys(recipe()) == set()


def test_starter_list_is_24_and_matches_both_languages() -> None:
    assert len(STARTER_TAGS) == 24
    assert len({tag.key for tag in STARTER_TAGS}) == 24
    assert starter_key("Vegetarian") == starter_key("vegetarisch") == "vegetarian"
    assert starter_key("Omas Rezepte") is None
