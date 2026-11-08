"""KH: tests for the About page (P8.1), the auto-update checkbox (P8.2) and the system check (P8.3): the pure
check functions, the files that bridge host scripts and container, and the admin-only routes."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mealie.kh.features.settings import get_kh_settings
from mealie.kh.system import auto_update, checks
from tests.utils.fixture_schemas import TestUser

GB = 1024**3
MB = 1024**2
NOW = datetime(2026, 11, 8, 12, 0, tzinfo=UTC)


@pytest.mark.parametrize(
    "image, version",
    [
        (None, "dev"),
        ("kuechenhelfer:dev", "dev"),
        ("ghcr.io/gamingnet006/own-recipe-app:v0.4-amd64", "v0.4"),
        ("ghcr.io/x/y:v0.5.1-rc.2-arm64", "v0.5.1-rc.2"),
        ("127.0.0.1:5000/x/y:v1.0-amd64", "v1.0"),
        ("registry.example.com:5000/x/y", "dev"),
    ],
)
def test_version_comes_from_the_image_tag(image: str | None, version: str):
    assert checks.kh_version(image) == version


@pytest.mark.parametrize(
    "free, state",
    [(50 * GB, "ok"), (2 * GB, "ok"), (2 * GB - 1, "warn"), (500 * MB, "warn"), (500 * MB - 1, "bad")],
)
def test_disk_light(free: int, state: str):
    assert checks.disk_check(free).state == state


def test_disk_value_is_gigabytes():
    assert checks.disk_check(int(12.34 * GB)).value == "12.3 GB"


@pytest.mark.parametrize(
    "age, state",
    [(timedelta(hours=5), "ok"), (timedelta(days=2), "ok"), (timedelta(days=2, minutes=1), "warn"),
     (timedelta(days=7), "warn"), (timedelta(days=7, minutes=1), "bad")],
)  # fmt: skip
def test_backup_light(age: timedelta, state: str):
    check = checks.backup_check(NOW - age, NOW)
    assert (check.state, check.value) == (state, (NOW - age).date().isoformat())


def test_no_backup_is_red():
    assert checks.backup_check(None, NOW) == checks.Check(key="backup", state="bad", value="")


def test_simple_lights():
    assert checks.ai_check(2) == checks.Check(key="ai", state="ok", value="2")
    assert checks.ai_check(0).state == "warn"
    assert checks.signup_check(False).state == "ok"
    assert checks.signup_check(True).state == "bad"
    assert checks.default_account_check(False).state == "ok"
    assert checks.default_account_check(True).state == "bad"
    assert checks.nutrition_check(7140) == checks.Check(key="nutrition", state="ok", value="7140")
    assert checks.nutrition_check(0).state == "bad"
    assert checks.database_check("sqlite") == checks.Check(key="database", state="info", value="sqlite")
    assert checks.module_check("telegram", True) == checks.Check(key="telegram", state="info", value="on")
    assert checks.module_check("whisper", False) == checks.Check(key="whisper", state="info", value="off")


def test_auto_update_light():
    assert checks.auto_update_check(None, None).state == "info"
    assert checks.auto_update_check(False, None).state == "warn"
    assert checks.auto_update_check(True, None).state == "ok"
    line = "2026-11-08 04:00 | up | Aktuell (v0.4), nichts zu tun | v0.4-amd64"
    assert checks.auto_update_check(True, line) == checks.Check(
        key="autoUpdate", state="ok", value="2026-11-08 04:00 Aktuell (v0.4), nichts zu tun (v0.4-amd64)"
    )
    failed = "2026-11-08 04:00 | down | Update auf v0.5 fehlgeschlagen | v0.4-amd64"
    assert checks.auto_update_check(True, failed).state == "bad"


def test_check_list_never_shows_secret_values(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setattr(get_kh_settings(), "telegram_token", "secret-token")
    monkeypatch.setattr(get_kh_settings(), "whisper_url", "http://secret-host:9000")
    listed = checks.module_checks(get_kh_settings())
    assert [(c.key, c.value) for c in listed] == [("telegram", "on"), ("whisper", "on")]
    assert "secret" not in str(listed)


def test_enabled_file_round_trip(tmp_path: Path):
    assert auto_update.read_enabled(tmp_path) is None
    auto_update.write_enabled(tmp_path, False)
    assert auto_update.read_enabled(tmp_path) is False
    auto_update.write_enabled(tmp_path, True)
    assert auto_update.read_enabled(tmp_path) is True
    assert (tmp_path / "kh" / "auto_update.json").read_text().strip() == '{"enabled": true}'


@pytest.mark.parametrize("content", ["", "not json", '{"enabled": "yes"}', "[]", '{"other": 1}'])
def test_broken_enabled_file_counts_as_missing(tmp_path: Path, content: str):
    (tmp_path / "kh").mkdir()
    (tmp_path / "kh" / "auto_update.json").write_text(content)
    assert auto_update.read_enabled(tmp_path) is None


def test_status_file(tmp_path: Path):
    assert auto_update.read_status(tmp_path) is None
    (tmp_path / "kh").mkdir()
    (tmp_path / "kh" / "auto_update_status.txt").write_text("2026-11-08 04:00 | up | ok | v0.4\n")
    assert auto_update.read_status(tmp_path) == "2026-11-08 04:00 | up | ok | v0.4"


ABOUT = "/api/kh/about"
AUTO_UPDATE = "/api/kh/admin/auto-update"
SYSTEM = "/api/kh/admin/system"


@pytest.fixture
def data_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Points the routes at an empty data folder."""
    monkeypatch.setattr("mealie.kh.system.routes.data_dir", lambda: tmp_path)
    return tmp_path


