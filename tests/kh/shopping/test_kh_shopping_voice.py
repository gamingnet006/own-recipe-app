"""KH: tests for adding by voice (D64): the text is split into articles, put on the list named or used last, merged
with open items, put back when ticked off; works with an API token, refused while the shopping list is off."""

from collections.abc import Callable, Generator

import pytest
from fastapi.testclient import TestClient

from mealie.kh.shopping.voice import (
    plan_additions,
    split_articles,
    split_frame,
    split_store,
    spoken_amount_to_digits,
    spoken_confirmation,
    spoken_summary,
    strip_verb,
)
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
        ("butter and milk", ["butter", "milk"]),
    ],
)
def test_the_text_is_split_into_articles(text: str, parts: list[str]):
    assert split_articles(text) == parts


@pytest.mark.parametrize(
    ("text", "names", "expected"),
    [
        ("Milch und Butter bei Rewe", ["Rewe", "Aldi"], ("Milch und Butter", "Rewe")),
        ("2 Liter Milch für Aldi", ["Rewe", "Aldi"], ("2 Liter Milch", "Aldi")),
        ("Zahnpasta auf die dm-Liste", ["Rewe", "dm"], ("Zahnpasta", "dm")),
        ("Zahnpasta auf die dm Liste.", ["Rewe", "dm Liste"], ("Zahnpasta", "dm Liste")),
        ("Brot", ["Rewe"], ("Brot", None)),
        ("Kaffee für Gäste", ["Rewe"], ("Kaffee für Gäste", None)),
        ("Milch bei Rewe", ["Rewe", "Rewe City"], ("Milch", "Rewe")),
        ("Shampoo bei Rossmann", ["Rossmann Innenstadt", "Rewe"], ("Shampoo", "Rossmann Innenstadt")),
        ("Shampoo bei Rewe", ["Rewe City", "Rewe Nord"], ("Shampoo bei Rewe", None)),
        ("Kuchen für Oma bei REWE!", ["Rewe"], ("Kuchen für Oma", "Rewe")),
        ("Butter auf die Aldi-Einkaufsliste", ["Rewe", "Aldi"], ("Butter", "Aldi")),
        ("Butter auf die Aldi Einkaufsliste", ["Rewe", "Aldi"], ("Butter", "Aldi")),
        ("Butter auf die Einkaufsliste", ["Rewe", "Aldi"], ("Butter", None)),
        ("Butter auf die Liste", ["Rewe", "Aldi"], ("Butter", None)),
        ("Butter auf die Einkaufsliste", ["Einkaufsliste"], ("Butter", "Einkaufsliste")),
        ("butter at Aldi", ["Rewe", "Aldi"], ("butter", "Aldi")),
        ("butter for the Aldi list", ["Rewe", "Aldi"], ("butter", "Aldi")),
        ("butter on the Aldi shopping list", ["Rewe", "Aldi"], ("butter", "Aldi")),
        ("butter to the list", ["Rewe", "Aldi"], ("butter", None)),
        ("Setz Milch auf meine Einkaufsliste", ["Rewe", "Aldi"], ("Setz Milch", None)),
        ("Füge Butter zur Aldi-Liste", ["Rewe", "Aldi"], ("Füge Butter", "Aldi")),
        ("Butter zum Aldi", ["Rewe", "Aldi"], ("Butter", "Aldi")),
        ("Butter aufs Aldi", ["Rewe", "Aldi"], ("Butter", "Aldi")),
        ("Butter ins Aldi", ["Rewe", "Aldi"], ("Butter", "Aldi")),
        ("Butter auf unsere Aldi-Liste", ["Rewe", "Aldi"], ("Butter", "Aldi")),
        ("Butter auf meiner Liste", ["Rewe", "Aldi"], ("Butter", None)),
        ("milk to my shopping list", ["Rewe", "Aldi"], ("milk", None)),
        ("eggs on our Aldi list", ["Rewe", "Aldi"], ("eggs", "Aldi")),
    ],
)
def test_the_store_said_at_the_end_picks_the_list(text: str, names: list[str], expected: tuple[str, str | None]):
    assert split_store(text, names) == expected


