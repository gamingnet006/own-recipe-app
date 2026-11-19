"""KH: tests for deleting an account without losing the family's recipes (D78): the admin's delete and the person's own
delete hand recipes, lists, plans, comments and timeline events to a person of the household and remove the rest."""

from collections.abc import Callable, Generator
from datetime import UTC, datetime
from uuid import UUID

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from mealie.db.models.household.mealplan import GroupMealPlan
from mealie.db.models.household.shopping_list import ShoppingList
from mealie.db.models.recipe import RecipeComment, RecipeModel, RecipeTimelineEvent
from mealie.db.models.users.user_to_recipe import UserToRecipe
from mealie.db.models.users.users import User
from mealie.kh.accounts.models import KhAccountLink
from mealie.kh.accounts.removal import ALONE_IN_HOUSEHOLD, LAST_ADMIN, LAST_PERSON, default_heir
from mealie.kh.notes.models import KhRecipeNote
from mealie.kh.wishes.models import KhRecipeWish
from mealie.repos.all_repositories import get_repositories
from tests import utils
from tests.utils import api_routes
from tests.utils.fixture_schemas import TestUser

PREVIEW = "/api/kh/account/delete-preview"
DELETE = "/api/kh/account/delete"
LINK = "/api/kh/admin/accounts"
SWITCH = "/api/kh/accounts/switch"

Person = Callable[..., TestUser]


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def group_name(api_client: TestClient, unique_user: TestUser) -> str:
    return api_client.get(api_routes.groups_self, headers=unique_user.token).json()["name"]


@pytest.fixture
def new_household(api_client: TestClient, admin_token, unique_user: TestUser) -> Callable[[], str]:
    """Makes an empty household in unique_user's group and returns its name."""

    def make() -> str:
        name = utils.random_string(12)
        body = {"name": name, "groupId": str(unique_user.group_id)}
        assert api_client.post(api_routes.admin_households, json=body, headers=admin_token).status_code == 201
        return name

    return make


@pytest.fixture
def person(
    api_client: TestClient, admin_token, session: Session, unique_user: TestUser, group_name: str
) -> Generator[Person]:
    """Makes a person in a household (unique_user's by default); everyone made is deleted again where possible."""
    made: list[UUID] = []

    def make(household: str | None = None, admin: bool = False, manager: bool = False) -> TestUser:
        if household is None:
            household = api_client.get(api_routes.households_self, headers=unique_user.token).json()["name"]
        data = {
            "fullName": utils.random_string(),
            "username": utils.random_string(),
            "email": utils.random_email(),
            "password": "useruser",
            "group": group_name,
            "household": household,
            "admin": admin,
            "canManageHousehold": manager,
        }
        assert api_client.post(api_routes.admin_users, json=data, headers=admin_token).status_code == 201
        token = utils.login({"username": data["email"], "password": "useruser"}, api_client)
        me = api_client.get(api_routes.users_self, headers=token).json()
        made.append(UUID(me["id"]))
        return TestUser(
            user_id=UUID(me["id"]),
            _group_id=UUID(me["groupId"]),
            _household_id=UUID(me["householdId"]),
            token=token,
            email=data["email"],
            username=data["username"],
            full_name=data["fullName"],
            password="useruser",
            repos=get_repositories(session, group_id=UUID(me["groupId"]), household_id=UUID(me["householdId"])),
        )

    yield make
    for user_id in made:
        api_client.delete(api_routes.admin_users_item_id(user_id), headers=admin_token)


def make_recipe(api_client: TestClient, owner: TestUser) -> str:
    """Creates a recipe as OWNER and returns its slug."""
    response = api_client.post(api_routes.recipes, json={"name": utils.random_string(14)}, headers=owner.token)
    assert response.status_code == 201
    return response.json()


def owner_of(session: Session, slug: str) -> UUID:
    session.expire_all()
    return session.scalars(sa.select(RecipeModel.user_id).where(RecipeModel.slug == slug)).one()


