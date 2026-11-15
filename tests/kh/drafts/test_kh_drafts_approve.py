"""KH: tests for approving and discarding drafts (phase 2, task 3): approval saves a Mealie recipe with the
recognized ID and keeps the draft as its origin; discarding and the daily cleanup remove exactly the
draft's own files and never a real recipe's folder."""

from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from mealie.kh.drafts.files import draft_dir, drafts_root, sweep_orphans
from mealie.kh.drafts.recognize import set_fields
from mealie.kh.drafts.repository import drafts_repo
from mealie.kh.drafts.schemas import DraftStatus
from mealie.kh.drafts.service import DraftService
from mealie.schema.recipe.recipe import RecipeOut
from mealie.services.recipe.recipe_data_service import RecipeDataService
from tests.kh.drafts.helpers import DRAFTS, get_draft, open_ids, png, post_draft
from tests.utils.fixture_schemas import TestUser

TEXT = "Testkuchen: 200 g Mehl, 100 g Zucker, 3 Eier, 1 Prise Salz. 30 Minuten backen."


def ready_draft(api_client: TestClient, user: TestUser, fake_ai, *, image: bool = False) -> dict[str, Any]:
    """A recognized draft from text, or from one generated image."""
    fake_ai("recipe.json")
    if image:
        response = post_draft(api_client, user, files=[("images", ("zettel.png", png(800, 600), "image/png"))])
    else:
        response = post_draft(api_client, user, data={"text": TEXT})
    draft = get_draft(api_client, user, response.json()["id"]).json()
    assert draft["status"] == "ready"
    return draft


def approve(api_client: TestClient, user: TestUser, draft_id: str, **body: Any):
    """POST approve, optionally with {"force": true}."""
    return api_client.post(f"{DRAFTS}/{draft_id}/approve", json=body, headers=user.token)


def stored_draft(session: Session, user: TestUser, **fields: Any):
    """A draft row written directly, for states the API does not produce on its own."""
    repo = drafts_repo(session, user.group_id, user.household_id)
    defaults = {"user_id": user.user_id, "source_type": "text", "source_text": TEXT}
    return repo.create({**defaults, "group_id": user.group_id, "household_id": user.household_id, **fields})


def test_approve_saves_recipe_with_recognized_id(api_client: TestClient, unique_user: TestUser, fake_ai):
    draft = ready_draft(api_client, unique_user, fake_ai)
    response = approve(api_client, unique_user, draft["id"])
    assert response.status_code == 200
    recipe = api_client.get(f"/api/recipes/{response.json()['slug']}", headers=unique_user.token).json()
    assert recipe["id"] == draft["recipe"]["id"]
    assert recipe["name"] == "Testkuchen"

    after = get_draft(api_client, unique_user, draft["id"]).json()
    assert after["status"] == "approved"
    assert after["recipeId"] == recipe["id"]
    assert after["approvedBy"] == str(unique_user.user_id)


def test_approve_image_draft_uses_first_original_as_cover(api_client: TestClient, unique_user: TestUser, fake_ai):
    draft = ready_draft(api_client, unique_user, fake_ai, image=True)
    slug = approve(api_client, unique_user, draft["id"]).json()["slug"]
    recipe = api_client.get(f"/api/recipes/{slug}", headers=unique_user.token).json()
    assert (RecipeDataService(UUID(recipe["id"])).dir_image / "original.webp").exists()
    assert recipe["image"]  # the cache key the page needs to request the image


def test_anyone_in_household_may_approve(
    api_client: TestClient, unique_user: TestUser, household_member: TestUser, fake_ai
):
    draft = ready_draft(api_client, unique_user, fake_ai)
    assert draft["id"] in open_ids(api_client, household_member)
    assert approve(api_client, household_member, draft["id"]).status_code == 200
    assert get_draft(api_client, unique_user, draft["id"]).json()["approvedBy"] == str(household_member.user_id)


def test_second_approve_conflicts(api_client: TestClient, unique_user: TestUser, fake_ai):
    draft = ready_draft(api_client, unique_user, fake_ai)
    slug = approve(api_client, unique_user, draft["id"]).json()["slug"]
    again = approve(api_client, unique_user, draft["id"])
    assert again.status_code == 409
    assert again.json()["detail"] == {"code": "already_approved", "slug": slug}


