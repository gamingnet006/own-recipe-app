"""KH: the question "Verträgst du etwas nicht?" is asked once per account: the status reports whether it was
answered or skipped, and the person marks it themselves."""

from fastapi.testclient import TestClient

from tests.utils.fixture_schemas import TestUser

ME = "/api/kh/onboarding/me"
ASKED = "/api/kh/onboarding/intolerances-asked"


def test_not_asked_by_default(api_client: TestClient, unique_user: TestUser):
    assert api_client.get(ME, headers=unique_user.token).json()["intolerancesAsked"] is False


def test_marking_it_asked_sticks(api_client: TestClient, unique_user: TestUser):
    assert api_client.post(ASKED, headers=unique_user.token).status_code == 200
    assert api_client.get(ME, headers=unique_user.token).json()["intolerancesAsked"] is True
    assert api_client.post(ASKED, headers=unique_user.token).status_code == 200  # asking twice is harmless


def test_needs_a_signed_in_person(api_client: TestClient):
    assert api_client.post(ASKED).status_code == 401


def admin_url(user_id) -> str:
    return f"/api/kh/admin/onboarding/{user_id}/intolerances"


def test_admin_sets_a_persons_choice_and_it_counts_as_asked(api_client: TestClient, admin_token, unique_user: TestUser):
    response = api_client.put(
        admin_url(unique_user.user_id), json={"allergens": ["gluten", "milk"]}, headers=admin_token
    )
    assert response.status_code == 200
    mine = api_client.get("/api/kh/users/self/allergies", headers=unique_user.token).json()
    assert set(mine["allergens"]) == {"gluten", "milk"}
    assert api_client.get(ME, headers=unique_user.token).json()["intolerancesAsked"] is True


def test_only_the_admin_sets_it_for_a_person(api_client: TestClient, unique_user: TestUser):
    response = api_client.put(admin_url(unique_user.user_id), json={"allergens": ["gluten"]}, headers=unique_user.token)
    assert response.status_code == 403


def test_an_unknown_person_is_a_404(api_client: TestClient, admin_token):
    response = api_client.put(
        admin_url("00000000-0000-4000-8000-000000000000"), json={"allergens": []}, headers=admin_token
    )
    assert response.status_code == 404
