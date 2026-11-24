"""KH: tests for reordering a ready draft's original photos in the review: the first photo is the cover."""

import io
from typing import Any

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.orm import Session

from tests.kh.drafts.conftest import fake_ai  # noqa: F401
from tests.kh.drafts.helpers import DRAFTS, get_draft, png, post_draft
from tests.kh.drafts.test_kh_drafts_approve import stored_draft
from tests.utils.fixture_schemas import TestUser

WIDTHS = [40, 60, 80]  # the three photos differ in width, so their order can be read back from the stored files


@pytest.fixture
def photos(api_client: TestClient, unique_user: TestUser, fake_ai) -> dict[str, Any]:  # noqa: F811
    """A ready photo draft with three originals of different widths."""
    fake_ai("recipe-amounts.json")
    files = [("images", (f"p{w}.png", png(w, 30), "image/png")) for w in WIDTHS]
    draft = post_draft(api_client, unique_user, files=files).json()
    return get_draft(api_client, unique_user, draft["id"]).json()


def put_order(api_client: TestClient, user: TestUser, draft_id: str, order: list[int]):
    """PUT the new order of the originals (their current numbers, from 1)."""
    return api_client.put(f"{DRAFTS}/{draft_id}/originals/order", json={"order": order}, headers=user.token)


def widths(api_client: TestClient, user: TestUser, draft_id: str) -> list[int]:
    """The widths of the originals in their current order."""
    sizes = []
    for n in range(1, len(WIDTHS) + 1):
        body = api_client.get(f"{DRAFTS}/{draft_id}/originals/{n}", headers=user.token).content
        sizes.append(Image.open(io.BytesIO(body)).width)
    return sizes


def test_originals_are_reordered(api_client: TestClient, unique_user: TestUser, photos: dict[str, Any]):
    assert widths(api_client, unique_user, photos["id"]) == WIDTHS
    response = put_order(api_client, unique_user, photos["id"], [3, 1, 2])
    assert response.status_code == 200
    assert widths(api_client, unique_user, photos["id"]) == [80, 40, 60]
    assert response.json()["originalFiles"] == get_draft(api_client, unique_user, photos["id"]).json()["originalFiles"]


@pytest.mark.parametrize("order", [[1, 2], [1, 2, 2], [0, 1, 2], [1, 2, 4], []])
def test_bad_orders_are_refused(
    api_client: TestClient, unique_user: TestUser, photos: dict[str, Any], order: list[int]
):
    assert put_order(api_client, unique_user, photos["id"], order).status_code == 422
    assert widths(api_client, unique_user, photos["id"]) == WIDTHS


def test_only_a_ready_draft_is_reordered(api_client: TestClient, unique_user: TestUser, photos: dict[str, Any]):
    api_client.post(f"{DRAFTS}/{photos['id']}/approve", json={}, headers=unique_user.token)
    assert put_order(api_client, unique_user, photos["id"], [3, 1, 2]).status_code == 409


def test_a_failed_draft_is_reordered_before_the_retry(api_client: TestClient, unique_user: TestUser, fake_ai):  # noqa: F811
    fake_ai(RuntimeError("recorded failure"))
    files = [("images", (f"p{w}.png", png(w, 30), "image/png")) for w in WIDTHS]
    draft = post_draft(api_client, unique_user, files=files).json()
    assert get_draft(api_client, unique_user, draft["id"]).json()["status"] == "failed"
    assert put_order(api_client, unique_user, draft["id"], [2, 3, 1]).status_code == 200
    assert widths(api_client, unique_user, draft["id"]) == [60, 80, 40]


def test_a_working_draft_is_not_reordered(api_client: TestClient, session: Session, unique_user: TestUser):
    working = stored_draft(session, unique_user, status="working", source_type="image", original_files=["a", "b"])
    assert put_order(api_client, unique_user, str(working.id), [2, 1]).status_code == 409


def test_other_households_draft_is_not_found(api_client: TestClient, h2_user: TestUser, photos: dict[str, Any]):
    assert put_order(api_client, h2_user, photos["id"], [3, 1, 2]).status_code == 404