@pytest.mark.parametrize(
    ("article", "expected"),
    [
        ("Zweimal Butter", "2 Butter"),
        ("einmal Butter", "1 Butter"),
        ("drei mal Milch", "3 Milch"),
        ("3-mal Butter", "3 Butter"),
        ("3 mal Butter", "3 Butter"),
        ("3x Butter", "3 Butter"),
        ("3× Butter", "3 Butter"),
        ("2 times butter", "2 butter"),
        ("twice butter", "2 butter"),
        ("ein Liter Milch", "1 Liter Milch"),
        ("einen Kasten Wasser", "1 Kasten Wasser"),
        ("eine Gurke", "1 Gurke"),
        ("zwölf Eier", "12 Eier"),
        ("one apple", "1 apple"),
        ("Three Apples", "3 Apples"),
        ("Eier", "Eier"),
        ("Einkaufswagen", "Einkaufswagen"),
        ("a loaf of bread", "a loaf of bread"),
        ("2 Butter", "2 Butter"),
        ("2,5 kg Mehl", "2,5 kg Mehl"),
        ("Zweibel", "Zweibel"),
        ("Ein paar Bananen", "Bananen"),
        ("paar Bananen", "Bananen"),
        ("ein bisschen Petersilie", "Petersilie"),
        ("ein wenig Petersilie", "Petersilie"),
        ("a couple of bananas", "bananas"),
        ("a few apples", "apples"),
        ("Einen halben Liter Sahne", "0,5 Liter Sahne"),
        ("eine halbe Gurke", "0,5 Gurke"),
        ("halbes Pfund Mehl", "0,5 Pfund Mehl"),
        ("half a liter of cream", "0,5 liter cream"),
    ],
)
def test_spoken_amounts_become_digits(article: str, expected: str):
    assert spoken_amount_to_digits(article) == expected


@pytest.mark.parametrize(
    ("spoken", "framed", "article"),
    [
        ("Setz Butter", False, "Butter"),
        ("Schreib mir bitte Milch", False, "Milch"),
        ("Bitte füge Eier", False, "Eier"),
        ("put butter", False, "butter"),
        ("please add milk", False, "milk"),
        ("Pack Nudeln", False, "Pack Nudeln"),
        ("Mach Mehl", False, "Mach Mehl"),
        ("Pack Nudeln", True, "Nudeln"),
        ("bitte tu Mehl", True, "Mehl"),
        ("Tuc Kekse", True, "Tuc Kekse"),
        ("Butter", True, "Butter"),
    ],
)
def test_a_leading_verb_phrase_is_stripped(spoken: str, framed: bool, article: str):
    assert strip_verb(spoken, framed) == article


@pytest.mark.parametrize(
    ("clause", "expected"),
    [("Milch drauf!", ("Milch", True)), ("put butter on it", ("put butter", True)), ("Milch.", ("Milch", False))],
)
def test_a_trailing_frame_word_is_split_off(clause: str, expected: tuple[str, bool]):
    assert split_frame(clause) == expected


@pytest.mark.parametrize(
    ("text", "names", "groups"),
    [
        ("Milch und Butter", ["Rewe", "Aldi"], [(None, ["Milch", "Butter"])]),
        ("Butter und Milch bei Aldi", ["Rewe", "Aldi"], [("Aldi", ["Butter", "Milch"])]),
        (
            "Butter auf die Aldi-Einkaufsliste und Tampons auf die dm-Einkaufsliste",
            ["Aldi", "dm"],
            [("Aldi", ["Butter"]), ("dm", ["Tampons"])],
        ),
        (
            "Butter bei Aldi und Eier und Tampons bei dm und Brot",
            ["Aldi", "dm"],
            [("Aldi", ["Butter"]), ("dm", ["Eier", "Tampons"]), (None, ["Brot"])],
        ),
        (
            "Setz 3-mal Butter und 4-mal Milch auf die Aldi-Einkaufsliste",
            ["Rewe", "Aldi"],
            [("Aldi", ["3-mal Butter", "4-mal Milch"])],
        ),
        (
            "please add butter and milk to the Aldi list",
            ["Rewe", "Aldi"],
            [("Aldi", ["butter", "milk"])],
        ),
        ("Milch bei Rewe", [], [(None, ["Milch bei Rewe"])]),
        ("", ["Rewe"], []),
        # a leading verb is stripped only when the sentence ends with a frame word or a store (else "Pack" is a pack)
        ("Pack Nudeln", ["Aldi"], [(None, ["Pack Nudeln"])]),
        ("Pack Nudeln und Milch", ["Aldi"], [(None, ["Pack Nudeln", "Milch"])]),
        ("Pack Nudeln und Milch drauf", ["Aldi"], [(None, ["Nudeln", "Milch"])]),
        ("Pack Nudeln und Milch bei Aldi", ["Aldi"], [("Aldi", ["Nudeln", "Milch"])]),
        ("Setz Butter auf die Aldi-Liste", ["Aldi"], [("Aldi", ["Butter"])]),
        ("Setz Butter", ["Aldi"], [(None, ["Butter"])]),
        ("Setz Milch auf meine Einkaufsliste", ["Aldi"], [(None, ["Milch"])]),
        ("Füge Butter zur Aldi-Liste hinzu", ["Aldi"], [("Aldi", ["Butter"])]),
        ("Add milk to my shopping list", ["Aldi"], [(None, ["milk"])]),
        ("put eggs on our Aldi list", ["Aldi"], [("Aldi", ["eggs"])]),
        ("please add milk", ["Aldi"], [(None, ["milk"])]),
        ("Butter und Pack Nudeln", ["Aldi"], [(None, ["Butter", "Pack Nudeln"])]),
        ("Butter und tu Milch dazu", ["Aldi"], [(None, ["Butter", "Milch"])]),
    ],
)
def test_the_clauses_are_grouped_by_the_next_store_said(
    text: str, names: list[str], groups: list[tuple[str | None, list[str]]]
):
    assert plan_additions(text, names) == groups


