"""KH: tests for the first-sign-in tour (D59): the admin sets it for a user, the person's own status reports it, and
finishing or skipping clears it. Only the admin may set it. Also "Neu in Kochheft" (D69): which version a person has
seen, and that a new person starts with the newest one as seen."""

import re
from collections.abc import Callable, Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mealie.kh.onboarding.news import NEWS_VERSION
from tests import utils
from tests.utils import api_routes
from tests.utils.fixture_schemas import TestUser

ME = "/api/kh/onboarding/me"
DONE = "/api/kh/onboarding/tour-done"


def tour_url(user_id: str) -> str:
    return f"/api/kh/admin/onboarding/{user_id}/tour"


@pytest.fixture
def make_user(api_client: TestClient, admin_token, unique_user: TestUser) -> Generator[Callable[[], dict]]:
    """Creates a user as the admin in unique_user's household and returns it with its own sign-in headers."""
    made: list[str] = []
    group = api_client.get(api_routes.groups_self, headers=unique_user.token).json()["name"]
    household = api_client.get(api_routes.households_self, headers=unique_user.token).json()["name"]

    def make() -> dict:
        body = {
            "fullName": utils.random_string(),
            "username": utils.random_string(),
            "email": utils.random_email(),
            "password": "useruser",
            "group": group,
            "household": household,
            "admin": False,
            "tokens": [],
        }
        created = api_client.post(api_routes.admin_users, json=body, headers=admin_token).json()
        made.append(created["id"])
        headers = utils.login({"username": body["email"], "password": "useruser"}, api_client)
        return {"id": created["id"], "headers": headers}

    yield make
    for user_id in made:
        assert api_client.delete(api_routes.admin_users_item_id(user_id), headers=admin_token).status_code in (200, 404)


def test_no_tour_by_default(api_client: TestClient, unique_user: TestUser):
    assert api_client.get(ME, headers=unique_user.token).json()["tour"] is False


def test_admin_sets_the_tour_and_the_person_finishes_it(api_client: TestClient, admin_token, make_user):
    user = make_user()
    assert api_client.post(tour_url(user["id"]), json={"tour": True}, headers=admin_token).status_code == 200
    assert api_client.get(ME, headers=user["headers"]).json()["tour"] is True
    assert api_client.post(DONE, headers=user["headers"]).status_code == 200
    assert api_client.get(ME, headers=user["headers"]).json()["tour"] is False


def test_admin_can_take_the_tour_back(api_client: TestClient, admin_token, make_user):
    user = make_user()
    api_client.post(tour_url(user["id"]), json={"tour": True}, headers=admin_token)
    api_client.post(tour_url(user["id"]), json={"tour": False}, headers=admin_token)
    assert api_client.get(ME, headers=user["headers"]).json()["tour"] is False


def test_the_tour_is_for_that_user_only(api_client: TestClient, admin_token, make_user, unique_user: TestUser):
    user = make_user()
    api_client.post(tour_url(user["id"]), json={"tour": True}, headers=admin_token)
    assert api_client.get(ME, headers=unique_user.token).json()["tour"] is False


def test_only_the_admin_sets_it(api_client: TestClient, unique_user: TestUser, make_user):
    user = make_user()
    assert api_client.post(tour_url(user["id"]), json={"tour": True}, headers=unique_user.token).status_code == 403
    api_client.cookies.clear()  # the sign-in of make_user also set a session cookie
    assert api_client.post(tour_url(user["id"]), json={"tour": True}).status_code in (401, 403)


def test_unknown_user_is_404(api_client: TestClient, admin_token):
    unknown = "00000000-0000-4000-8000-000000000000"
    assert api_client.post(tour_url(unknown), json={"tour": True}, headers=admin_token).status_code == 404


def test_tour_done_without_a_tour_is_harmless(api_client: TestClient, unique_user: TestUser):
    assert api_client.post(DONE, headers=unique_user.token).status_code == 200
    assert api_client.post(DONE).status_code == 401


NEWS_SEEN = "/api/kh/onboarding/news-seen"
WHATS_NEW_TS = Path(__file__).parents[3] / "frontend/kh/app/lib/whats-new.ts"


def test_the_backend_knows_the_newest_news_version_the_frontend_lists_first():
    """Both lists must agree, or a new person would see news for a version the tour already covers (or none)."""
    first = re.search(r'version:\s*"([^"]+)"', WHATS_NEW_TS.read_text())
    assert first and first.group(1) == NEWS_VERSION


def test_news_seen_starts_empty_and_is_saved(api_client: TestClient, unique_user: TestUser):
    assert api_client.get(ME, headers=unique_user.token).json()["newsSeen"] is None
    assert api_client.post(NEWS_SEEN, json={"version": "1.3"}, headers=unique_user.token).status_code == 200
    assert api_client.get(ME, headers=unique_user.token).json()["newsSeen"] == "1.3"


def test_news_seen_is_per_person_and_needs_a_sign_in(api_client: TestClient, unique_user: TestUser, make_user):
    other = make_user()
    api_client.post(NEWS_SEEN, json={"version": "0.5"}, headers=unique_user.token)
    assert api_client.get(ME, headers=other["headers"]).json()["newsSeen"] == NEWS_VERSION
    api_client.cookies.clear()  # the sign-in of make_user also set a session cookie
    assert api_client.post(NEWS_SEEN, json={"version": "1.3"}).status_code == 401


def test_news_seen_refuses_an_overlong_version(api_client: TestClient, unique_user: TestUser):
    assert api_client.post(NEWS_SEEN, json={"version": "1" * 21}, headers=unique_user.token).status_code == 422


def test_an_admin_created_user_has_the_newest_news_as_seen(api_client: TestClient, make_user):
    assert api_client.get(ME, headers=make_user()["headers"]).json()["newsSeen"] == NEWS_VERSION
