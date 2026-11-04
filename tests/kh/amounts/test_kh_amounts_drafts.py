"""KH: tests for the amounts of a draft (v0.2 plan 2, task 2, A1): read when recognized, kept in the draft, saved on
approval with the saved recipe's IDs, readable by the group only, and gone with the recipe."""

from typing import Any
from uuid import uuid4

import sqlalchemy as sa
from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi.testclient import TestClient

from mealie.db.init_db import ALEMBIC_DIR
from mealie.kh.amounts.models import KhIngredientExtra
from mealie.services.parser_services._base import DataMatcher
from tests.kh.drafts.helpers import DRAFTS, get_draft, post_draft
from tests.utils.fixture_schemas import TestUser

AMOUNTS = "/api/kh/amounts"


def recognized(api_client: TestClient, user: TestUser, fake_ai, recipe_file: str = "recipe-amounts.json") -> dict:
    """A text draft recognized from a recorded recipe, as the review gets it."""
    fake_ai(recipe_file)
    draft = post_draft(api_client, user, data={"text": "Ein Testkuchen."}).json()
    return get_draft(api_client, user, draft["id"]).json()


def approved(api_client: TestClient, user: TestUser, fake_ai) -> dict[str, Any]:
    """The recipe a recognized draft became on approval, as Mealie returns it."""
    draft = recognized(api_client, user, fake_ai)
    slug = api_client.post(f"{DRAFTS}/{draft['id']}/approve", json={}, headers=user.token).json()["slug"]
    return api_client.get(f"/api/recipes/{slug}", headers=user.token).json()


def test_recognizing_reads_the_amounts(api_client: TestClient, unique_user: TestUser, german: DataMatcher, fake_ai):
    draft = recognized(api_client, unique_user, fake_ai)
    lines = draft["recipe"]["recipeIngredient"]
    first = lines[0]
    assert (first["title"], first["quantity"], first["unit"]["name"], first["food"]["name"]) == (
        "Für den Teig",
        250,
        "Gramm",
        "Mehl",
    )
    assert first["originalText"] == "250 g Mehl"
    assert lines[1]["quantity"] == 2
    extras = {extra["referenceId"]: extra for extra in draft["recipe"]["khAmounts"]["extras"]}
    assert extras[lines[1]["referenceId"]]["upper"] == 3
    assert extras[lines[3]["referenceId"]]["fixed"] and extras[lines[4]["referenceId"]]["fixed"]
    assert (lines[5]["note"], lines[5]["quantity"] or None) == ("eine Handvoll Nüsse", None)
    assert lines[6]["note"] == ""


def test_link_recipe_data_is_read_too(api_client: TestClient, unique_user: TestUser, german: DataMatcher, fake_page):
    fake_page("page.html")
    draft = post_draft(api_client, unique_user, data={"url": "https://example.com/testkuchen"}).json()
    lines = get_draft(api_client, unique_user, draft["id"]).json()["recipe"]["recipeIngredient"]
    assert [line["quantity"] for line in lines] == [200, 100, 3, 1]


def test_approve_keeps_the_extras(api_client: TestClient, unique_user: TestUser, german: DataMatcher, fake_ai):
    recipe = approved(api_client, unique_user, fake_ai)
    amounts = api_client.get(f"{AMOUNTS}/{recipe['id']}", headers=unique_user.token).json()
    uppers = {extra["referenceId"]: extra["upper"] for extra in amounts["extras"]}
    assert uppers[recipe["recipeIngredient"][1]["referenceId"]] == 3


def test_amounts_stay_in_the_group(
    api_client: TestClient, unique_user: TestUser, g2_user: TestUser, german: DataMatcher, fake_ai
):
    recipe = approved(api_client, unique_user, fake_ai)
    assert api_client.get(f"{AMOUNTS}/{recipe['id']}", headers=g2_user.token).status_code == 404
    assert api_client.get(f"{AMOUNTS}/{uuid4()}", headers=unique_user.token).status_code == 404


def test_deleting_a_recipe_deletes_its_amounts(
    api_client: TestClient, unique_user: TestUser, german: DataMatcher, fake_ai
):
    recipe = approved(api_client, unique_user, fake_ai)
    assert api_client.delete(f"/api/recipes/{recipe['slug']}", headers=unique_user.token).status_code == 200
    rows = unique_user.repos.session.execute(
        sa.select(KhIngredientExtra).where(KhIngredientExtra.recipe_id == recipe["id"])
    ).all()
    assert rows == []


def test_kh0003_follows_kh0002():
    script = ScriptDirectory.from_config(Config(str(ALEMBIC_DIR / "alembic.ini")))
    assert script.get_revision("kh0003").down_revision == "kh0002"
    assert "kh0003" in {revision.revision for revision in script.iterate_revisions("kh@head", "base")}
