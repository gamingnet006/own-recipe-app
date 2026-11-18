"""KH: tests for editing a draft's recognized recipe line by line in the review (D55), and for approving it with
categories: name, ingredient (read anew like the recognition does) and step edits, and the error cases."""

from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from tests.kh.amounts.conftest import german  # noqa: F401  the group with German units and foods
from tests.kh.amounts.helpers import approve, recognized
from tests.kh.drafts.conftest import fake_ai  # noqa: F401
from tests.kh.drafts.helpers import DRAFTS, get_draft
from tests.utils.fixture_schemas import TestUser


@pytest.fixture
def ready(api_client: TestClient, unique_user: TestUser, german, fake_ai) -> dict[str, Any]:  # noqa: F811
    """A draft recognized from a recorded recipe, in a group with German units and foods."""
    return recognized(api_client, unique_user, fake_ai)


def edit(api_client: TestClient, user: TestUser, draft_id: str, body: dict[str, Any]):
    """PATCH one edit of the draft's recipe."""
    return api_client.patch(f"{DRAFTS}/{draft_id}/recipe", json=body, headers=user.token)


def test_name_is_edited(api_client: TestClient, unique_user: TestUser, ready: dict[str, Any]):
    draft = ready
    response = edit(api_client, unique_user, draft["id"], {"name": "  Besserer Kuchen "})
    assert response.status_code == 200
    assert response.json()["recipe"]["name"] == "Besserer Kuchen"
    assert get_draft(api_client, unique_user, draft["id"]).json()["recipe"]["name"] == "Besserer Kuchen"


def test_bad_names_are_refused(api_client: TestClient, unique_user: TestUser, ready: dict[str, Any]):
    draft = ready
    for name in ["   ", "x" * 201]:
        assert edit(api_client, unique_user, draft["id"], {"name": name}).status_code == 422
    assert edit(api_client, unique_user, draft["id"], {}).status_code == 422
    both = {"name": "A", "step": {"index": 0, "text": "B"}}
    assert edit(api_client, unique_user, draft["id"], both).status_code == 422


def test_ingredient_is_read_anew(api_client: TestClient, unique_user: TestUser, ready: dict[str, Any]):
    draft = ready
    old = draft["recipe"]["recipeIngredient"][2]  # "3 Eier"
    response = edit(api_client, unique_user, draft["id"], {"ingredient": {"index": 2, "text": "250 g Mehl"}})
    assert response.status_code == 200
    line = response.json()["recipe"]["recipeIngredient"][2]
    assert (line["quantity"], line["unit"]["name"], line["food"]["name"]) == (250, "Gramm", "Mehl")
    assert (line["referenceId"], line["originalText"]) == (old["referenceId"], "250 g Mehl")


def test_ingredient_with_range_and_without_amount(api_client: TestClient, unique_user: TestUser, ready: dict[str, Any]):
    draft = ready
    ref = draft["recipe"]["recipeIngredient"][2]["referenceId"]
    body = {"ingredient": {"index": 2, "text": "2–3 EL Zucker"}}
    recipe = edit(api_client, unique_user, draft["id"], body).json()["recipe"]
    assert [e["upper"] for e in recipe["khAmounts"]["extras"] if e["referenceId"] == ref] == [3]

    body = {"ingredient": {"index": 2, "text": "nach Geschmack Pfeffer"}}
    recipe = edit(api_client, unique_user, draft["id"], body).json()["recipe"]
    line = recipe["recipeIngredient"][2]
    assert (line["quantity"] or None, line["note"]) == (None, "nach Geschmack Pfeffer")

    recipe = edit(api_client, unique_user, draft["id"], {"ingredient": {"index": 2, "text": "Eier"}}).json()["recipe"]
    assert not [e for e in recipe["khAmounts"]["extras"] if e["referenceId"] == ref]  # the old range is gone


def test_step_edit_keeps_links_whose_text_stays(api_client: TestClient, unique_user: TestUser, ready: dict[str, Any]):
    draft = ready
    before = [link["text"] for link in draft["recipe"]["khAmounts"]["stepAmounts"] if link["step"] == 0]
    assert "250 g" in before and "2 EL" in before
    body = {"step": {"index": 0, "text": "Zuerst 250 g Mehl verrühren."}}
    recipe = edit(api_client, unique_user, draft["id"], body).json()["recipe"]
    assert recipe["recipeInstructions"][0]["text"] == "Zuerst 250 g Mehl verrühren."
    after = [(link["text"], link["start"]) for link in recipe["khAmounts"]["stepAmounts"] if link["step"] == 0]
    assert after == [("250 g", 7)]  # the 2 EL link is dropped, the other follows its text


