"""KH: tests for reading Kochheft's own recipe text without AI (D62). EXPORT below is written by hand to match what
recipeText() in frontend/kh/app/lib/recipe-text.ts makes at scale 1; keep both in sync."""

from fastapi.testclient import TestClient

from mealie.kh.drafts.text_format import parse_kochheft_text
from tests.kh.drafts.helpers import get_draft, post_draft
from tests.utils.fixture_schemas import TestUser

EXPORT = """Testkuchen
Portionen: 4 · Vorbereitung: 15 Min. · Zubereitung: 30 Min. · Gesamt: 45 Min.

Zutaten:
Für den Teig
- 200 g Mehl
- 100 g Zucker
Für den Guss
- 3 Eier

Zubereitung:
1. Ofen auf 180 Grad vorheizen.
Backen
2. 30 Minuten backen.

Notizen:
Schmeckt auch kalt.

Quelle: https://example.org/testkuchen

Exportiert aus Kochheft
"""


def test_round_trip_of_the_export():
    recipe = parse_kochheft_text(EXPORT)
    assert recipe
    assert recipe.name == "Testkuchen"
    assert recipe.recipe_servings == 4
    assert (recipe.prep_time, recipe.perform_time, recipe.total_time) == ("15 Min.", "30 Min.", "45 Min.")
    assert [(line.title, line.note) for line in recipe.recipe_ingredient] == [
        ("Für den Teig", "200 g Mehl"),
        (None, "100 g Zucker"),
        ("Für den Guss", "3 Eier"),
    ]
    assert [(step.title, step.text) for step in recipe.recipe_instructions] == [
        ("", "Ofen auf 180 Grad vorheizen."),
        ("Backen", "30 Minuten backen."),
    ]
    assert [note.text for note in recipe.notes] == ["Schmeckt auch kalt."]
    assert recipe.org_url == "https://example.org/testkuchen"


def test_minimal_export_without_info_notes_and_source():
    text = "Brot\n\nZutaten:\n- 500 g Mehl\n\nZubereitung:\n1. Backen.\n\nExportiert aus Kochheft"
    recipe = parse_kochheft_text(text)
    assert recipe
    assert recipe.recipe_servings == 0
    assert recipe.notes == []
    assert recipe.org_url is None


def test_servings_with_a_comma():
    recipe = parse_kochheft_text(EXPORT.replace("Portionen: 4", "Portionen: 2,5"))
    assert recipe and recipe.recipe_servings == 2.5


def test_other_texts_are_not_ours():
    assert parse_kochheft_text("Testkuchen: 200 g Mehl, 3 Eier. 30 Minuten backen.") is None
    assert parse_kochheft_text(EXPORT.replace("Exportiert aus Kochheft", "")) is None
    assert parse_kochheft_text(EXPORT.replace("Zutaten:", "Zutaten")) is None
    assert parse_kochheft_text(EXPORT.replace("\nZubereitung:\n", "\nSchritte:\n")) is None
    assert parse_kochheft_text(EXPORT + "Noch etwas.") is None  # the signature must be the last line
    assert parse_kochheft_text("") is None


def test_export_text_needs_no_ai(api_client: TestClient, unique_user: TestUser, fake_ai):
    calls = fake_ai(Exception("the AI must not be called"))
    response = post_draft(api_client, unique_user, data={"text": EXPORT})
    draft = get_draft(api_client, unique_user, response.json()["id"]).json()
    assert draft["status"] == "ready"
    assert draft["aiModel"] is None
    assert calls == []
    flour = draft["recipe"]["recipeIngredient"][0]
    assert flour["quantity"] == 200  # the amount reading of D39 ran on the note
    assert draft["recipe"]["orgURL"] == "https://example.org/testkuchen"


def test_only_the_last_line_is_the_source():
    text = EXPORT.replace("Schmeckt auch kalt.", "Quelle: Oma Erna\nSchmeckt auch kalt.")
    recipe = parse_kochheft_text(text)
    assert recipe
    assert [note.text for note in recipe.notes] == ["Quelle: Oma Erna\nSchmeckt auch kalt."]
    assert recipe.org_url == "https://example.org/testkuchen"
    no_source = parse_kochheft_text(text.replace("Quelle: https://example.org/testkuchen\n\n", ""))
    assert no_source and no_source.org_url is None  # the note line stays a note


def test_servings_with_a_yield_word():
    # recipeText() writes "Portionen: 13 Muffins" for a recipe whose yield is "12 Muffins" scaled to 13
    recipe = parse_kochheft_text(EXPORT.replace("Portionen: 4", "Portionen: 13 Muffins"))
    assert recipe
    assert (recipe.recipe_servings, recipe.recipe_yield_quantity, recipe.recipe_yield) == (13, 13, "Muffins")
