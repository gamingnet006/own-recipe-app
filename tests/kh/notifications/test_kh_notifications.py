"""KH: tests for "Mitteilungen" (D75): the evening hints, the bundler, the settings and devices API, who gets an
event (household, toggles, never the one who caused it), a gone device losing its subscription, the evening reminder
once a day, and the news once per version. The push call itself is replaced: no real push is ever sent."""

import json
import re
import stat
from collections.abc import Callable, Generator
from datetime import datetime, timedelta

import pytest
import sqlalchemy as sa
from dateutil.tz import tzlocal
from fastapi.testclient import TestClient
from pywebpush import WebPushException
from sqlalchemy.orm import Session

from mealie.db.models.household.mealplan import GroupMealPlan
from mealie.kh.notifications import events, keys, sender, tasks
from mealie.kh.notifications.bundle import Bundler
from mealie.kh.notifications.endpoints import is_push_endpoint
from mealie.kh.notifications.hints import PlannedRecipe, evening_message
from mealie.kh.notifications.models import KhNotificationSettings, KhPushSubscription
from mealie.kh.notifications.sender import FALLBACK_SUBJECT, vapid_subject
from mealie.kh.onboarding.news import NEWS_VERSION
from tests import utils
from tests.utils import api_routes
from tests.utils.fixture_schemas import TestUser

BASE = "/api/kh/notifications"
REAL_DELIVER = sender._deliver  # the fixture below replaces it by a recorder
ON = {
    "plan": True,
    "evening": True,
    "shopping": True,
    "wishes": True,
    "intake": True,
    "news": True,
    "eveningTime": "18:00",
}


# --- pure parts -------------------------------------------------------------------------------------------------


def test_evening_message_names_tomorrows_dishes_and_nothing_when_empty():
    assert evening_message([]) is None
    assert evening_message([PlannedRecipe("Lasagne"), PlannedRecipe("Salat")]) == ("Morgen: Lasagne, Salat", "")


def test_evening_message_hints_at_thawing_by_food_label():
    recipe = PlannedRecipe(
        "Lasagne",
        foods=[("Hackfleisch", "Fleisch"), ("Lachs", "Meeresfrüchte"), ("Erbsen", "tiefkühlware"), ("Mehl", "Backen")],
    )
    assert evening_message([recipe, PlannedRecipe("Bolo", foods=[("Hackfleisch", "Fleisch")])]) == (
        "Morgen: Lasagne, Bolo",
        "Denk ans Auftauen: Hackfleisch, Lachs, Erbsen",
    )


def test_evening_message_hints_at_steps_for_the_day_before_and_shortens_them():
    long_step = "Die Bohnen über Nacht in reichlich kaltem Wasser einweichen, damit sie am nächsten Tag weich werden."
    recipe = PlannedRecipe(
        "Eintopf", steps=["Zwiebeln würfeln.", "Fleisch am Vortag marinieren. Danach kühlen.", long_step]
    )
    title, body = evening_message([recipe])  # type: ignore[misc]
    assert body.splitlines()[0] == "Am Vortag vorbereiten: Fleisch am Vortag marinieren"
    assert re.fullmatch(r"Am Vortag vorbereiten: .{1,62} …", body.splitlines()[1]) or body.splitlines()[1].endswith(
        "werden"
    )
    assert "Zwiebeln" not in body


def test_bundler_sends_first_at_once_and_bundles_the_rest_for_one_window():
    now = [0.0]
    bundler = Bundler(900, clock=lambda: now[0])
    assert bundler.add("list", "ctx", ["Milch"]) is True
    assert bundler.add("list", "ctx", ["Butter"]) is False
    assert bundler.add("list", "ctx", ["Eier"]) is False
    assert bundler.due() == []
    now[0] = 901
    assert bundler.due() == [("ctx", ["Butter", "Eier"])]
    assert bundler.due() == []  # the window started anew
    assert bundler.add("list", "ctx", ["Brot"]) is False
    now[0] = 2000
    assert bundler.due() == [("ctx", ["Brot"])]
    now[0] = 3000
    assert bundler.due() == []
    assert bundler.add("list", "ctx", ["Reis"]) is True  # forgotten, so it goes out at once again


