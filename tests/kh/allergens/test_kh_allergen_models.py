"""KH: the nutrition and allergen tables (D44): rows read back, the unique constraints hold, and the rows go with the
recipe, food or user they hang on."""

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from mealie.kh.allergens.models import KhRecipeAllergen, KhSubstitution, KhUserAllergies
from mealie.kh.nutrition.models import KhFoodNutrition
from tests.kh.nutrition.helpers import new_food, new_recipe
from tests.utils import api_routes, random_email, random_string
from tests.utils.fixture_schemas import TestUser


def count(session: Session, model: type, column: sa.Column, value) -> int:
    """How many rows of MODEL have COLUMN equal to VALUE."""
    session.expire_all()
    return len(session.execute(sa.select(model).where(column == value)).scalars().all())


def test_rows_read_back(api_client: TestClient, unique_user: TestUser, session: Session) -> None:
    food = new_food(unique_user, random_string())
    recipe = new_recipe(api_client, unique_user, [])
    session.add(KhFoodNutrition(session=session, food_id=food.id, bls_code="B100000", confirmed=True, piece_grams=80))
    session.add(KhRecipeAllergen(session=session, recipe_id=recipe["id"], allergen="eggs", present=False))
    session.add(KhUserAllergies(session=session, user_id=unique_user.user_id, allergens=["nuts", "milk"]))
    session.add(
        KhSubstitution(
            session=session,
            household_id=unique_user.household_id,
            match="butter",
            replacement="Margarine",
            allergen="milk",
        )
    )
    session.commit()
    session.expire_all()

    nutrition = session.execute(sa.select(KhFoodNutrition).where(KhFoodNutrition.food_id == food.id)).scalar_one()
    assert (nutrition.bls_code, nutrition.confirmed, nutrition.piece_grams) == ("B100000", True, 80)
    allergen = session.execute(
        sa.select(KhRecipeAllergen).where(KhRecipeAllergen.recipe_id == recipe["id"])
    ).scalar_one()
    assert (allergen.allergen, allergen.present) == ("eggs", False)
    mine = session.execute(
        sa.select(KhUserAllergies).where(KhUserAllergies.user_id == unique_user.user_id)
    ).scalar_one()
    assert mine.allergens == ["nuts", "milk"]
    substitution = session.execute(
        sa.select(KhSubstitution).where(KhSubstitution.household_id == unique_user.household_id)
    ).scalar_one()
    assert (substitution.match, substitution.replacement, substitution.allergen) == ("butter", "Margarine", "milk")


def test_unique_constraints_hold(api_client: TestClient, unique_user: TestUser, session: Session) -> None:
    food = new_food(unique_user, random_string())
    recipe = new_recipe(api_client, unique_user, [])
    for row in (
        lambda: KhFoodNutrition(session=session, food_id=food.id, confirmed=False),
        lambda: KhRecipeAllergen(session=session, recipe_id=recipe["id"], allergen="soy", present=True),
    ):
        session.add(row())
        session.commit()
        session.add(row())
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
    # one recipe may hold different allergens
    session.add(KhRecipeAllergen(session=session, recipe_id=recipe["id"], allergen="milk", present=True))
    session.commit()


def test_rows_go_with_the_recipe(api_client: TestClient, unique_user: TestUser, session: Session) -> None:
    recipe = new_recipe(api_client, unique_user, [])
    session.add(KhRecipeAllergen(session=session, recipe_id=recipe["id"], allergen="eggs", present=True))
    session.commit()

    api_client.delete(api_routes.recipes_slug(recipe["slug"]), headers=unique_user.token)

    assert count(session, KhRecipeAllergen, KhRecipeAllergen.recipe_id, recipe["id"]) == 0


def test_the_mapping_goes_with_a_deleted_or_merged_food(
    api_client: TestClient, unique_user: TestUser, session: Session
) -> None:
    deleted, merged, target = (new_food(unique_user, random_string()) for _ in range(3))
    for food in (deleted, merged):
        session.add(KhFoodNutrition(session=session, food_id=food.id, bls_code="B100000", confirmed=True))
    session.commit()

    assert api_client.delete(f"{api_routes.foods}/{deleted.id}", headers=unique_user.token).status_code == 200
    merge = {"fromFood": str(merged.id), "toFood": str(target.id)}
    assert api_client.put(api_routes.foods_merge, json=merge, headers=unique_user.token).status_code == 200

    assert count(session, KhFoodNutrition, KhFoodNutrition.food_id, deleted.id) == 0
    assert count(session, KhFoodNutrition, KhFoodNutrition.food_id, merged.id) == 0


def test_the_profile_goes_with_a_deleted_user(
    api_client: TestClient, unique_user: TestUser, admin_token, session: Session
) -> None:
    group = api_client.get(api_routes.groups_self, headers=unique_user.token).json()
    household = api_client.get(api_routes.households_self, headers=unique_user.token).json()
    user = {
        "fullName": random_string(),
        "username": random_string(),
        "email": random_email(),
        "password": "useruser",
        "group": group["name"],
        "household": household["name"],
        "admin": False,
        "tokens": [],
    }
    created = api_client.post(api_routes.admin_users, json=user, headers=admin_token).json()
    session.add(KhUserAllergies(session=session, user_id=created["id"], allergens=["fish"]))
    session.commit()

    assert api_client.delete(f"{api_routes.admin_users}/{created['id']}", headers=admin_token).status_code == 200

    assert count(session, KhUserAllergies, KhUserAllergies.user_id, created["id"]) == 0
