"""KH: the book tables (D43): a row of each reads back, the Mealie rows they hang on take them along when deleted,
and a recipe has at most one flags row."""

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from mealie.kh.books.models import KhCookbookPrint, KhRecipeFlags
from mealie.kh.duplicates.models import KhDuplicateIgnored
from tests.utils import api_routes, random_string
from tests.utils.fixture_schemas import TestUser


def new_recipe(api_client: TestClient, user: TestUser) -> dict:
    """A fresh recipe as Mealie returns it."""
    slug = api_client.post(api_routes.recipes, json={"name": random_string()}, headers=user.token).json()
    return api_client.get(api_routes.recipes_slug(slug), headers=user.token).json()


def new_cookbook_id(api_client: TestClient, user: TestUser) -> str:
    """A fresh cookbook's ID."""
    response = api_client.post(api_routes.households_cookbooks, json={"name": random_string()}, headers=user.token)
    return response.json()["id"]


def count(session: Session, model: type, column: sa.Column, value: str) -> int:
    """How many rows of MODEL have COLUMN equal to VALUE."""
    return len(session.execute(sa.select(model).where(column == value)).scalars().all())


def test_rows_read_back_and_go_with_the_recipe(api_client: TestClient, unique_user: TestUser, session: Session):
    """Flags and ignored pairs are deleted with their recipe."""
    first, second = new_recipe(api_client, unique_user), new_recipe(api_client, unique_user)
    a, b = sorted([first["id"], second["id"]])
    session.add(KhRecipeFlags(session=session, recipe_id=a, own_photo=True))
    session.add(KhDuplicateIgnored(session=session, group_id=unique_user.group_id, recipe_a=a, recipe_b=b))
    session.commit()
    flags = session.execute(sa.select(KhRecipeFlags).where(KhRecipeFlags.recipe_id == a)).scalar_one()
    assert flags.own_photo is True

    doomed = first if first["id"] == a else second
    api_client.delete(api_routes.recipes_slug(doomed["slug"]), headers=unique_user.token)
    session.expire_all()
    assert count(session, KhRecipeFlags, KhRecipeFlags.recipe_id, a) == 0
    assert count(session, KhDuplicateIgnored, KhDuplicateIgnored.recipe_a, a) == 0


def test_print_settings_go_with_the_cookbook(api_client: TestClient, unique_user: TestUser, session: Session):
    """Print settings are stored as JSON and deleted with their cookbook."""
    cookbook_id = new_cookbook_id(api_client, unique_user)
    session.add(KhCookbookPrint(session=session, cookbook_id=cookbook_id, settings={"title": "Unser Buch"}))
    session.commit()
    row = session.execute(sa.select(KhCookbookPrint).where(KhCookbookPrint.cookbook_id == cookbook_id)).scalar_one()
    assert row.settings == {"title": "Unser Buch"}

    api_client.delete(api_routes.households_cookbooks_item_id(cookbook_id), headers=unique_user.token)
    session.expire_all()
    assert count(session, KhCookbookPrint, KhCookbookPrint.cookbook_id, cookbook_id) == 0


def test_a_recipe_has_one_flags_row(api_client: TestClient, unique_user: TestUser, session: Session):
    """A second flags row for the same recipe is refused."""
    recipe_id = new_recipe(api_client, unique_user)["id"]
    session.add(KhRecipeFlags(session=session, recipe_id=recipe_id))
    session.commit()
    session.add(KhRecipeFlags(session=session, recipe_id=recipe_id))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()