def test_about_names_version_and_notices(api_client: TestClient, unique_user: TestUser, monkeypatch, tmp_path: Path):
    notices = tmp_path / "notices.md"
    notices.write_text("# Third-party notices\n")
    settings = get_kh_settings()
    monkeypatch.setattr(settings, "notices_file", notices)
    monkeypatch.setattr(settings, "image", "ghcr.io/x/y:v0.4-arm64")
    answer = api_client.get(ABOUT, headers=unique_user.token).json()
    assert answer == {"version": "v0.4", "notices": "# Third-party notices\n"}


def test_about_without_notices_file_is_empty(api_client: TestClient, unique_user: TestUser, monkeypatch, tmp_path):
    monkeypatch.setattr(get_kh_settings(), "notices_file", tmp_path / "missing.md")
    assert api_client.get(ABOUT, headers=unique_user.token).json()["notices"] == ""


def test_about_needs_a_login(api_client: TestClient):
    assert api_client.get(ABOUT).status_code == 401


def test_features_name_the_source_url(api_client: TestClient):
    assert api_client.get("/api/kh/features").json()["sourceUrl"] == get_kh_settings().source_url


def test_auto_update_route_reads_and_writes(api_client: TestClient, admin_token, data_dir: Path):
    assert api_client.get(AUTO_UPDATE, headers=admin_token).json() == {"enabled": None, "status": None}
    assert api_client.put(AUTO_UPDATE, json={"enabled": False}, headers=admin_token).json()["enabled"] is False
    assert auto_update.read_enabled(data_dir) is False
    (data_dir / "kh" / "auto_update_status.txt").write_text("2026-11-08 04:00 | up | ok | v0.4\n")
    assert api_client.get(AUTO_UPDATE, headers=admin_token).json() == {
        "enabled": False,
        "status": "2026-11-08 04:00 ok (v0.4)",
    }


def test_auto_update_route_is_for_admins(api_client: TestClient, unique_user: TestUser, data_dir: Path):
    assert api_client.get(AUTO_UPDATE, headers=unique_user.token).status_code == 403
    assert api_client.put(AUTO_UPDATE, json={"enabled": True}, headers=unique_user.token).status_code == 403
    assert auto_update.read_enabled(data_dir) is None


def test_system_route_lists_every_row(api_client: TestClient, admin_token, data_dir: Path):
    rows = api_client.get(SYSTEM, headers=admin_token).json()
    assert [row["key"] for row in rows] == [
        "version", "database", "disk", "backup", "ai", "signup", "defaultAccount", "autoUpdate", "nutrition",
        "telegram", "whisper",
    ]  # fmt: skip
    assert {row["state"] for row in rows} <= {"ok", "warn", "bad", "info"}
    by_key = {row["key"]: row for row in rows}
    assert by_key["backup"]["state"] == "bad"  # the empty test data folder has no backup
    assert by_key["defaultAccount"]["state"] in {"ok", "bad"}


def test_system_route_is_for_admins(api_client: TestClient, unique_user: TestUser):
    assert api_client.get(SYSTEM, headers=unique_user.token).status_code == 403