def fill_account(api_client: TestClient, session: Session, owner: TestUser) -> dict:
    """Gives OWNER a recipe with a comment, timeline event and favorite, a shopping list, a plan entry and a wish."""
    slug = make_recipe(api_client, owner)
    recipe_id = api_client.get(api_routes.recipes_slug(slug), headers=owner.token).json()["id"]
    comment = {"recipeId": recipe_id, "text": "lecker"}
    assert api_client.post(api_routes.comments, json=comment, headers=owner.token).status_code == 201
    event = {"recipe_id": recipe_id, "user_id": str(owner.user_id), "subject": "gekocht", "event_type": "info"}
    assert api_client.post(api_routes.recipes_timeline_events, json=event, headers=owner.token).status_code == 201
    favorite = api_routes.users_id_favorites_slug(owner.user_id, slug)
    assert api_client.post(favorite, headers=owner.token).status_code == 200
    shopping = api_client.post(api_routes.households_shopping_lists, json={"name": "Liste"}, headers=owner.token)
    assert shopping.status_code == 201
    plan = {"date": datetime.now(UTC).date().strftime("%Y-%m-%d"), "entryType": "dinner", "title": "Essen"}
    assert api_client.post(api_routes.households_mealplans, json=plan, headers=owner.token).status_code == 201
    session.add(
        KhRecipeWish(
            session=session,
            group_id=owner.group_id,
            household_id=owner._household_id,
            user_id=owner.user_id,
            recipe_id=recipe_id,
        )
    )
    session.add(
        KhRecipeNote(
            session=session,
            group_id=owner.group_id,
            household_id=owner._household_id,
            recipe_id=recipe_id,
            text="weniger Zucker",
            updated_by=owner.user_id,
        )
    )
    session.commit()
    return {"slug": slug, "recipe_id": recipe_id, "list_id": shopping.json()["id"]}


def rows_of(session: Session, user_id: UUID) -> dict[str, int]:
    """How many rows of each kind still point at USER_ID."""
    session.expire_all()

    def count(column) -> int:
        return session.scalar(sa.select(sa.func.count()).select_from(column.class_).where(column == user_id)) or 0

    return {
        "recipes": count(RecipeModel.user_id),
        "lists": count(ShoppingList.user_id),
        "plans": count(GroupMealPlan.user_id),
        "comments": count(RecipeComment.user_id),
        "events": count(RecipeTimelineEvent.user_id),
        "favorites": count(UserToRecipe.user_id),
        "wishes": count(KhRecipeWish.user_id),
        "notes": count(KhRecipeNote.updated_by),
        "user": count(User.id),
    }


def user_exists(session: Session, user_id: UUID) -> bool:
    session.expire_all()
    return session.get(User, user_id) is not None


def test_admin_delete_hands_everything_to_the_default_heir(
    api_client: TestClient, admin_token, session: Session, unique_user: TestUser, h2_user: TestUser, person: Person
):
    leaver = person()
    made = fill_account(api_client, session, leaver)
    other = make_recipe(api_client, h2_user)
    heir = default_heir(session, session.get(User, leaver.user_id))
    assert heir is not None
    before = rows_of(session, heir.id)

    response = api_client.delete(api_routes.admin_users_item_id(leaver.user_id), headers=admin_token)

    assert response.status_code == 200
    assert rows_of(session, leaver.user_id) == dict.fromkeys(rows_of(session, leaver.user_id), 0)
    after = rows_of(session, heir.id)
    gained = {kind: after[kind] - before[kind] for kind in after}
    assert gained | {"favorites": 0, "wishes": 0, "user": 0} == {
        "notes": 1,
        "recipes": 1,
        "lists": 1,
        "plans": 1,
        "comments": 1,
        "events": 2,
        "favorites": 0,
        "wishes": 0,
        "user": 0,
    }
    assert owner_of(session, made["slug"]) == heir.id
    assert owner_of(session, other) == h2_user.user_id  # another household is untouched
    # the recipe opens and is listed for the household
    assert api_client.get(api_routes.recipes_slug(made["slug"]), headers=unique_user.token).status_code == 200
    listed = api_client.get(api_routes.recipes, params={"perPage": -1}, headers=unique_user.token).json()["items"]
    assert made["slug"] in [item["slug"] for item in listed]


def test_admin_delete_to_a_chosen_person(
    api_client: TestClient, admin_token, session: Session, unique_user: TestUser, person: Person
):
    leaver = person()
    chosen = person()
    slug = fill_account(api_client, session, leaver)["slug"]

    url = f"{api_routes.admin_users_item_id(leaver.user_id)}?transferTo={chosen.user_id}"
    assert api_client.delete(url, headers=admin_token).status_code == 200

    assert owner_of(session, slug) == chosen.user_id


