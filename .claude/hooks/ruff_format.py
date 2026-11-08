"""KH: Claude Code hook (PostToolUse on Edit/Write) that runs ruff format on an edited Python or Markdown file,
with the ruff version from uv.lock, so the CI's `ruff format . --check` (it also reads code blocks in Markdown)
stays green."""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

SUFFIXES = {".py", ".md"}


def ruff_version(root: Path) -> str | None:
    """The ruff version pinned in uv.lock, or None when it is not found."""
    lock = root / "uv.lock"
    match = re.search(r'name = "ruff"\nversion = "([^"]+)"', lock.read_text()) if lock.exists() else None
    return match.group(1) if match else None


def main() -> int:
    """Formats the edited file; exits 2 with ruff's message when ruff fails (e.g. a syntax error)."""
    data = json.load(sys.stdin)
    file_path = (data.get("tool_input") or {}).get("file_path") or ""
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd())
    path = Path(file_path)
    if path.suffix not in SUFFIXES or not path.is_file() or root not in path.resolve().parents:
        return 0
    version = ruff_version(root)
    ruff = f"ruff@{version}" if version else "ruff"
    result = subprocess.run(["uvx", ruff, "format", str(path)], cwd=root, capture_output=True, text=True)
    if result.returncode != 0:
        sys.stderr.write(f"ruff format failed for {path}:\n{result.stderr or result.stdout}\n")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