# --- fixtures ---------------------------------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def fake_push(monkeypatch: pytest.MonkeyPatch, unique_user: TestUser) -> list[tuple[str, dict]]:
    """Runs background jobs at once in the test's session, records every push as (endpoint, payload), and starts each
    test with empty bundles. Raise by putting an exception into FAKE_FAILURES[endpoint]."""
    sent: list[tuple[str, dict]] = []
    session = unique_user.repos.session

    def deliver(subscription: KhPushSubscription, payload: str) -> None:
        failure = FAILURES.get(subscription.endpoint)
        if failure:
            raise failure
        sent.append((subscription.endpoint, json.loads(payload)))

    monkeypatch.setattr(sender, "_deliver", deliver)
    monkeypatch.setattr(sender, "dispatch", lambda job, *args: job(session, *args))
    monkeypatch.setattr(events, "plan_bundles", Bundler(events.PLAN_WINDOW_SECONDS))
    monkeypatch.setattr(events, "shopping_bundles", Bundler(events.SHOPPING_WINDOW_SECONDS))
    FAILURES.clear()
    # unique_user outlives a test, so devices and choices of earlier tests are cleared
    session.execute(sa.delete(KhPushSubscription))
    session.execute(sa.delete(KhNotificationSettings))
    session.commit()
    return sent


FAILURES: dict[str, Exception] = {}


def gone(status_code: int) -> WebPushException:
    """What pywebpush raises when the push service answers with STATUS_CODE."""

    class Response:
        pass

    response = Response()
    response.status_code = status_code  # type: ignore[attr-defined]
    return WebPushException("push failed", response=response)  # type: ignore[arg-type]


def subscribe(api_client: TestClient, user: TestUser | dict, endpoint: str) -> None:
    headers = user.token if isinstance(user, TestUser) else user["headers"]
    body = {"endpoint": endpoint, "keys": {"p256dh": "key", "auth": "auth"}}
    assert api_client.post(f"{BASE}/subscriptions", json=body, headers=headers).status_code == 204


@pytest.fixture
def housemate(api_client: TestClient, admin_token, unique_user: TestUser) -> Generator[Callable[[], dict]]:
    """Makes users in unique_user's household as the admin; each comes with its sign-in headers."""
    made: list[str] = []
    group = api_client.get(api_routes.groups_self, headers=unique_user.token).json()["name"]
    household = api_client.get(api_routes.households_self, headers=unique_user.token).json()["name"]

    def make() -> dict:
        body = {
            "fullName": utils.random_string(),
            "username": utils.random_string(),
            "email": utils.random_email(),
            "password": "useruser",
            "group": group,
            "household": household,
            "admin": False,
            "tokens": [],
        }
        created = api_client.post(api_routes.admin_users, json=body, headers=admin_token).json()
        made.append(created["id"])
        headers = utils.login({"username": body["email"], "password": "useruser"}, api_client)
        return {"id": created["id"], "headers": headers, "name": body["fullName"]}

    yield make
    api_client.cookies.clear()
    for user_id in made:
        assert api_client.delete(api_routes.admin_users_item_id(user_id), headers=admin_token).status_code in (200, 404)


def turn_on(api_client: TestClient, user: TestUser | dict, **changes) -> None:
    """Signs the user up with one device ("<id>-device") and sets the switches to ON updated by CHANGES."""
    headers = user.token if isinstance(user, TestUser) else user["headers"]
    user_id = str(user.user_id) if isinstance(user, TestUser) else user["id"]
    subscribe(api_client, user, f"https://fcm.googleapis.com/fcm/send/{user_id}")
    assert api_client.put(f"{BASE}/settings", json={**ON, **changes}, headers=headers).status_code == 200


def endpoints(sent: list[tuple[str, dict]]) -> set[str]:
    return {endpoint for endpoint, _ in sent}


# --- settings and devices ---------------------------------------------------------------------------------------


def test_everything_is_off_until_notifications_are_turned_on(api_client: TestClient, unique_user: TestUser):
    settings = api_client.get(f"{BASE}/settings", headers=unique_user.token).json()
    assert settings == dict.fromkeys(("plan", "evening", "shopping", "wishes", "intake", "news"), False) | {
        "eveningTime": "18:00"
    }
    assert api_client.get(f"{BASE}/subscriptions", headers=unique_user.token).json() == []


def test_the_first_device_switches_on_plan_evening_and_wishes(api_client: TestClient, unique_user: TestUser):
    subscribe(api_client, unique_user, "https://fcm.googleapis.com/fcm/send/a")
    settings = api_client.get(f"{BASE}/settings", headers=unique_user.token).json()
    assert [k for k in ("plan", "evening", "shopping", "wishes", "intake", "news") if settings[k]] == [
        "plan",
        "evening",
        "wishes",
    ]


