"""KH: tests for adding by voice (D64): the text is split into articles, put on the list named or used last, merged
with open items, put back when ticked off; works with an API token, refused while the shopping list is off."""

from collections.abc import Callable, Generator

import pytest
from fastapi.testclient import TestClient

from mealie.kh.shopping.voice import split_articles, spoken_confirmation
from tests.kh.addons.test_kh_addons import addons  # noqa: F401  the add-on switches of unique_user's household
from tests.kh.drafts.test_kh_drafts_share import device_token
from tests.utils import api_routes
from tests.utils.fixture_schemas import TestUser

ADD = "/api/kh/shopping/add"


@pytest.fixture
def lists(api_client: TestClient, unique_user: TestUser) -> Generator[dict[str, str]]:
    """Two lists, Rewe made first and Aldi later; returns their ids by name. The lists are removed afterwards."""
    ids: dict[str, str] = {}
    for name in ("Rewe", "Aldi"):
        made = api_client.post(api_routes.households_shopping_lists, json={"name": name}, headers=unique_user.token)
        ids[name] = made.json()["id"]
    yield ids
    for list_id in ids.values():
        api_client.delete(api_routes.households_shopping_lists_item_id(list_id), headers=unique_user.token)


def items_of(api_client: TestClient, user: TestUser, list_id: str) -> list[dict]:
    """The items on a list, as the household API shows them."""
    answer = api_client.get(api_routes.households_shopping_lists_item_id(list_id), headers=user.token)
    return answer.json()["listItems"]


@pytest.mark.parametrize(
    ("text", "parts"),
    [
        ("Milch", ["Milch"]),
        ("Milch und 2 Butter", ["Milch", "2 Butter"]),
        ("Milch, Butter und Eier", ["Milch", "Butter", "Eier"]),
        ("2,5 kg Mehl UND Salz", ["2,5 kg Mehl", "Salz"]),
        ("Hundefutter", ["Hundefutter"]),
    ],
)
def test_the_text_is_split_into_articles(text: str, parts: list[str]):
    assert split_articles(text) == parts


def test_the_confirmation_is_a_german_sentence():
    assert spoken_confirmation(["Milch"], "Rewe") == "Milch steht auf der Liste Rewe."
    assert spoken_confirmation(["Milch", "Butter"], "Rewe") == "Milch und Butter stehen auf der Liste Rewe."
    assert (
        spoken_confirmation(["Milch", "Butter", "Eier"], "Rewe") == "Milch, Butter und Eier stehen auf der Liste Rewe."
    )


def test_two_articles_land_on_the_list_updated_last(api_client: TestClient, unique_user: TestUser, lists):
    response = api_client.post(ADD, json={"text": "Milch und 2 Butter"}, headers=unique_user.token)
    assert response.status_code == 200
    assert response.json()["message"] == "Milch und Butter stehen auf der Liste Aldi."
    items = {item["food"]["name"]: item for item in items_of(api_client, unique_user, lists["Aldi"])}
    assert set(items) == {"Milch", "Butter"}
    assert items["Butter"]["quantity"] == 2
    assert items_of(api_client, unique_user, lists["Rewe"]) == []


def test_the_list_is_found_by_name_ignoring_case(api_client: TestClient, unique_user: TestUser, lists):
    response = api_client.post(ADD, json={"text": "Brot", "list": "rEWE"}, headers=unique_user.token)
    assert response.json()["message"] == "Brot steht auf der Liste Rewe."
    assert len(items_of(api_client, unique_user, lists["Rewe"])) == 1


def test_an_unknown_list_name_is_404(api_client: TestClient, unique_user: TestUser, lists):
    assert api_client.post(ADD, json={"text": "Brot", "list": "Lidl"}, headers=unique_user.token).status_code == 404


