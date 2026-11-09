"""KH: fixtures shared by Kochheft's tests: a family member next to unique_user, and a group without AI
providers or notices."""

from collections.abc import Generator
from uuid import UUID

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from mealie.kh.ai.models import KhAiProviderState
from mealie.kh.notices.models import KhNotice, KhNoticeRead
from mealie.repos.all_repositories import get_repositories
from tests import utils
from tests.utils import api_routes
from tests.utils.fixture_schemas import TestUser


@pytest.fixture(scope="module")
def household_member(
    session: Session, admin_token, api_client: TestClient, unique_user: utils.TestUser
) -> Generator[utils.TestUser]:
    """A second account in unique_user's household, like a family member invited by link."""
    group = api_client.get(api_routes.groups_self, headers=unique_user.token).json()
    household = api_client.get(api_routes.households_self, headers=unique_user.token).json()
    user_data = {
        "fullName": utils.random_string(),
        "username": utils.random_string(),
        "email": utils.random_email(),
        "password": "useruser",
        "group": group["name"],
        "household": household["name"],
        "admin": False,
        "tokens": [],
    }
    assert api_client.post(api_routes.admin_users, json=user_data, headers=admin_token).status_code == 201
    token = utils.login({"username": user_data["email"], "password": "useruser"}, api_client)
    me = api_client.get(api_routes.users_self, headers=token).json()
    yield utils.TestUser(
        user_id=UUID(me["id"]),
        _group_id=UUID(me["groupId"]),
        _household_id=UUID(me["householdId"]),
        token=token,
        email=user_data["email"],
        username=user_data["username"],
        full_name=user_data["fullName"],
        password=user_data["password"],
        repos=get_repositories(session, group_id=UUID(me["groupId"]), household_id=UUID(me["householdId"])),
    )


def clear_ai(user: TestUser) -> None:
    """Removes the group's providers with their state, and the group's notices and reads."""
    repos = user.repos
    for provider in repos.group_ai_providers.get_all():
        repos.session.execute(sa.delete(KhAiProviderState).where(KhAiProviderState.provider_id == provider.id))
        repos.group_ai_providers.delete(provider.id)
    repos.session.execute(sa.delete(KhNotice).where(KhNotice.group_id == user.group_id))
    repos.session.execute(sa.delete(KhNoticeRead).where(KhNoticeRead.user_id == user.user_id))
    repos.session.commit()


@pytest.fixture
def clean_ai(unique_user: TestUser) -> Generator[None]:
    """unique_user lives for a whole module: every test starts and ends without providers or notices."""
    clear_ai(unique_user)
    yield
    clear_ai(unique_user)