def test_settings_round_trip_and_the_time_is_checked(api_client: TestClient, unique_user: TestUser):
    body = {**ON, "shopping": False, "eveningTime": "07:30"}
    assert api_client.put(f"{BASE}/settings", json=body, headers=unique_user.token).json() == body
    assert api_client.get(f"{BASE}/settings", headers=unique_user.token).json() == body
    for bad in ("7:30", "24:00", "noon"):
        assert (
            api_client.put(f"{BASE}/settings", json={**ON, "eveningTime": bad}, headers=unique_user.token).status_code
            == 422
        )


def test_devices_are_listed_labelled_and_removed_by_their_owner_only(
    api_client: TestClient, unique_user: TestUser, h2_user: TestUser
):
    ua = {"user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X)"}
    body = {"endpoint": "https://fcm.googleapis.com/fcm/send/mine", "keys": {"p256dh": "k", "auth": "a"}}
    assert api_client.post(f"{BASE}/subscriptions", json=body, headers=unique_user.token | ua).status_code == 204
    subscribe(api_client, h2_user, "https://fcm.googleapis.com/fcm/send/theirs")
    devices = api_client.get(f"{BASE}/subscriptions", headers=unique_user.token).json()
    assert [(d["endpoint"], d["userAgent"]) for d in devices] == [
        ("https://fcm.googleapis.com/fcm/send/mine", "iPhone")
    ]
    api_client.delete(
        f"{BASE}/subscriptions",
        params={"endpoint": "https://fcm.googleapis.com/fcm/send/theirs"},
        headers=unique_user.token,
    )
    assert len(api_client.get(f"{BASE}/subscriptions", headers=h2_user.token).json()) == 1
    api_client.delete(
        f"{BASE}/subscriptions",
        params={"endpoint": "https://fcm.googleapis.com/fcm/send/mine"},
        headers=unique_user.token,
    )
    assert api_client.get(f"{BASE}/subscriptions", headers=unique_user.token).json() == []


def test_a_subscription_needs_an_https_endpoint_and_a_sign_in(api_client: TestClient, unique_user: TestUser):
    body = {"endpoint": "http://push.example/x", "keys": {"p256dh": "k", "auth": "a"}}
    assert api_client.post(f"{BASE}/subscriptions", json=body, headers=unique_user.token).status_code == 422
    api_client.cookies.clear()
    assert api_client.get(f"{BASE}/settings").status_code == 401


def test_the_key_is_stable_and_stored_for_the_app_only(api_client: TestClient, unique_user: TestUser):
    first = api_client.get(f"{BASE}/key", headers=unique_user.token).json()["key"]
    assert first == api_client.get(f"{BASE}/key", headers=unique_user.token).json()["key"] == keys.public_key()
    assert len(first) == 87  # 65 bytes, URL-safe base64 without padding
    assert stat.S_IMODE(keys._key_file().stat().st_mode) == 0o600


def test_a_deleted_user_loses_devices_and_choices(
    api_client: TestClient, admin_token, housemate, unique_user: TestUser
):
    user = housemate()
    turn_on(api_client, user)
    assert api_client.delete(api_routes.admin_users_item_id(user["id"]), headers=admin_token).status_code in (200, 404)
    session = unique_user.repos.session
    assert (
        session.execute(sa.select(KhPushSubscription).where(KhPushSubscription.user_id == user["id"])).first() is None
    )
    assert (
        session.execute(sa.select(KhNotificationSettings).where(KhNotificationSettings.user_id == user["id"])).first()
        is None
    )


# --- test message and gone devices ------------------------------------------------------------------------------


def test_the_test_message_reaches_the_callers_devices_only(
    api_client: TestClient, fake_push, unique_user: TestUser, h2_user: TestUser
):
    turn_on(api_client, unique_user)
    turn_on(api_client, h2_user)
    assert api_client.post(f"{BASE}/test", headers=unique_user.token).json() == {"sent": 1}
    assert fake_push == [
        (
            f"https://fcm.googleapis.com/fcm/send/{unique_user.user_id}",
            {"title": "Kochheft", "body": "Test von Kochheft", "url": "/"},
        )
    ]


