"""KH: a person who joins through an invite link is a "Familie" account: they can organize (categories, tags) but not
invite or manage, and they cannot give themselves "advanced" (API tokens)."""

from fastapi.testclient import TestClient

from tests.utils import api_routes
from tests.utils.factories import user_registration_factory
from tests.utils.fixture_schemas import TestUser


def test_invited_person_gets_the_family_flags(api_client: TestClient, admin_user: TestUser):
    invite = api_client.post(api_routes.households_invitations, json={"uses": 1}, headers=admin_user.token).json()[
        "token"
    ]
    registration = user_registration_factory()
    registration.group = ""
    registration.household = ""
    registration.group_token = invite
    registration.advanced = True  # the registration page offers it; an invited person must not get it
    assert api_client.post(api_routes.users_register, json=registration.model_dump(by_alias=True)).status_code == 201

    login = api_client.post(
        api_routes.auth_token, data={"username": registration.email, "password": registration.password}
    )
    me = api_client.get(
        api_routes.users_self, headers={"Authorization": f"Bearer {login.json()['access_token']}"}
    ).json()

    assert me["canOrganize"] is True
    assert me["advanced"] is False
    assert (me["admin"], me["canInvite"], me["canManage"], me["canManageHousehold"]) == (False, False, False, False)
