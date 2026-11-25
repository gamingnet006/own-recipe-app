"""KH: tests for accounts without e-mail (D53): placeholder addresses, the first-sign-in password, welcome and confirm
links, the admin switch "e-mail required", and the clean-up when a user is deleted. No test sends real mail."""

import re
import time
from collections.abc import Callable, Generator
from datetime import timedelta

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient

from mealie.core.settings.settings import AppSettings
from mealie.kh.accounts.models import KhAccountLink
from mealie.kh.features.settings import get_kh_settings
from mealie.kh.onboarding.mails import send_account_mail
from mealie.kh.onboarding.models import KhAccountSettings, KhAccountToken, KhUserOnboarding
from mealie.services.email import EmailService
from tests import utils
from tests.utils import api_routes
from tests.utils.fixture_schemas import TestUser

ME = "/api/kh/onboarding/me"
PASSWORD = "/api/kh/onboarding/password"
EMAIL = "/api/kh/onboarding/email"
CONFIRM = "/api/kh/onboarding/confirm-email"
WELCOME = "/api/kh/onboarding/welcome"
SETTINGS = "/api/kh/admin/account-settings"
NEW_PASSWORD = "first-own-password"


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def smtp(monkeypatch: pytest.MonkeyPatch) -> Callable[[bool], list]:
    """Switches mail sending on or off and captures what would be sent as (address, template) pairs."""
    sent: list = []

    def set_smtp(enabled: bool) -> list:
        monkeypatch.setattr(AppSettings, "SMTP_ENABLE", property(lambda self: enabled))
        return sent

    monkeypatch.setattr(EmailService, "send_email", lambda self, to, data: sent.append((to, data)) or True)
    set_smtp.sent = sent  # type: ignore[attr-defined]
    return set_smtp


@pytest.fixture
def make_user(api_client: TestClient, admin_token, unique_user: TestUser) -> Generator[Callable[..., dict]]:
    """Creates a user as the admin (e-mail "" for none) in unique_user's household; all are deleted again."""
    made: list[str] = []
    group = api_client.get(api_routes.groups_self, headers=unique_user.token).json()["name"]
    household = api_client.get(api_routes.households_self, headers=unique_user.token).json()["name"]

    def make(email: str = "", **extra) -> dict:
        body = {
            "fullName": utils.random_string(),
            "username": utils.random_string(),
            "email": email,
            "password": "useruser",
            "group": group,
            "household": household,
            "admin": False,
            "tokens": [],
            **extra,
        }
        response = api_client.post(api_routes.admin_users, json=body, headers=admin_token)
        assert response.status_code == 201, response.text
        made.append(response.json()["id"])
        return {**body, **response.json()}

    yield make
    for user_id in made:
        assert api_client.delete(api_routes.admin_users_item_id(user_id), headers=admin_token).status_code in (200, 404)


def sign_in(api_client: TestClient, username: str, password: str) -> dict[str, str]:
    return utils.login({"username": username, "password": password}, api_client)


def token_of(link_text: str) -> str:
    return re.search(r"token=([\w-]+)", link_text).group(1)  # type: ignore[union-attr]


def test_admin_creates_user_without_email(api_client: TestClient, smtp, make_user):
    user = make_user()
    assert user["email"].endswith("@no-email.invalid")
    assert (
        api_client.get(api_routes.users_self, headers=sign_in(api_client, user["username"], "useruser")).status_code
        == 200
    )


def test_placeholders_are_unique(make_user):
    assert make_user()["email"] != make_user()["email"]


def test_new_user_chooses_a_password(api_client: TestClient, make_user):
    user = make_user()
    headers = sign_in(api_client, user["username"], "useruser")
    assert api_client.get(ME, headers=headers).json()["mustChangePassword"] is True
    assert api_client.post(PASSWORD, json={"password": "short"}, headers=headers).status_code == 400
    time.sleep(1.1)  # Mealie's logout watermark is whole seconds: a session from the same second would stay valid
    answer = api_client.post(PASSWORD, json={"password": NEW_PASSWORD}, headers=headers)
    assert answer.status_code == 200
    api_client.cookies.clear()  # the answer also set a session cookie; check the bearer tokens alone
    assert api_client.get(ME, headers=headers).status_code == 401  # the session opened with the admin's password ended
    fresh = {"Authorization": f"Bearer {answer.json()['access_token']}"}
    assert api_client.get(ME, headers=fresh).json()["mustChangePassword"] is False
    assert (
        api_client.post(api_routes.auth_token, data={"username": user["username"], "password": "useruser"}).status_code
        == 401
    )
    sign_in(api_client, user["username"], NEW_PASSWORD)