def test_the_confirmation_is_a_german_sentence():
    assert spoken_confirmation(["Milch"], "Rewe") == "Milch steht auf der Liste Rewe."
    assert spoken_confirmation(["Milch", "Butter"], "Rewe") == "Milch und Butter stehen auf der Liste Rewe."
    assert (
        spoken_confirmation(["Milch", "Butter", "Eier"], "Rewe") == "Milch, Butter und Eier stehen auf der Liste Rewe."
    )
    assert (
        spoken_summary([("Aldi", ["Butter"]), ("dm", ["Tampons"])])
        == "Butter steht auf der Liste Aldi. Tampons steht auf der Liste dm."
    )


def test_two_articles_land_on_the_list_updated_last(api_client: TestClient, unique_user: TestUser, lists):
    response = api_client.post(ADD, json={"text": "Milch und 2 Butter"}, headers=unique_user.token)
    assert response.status_code == 200
    assert response.json()["message"] == "Milch und Butter stehen auf der Liste Aldi."
    items = {item["food"]["name"]: item for item in items_of(api_client, unique_user, lists["Aldi"])}
    assert set(items) == {"Milch", "Butter"}
    assert items["Butter"]["quantity"] == 2
    assert items_of(api_client, unique_user, lists["Rewe"]) == []


def test_the_store_said_picks_the_list_but_an_explicit_list_wins(api_client: TestClient, unique_user: TestUser, lists):
    said = api_client.post(ADD, json={"text": "Milch bei Rewe"}, headers=unique_user.token)
    assert said.json()["message"] == "Milch steht auf der Liste Rewe."
    both = api_client.post(ADD, json={"text": "Brot bei Rewe", "list": "Aldi"}, headers=unique_user.token)
    assert both.json()["message"] == "Brot bei Rewe steht auf der Liste Aldi."


def test_the_list_is_found_by_name_ignoring_case(api_client: TestClient, unique_user: TestUser, lists):
    response = api_client.post(ADD, json={"text": "Brot", "list": "rEWE"}, headers=unique_user.token)
    assert response.json()["message"] == "Brot steht auf der Liste Rewe."
    assert len(items_of(api_client, unique_user, lists["Rewe"])) == 1


def test_an_unknown_list_name_is_404(api_client: TestClient, unique_user: TestUser, lists):
    response = api_client.post(ADD, json={"text": "Brot", "list": "Lidl"}, headers=unique_user.token)
    assert response.status_code == 404
    assert response.json()["message"] == "Die Liste Lidl gibt es nicht."  # D88: Siri reads the top-level message


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


def test_without_any_list_one_is_made(api_client: TestClient, unique_user: TestUser):
    """A new family says "Hey Siri" before anyone made a list: Kochheft makes "Einkaufsliste" instead of failing."""
    response = api_client.post(ADD, json={"text": "Quark"}, headers=unique_user.token)
    assert (response.status_code, response.json()["message"]) == (200, "Quark steht auf der Liste Einkaufsliste.")
    made = api_client.get(api_routes.households_shopping_lists, headers=unique_user.token).json()["items"]
    assert [entry["name"] for entry in made] == ["Einkaufsliste"]
    assert [item["food"]["name"] for item in items_of(api_client, unique_user, made[0]["id"])] == ["Quark"]