def test_bad_index_and_empty_text(api_client: TestClient, unique_user: TestUser, ready: dict[str, Any]):
    draft = ready
    for body in [
        {"ingredient": {"index": 99, "text": "1 g Salz"}},
        {"ingredient": {"index": -1, "text": "1 g Salz"}},
        {"step": {"index": 3, "text": "Text"}},
        {"step": {"index": 0, "text": "  "}},
    ]:
        assert edit(api_client, unique_user, draft["id"], body).status_code == 422


def test_only_a_ready_draft_is_edited(api_client: TestClient, unique_user: TestUser, ready: dict[str, Any]):
    draft = ready
    assert approve(api_client, unique_user, draft).status_code == 200
    response = edit(api_client, unique_user, draft["id"], {"name": "Neu"})
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "not_ready"


def test_other_household_gets_404(
    api_client: TestClient, unique_user: TestUser, h2_user: TestUser, ready: dict[str, Any]
):
    draft = ready
    assert edit(api_client, h2_user, draft["id"], {"name": "Neu"}).status_code == 404
    assert edit(api_client, unique_user, str(uuid4()), {"name": "Neu"}).status_code == 404


def test_approve_saves_the_categories(api_client: TestClient, unique_user: TestUser, ready: dict[str, Any]):
    made = api_client.post("/api/organizers/categories", json={"name": "Kuchen D55"}, headers=unique_user.token).json()
    draft = ready
    category = {"id": made["id"], "name": made["name"], "slug": made["slug"]}
    slug = approve(api_client, unique_user, draft, recipeCategory=[category]).json()["slug"]
    recipe = api_client.get(f"/api/recipes/{slug}", headers=unique_user.token).json()
    assert [c["id"] for c in recipe["recipeCategory"]] == [made["id"]]


def links_of(recipe: dict[str, Any], reference_id: str) -> list[str]:
    """The texts of the step links of one ingredient line."""
    return [link["text"] for link in recipe["khAmounts"]["stepAmounts"] if link["referenceId"] == reference_id]


def test_new_amount_drops_the_step_links_of_the_line(api_client: TestClient, unique_user: TestUser, ready):
    ref = ready["recipe"]["recipeIngredient"][0]["referenceId"]  # "250 g Mehl", linked from step 0
    assert links_of(ready["recipe"], ref)
    kept = edit(api_client, unique_user, ready["id"], {"ingredient": {"index": 0, "text": "250 g Mehl, gesiebt"}})
    assert links_of(kept.json()["recipe"], ref)  # only the note changed
    gone = edit(api_client, unique_user, ready["id"], {"ingredient": {"index": 0, "text": "500 g Mehl"}})
    assert links_of(gone.json()["recipe"], ref) == []


def test_approve_after_an_ingredient_edit(api_client: TestClient, unique_user: TestUser, ready):
    edit(api_client, unique_user, ready["id"], {"ingredient": {"index": 2, "text": "250 g Mehl"}})
    slug = approve(api_client, unique_user, ready).json()["slug"]
    recipe = api_client.get(f"/api/recipes/{slug}", headers=unique_user.token).json()
    line = recipe["recipeIngredient"][2]
    assert (line["quantity"], line["food"]["name"], line["originalText"]) == (250, "Mehl", "250 g Mehl")


def test_edit_never_writes_into_an_approved_draft(
    api_client: TestClient, unique_user: TestUser, ready, monkeypatch: pytest.MonkeyPatch
):
    """The draft is approved between the edit's status check and its write."""
    from mealie.kh.drafts import service

    real = service.DraftService.get

    def get_then_approve(self, draft_id):
        draft = real(self, draft_id)
        monkeypatch.setattr(service.DraftService, "get", real)
        assert approve(api_client, unique_user, ready).status_code == 200
        return draft

    monkeypatch.setattr(service.DraftService, "get", get_then_approve)
    assert edit(api_client, unique_user, ready["id"], {"name": "Zu spät"}).status_code == 409
    assert get_draft(api_client, unique_user, ready["id"]).json()["recipe"]["name"] == ready["recipe"]["name"]