def test_admin_delete_to_a_foreign_household_is_refused(
    api_client: TestClient, admin_token, session: Session, h2_user: TestUser, person: Person
):
    leaver = person()
    slug = fill_account(api_client, session, leaver)["slug"]

    url = f"{api_routes.admin_users_item_id(leaver.user_id)}?transferTo={h2_user.user_id}"
    assert api_client.delete(url, headers=admin_token).status_code == 422

    assert owner_of(session, slug) == leaver.user_id


def test_default_heir_prefers_a_manager_then_the_oldest(
    session: Session, person: Person, new_household: Callable[[], str]
):
    household = new_household()
    leaver = person(household)
    oldest = person(household)
    manager = person(household, manager=True)
    person(household)

    leaver_row = session.get(User, leaver.user_id)
    assert default_heir(session, leaver_row).id == manager.user_id  # type: ignore[union-attr]
    session.execute(sa.update(User).where(User.id == manager.user_id).values(can_manage_household=False))
    session.commit()
    assert default_heir(session, leaver_row).id == oldest.user_id  # type: ignore[union-attr]


def test_default_heir_is_none_when_alone(session: Session, person: Person, new_household: Callable[[], str]):
    alone = person(new_household())
    assert default_heir(session, session.get(User, alone.user_id)) is None


def test_admin_delete_alone_with_recipes_is_refused(
    api_client: TestClient, admin_token, session: Session, person: Person, new_household: Callable[[], str]
):
    alone = person(new_household())
    slug = make_recipe(api_client, alone)

    response = api_client.delete(api_routes.admin_users_item_id(alone.user_id), headers=admin_token)

    assert response.status_code == 409
    assert ALONE_IN_HOUSEHOLD in response.text
    assert owner_of(session, slug) == alone.user_id


def test_admin_delete_alone_with_nothing_goes_through(
    api_client: TestClient, admin_token, session: Session, person: Person, new_household: Callable[[], str]
):
    alone = person(new_household())
    assert api_client.delete(api_routes.admin_users_item_id(alone.user_id), headers=admin_token).status_code == 200
    assert not user_exists(session, alone.user_id)


def test_delete_preview_names_the_heir(api_client: TestClient, session: Session, person: Person):
    leaver = person()
    fill_account(api_client, session, leaver)

    body = api_client.get(PREVIEW, headers=leaver.token).json()

    heir = default_heir(session, session.get(User, leaver.user_id))
    assert body["heir"]["id"] == str(heir.id)  # type: ignore[union-attr]
    assert (body["recipes"], body["lists"], body["blocked"]) == (1, 1, None)


def test_admin_sees_the_default_heir(
    api_client: TestClient, admin_token, session: Session, person: Person, new_household: Callable[[], str]
):
    household = new_household()
    leaver = person(household)
    url = f"{LINK}/{leaver.user_id}/heir"
    assert api_client.get(url, headers=admin_token).json() is None
    heir = person(household)

    assert api_client.get(url, headers=admin_token).json()["id"] == str(heir.user_id)


def test_self_delete(api_client: TestClient, session: Session, unique_user: TestUser, person: Person):
    leaver = person()
    made = fill_account(api_client, session, leaver)

    response = api_client.post(DELETE, json={"confirm": leaver.username.upper()}, headers=leaver.token)

    assert response.status_code == 204
    assert "mealie.access_token=" in response.headers["set-cookie"]
    assert not user_exists(session, leaver.user_id)
    assert owner_of(session, made["slug"]) != leaver.user_id
    assert api_client.get(api_routes.recipes_slug(made["slug"]), headers=unique_user.token).status_code == 200
    assert api_client.get(api_routes.users_self, headers=leaver.token).status_code == 401


def test_self_delete_needs_the_username(api_client: TestClient, session: Session, person: Person):
    leaver = person()
    response = api_client.post(DELETE, json={"confirm": "falsch"}, headers=leaver.token)
    assert response.status_code == 422
    assert user_exists(session, leaver.user_id)


def test_self_delete_refused_for_the_last_admin(api_client: TestClient, session: Session, person: Person):
    last_admin = person(admin=True)
    response = api_client.post(DELETE, json={"confirm": last_admin.username}, headers=last_admin.token)
    assert response.status_code == 409
    assert LAST_ADMIN in response.text
    assert api_client.get(PREVIEW, headers=last_admin.token).json()["blocked"] == LAST_ADMIN
    assert user_exists(session, last_admin.user_id)


def test_self_delete_refused_when_alone_in_the_household(
    api_client: TestClient, session: Session, person: Person, new_household: Callable[[], str]
):
    alone = person(new_household())
    response = api_client.post(DELETE, json={"confirm": alone.username}, headers=alone.token)
    assert response.status_code == 409
    assert LAST_PERSON in response.text
    assert user_exists(session, alone.user_id)


