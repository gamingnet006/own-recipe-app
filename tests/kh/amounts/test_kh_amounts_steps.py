"""KH: tests for amounts in the step text (v0.2 plan 2, task 5, A2, D19): an ingredient's amount or a part of it is
linked where the step names it, other numbers stay free, links follow an edited text, and the review can unlink."""

from uuid import uuid4

from fastapi.testclient import TestClient

from mealie.kh.amounts.schemas import StepAmountOut
from mealie.kh.amounts.steps import link_quantities, name_stems, recheck_link
from mealie.schema.recipe.recipe_ingredient import RecipeIngredient
from mealie.services.parser_services._base import DataMatcher
from tests.kh.amounts.helpers import amounts_of, approve, approved, build_recipe, recognized
from tests.utils.fixture_schemas import TestUser


def links(german: DataMatcher, lines: list[str], steps: list[str]) -> list[tuple[int, int, str, float]]:
    """The links found in STEPS, as (start, end, text, fraction)."""
    found = link_quantities(build_recipe(german, lines, steps), german.units_by_alias)
    return [(link.start, link.end, link.text, round(link.fraction, 3)) for link in found]


def test_whole_amount_is_linked(german: DataMatcher):
    assert links(german, ["250 g Mehl"], ["250 g Mehl unterrühren."]) == [(0, 5, "250 g", 1)]


def test_parts_are_linked(german: DataMatcher):
    assert links(german, ["250 g Mehl"], ["Die Hälfte, 125 g Mehl, zuerst"]) == [(12, 17, "125 g", 0.5)]
    assert links(german, ["250 g Mehl"], ["83 g Mehl"]) == [(0, 4, "83 g", 0.333)]


def test_egg_parts_are_linked(german: DataMatcher):
    # v1.3: "2 Eigelbe" uses the eggs too, so it scales with them (Grießpudding at more servings)
    steps = ["2 Eigelbe verrühren.", "2 Eiweiß steif schlagen.", "1 Eidotter dazu."]
    found = link_quantities(build_recipe(german, ["2 Eier"], steps), german.units_by_alias)
    assert [(link.step, link.text, round(link.fraction, 3)) for link in found] == [
        (0, "2", 1),
        (1, "2", 1),
        (2, "1", 0.5),
    ]


def test_egg_parts_of_a_plural_name():
    # review: a line named "Eier" (no seeded food) still links "2 Eigelbe": the parts join the stem, not the word
    assert "eigelb" in name_stems(RecipeIngredient(quantity=2, note="Eier, frisch"))


def test_other_compounds_stay_free(german: DataMatcher):
    # only the egg parts join the name; "2 Eierlikör" is no part of the eggs
    assert links(german, ["2 Eier"], ["2 Eierlikör dazu."]) == []


def test_same_amount_twice(german: DataMatcher):
    # Review focus 5: each place gets its own link
    found = links(german, ["100 g Zucker"], ["100 g Zucker hier, 100 g Zucker dort"])
    assert [start for start, *_ in found] == [0, 19]


def test_other_numbers_stay_free(german: DataMatcher):
    steps = [
        "Bei 180 Grad 30 Minuten backen.",
        "250 ml Mehl dazu.",
        "2-3 EL Zucker darüber.",
        "200 g Butter schmelzen.",
    ]
    assert links(german, ["250 g Mehl", "2 EL Zucker"], steps) == []


def test_recheck_follows_the_text():
    link = StepAmountOut(step=0, start=0, end=5, text="250 g", reference_id=uuid4(), fraction=1)
    assert recheck_link("250 g Mehl unterrühren.", link) == link
    moved = recheck_link("Zuerst: 250 g Mehl unterrühren.", link)
    assert moved is not None and (moved.start, moved.end) == (8, 13)
    assert recheck_link("Mehl unterrühren.", link) is None
    assert recheck_link("1250 g Mehl unterrühren.", link) is None  # not part of another number
    # also where the old place now sits inside another number
    added = link.model_copy(update={"start": 4, "end": 9})
    assert recheck_link("Ad 1250 g Mehl", added) is None
    # two places: the one nearest the old start
    later = link.model_copy(update={"start": 20, "end": 25})
    nearest = recheck_link("X 250 g Mehl und dann 250 g Mehl", later)
    assert nearest is not None and nearest.start == 22


