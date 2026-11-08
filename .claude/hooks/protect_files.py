"""KH: Claude Code hook (PreToolUse on Edit/Write) that blocks edits CLAUDE.md forbids: secrets in .env,
the generated TypeScript types, and every locale file except en-US (managed by Crowdin)."""

import json
import os
import sys
from pathlib import PurePosixPath

GENERATED = "frontend/app/lib/api/types/"
LOCALES = "frontend/app/lang/messages/"


def reason(path: str) -> str | None:
    """Why PATH (relative to the repo) must not be edited, or None when it may be."""
    name = PurePosixPath(path).name
    if name == ".env" or (name.startswith(".env.") and name != ".env.example"):
        return "secrets live only in .env, never written by Claude; use placeholders in .env.example"
    if path.startswith(GENERATED):
        return "generated from the Pydantic schemas; run the generator (task dev:generate) instead"
    if path.startswith(LOCALES) and name != "en-US.json":
        return "other locales are managed by Crowdin; only en-US.json may change"
    return None


def main() -> int:
    """Reads the hook input and exits 2 with the reason when the edit is forbidden."""
    data = json.load(sys.stdin)
    file_path = (data.get("tool_input") or {}).get("file_path") or ""
    root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    path = os.path.relpath(os.path.abspath(file_path), root).replace(os.sep, "/") if file_path else ""
    if path and (why := reason(path)):
        print(f"Blocked edit of {path}: {why}.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
