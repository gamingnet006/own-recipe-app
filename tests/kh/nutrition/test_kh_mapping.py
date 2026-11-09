"""KH: tests of the food to BLS mapping (D44): the suggestion, the listing and the endpoints."""

from fastapi.testclient import TestClient

from mealie.kh.amounts.parse import stem
from mealie.kh.nutrition.bls import BLS_SEARCH_LIMIT, load_bls
from mealie.kh.nutrition.mapping import load_aliases, suggest_code
from tests.kh.nutrition.helpers import new_food, new_recipe, set_can_organize
from tests.utils import random_string
from tests.utils.fixture_schemas import TestUser

NUTRITION = "/api/kh/nutrition"


def test_suggest_code_uses_the_alias_first(small_bls) -> None:
    foods = load_bls()
    aliases = {"mehl": "B100001"}  # a deliberate alias to the second flour

    assert suggest_code("Mehl", foods, aliases) == "B100001"


def test_suggest_code_falls_back_to_the_shortest_name_starting_with_the_stem(small_bls) -> None:
    foods = load_bls()

    assert suggest_code("Kartoffeln", foods, {}) == "B700000"  # "Kartoffel roh" before "Kartoffel gekocht"
    assert suggest_code("Rote Zwiebeln", foods, {}) == "B800000"  # its words are tried too
    assert suggest_code("Äpfel", foods, {}) == "B900000"  # umlauts meet their plain letters
    assert suggest_code("Pfefferminze", foods, {}) is None
    assert suggest_code("Weizenmehl", foods, {}) == "B100000"


def test_suggest_code_finds_a_compound_the_bls_writes_apart(small_bls) -> None:
    assert suggest_code("Dinkelvollkornmehl", load_bls(), {}) == "B100003"


def test_suggest_code_takes_the_noun_before_the_adjective(small_bls) -> None:
    foods = load_bls()

    for name in ("Grüne Bohnen", "Weiße Bohnen"):  # not Grünkohl, not Weißkohl
        assert foods[suggest_code(name, foods, {"boh": "C500003"}) or ""].name.startswith("Bohne")
    assert suggest_code("Frische Zwiebeln", foods, {}) == "B800000"  # not Frischkäse


def test_suggest_code_does_not_take_eis_for_ei(small_bls) -> None:
    foods = load_bls()
    aliases = {"ei": "B400000", "=eis": "C500006"}  # "=" marks an alias for the exact name only

    assert suggest_code("Eis", foods, aliases) == "C500006"
    assert suggest_code("Eier", foods, aliases) == "B400000"


def test_suggest_code_ignores_an_alias_the_table_does_not_have(small_bls) -> None:
    assert suggest_code("Mehl", load_bls(), {"mehl": "NOPE"}) == "B100002"  # the prefix fallback instead


def test_the_shipped_aliases_point_to_real_bls_foods() -> None:
    aliases = load_aliases()
    foods = load_bls()

    assert len(aliases) >= 55
    assert [code for code in aliases.values() if code not in foods] == []
    assert foods[suggest_code("Eis", foods, aliases) or ""].name.startswith("Speiseeis")  # not the egg
    for name, (low, high) in {"Mehl": (300, 380), "Butter": (700, 790), "Zucker": (380, 420), "Ei": (120, 160)}.items():
        assert low <= foods[aliases[stem(name)]].kcal <= high  # kcal per 100 g, a sanity check of the codes