def test_editing_a_recipe_rechecks_the_links(
    api_client: TestClient, unique_user: TestUser, german: DataMatcher, fake_ai
):
    recipe = approved(api_client, unique_user, fake_ai)
    assert [(link["start"], link["text"]) for link in amounts_of(api_client, unique_user, recipe)["stepAmounts"]] == [
        (0, "250 g"),
        (15, "2 EL"),
    ]
    recipe["recipeInstructions"][0]["text"] = "Zuerst: " + recipe["recipeInstructions"][0]["text"]
    recipe = api_client.put(f"/api/recipes/{recipe['slug']}", json=recipe, headers=unique_user.token).json()
    assert [link["start"] for link in amounts_of(api_client, unique_user, recipe)["stepAmounts"]] == [8, 23]
    recipe["recipeIngredient"] = recipe["recipeIngredient"][1:]  # without the Mehl line
    recipe = api_client.put(f"/api/recipes/{recipe['slug']}", json=recipe, headers=unique_user.token).json()
    assert [link["text"] for link in amounts_of(api_client, unique_user, recipe)["stepAmounts"]] == ["2 EL"]


def test_review_can_unlink(api_client: TestClient, unique_user: TestUser, german: DataMatcher, fake_ai):
    recipe = approved(api_client, unique_user, fake_ai, linkedSteps=[])
    assert amounts_of(api_client, unique_user, recipe)["stepAmounts"] == []


def test_unknown_link_indices_are_refused(api_client: TestClient, unique_user: TestUser, german: DataMatcher, fake_ai):
    draft = recognized(api_client, unique_user, fake_ai)
    assert approve(api_client, unique_user, draft, linkedSteps=[99]).status_code == 422


def test_moving_a_step_moves_its_links(api_client: TestClient, unique_user: TestUser, german: DataMatcher, fake_ai):
    # Review focus 3: the editor sends the steps with their old IDs in the new order; Mealie saves new IDs
    recipe = approved(api_client, unique_user, fake_ai)
    recipe["recipeInstructions"].reverse()
    recipe = api_client.put(f"/api/recipes/{recipe['slug']}", json=recipe, headers=unique_user.token).json()
    assert {link["step"] for link in amounts_of(api_client, unique_user, recipe)["stepAmounts"]} == {2}
    # a bulk change (tags) writes new step IDs too, but leaves the places
    tag = api_client.post("/api/organizers/tags", json={"name": "Mengen"}, headers=unique_user.token).json()
    bulk = {"recipes": [recipe["slug"]], "tags": [tag]}
    assert api_client.post("/api/recipes/bulk-actions/tag", json=bulk, headers=unique_user.token).status_code == 200
    assert {link["step"] for link in amounts_of(api_client, unique_user, recipe)["stepAmounts"]} == {2}


def test_editing_a_line_drops_its_amounts(api_client: TestClient, unique_user: TestUser, german: DataMatcher, fake_ai):
    # Review focus 3: range end, fixed mark and step links belong to a line's amount; a new amount or unit drops them
    recipe = approved(api_client, unique_user, fake_ai)
    lines = recipe["recipeIngredient"]
    mehl, zucker, oel = lines[0]["referenceId"], lines[1]["referenceId"], lines[4]["referenceId"]
    lines[0]["quantity"] = 300  # 250 g Mehl → 300 g
    lines[1]["quantity"] = 4  # 2–3 EL Zucker → 4 EL
    lines[4]["quantity"] = 2  # etwas Öl → 2
    recipe = api_client.put(f"/api/recipes/{recipe['slug']}", json=recipe, headers=unique_user.token).json()
    amounts = amounts_of(api_client, unique_user, recipe)
    left = {extra["referenceId"] for extra in amounts["extras"]} | {
        link["referenceId"] for link in amounts["stepAmounts"]
    }
    assert not left & {mehl, zucker, oel}
    assert amounts["extras"]  # the Prise keeps its mark


def test_a_new_unit_drops_the_links(api_client: TestClient, unique_user: TestUser, german: DataMatcher, fake_ai):
    recipe = approved(api_client, unique_user, fake_ai)
    recipe["recipeIngredient"][0]["unit"] = recipe["recipeIngredient"][1]["unit"]  # 250 g Mehl → 250 EL
    recipe = api_client.put(f"/api/recipes/{recipe['slug']}", json=recipe, headers=unique_user.token).json()
    assert [link["text"] for link in amounts_of(api_client, unique_user, recipe)["stepAmounts"]] == ["2 EL"]