@pytest.mark.parametrize("status_code", [404, 410])
def test_a_device_the_push_service_does_not_know_loses_its_subscription(
    api_client: TestClient, unique_user: TestUser, status_code: int
):
    turn_on(api_client, unique_user)
    FAILURES[f"https://fcm.googleapis.com/fcm/send/{unique_user.user_id}"] = gone(status_code)
    assert api_client.post(f"{BASE}/test", headers=unique_user.token).json() == {"sent": 0}
    assert api_client.get(f"{BASE}/subscriptions", headers=unique_user.token).json() == []


def test_any_other_failure_keeps_the_device(api_client: TestClient, unique_user: TestUser):
    turn_on(api_client, unique_user)
    FAILURES[f"https://fcm.googleapis.com/fcm/send/{unique_user.user_id}"] = gone(500)
    assert api_client.post(f"{BASE}/test", headers=unique_user.token).json() == {"sent": 0}
    assert len(api_client.get(f"{BASE}/subscriptions", headers=unique_user.token).json()) == 1


# --- events -----------------------------------------------------------------------------------------------------


def test_a_plan_entry_reaches_the_household_but_not_the_planner(
    api_client: TestClient, fake_push, housemate, unique_user: TestUser, h2_user: TestUser
):
    mate = housemate()
    for user in (unique_user, mate, h2_user):
        turn_on(api_client, user)
    name = utils.random_string()
    recipe = api_client.post(api_routes.recipes, json={"name": name}, headers=unique_user.token).json()
    day = (datetime.now(tzlocal()) + timedelta(days=3)).date()
    body = {
        "date": day.isoformat(),
        "entryType": "dinner",
        "recipeId": api_client.get(api_routes.recipes_slug(recipe), headers=unique_user.token).json()["id"],
    }
    assert api_client.post(api_routes.households_mealplans, json=body, headers=unique_user.token).status_code == 201
    assert endpoints(fake_push) == {f"https://fcm.googleapis.com/fcm/send/{mate['id']}"}
    weekday = ("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So")[day.weekday()]
    assert (
        fake_push[0][1]["body"] == f"{unique_user.full_name} hat {name} für {weekday} {day.day}.{day.month}. eingeplant"
    )


def test_a_switched_off_event_sends_nothing(api_client: TestClient, fake_push, housemate, unique_user: TestUser):
    mate = housemate()
    turn_on(api_client, mate, plan=False, wishes=False)
    events.notify_plan_created(unique_user.user_id, unique_user.household_id, "Lasagne", datetime.now(tzlocal()).date())
    events.notify_wish(unique_user.user_id, unique_user.household_id, "Lasagne")
    assert fake_push == []


def test_a_wish_reaches_the_housemates(api_client: TestClient, fake_push, housemate, unique_user: TestUser):
    mate = housemate()
    turn_on(api_client, mate)
    name = utils.random_string()
    slug = api_client.post(api_routes.recipes, json={"name": name}, headers=unique_user.token).json()
    recipe_id = api_client.get(api_routes.recipes_slug(slug), headers=unique_user.token).json()["id"]
    assert api_client.put(f"/api/kh/wishes/{recipe_id}", headers=unique_user.token).status_code == 204
    assert [payload["body"] for _, payload in fake_push] == [f"{unique_user.full_name} wünscht sich {name}"]


def test_shopping_items_go_out_bundled_per_list(
    api_client: TestClient, fake_push, housemate, unique_user: TestUser, monkeypatch: pytest.MonkeyPatch
):
    mate = housemate()
    turn_on(api_client, mate, shopping=True)
    lists = api_client.post(
        api_routes.households_shopping_lists, json={"name": "Rewe"}, headers=unique_user.token
    ).json()
    now = [0.0]
    monkeypatch.setattr(events, "shopping_bundles", Bundler(events.SHOPPING_WINDOW_SECONDS, clock=lambda: now[0]))

    def add(note: str) -> None:
        body = [{"shoppingListId": lists["id"], "note": note, "quantity": 1}]
        assert (
            api_client.post(
                api_routes.households_shopping_items_create_bulk, json=body, headers=unique_user.token
            ).status_code
            == 201
        )

    add("Milch")
    add("Butter")
    add("Eier")
    assert [p["body"] for _, p in fake_push] == [f"{unique_user.full_name} hat Milch auf Rewe gesetzt"]
    now[0] = events.SHOPPING_WINDOW_SECONDS + 1
    events.flush_bundles()
    assert fake_push[1][1]["body"] == f"{unique_user.full_name} hat 2 Sachen auf Rewe gesetzt: Butter, Eier"
    assert len(fake_push) == 2


