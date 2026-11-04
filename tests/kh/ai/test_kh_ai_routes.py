"""KH: tests for the AI list's routes (D39): managers read and set the order, every group member may ask whether
any AI is available, and nothing more."""

from datetime import timedelta
from uuid import uuid4

from fastapi.testclient import TestClient

from mealie.db.models._model_utils.datetime import get_utc_now
from mealie.kh.ai.state import save_state
from tests.utils.fixture_schemas import TestUser

PROVIDERS = "/api/kh/ai/providers"
ORDER = "/api/kh/ai/providers/order"
STATUS = "/api/kh/ai/status"


def put_order(api_client: TestClient, user: TestUser, ids: list) -> int:
    """PUT the order and return the status code."""
    return api_client.put(ORDER, json={"providerIds": [str(i) for i in ids]}, headers=user.token).status_code


def test_order_round_trip(api_client: TestClient, unique_user: TestUser, providers):
    a, b, c = (providers[name].id for name in "ABC")
    assert put_order(api_client, unique_user, [c, a, b]) == 200
    listed = api_client.get(PROVIDERS, headers=unique_user.token).json()
    assert [(p["name"], p["position"]) for p in listed] == [("C", 0), ("A", 1), ("B", 2)]
    assert {"providerId", "model", "status", "pausedUntil", "supportsImages"} <= listed[0].keys()


def test_order_must_name_every_provider(api_client: TestClient, unique_user: TestUser, providers):
    a, b, c = (providers[name].id for name in "ABC")
    assert put_order(api_client, unique_user, [a, b]) == 422
    assert put_order(api_client, unique_user, [a, b, c, uuid4()]) == 422
    assert put_order(api_client, unique_user, [a, a, b, c]) == 422


def test_member_cannot_see_or_order(api_client: TestClient, household_member: TestUser, providers):
    headers = household_member.token
    assert api_client.get(PROVIDERS, headers=headers).status_code == 403
    assert put_order(api_client, household_member, [p.id for p in providers.values()]) == 403
    assert api_client.get("/api/kh/notices", headers=headers).status_code == 403
    assert api_client.post("/api/kh/notices/read", headers=headers).status_code == 403


def test_member_sees_only_availability(api_client: TestClient, household_member: TestUser, providers):
    response = api_client.get(STATUS, headers=household_member.token)
    assert response.status_code == 200
    assert response.json() == {"available": True, "configured": True}


def test_status_without_providers(api_client: TestClient, unique_user: TestUser, clean_ai):
    # no provider at all: the intake says AI is not set up, not "try later"
    assert api_client.get(STATUS, headers=unique_user.token).json() == {"available": False, "configured": False}


def test_status_follows_pauses(api_client: TestClient, unique_user: TestUser, providers):
    assert api_client.get(STATUS, headers=unique_user.token).json() == {"available": True, "configured": True}
    for provider in providers.values():
        save_state(
            unique_user.repos.session, provider.id, status="quota", paused_until=get_utc_now() + timedelta(hours=1)
        )
    assert api_client.get(STATUS, headers=unique_user.token).json() == {"available": False, "configured": True}