def test_password_endpoint_needs_the_flag(api_client: TestClient, unique_user: TestUser):
    assert api_client.post(PASSWORD, json={"password": NEW_PASSWORD}, headers=unique_user.token).status_code == 400


def test_welcome_mail_only_with_real_address_and_smtp(smtp, make_user):
    smtp(False)
    make_user(utils.random_email())
    assert smtp.sent == []  # type: ignore[attr-defined]
    smtp(True)
    address = utils.random_email()
    user = make_user(address)
    ((to, mail),) = smtp.sent  # type: ignore[attr-defined]
    assert to == address and "/willkommen?token=" in mail.button_link
    assert "useruser" not in mail.message_top + mail.message_bottom + mail.button_link
    assert user["username"] in mail.message_top
    make_user()  # no address: no mail
    assert len(smtp.sent) == 1  # type: ignore[attr-defined]


def test_welcome_link_sets_password_and_is_single_use(api_client: TestClient, smtp, make_user):
    smtp(True)
    user = make_user(utils.random_email())
    token = token_of(smtp.sent[0][1].button_link)  # type: ignore[attr-defined]
    assert api_client.get(WELCOME, params={"token": token}).json()["username"] == user["username"]
    assert api_client.post(WELCOME, json={"token": token, "password": NEW_PASSWORD}).status_code == 200
    headers = sign_in(api_client, user["username"], NEW_PASSWORD)
    assert api_client.get(ME, headers=headers).json()["mustChangePassword"] is False
    assert api_client.post(WELCOME, json={"token": token, "password": NEW_PASSWORD}).status_code == 400


def test_expired_welcome_link(api_client: TestClient, smtp, make_user, session):
    smtp(True)
    make_user(utils.random_email())
    token = token_of(smtp.sent[0][1].button_link)  # type: ignore[attr-defined]
    for row in session.execute(sa.select(KhAccountToken)).scalars():
        row.created_at = row.created_at - timedelta(hours=get_kh_settings().account_link_hours + 1)
    session.commit()
    assert api_client.get(WELCOME, params={"token": token}).status_code == 400
    assert api_client.post(WELCOME, json={"token": token, "password": NEW_PASSWORD}).status_code == 400


def test_account_settings(api_client: TestClient, smtp, admin_token, unique_user: TestUser):
    smtp(False)
    assert api_client.put(SETTINGS, json={"emailRequired": True}, headers=admin_token).status_code == 400
    smtp(True)
    assert api_client.put(SETTINGS, json={"emailRequired": True}, headers=unique_user.token).status_code == 403
    assert api_client.put(SETTINGS, json={"emailRequired": True}, headers=admin_token).status_code == 200
    assert api_client.get(SETTINGS, headers=admin_token).json() == {
        "emailRequired": True,
        "locale": None,
        "accent": None,
    }
    api_client.put(SETTINGS, json={"emailRequired": False}, headers=admin_token)


@pytest.fixture
def email_required(api_client: TestClient, smtp, admin_token) -> Generator[None]:
    """The switch on (mail sending on) for one test, off again afterwards."""
    smtp(True)
    api_client.put(SETTINGS, json={"emailRequired": True}, headers=admin_token)
    yield
    api_client.put(SETTINGS, json={"emailRequired": False}, headers=admin_token)


def test_required_email_is_confirmed_by_link(api_client: TestClient, smtp, email_required, make_user, unique_user):
    user = make_user()
    headers = sign_in(api_client, user["username"], "useruser")
    assert api_client.get(ME, headers=headers).json()["needsEmail"] is True
    taken = api_client.post(EMAIL, json={"email": unique_user.email}, headers=headers)
    assert taken.status_code == 409
    address = utils.random_email()
    assert api_client.post(EMAIL, json={"email": address}, headers=headers).status_code == 200
    ((to, mail),) = smtp.sent  # type: ignore[attr-defined]
    assert to == address and "/email-bestaetigen?token=" in mail.button_link
    assert api_client.get(ME, headers=headers).json()["pendingEmail"] == address
    assert api_client.post(CONFIRM, json={"token": token_of(mail.button_link)}).status_code == 200
    status_now = api_client.get(ME, headers=headers).json()
    assert status_now["needsEmail"] is False and status_now["pendingEmail"] is None
    assert api_client.get(api_routes.users_self, headers=headers).json()["email"] == address