def test_self_delete_refused_with_an_api_token(api_client: TestClient, session: Session, person: Person):
    leaver = person()
    created = api_client.post(api_routes.users_api_tokens, json={"name": "Kurzbefehle"}, headers=leaver.token)
    response = api_client.post(DELETE, json={"confirm": leaver.username}, headers=bearer(created.json()["token"]))
    assert response.status_code == 400
    assert user_exists(session, leaver.user_id)


def test_self_delete_takes_the_linked_accounts_too(
    api_client: TestClient, admin_token, session: Session, h2_user: TestUser, person: Person
):
    leaver = person()
    linked = api_client.post(
        LINK, json={"userId": str(leaver.user_id), "householdId": str(h2_user._household_id)}, headers=admin_token
    ).json()
    switched = api_client.post(SWITCH, json={"userId": linked["userId"]}, headers=leaver.token).json()
    linked_slug = make_recipe(api_client, TestUser(**{**leaver.__dict__, "token": bearer(switched["access_token"])}))
    own_slug = make_recipe(api_client, leaver)

    response = api_client.post(DELETE, json={"confirm": leaver.username}, headers=leaver.token)

    assert response.status_code == 204
    assert not user_exists(session, leaver.user_id) and not user_exists(session, UUID(linked["userId"]))
    assert owner_of(session, linked_slug) == h2_user.user_id
    assert owner_of(session, own_slug) != leaver.user_id
    links = sa.select(KhAccountLink).where(KhAccountLink.primary_user_id == leaver.user_id)
    assert not session.scalars(links).all()


def test_self_delete_refused_when_a_linked_account_is_alone(
    api_client: TestClient, admin_token, session: Session, person: Person, new_household: Callable[[], str]
):
    leaver = person()
    household = new_household()
    empty_id = api_client.get(api_routes.admin_households, params={"perPage": -1}, headers=admin_token).json()
    empty_id = next(item["id"] for item in empty_id["items"] if item["name"] == household)
    api_client.post(LINK, json={"userId": str(leaver.user_id), "householdId": empty_id}, headers=admin_token)

    response = api_client.post(DELETE, json={"confirm": leaver.username}, headers=leaver.token)

    assert response.status_code == 409
    assert household in response.text
    assert user_exists(session, leaver.user_id)


def test_comments_and_events_of_a_lone_member_go_to_the_group(
    api_client: TestClient,
    admin_token,
    session: Session,
    unique_user: TestUser,
    person: Person,
    new_household: Callable[[], str],
):
    alone = person(new_household())  # alone in the household and owns nothing, but works on the group's recipes
    slug = make_recipe(api_client, unique_user)
    recipe_id = api_client.get(api_routes.recipes_slug(slug), headers=unique_user.token).json()["id"]
    assert api_client.post(api_routes.comments, json={"recipeId": recipe_id, "text": "ok"}, headers=alone.token)
    event = {"recipe_id": recipe_id, "user_id": str(alone.user_id), "subject": "gekocht", "event_type": "info"}
    assert api_client.post(api_routes.recipes_timeline_events, json=event, headers=alone.token).status_code == 201

    assert api_client.delete(api_routes.admin_users_item_id(alone.user_id), headers=admin_token).status_code == 200

    session.expire_all()
    heir = session.scalars(sa.select(RecipeComment.user_id).where(RecipeComment.recipe_id == recipe_id)).one()
    assert heir != alone.user_id and user_exists(session, heir)
    events = session.scalars(
        sa.select(RecipeTimelineEvent.user_id).where(RecipeTimelineEvent.recipe_id == recipe_id)
    ).all()
    assert (
        alone.user_id not in events
        and "gekocht"
        in session.scalars(
            sa.select(RecipeTimelineEvent.subject).where(RecipeTimelineEvent.recipe_id == recipe_id)
        ).all()
    )


def test_the_last_user_of_a_group_can_be_deleted_with_recipes(
    api_client: TestClient, admin_token, session: Session, h2_user: TestUser
):
    from tests.fixtures.fixture_users import build_unique_user

    last = build_unique_user(session, utils.random_string(), api_client)  # a group of its own
    make_recipe(api_client, last)

    assert api_client.delete(api_routes.admin_users_item_id(last.user_id), headers=admin_token).status_code == 200
    assert not user_exists(session, last.user_id)
