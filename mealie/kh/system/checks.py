"""KH: the traffic lights of the system check (P8.3). Every check is a pure function of plain values, so each rule
x"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

from mealie.kh.features.settings import KhSettings
from mealie.kh.system.auto_update import parse_status

State = Literal["ok", "warn", "bad", "info"]

GB = 1024**3
DISK_WARN_BYTES = 2 * GB
DISK_BAD_BYTES = 500 * 1024**2
BACKUP_WARN_DAYS = 2
BACKUP_BAD_DAYS = 7


@dataclass(frozen=True)
class Check:
    """One row: what is checked (key), its light and a detail the row shows."""

    key: str
    state: State
    value: str


def kh_version(image: str | None) -> str:
    """The release the running image stands for: its tag without the architecture, "dev" for a local build."""
    tag = (image or "").rpartition(":")[2]
    if "/" in tag or not tag.startswith("v"):  # no tag at all, or the colon belonged to a registry port
        return "dev"
    return tag.removesuffix("-amd64").removesuffix("-arm64")


def version_check(image: str | None) -> Check:
    return Check("version", "info", kh_version(image))


def database_check(engine: str) -> Check:
    return Check("database", "info", engine)


def disk_check(free_bytes: int) -> Check:
    """Free space in the data folder: yellow under 2 GB, red under 500 MB."""
    state: State = "bad" if free_bytes < DISK_BAD_BYTES else "warn" if free_bytes < DISK_WARN_BYTES else "ok"
    return Check("disk", state, f"{free_bytes / GB:.1f} GB")


def backup_check(newest: datetime | None, now: datetime) -> Check:
    """The newest Mealie backup: yellow older than 2 days, red older than 7 days or none at all."""
    if newest is None:
        return Check("backup", "bad", "")
    age = now - newest
    state: State = (
        "bad" if age > timedelta(days=BACKUP_BAD_DAYS) else "warn" if age > timedelta(days=BACKUP_WARN_DAYS) else "ok"
    )
    return Check("backup", state, newest.date().isoformat())


def ai_check(providers: int) -> Check:
    return Check("ai", "ok" if providers else "warn", str(providers))


def signup_check(allowed: bool) -> Check:
    """Self-registration must stay off (D22); on is red."""
    return Check("signup", "bad" if allowed else "ok", "on" if allowed else "off")


def default_account_check(in_use: bool) -> Check:
    """Mealie's well-known first account must be gone; still there is red."""
    return Check("defaultAccount", "bad" if in_use else "ok", "")


def auto_update_check(enabled: bool | None, status_line: str | None) -> Check:
    """The checkbox (None: only .env knows) with the last run; a failed run is red."""
    text, went_well = parse_status(status_line) if status_line else ("", True)
    if not went_well:
        return Check("autoUpdate", "bad", text)
    state: State = "info" if enabled is None else "ok" if enabled else "warn"
    return Check("autoUpdate", state, text)


def nutrition_check(rows: int) -> Check:
    return Check("nutrition", "ok" if rows else "bad", str(rows))


def module_check(key: str, present: bool) -> Check:
    """An optional module is on when its setting is set; its value is never shown."""
    return Check(key, "info", "on" if present else "off")


def module_checks(settings: KhSettings) -> list[Check]:
    return [
        module_check("telegram", bool(settings.telegram_token)),
        module_check("whisper", bool(settings.whisper_url)),
    ]
