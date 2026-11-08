"""KH: the bridge to kh/ops/auto_update.sh (P8.2): the app writes the checkbox into data/kh/auto_update.json and reads
the last run's line from data/kh/auto_update_status.txt. The script runs on the host, the app in the container; the
data folder is the only thing both see."""

import json
from pathlib import Path

ENABLED_FILE = "auto_update.json"
STATUS_FILE = "auto_update_status.txt"


def _kh_file(data_dir: Path, name: str) -> Path:
    return data_dir / "kh" / name


def read_enabled(data_dir: Path) -> bool | None:
    """The checkbox, or None when there is no (usable) file and the script falls back to .env."""
    try:
        enabled = json.loads(_kh_file(data_dir, ENABLED_FILE).read_text()).get("enabled")
    except OSError, ValueError, AttributeError:
        return None
    return enabled if isinstance(enabled, bool) else None


def write_enabled(data_dir: Path, enabled: bool) -> None:
    """Stores the checkbox where auto_update.sh reads it before KH_AUTO_UPDATE from .env."""
    file = _kh_file(data_dir, ENABLED_FILE)
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps({"enabled": enabled}) + "\n")


def read_status(data_dir: Path) -> str | None:
    """The last run's line "date | up|down | message | version", or None before the first run."""
    try:
        return _kh_file(data_dir, STATUS_FILE).read_text().strip() or None
    except OSError:
        return None


def parse_status(line: str) -> tuple[str, bool]:
    """Turns a status line into the text to show ("date message (version)") and whether the run went well."""
    date, result, message, version = ([*line.split(" | ", 3), "", "", ""])[:4]
    text = f"{date} {message}".strip()
    return (f"{text} ({version})" if version else text), result != "down"