def test_nobody_is_blocked_without_smtp(api_client: TestClient, smtp, email_required, make_user):
    user = make_user()
    smtp(False)
    assert api_client.get(ME, headers=sign_in(api_client, user["username"], "useruser")).json()["needsEmail"] is False


def test_linked_account_never_needs_email(api_client: TestClient, email_required, make_user, session):
    user = make_user()
    other = make_user()
    session.add(KhAccountLink(session=session, primary_user_id=other["id"], user_id=user["id"]))
    session.commit()
    assert api_client.get(ME, headers=sign_in(api_client, user["username"], "useruser")).json()["needsEmail"] is False


def test_blank_email_keeps_the_placeholder(api_client: TestClient, admin_token, make_user):
    user = make_user()
    stored = user["email"]
    edit = {**api_client.get(api_routes.admin_users_item_id(user["id"]), headers=admin_token).json(), "email": ""}
    assert api_client.put(api_routes.admin_users_item_id(user["id"]), json=edit, headers=admin_token).status_code == 200
    headers = sign_in(api_client, user["username"], "useruser")
    own = api_client.get(api_routes.users_self, headers=headers).json()
    assert own["email"] == stored
    assert (
        api_client.put(api_routes.users_item_id(user["id"]), json={**own, "email": ""}, headers=headers).status_code
        == 200
    )
    assert api_client.get(api_routes.users_self, headers=headers).json()["email"] == stored


def test_mealie_password_reset_ends_the_first_step(api_client: TestClient, admin_token, make_user):
    user = make_user(utils.random_email())
    reset = api_client.post(
        api_routes.admin_users_password_reset_token, json={"email": user["email"]}, headers=admin_token
    )
    body = {
        "token": reset.json()["token"],
        "email": user["email"],
        "password": NEW_PASSWORD,
        "passwordConfirm": NEW_PASSWORD,
    }
    assert api_client.post(api_routes.users_reset_password, json=body).status_code == 200
    assert (
        api_client.get(ME, headers=sign_in(api_client, user["username"], NEW_PASSWORD)).json()["mustChangePassword"]
        is False
    )


def test_deleting_a_user_removes_its_rows(api_client: TestClient, smtp, admin_token, make_user, session):
    smtp(True)
    user = make_user(utils.random_email())
    assert api_client.delete(api_routes.admin_users_item_id(user["id"]), headers=admin_token).status_code in (200, 404)
    session.expire_all()
    assert session.execute(sa.select(KhUserOnboarding).where(KhUserOnboarding.user_id == user["id"])).first() is None
    assert session.execute(sa.select(KhAccountToken).where(KhAccountToken.user_id == user["id"])).first() is None


def test_features_tell_whether_mail_is_ready(api_client: TestClient, smtp):
    smtp(True)
    assert api_client.get("/api/kh/features").json()["emailReady"] is True
    smtp(False)
    assert api_client.get("/api/kh/features").json()["emailReady"] is False


def test_welcome_link_ends_when_the_person_chose_a_password(api_client: TestClient, smtp, make_user):
    # review: a mail that reached the wrong person must not reset the password later
    smtp(True)
    user = make_user(utils.random_email())
    token = token_of(smtp.sent[0][1].button_link)  # type: ignore[attr-defined]
    headers = sign_in(api_client, user["username"], "useruser")
    assert api_client.post(PASSWORD, json={"password": NEW_PASSWORD}, headers=headers).status_code == 200
    assert api_client.get(WELCOME, params={"token": token}).status_code == 400
    assert api_client.post(WELCOME, json={"token": token, "password": "someone-else-1"}).status_code == 400
    sign_in(api_client, user["username"], NEW_PASSWORD)