def test_list_puts_unconfirmed_first_and_counts_recipes(
    small_bls, api_client: TestClient, unique_user: TestUser
) -> None:
    flour, butter = new_food(unique_user, "Mehl"), new_food(unique_user, "Butter")
    unused = new_food(unique_user, "Ungenutzt")
    new_recipe(api_client, unique_user, [(250, "g", "Mehl", ""), (100, "g", "Butter", "")])
    new_recipe(api_client, unique_user, [(1, None, "Mehl", "")])
    api_client.put(
        f"{NUTRITION}/foods/{butter.id}", json={"blsCode": "B200000", "confirmed": True}, headers=unique_user.token
    )

    listing = api_client.get(f"{NUTRITION}/foods", headers=unique_user.token).json()
    ours = [row for row in listing if row["foodId"] in (str(flour.id), str(butter.id), str(unused.id))]

    assert [row["foodName"] for row in ours] == ["Mehl", "Butter"]  # unconfirmed first; unused is not listed
    mehl, butter_row = ours
    assert mehl["recipeCount"] == 2 and mehl["suggested"] is True and mehl["blsCode"] == "B100000"
    assert mehl["blsName"] == "Weizen Mehl, Type 405" and mehl["confirmed"] is False
    assert butter_row["recipeCount"] == 1 and butter_row["confirmed"] is True and butter_row["suggested"] is False


def test_put_round_trip(small_bls, api_client: TestClient, unique_user: TestUser) -> None:
    food = new_food(unique_user, random_string())
    body = {"blsCode": "B700001", "confirmed": True, "pieceGrams": 130}

    put = api_client.put(f"{NUTRITION}/foods/{food.id}", json=body, headers=unique_user.token)

    assert put.status_code == 200
    assert put.json() == {
        "foodId": str(food.id),
        "foodName": food.name,
        "blsCode": "B700001",
        "blsName": "Kartoffel gekocht",
        "confirmed": True,
        "suggested": False,
        "pieceGrams": 130,
        "recipeCount": 0,
    }
    again = api_client.put(
        f"{NUTRITION}/foods/{food.id}", json={"blsCode": None, "confirmed": True}, headers=unique_user.token
    )
    assert again.json()["blsCode"] is None and again.json()["suggested"] is False and again.json()["pieceGrams"] is None


def test_put_rejects_an_unknown_code_and_a_food_of_another_group(
    small_bls, api_client: TestClient, unique_user: TestUser, g2_user: TestUser
) -> None:
    food = new_food(unique_user, random_string())
    set_can_organize(g2_user, True)  # so the other group's 404 is the answer, not a missing permission

    unknown = api_client.put(
        f"{NUTRITION}/foods/{food.id}", json={"blsCode": "NOPE", "confirmed": True}, headers=unique_user.token
    )
    foreign = api_client.put(
        f"{NUTRITION}/foods/{food.id}", json={"blsCode": "B100000", "confirmed": True}, headers=g2_user.token
    )

    assert unknown.status_code == 422
    assert foreign.status_code == 404


def test_put_needs_the_organize_permission_like_editing_a_food(
    small_bls, api_client: TestClient, unique_user_fn_scoped: TestUser
) -> None:
    user = unique_user_fn_scoped
    food = new_food(user, random_string())
    body = {"blsCode": "B200000", "confirmed": True}
    set_can_organize(user, False)

    assert api_client.put(f"{NUTRITION}/foods/{food.id}", json=body, headers=user.token).status_code == 403

    set_can_organize(user, True)

    assert api_client.put(f"{NUTRITION}/foods/{food.id}", json=body, headers=user.token).status_code == 200


def test_bls_search_returns_code_name_and_kcal(small_bls, api_client: TestClient, unique_user: TestUser) -> None:
    hits = api_client.get(f"{NUTRITION}/bls", params={"q": "mehl"}, headers=unique_user.token).json()

    assert hits[0] == {"code": "B100000", "name": "Weizen Mehl, Type 405", "kcal": 340}
    assert api_client.get(f"{NUTRITION}/bls", params={"q": "xyz"}, headers=unique_user.token).json() == []


def test_bls_search_caps_at_twenty(api_client: TestClient, unique_user: TestUser) -> None:
    hits = api_client.get(f"{NUTRITION}/bls", params={"q": "e"}, headers=unique_user.token).json()  # the real table

    assert BLS_SEARCH_LIMIT == 20 and len(hits) == 20