def test_a_ready_draft_is_announced_to_the_household(api_client: TestClient, fake_push, unique_user: TestUser):
    turn_on(api_client, unique_user, intake=True)
    events.notify_draft_ready(unique_user.household_id, "Lasagne")
    assert [p["body"] for _, p in fake_push] == ["Zum Prüfen bereit: Lasagne"]
    assert fake_push[0][1]["url"].endswith("/drafts")


# --- evening reminder and news ----------------------------------------------------------------------------------


def plan_for_tomorrow(unique_user: TestUser, title: str) -> None:
    session = unique_user.repos.session
    tomorrow = datetime.now(tzlocal()).date() + timedelta(days=1)
    session.add(
        GroupMealPlan(
            session=session,
            date=tomorrow,
            entry_type="dinner",
            title=title,
            text="",
            group_id=unique_user.group_id,
            user_id=unique_user.user_id,
        )
    )
    session.commit()


def test_the_evening_reminder_comes_once_a_day_after_the_chosen_time(
    api_client: TestClient, fake_push, unique_user: TestUser
):
    turn_on(api_client, unique_user, eveningTime="19:30")
    plan_for_tomorrow(unique_user, "Lasagne")
    session, today = unique_user.repos.session, datetime.now(tzlocal()).replace(hour=19, minute=0, second=0)
    assert tasks.send_due_evenings(session, today) == 0  # not yet
    assert tasks.send_due_evenings(session, today.replace(minute=31)) == 1
    assert tasks.send_due_evenings(session, today.replace(minute=45)) == 0  # once per day
    assert fake_push[0][1]["title"] == "Morgen: Lasagne"
    assert (
        tasks.send_due_evenings(session, today.replace(minute=45) + timedelta(days=1)) == 0
    )  # nothing planned that day


def test_the_evening_reminder_respects_the_switch_and_an_empty_plan(
    api_client: TestClient, fake_push, unique_user: TestUser
):
    turn_on(api_client, unique_user, evening=False)
    plan_for_tomorrow(unique_user, "Lasagne")
    assert tasks.send_due_evenings(unique_user.repos.session, datetime.now(tzlocal()).replace(hour=23, minute=59)) == 0
    assert fake_push == []


def test_the_news_go_out_once_per_version(api_client: TestClient, fake_push, unique_user: TestUser):
    marker = tasks._news_marker()
    marker.unlink(missing_ok=True)
    turn_on(api_client, unique_user, news=True)
    session = unique_user.repos.session
    assert tasks.send_news_once(session) == 1
    assert tasks.send_news_once(session) == 0
    assert fake_push[0][1]["title"] == f"Neu in Kochheft {NEWS_VERSION}"
    marker.write_text("0.1")
    assert tasks.send_news_once(session) == 1


# --- review fixes -----------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "url",
    [
        "https://fcm.googleapis.com/fcm/send/abc",
        "https://updates.push.services.mozilla.com/wpush/v2/abc",
        "https://web.push.apple.com/abc",
        "https://api.sandbox.push.apple.com/3/device/abc",
        "https://wns2-par02p.notify.windows.com/w/?token=abc",
    ],
)
def test_known_push_services_are_accepted(url: str):
    assert is_push_endpoint(url)


@pytest.mark.parametrize(
    "url",
    [
        "https://192.168.1.1:8443/x",
        "https://192.168.1.1/x",
        "http://fcm.googleapis.com/x",
        "https://fcm.googleapis.com:8443/x",
        "https://user@fcm.googleapis.com/x",
        "https://evil.com\\@fcm.googleapis.com/x",
        "https://fcm.googleapis.com.evil.com/x",
        "https://evilfcm.googleapis.com/x",
        "https://evil.com/?h=fcm.googleapis.com",
        "https://notpush.apple.com.evil.com/x",
        "https://push.apple.com/x",
        "https://fcm.googleapis.com/x y",
        "",
    ],
)
def test_other_addresses_are_refused(api_client: TestClient, unique_user: TestUser, url: str):
    assert not is_push_endpoint(url)
    body = {"endpoint": url, "keys": {"p256dh": "k", "auth": "a"}}
    assert api_client.post(f"{BASE}/subscriptions", json=body, headers=unique_user.token).status_code == 422


