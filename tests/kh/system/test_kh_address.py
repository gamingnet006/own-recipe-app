"""KH: tests for the address change detection (D85): the pure compare, the stored file, the system-check row, the
features field and the push message. No real push is sent."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from mealie.core.config import get_app_dirs
from mealie.kh.notifications import tasks
from mealie.kh.system import address, checks
from tests.kh.notifications.test_kh_notifications import fake_push, turn_on  # noqa: F401
from tests.utils.fixture_schemas import TestUser

NOW = datetime(2026, 11, 1, tzinfo=UTC)
OLD, NEW = "https://kochbuch.example.org", "https://kochen.example.com"


def test_first_real_address_is_stored_without_a_change():
    assert address.next_state(None, OLD + "/", NOW) == address.AddressState(current=OLD)


@pytest.mark.parametrize("url", ["http://localhost:8080", "http://localhost:9091", "http://127.0.0.1:9000"])
def test_a_placeholder_address_is_not_set(url: str):
    stored = address.AddressState(current=OLD)
    assert address.next_state(None, url, NOW) is None
    assert address.next_state(stored, url, NOW) == stored


def test_a_different_address_is_a_change_and_the_same_one_is_not():
    stored = address.AddressState(current=OLD)
    assert address.next_state(stored, OLD, NOW) == stored
    changed = address.next_state(stored, NEW, NOW)
    assert changed == address.AddressState(current=NEW, previous=OLD, changed_at=NOW.isoformat())


def test_a_change_is_recent_for_60_days():
    state = address.AddressState(current=NEW, previous=OLD, changed_at=NOW.isoformat())
    assert address.recent_change(state, NOW + timedelta(days=59))
    assert not address.recent_change(state, NOW + timedelta(days=61))
    assert not address.recent_change(address.AddressState(current=OLD), NOW)


def test_the_state_is_stored_and_a_broken_file_counts_as_nothing(tmp_path):
    assert address.read_state(tmp_path) is None
    address.refresh(tmp_path, OLD)
    address.refresh(tmp_path, NEW)
    state = address.read_state(tmp_path)
    assert state and (state.current, state.previous) == (NEW, OLD) and state.changed_at
    (tmp_path / "kh" / "address.json").write_text("not json")
    assert address.read_state(tmp_path) is None


def test_the_check_row_warns_for_a_recent_change_and_else_only_hints():
    state = address.AddressState(current=NEW, previous=OLD, changed_at=NOW.isoformat())
    assert checks.address_check(state, NOW) == checks.Check("address", "warn", f"{NEW} {OLD}")
    assert checks.address_check(state, NOW + timedelta(days=61)).state == "info"
    assert checks.address_check(None, NOW).state == "info"


def test_a_change_is_pushed_once(api_client: TestClient, fake_push, unique_user: TestUser, monkeypatch):  # noqa: F811
    folder = get_app_dirs().DATA_DIR
    path = folder / "kh" / "address.json"
    path.unlink(missing_ok=True)
    turn_on(api_client, unique_user, news=True)
    session = unique_user.repos.session
    monkeypatch.setattr(tasks, "get_app_settings", lambda: SimpleNamespace(BASE_URL=OLD))
    assert tasks.send_address_change_once(session) == 0  # first start: stored only
    monkeypatch.setattr(tasks, "get_app_settings", lambda: SimpleNamespace(BASE_URL=NEW))
    assert tasks.send_address_change_once(session) == 1
    assert tasks.send_address_change_once(session) == 0
    assert fake_push[0][1]["title"] == "Kochheft hat eine neue Adresse"
    assert api_client.get("/api/kh/features").json()["addressChangedAt"]
    path.unlink()