def test_approve_needs_ready(api_client: TestClient, session: Session, unique_user: TestUser):
    for state in ("working", "failed"):
        draft = stored_draft(session, unique_user, status=state)
        response = approve(api_client, unique_user, str(draft.id))
        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "not_ready"


def test_list_hides_approved(api_client: TestClient, unique_user: TestUser, fake_ai):
    draft = ready_draft(api_client, unique_user, fake_ai)
    approve(api_client, unique_user, draft["id"])
    assert draft["id"] not in open_ids(api_client, unique_user)


def test_discard_removes_row_originals_and_recognition_dir(api_client: TestClient, unique_user: TestUser, fake_ai):
    draft = ready_draft(api_client, unique_user, fake_ai, image=True)
    recognition = RecipeOut.directory_from_id(draft["recipe"]["id"])
    assert draft_dir(draft["id"]).exists()
    assert recognition.exists()

    response = api_client.delete(f"{DRAFTS}/{draft['id']}", headers=unique_user.token)
    assert response.status_code == 204
    assert get_draft(api_client, unique_user, draft["id"]).status_code == 404
    assert not draft_dir(draft["id"]).exists()
    assert not recognition.exists()


def test_discard_keeps_folder_of_existing_recipe(
    api_client: TestClient, session: Session, unique_user: TestUser, fake_ai
):
    saved = ready_draft(api_client, unique_user, fake_ai)
    approve(api_client, unique_user, saved["id"])
    # a second draft that claims the saved recipe's ID: discarding it must not touch that recipe's folder
    twin = stored_draft(session, unique_user, status="ready", recipe=saved["recipe"])
    assert api_client.delete(f"{DRAFTS}/{twin.id}", headers=unique_user.token).status_code == 204
    assert RecipeOut.directory_from_id(saved["recipe"]["id"]).exists()


def test_discard_needs_ready_or_failed(api_client: TestClient, session: Session, unique_user: TestUser, fake_ai):
    working = stored_draft(session, unique_user, status="working")
    response = api_client.delete(f"{DRAFTS}/{working.id}", headers=unique_user.token)
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "still_working"

    approved = ready_draft(api_client, unique_user, fake_ai)
    approve(api_client, unique_user, approved["id"])
    response = api_client.delete(f"{DRAFTS}/{approved['id']}", headers=unique_user.token)
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "already_approved"


def test_original_is_served_only_to_household(
    api_client: TestClient, unique_user: TestUser, h2_user: TestUser, fake_ai
):
    draft = ready_draft(api_client, unique_user, fake_ai, image=True)
    response = api_client.get(f"{DRAFTS}/{draft['id']}/originals/1", headers=unique_user.token)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/webp"
    assert api_client.get(f"{DRAFTS}/{draft['id']}/originals/1", headers=h2_user.token).status_code == 404
    for n in (0, 2):
        assert api_client.get(f"{DRAFTS}/{draft['id']}/originals/{n}", headers=unique_user.token).status_code == 404


def test_origin(api_client: TestClient, unique_user: TestUser, h2_user: TestUser, fake_ai):
    draft = ready_draft(api_client, unique_user, fake_ai)
    approve(api_client, unique_user, draft["id"])
    recipe_id = get_draft(api_client, unique_user, draft["id"]).json()["recipeId"]

    origin = api_client.get(f"/api/kh/recipes/{recipe_id}/origin", headers=unique_user.token)
    assert origin.status_code == 200
    assert origin.json()["draftId"] == draft["id"]
    assert origin.json()["sourceType"] == "text"
    assert origin.json()["userName"] == unique_user.full_name
    assert origin.json()["createdAt"]
    assert origin.json()["originalCount"] == 0
    assert api_client.get(f"/api/kh/recipes/{recipe_id}/origin", headers=h2_user.token).status_code == 404
    assert api_client.get(f"/api/kh/recipes/{uuid4()}/origin", headers=unique_user.token).status_code == 404


