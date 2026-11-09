"""KH: the allergen routes (D44): hits with their source lines, per-recipe corrections, and who may correct."""

from fastapi.testclient import TestClient

from tests.kh.nutrition.helpers import new_recipe
from tests.utils.fixture_schemas import TestUser

KH = "/api/kh"


def url(slug: str, allergen: str = "") -> str:
    return f"{KH}/recipes/{slug}/allergens" + (f"/{allergen}" if allergen else "")


def pesto_pasta(api_client: TestClient, user: TestUser) -> str:
    """A recipe with a food line (Pesto), a line without a food ("Kokosmilch" as text) and an innocent one."""
    return new_recipe(
        api_client,
        user,
        [
            (200, "g", "Weizenmehl", ""),
            (2, "EL", "Pesto", ""),
            (None, None, None, "Kokosmilch"),
            (1, "Prise", "Salz", ""),
        ],
    )["slug"]


def hits(api_client: TestClient, user: TestUser, slug: str) -> dict:
    return {h["allergen"]: h for h in api_client.get(url(slug), headers=user.token).json()["hits"]}


def test_hits_list_the_source_lines(api_client: TestClient, unique_user: TestUser):
    found = hits(api_client, unique_user, pesto_pasta(api_client, unique_user))
    assert set(found) == {"gluten", "nuts", "milk"}
    assert found["gluten"] == {"allergen": "gluten", "lines": ["200 Gramm Weizenmehl"], "corrected": None}
    assert found["nuts"]["lines"] == ["2 Esslöffel Pesto"]


def test_a_line_without_food_is_checked_by_its_text(api_client: TestClient, unique_user: TestUser):
    slug = new_recipe(api_client, unique_user, [(None, None, None, "1 Handvoll Haselnüsse")])["slug"]
    assert set(hits(api_client, unique_user, slug)) == {"nuts"}


def test_corrections_round_trip_and_null_clears(api_client: TestClient, unique_user: TestUser):
    slug = pesto_pasta(api_client, unique_user)
    headers = unique_user.token
    put = api_client.put(url(slug, "nuts"), json={"present": False}, headers=headers)
    assert put.status_code == 200 and put.json() == {"present": False}
    assert hits(api_client, unique_user, slug)["nuts"]["corrected"] is False  # stays, so the UI can undo it

    api_client.put(url(slug, "sesame"), json={"present": True}, headers=headers)
    assert hits(api_client, unique_user, slug)["sesame"] == {"allergen": "sesame", "lines": [], "corrected": True}

    api_client.put(url(slug, "nuts"), json={"present": None}, headers=headers)
    api_client.put(url(slug, "sesame"), json={"present": None}, headers=headers)
    assert set(hits(api_client, unique_user, slug)) == {"gluten", "nuts", "milk"}
    assert hits(api_client, unique_user, slug)["nuts"]["corrected"] is None


def test_other_household_reads_but_cannot_correct(api_client: TestClient, unique_user: TestUser, h2_user: TestUser):
    slug = pesto_pasta(api_client, unique_user)
    assert "nuts" in hits(api_client, h2_user, slug)
    denied = api_client.put(url(slug, "nuts"), json={"present": False}, headers=h2_user.token)
    assert denied.status_code == 403
    assert hits(api_client, unique_user, slug)["nuts"]["corrected"] is None


def test_bad_key_and_unknown_recipe(api_client: TestClient, unique_user: TestUser):
    slug = pesto_pasta(api_client, unique_user)
    assert api_client.put(url(slug, "zimt"), json={"present": True}, headers=unique_user.token).status_code == 422
    assert api_client.get(url("gibt-es-nicht"), headers=unique_user.token).status_code == 404
    assert (
        api_client.put(url("gibt-es-nicht", "nuts"), json={"present": True}, headers=unique_user.token).status_code
        == 404
    )