def test_an_open_article_gets_the_amount_and_a_ticked_one_is_put_back(
    api_client: TestClient, unique_user: TestUser, lists
):
    api_client.post(ADD, json={"text": "2 Äpfel", "list": "Rewe"}, headers=unique_user.token)
    api_client.post(ADD, json={"text": "3 Äpfel", "list": "Rewe"}, headers=unique_user.token)
    (apples,) = items_of(api_client, unique_user, lists["Rewe"])
    assert apples["quantity"] == 3  # the amount said last replaces the old one
    apples["checked"] = True
    done = api_client.put(
        api_routes.households_shopping_items_item_id(apples["id"]), json=apples, headers=unique_user.token
    )
    assert done.status_code == 200
    api_client.post(ADD, json={"text": "Äpfel", "list": "Rewe"}, headers=unique_user.token)
    (again,) = items_of(api_client, unique_user, lists["Rewe"])
    assert (again["id"], again["checked"]) == (apples["id"], False)


def test_an_api_token_may_add(api_client: TestClient, unique_user: TestUser, lists):
    _, device = device_token(api_client, unique_user, "Siri")
    response = api_client.post(ADD, json={"text": "Quark"}, headers=device)
    assert response.status_code == 200
    assert response.json()["message"] == "Quark steht auf der Liste Aldi."


def test_without_a_list_the_answer_is_404(api_client: TestClient, g2_user: TestUser):
    response = api_client.post(ADD, json={"text": "Quark"}, headers=g2_user.token)
    assert (response.status_code, response.json()["detail"]["message"]) == (404, "Es gibt noch keine Einkaufsliste.")


def test_a_text_without_an_article_is_422(api_client: TestClient, unique_user: TestUser, lists):
    assert api_client.post(ADD, json={"text": "2 kg"}, headers=unique_user.token).status_code == 422


def test_another_groups_list_is_not_used(api_client: TestClient, g2_user: TestUser, lists):
    mine = api_client.post(ADD, json={"text": "Tee", "list": "Aldi"}, headers=g2_user.token)
    assert mine.status_code == 404


def test_refused_while_the_shopping_list_is_off(
    api_client: TestClient,
    unique_user: TestUser,
    addons: Callable[..., None],  # noqa: F811
):
    addons(shopping=False)
    assert api_client.post(ADD, json={"text": "Brot"}, headers=unique_user.token).status_code == 403


def only_item(api_client: TestClient, user: TestUser, list_id: str) -> dict:
    """The one item on the list."""
    (item,) = items_of(api_client, user, list_id)
    return item


def tick(api_client: TestClient, user: TestUser, item: dict) -> None:
    """Ticks the item off."""
    item["checked"] = True
    assert (
        api_client.put(
            api_routes.households_shopping_items_item_id(item["id"]), json=item, headers=user.token
        ).status_code
        == 200
    )


def say(api_client: TestClient, user: TestUser, text: str) -> None:
    """Says TEXT to the list Rewe."""
    assert api_client.post(ADD, json={"text": text, "list": "Rewe"}, headers=user.token).status_code == 200


def test_a_ticked_off_article_takes_the_unit_said_not_the_old_one(api_client: TestClient, unique_user: TestUser, lists):
    say(api_client, unique_user, "Butter 250 g")
    tick(api_client, unique_user, only_item(api_client, unique_user, lists["Rewe"]))
    say(api_client, unique_user, "2 Butter")
    item = only_item(api_client, unique_user, lists["Rewe"])
    assert (item["checked"], item["quantity"], item["unit"]) == (False, 2, None)


def test_an_open_article_takes_a_different_unit_instead_of_a_second_item(
    api_client: TestClient, unique_user: TestUser, lists
):
    say(api_client, unique_user, "Milch")
    say(api_client, unique_user, "2 Liter Milch")
    item = only_item(api_client, unique_user, lists["Rewe"])
    assert (item["quantity"], item["unit"]["abbreviation"]) == (2, "l")


def test_an_article_without_an_amount_keeps_the_amount_there(api_client: TestClient, unique_user: TestUser, lists):
    say(api_client, unique_user, "3 Liter Milch")
    say(api_client, unique_user, "Milch")
    item = only_item(api_client, unique_user, lists["Rewe"])
    assert (item["quantity"], item["unit"]["abbreviation"]) == (3, "l")