def test_welcome_link_ends_when_the_admin_changes_the_address(api_client: TestClient, smtp, admin_token, make_user):
    smtp(True)
    user = make_user(utils.random_email())
    token = token_of(smtp.sent[0][1].button_link)  # type: ignore[attr-defined]
    edit = {**api_client.get(api_routes.admin_users_item_id(user["id"]), headers=admin_token).json()}
    edit["email"] = utils.random_email()
    assert api_client.put(api_routes.admin_users_item_id(user["id"]), json=edit, headers=admin_token).status_code == 200
    assert api_client.post(WELCOME, json={"token": token, "password": NEW_PASSWORD}).status_code == 400


def test_admins_are_never_asked_for_an_address(api_client: TestClient, email_required, make_user):
    # review: the admin who turns the switch on must never be locked out by it
    admin = make_user(admin=True)
    headers = sign_in(api_client, admin["username"], "useruser")
    assert api_client.get(ME, headers=headers).json()["needsEmail"] is False


def test_failed_confirm_mail_leaves_no_pending_address(
    api_client: TestClient, smtp, email_required, make_user, monkeypatch: pytest.MonkeyPatch
):
    user = make_user()
    headers = sign_in(api_client, user["username"], "useruser")
    monkeypatch.setattr(EmailService, "send_email", lambda self, to, data: False)
    assert api_client.post(EMAIL, json={"email": utils.random_email()}, headers=headers).status_code == 503
    assert api_client.get(ME, headers=headers).json()["pendingEmail"] is None


def test_api_token_cannot_change_the_first_password(api_client: TestClient, make_user):
    user = make_user()
    headers = sign_in(api_client, user["username"], "useruser")
    created = api_client.post(api_routes.users_api_tokens, json={"name": utils.random_string()}, headers=headers)
    api = bearer(created.json()["token"])
    assert api_client.post(PASSWORD, json={"password": NEW_PASSWORD}, headers=api).status_code == 400
    sign_in(api_client, user["username"], "useruser")  # the password did not change


def test_account_mails_are_in_the_persons_language_and_call_the_app_by_its_name(smtp):
    smtp(True)
    send_account_mail("verify", "a@example.com", "tok", "en-US")
    send_account_mail("verify", "a@example.com", "tok", "de-DE")
    (_, english), (_, german) = smtp.sent  # type: ignore[attr-defined]
    assert "Cookbook account" in english.message_top and "Kochheft" not in english.message_top
    assert "Kochheft-Konto" in german.message_top


def test_the_welcome_mail_uses_the_installation_language_first(smtp, make_user, session):
    smtp(True)
    row = session.execute(sa.select(KhAccountSettings)).scalars().first() or KhAccountSettings(session=session)
    row.locale = "en-US"
    session.add(row)
    session.commit()
    try:
        make_user(utils.random_email())
        assert smtp.sent[0][1].subject == "Your Cookbook account"  # type: ignore[attr-defined]
    finally:
        row.locale = None
        session.commit()
    make_user(utils.random_email())  # no installation language: German
    assert smtp.sent[1][1].subject == "Dein Kochheft-Konto"  # type: ignore[attr-defined]


def test_a_second_confirmation_mail_within_the_cooldown_is_refused_in_the_persons_language(
    api_client: TestClient, smtp, email_required, make_user, monkeypatch: pytest.MonkeyPatch
):
    smtp(True)
    headers = sign_in(api_client, make_user(utils.random_email())["username"], "useruser")
    address = utils.random_email()
    assert api_client.post(EMAIL, json={"email": address}, headers=headers).status_code == 200
    again = api_client.post(EMAIL, json={"email": address}, headers={**headers, "Accept-Language": "en-US"})
    assert again.status_code == 429
    assert "Wait 60 seconds" in again.json()["detail"]
    german = api_client.post(EMAIL, json={"email": address}, headers={**headers, "Accept-Language": "de-DE"})
    assert german.status_code == 429 and "Warte 60 Sekunden" in german.json()["detail"]
    assert len(smtp.sent) == 2  # type: ignore[attr-defined]  # the welcome mail and the first confirmation
    monkeypatch.setattr(get_kh_settings(), "verify_mail_cooldown_seconds", 0)
    assert api_client.post(EMAIL, json={"email": address}, headers=headers).status_code == 200