def test_an_old_row_with_a_foreign_endpoint_is_never_called(unique_user: TestUser):
    row = KhPushSubscription(
        session=unique_user.repos.session,
        user_id=unique_user.user_id,
        endpoint="https://192.168.1.1/x",
        p256dh="k",
        auth="a",
    )
    with pytest.raises(ValueError, match="push service"):
        REAL_DELIVER(row, "{}")


def test_the_push_session_does_not_follow_redirects():
    assert sender._NoRedirectSession().get_redirect_target(object()) is None


def test_two_people_adding_to_one_list_are_bundled_and_credited_separately(
    api_client: TestClient, fake_push, housemate, unique_user: TestUser, monkeypatch: pytest.MonkeyPatch
):
    anna, bert = housemate(), housemate()
    for user in (unique_user, anna, bert):
        turn_on(api_client, user, shopping=True)
    now = [0.0]
    monkeypatch.setattr(events, "shopping_bundles", Bundler(events.SHOPPING_WINDOW_SECONDS, clock=lambda: now[0]))
    list_id = api_client.post(
        api_routes.households_shopping_lists, json={"name": "Rewe"}, headers=unique_user.token
    ).json()["id"]
    events.notify_items_added(anna["id"], unique_user.household_id, list_id, ["Milch"])
    events.notify_items_added(bert["id"], unique_user.household_id, list_id, ["Brot"])

    def ep(user) -> str:
        return f"https://fcm.googleapis.com/fcm/send/{user.user_id if isinstance(user, TestUser) else user['id']}"

    assert {(endpoint, payload["body"]) for endpoint, payload in fake_push} == {
        (ep(unique_user), f"{anna['name']} hat Milch auf Rewe gesetzt"),
        (ep(bert), f"{anna['name']} hat Milch auf Rewe gesetzt"),
        (ep(unique_user), f"{bert['name']} hat Brot auf Rewe gesetzt"),
        (ep(anna), f"{bert['name']} hat Brot auf Rewe gesetzt"),
    }


@pytest.mark.parametrize(
    ("base_url", "expected"),
    [
        ("https://kochheft.example.org", ("https://kochheft.example.org", True)),
        ("https://kochheft.example.org:8443/x", ("https://kochheft.example.org", True)),
        ("http://kochheft.example.org", ("mailto:kochheft@kochheft.example.org", True)),
        ("http://localhost:9091", (FALLBACK_SUBJECT, False)),
        ("http://192.168.1.5:9091", (FALLBACK_SUBJECT, False)),
        ("http://kochheft.local", (FALLBACK_SUBJECT, False)),
        ("", (FALLBACK_SUBJECT, False)),
    ],
)
def test_the_vapid_subject_prefers_https_then_a_real_host(base_url: str, expected: tuple[str, bool]):
    assert vapid_subject(base_url) == expected


def evening_row(session: Session, user: TestUser, time: str, last: str | None = None) -> KhNotificationSettings:
    row = session.execute(
        sa.select(KhNotificationSettings).where(KhNotificationSettings.user_id == user.user_id)
    ).scalar_one()
    row.evening_time, row.last_evening = time, last
    session.commit()
    return row


def test_a_late_evening_time_still_fires_once_just_after_midnight(
    api_client: TestClient, fake_push, unique_user: TestUser
):
    turn_on(api_client, unique_user)
    session = unique_user.repos.session
    evening_row(session, unique_user, "23:58")
    today = datetime.now(tzlocal()).replace(hour=0, minute=3, second=0, microsecond=0)
    session.add(
        GroupMealPlan(
            session=session,
            date=today.date(),
            entry_type="dinner",
            title="Pizza",
            text="",
            group_id=unique_user.group_id,
            user_id=unique_user.user_id,
        )
    )
    session.commit()
    assert tasks.send_due_evenings(session, today - timedelta(minutes=8)) == 0  # 23:55, not yet
    assert tasks.send_due_evenings(session, today) == 1  # 00:03 sees yesterday's 23:58, and "tomorrow" is today
    assert fake_push[0][1]["title"] == "Morgen: Pizza"
    assert tasks.send_due_evenings(session, today + timedelta(minutes=5)) == 0  # once
    evening_row(session, unique_user, "23:58", None)
    assert tasks.send_due_evenings(session, today.replace(minute=30)) == 0  # past the 10 minutes of grace