def test_a_named_list_is_not_made(api_client: TestClient, unique_user: TestUser):
    """Only the plain "Auf die Einkaufsliste" makes the first list; a list asked for by name must exist."""
    response = api_client.post(ADD, json={"text": "Quark", "list": "Lidl"}, headers=unique_user.token)
    assert (response.status_code, response.json()["message"]) == (404, "Die Liste Lidl gibt es nicht.")


def test_a_text_without_an_article_is_422(api_client: TestClient, unique_user: TestUser, lists):
    response = api_client.post(ADD, json={"text": "2 kg"}, headers=unique_user.token)
    assert response.status_code == 422
    assert response.json()["message"] == "Ich habe keinen Artikel verstanden."


def test_another_groups_list_is_not_used(api_client: TestClient, g2_user: TestUser, lists):
    mine = api_client.post(ADD, json={"text": "Tee", "list": "Aldi"}, headers=g2_user.token)
    assert mine.status_code == 404


def test_refused_while_the_shopping_list_is_off(
    api_client: TestClient,
    unique_user: TestUser,
    addons: Callable[..., None],  # noqa: F811
):
    addons(shopping=False)
    response = api_client.post(ADD, json={"text": "Brot"}, headers=unique_user.token)
    assert response.status_code == 403
    assert "ausgeschaltet" in response.json()["message"]
    assert response.json()["detail"]["message"] == response.json()["message"]


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


def test_two_stores_in_one_sentence_write_two_lists(api_client: TestClient, unique_user: TestUser, lists):
    said = "Butter auf die Rewe-Einkaufsliste und Zweimal Milch auf die Aldi-Einkaufsliste"
    response = api_client.post(ADD, json={"text": said}, headers=unique_user.token)
    assert response.status_code == 200
    assert response.json()["message"] == "Butter steht auf der Liste Rewe. Milch steht auf der Liste Aldi."
    assert [item["food"]["name"] for item in items_of(api_client, unique_user, lists["Rewe"])] == ["Butter"]
    (milk,) = items_of(api_client, unique_user, lists["Aldi"])
    assert (milk["food"]["name"], milk["quantity"]) == ("Milch", 2)


def test_amounts_said_in_words_and_a_sentence_frame(api_client: TestClient, unique_user: TestUser, lists):
    said = "Setz 3-mal Butter und einen Liter Milch auf die Aldi-Einkaufsliste"
    response = api_client.post(ADD, json={"text": said}, headers=unique_user.token)
    assert response.json()["message"] == "Butter und Milch stehen auf der Liste Aldi."
    items = {item["food"]["name"]: item for item in items_of(api_client, unique_user, lists["Aldi"])}
    assert items["Butter"]["quantity"] == 3
    assert (items["Milch"]["quantity"], items["Milch"]["unit"]["abbreviation"]) == (1, "l")


def test_an_explicit_list_wins_over_every_store_said(api_client: TestClient, unique_user: TestUser, lists):
    said = "Butter bei Aldi und Milch bei Rewe"
    response = api_client.post(ADD, json={"text": said, "list": "Rewe"}, headers=unique_user.token)
    assert response.json()["message"].endswith("stehen auf der Liste Rewe.")
    assert len(items_of(api_client, unique_user, lists["Rewe"])) == 2
    assert items_of(api_client, unique_user, lists["Aldi"]) == []


def test_nothing_is_written_when_any_part_fails(api_client: TestClient, unique_user: TestUser, lists):
    response = api_client.post(ADD, json={"text": "Butter bei Aldi und 2 kg bei Rewe"}, headers=unique_user.token)
    assert response.status_code == 422
    assert items_of(api_client, unique_user, lists["Aldi"]) == []
    assert items_of(api_client, unique_user, lists["Rewe"]) == []


def test_nothing_is_made_when_the_first_group_fails(api_client: TestClient, unique_user_fn_scoped: TestUser):
    user = unique_user_fn_scoped  # its own household: the module's user may have its first list already
    response = api_client.post(ADD, json={"text": "2 kg"}, headers=user.token)
    assert response.status_code == 422
    assert api_client.get(api_routes.households_shopping_lists, headers=user.token).json()["items"] == []


def test_half_a_liter_is_half_a_liter_and_a_few_is_no_amount(api_client: TestClient, unique_user: TestUser, lists):
    api_client.post(ADD, json={"text": "Einen halben Liter Sahne und ein paar Bananen"}, headers=unique_user.token)
    items = {item["food"]["name"]: item for item in items_of(api_client, unique_user, lists["Aldi"])}
    assert (items["Sahne"]["quantity"], items["Sahne"]["unit"]["abbreviation"]) == (0.5, "l")
    assert items["Bananen"]["quantity"] == 0