def test_deleting_recipe_drops_origin_and_sweep_removes_folder(
    api_client: TestClient, session: Session, unique_user: TestUser, fake_ai
):
    draft = ready_draft(api_client, unique_user, fake_ai, image=True)
    slug = approve(api_client, unique_user, draft["id"]).json()["slug"]
    assert api_client.delete(f"/api/recipes/{slug}", headers=unique_user.token).status_code == 200

    sweep_orphans()
    session.expire_all()
    assert drafts_repo(session, unique_user.group_id, unique_user.household_id).get_one(draft["id"]) is None
    assert not draft_dir(draft["id"]).exists()


def test_sweep_keeps_folders_with_rows(api_client: TestClient, unique_user: TestUser, fake_ai):
    draft = ready_draft(api_client, unique_user, fake_ai, image=True)
    stray = drafts_root() / str(uuid4())
    stray.mkdir(parents=True)

    sweep_orphans()
    assert draft_dir(draft["id"]).exists()
    assert not stray.exists()


def test_approve_takes_servings_and_yield_from_the_review(api_client: TestClient, unique_user: TestUser, fake_ai):
    draft = ready_draft(api_client, unique_user, fake_ai)
    changes = {"recipeServings": 4, "recipeYieldQuantity": 1, "recipeYield": "Springform Ø 26 cm"}
    response = api_client.post(f"{DRAFTS}/{draft['id']}/approve", json=changes, headers=unique_user.token)
    recipe = api_client.get(f"/api/recipes/{response.json()['slug']}", headers=unique_user.token).json()
    assert {key: recipe[key] for key in changes} == changes


def test_approve_refuses_negative_servings(api_client: TestClient, unique_user: TestUser, fake_ai):
    draft = ready_draft(api_client, unique_user, fake_ai)
    response = api_client.post(
        f"{DRAFTS}/{draft['id']}/approve", json={"recipeServings": -1}, headers=unique_user.token
    )
    assert response.status_code == 422
    assert get_draft(api_client, unique_user, draft["id"]).json()["status"] == "ready"


def test_an_approval_in_between_wins_cleanly(
    api_client: TestClient, unique_user: TestUser, fake_ai, monkeypatch: pytest.MonkeyPatch
):
    """Two people approve at once: the other saves between this one's checks and its claim."""
    draft = ready_draft(api_client, unique_user, fake_ai)
    recipes_before = api_client.get("/api/recipes", headers=unique_user.token).json()["total"]

    def approved_meanwhile(self: DraftService, current) -> list:
        set_fields(self.session, current.id, status=DraftStatus.approved)
        return []

    monkeypatch.setattr(DraftService, "_new_duplicates", approved_meanwhile)
    response = api_client.post(f"{DRAFTS}/{draft['id']}/approve", json={}, headers=unique_user.token)
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "already_approved"
    assert api_client.get("/api/recipes", headers=unique_user.token).json()["total"] == recipes_before


@pytest.mark.parametrize("other", ["h2_user", "g2_user"])
def test_another_household_cannot_act_on_a_draft(
    api_client: TestClient, unique_user: TestUser, fake_ai, request: pytest.FixtureRequest, other: str
):
    draft = ready_draft(api_client, unique_user, fake_ai, image=True)
    stranger: TestUser = request.getfixturevalue(other)
    path = f"{DRAFTS}/{draft['id']}"
    assert api_client.post(f"{path}/approve", json={}, headers=stranger.token).status_code == 404
    assert api_client.post(f"{path}/retry", headers=stranger.token).status_code == 404
    assert api_client.delete(path, headers=stranger.token).status_code == 404
    assert api_client.get(f"{path}/originals/1", headers=stranger.token).status_code == 404
    assert get_draft(api_client, unique_user, draft["id"]).json()["status"] == "ready"

    recipe_id = api_client.post(f"{path}/approve", json={}, headers=unique_user.token)
    assert recipe_id.status_code == 200
    saved = get_draft(api_client, unique_user, draft["id"]).json()["recipeId"]
    assert api_client.get(f"/api/kh/recipes/{saved}/origin", headers=stranger.token).status_code == 404
