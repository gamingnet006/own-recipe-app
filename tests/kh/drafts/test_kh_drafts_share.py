"""KH: tests for the share shortcut (v0.1.1): a device hands in a link or a photo with its own Mealie API token,
the household sees the draft like any other, and once the token is revoked the device gets no further."""

from fastapi.testclient import TestClient

from tests.kh.drafts.helpers import DRAFTS, get_draft, png
from tests.utils.fixture_schemas import TestUser

LINK = "https://example.org/testkuchen"


def device_token(api_client: TestClient, user: TestUser, name: str) -> tuple[int, dict[str, str]]:
    """A device's own API token, as the guide has it made under Profile → API Tokens."""
    created = api_client.post("/api/users/api-tokens", json={"name": name}, headers=user.token).json()
    return created["id"], {"Authorization": f"Bearer {created['token']}"}


def test_a_device_token_hands_in_a_link(api_client: TestClient, unique_user: TestUser, fake_page):
    fake_page("page.html")
    _, device = device_token(api_client, unique_user, "iPhone")
    response = api_client.post(DRAFTS, data={"url": LINK}, headers=device)
    assert response.status_code == 201
    draft = get_draft(api_client, unique_user, response.json()["id"]).json()
    assert draft["status"] == "ready"


def test_a_device_token_hands_in_a_photo(api_client: TestClient, unique_user: TestUser, fake_ai):
    fake_ai("recipe.json")
    _, device = device_token(api_client, unique_user, "iPad")
    response = api_client.post(DRAFTS, files={"images": ("zettel.png", png(400, 300), "image/png")}, headers=device)
    assert response.status_code == 201


def test_a_revoked_device_token_gets_no_further(api_client: TestClient, unique_user: TestUser):
    token_id, device = device_token(api_client, unique_user, "verlorenes iPhone")
    assert api_client.delete(f"/api/users/api-tokens/{token_id}", headers=unique_user.token).status_code == 200
    assert api_client.post(DRAFTS, data={"text": "Testkuchen: 200 g Mehl."}, headers=device).status_code == 401
