#!/bin/sh
# KH: tests the logic of release.sh without git pushes, GitHub or Docker: version check,
# repo name from the remote URL, image names, CHANGELOG entry, list lookups and argument checks.
set -eu

here=$(cd "$(dirname "$0")" && pwd)
set -- --lib
. "$here/release.sh"

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
failures=0

# Reports a failed check without stopping, so all checks run.
check() {
  if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1: expected '$3', got '$2'"; failures=$((failures + 1)); fi
}

# Prints yes/no for a command's exit status.
yes_no() {
  if "$@" >/dev/null 2>&1; then echo yes; else echo no; fi
}

# --- versions: vMAJOR.MINOR, optional .PATCH and -rc.N ---
check "phase release is valid" "$(yes_no valid_version v0.1)" "yes"
check "patch release is valid" "$(yes_no valid_version v1.12.3)" "yes"
check "release candidate is valid" "$(yes_no valid_version v0.0-rc.1)" "yes"
check "missing v is invalid" "$(yes_no valid_version 0.1)" "no"
check "missing minor is invalid" "$(yes_no valid_version v0)" "no"
check "other suffix is invalid" "$(yes_no valid_version v0.1-beta)" "no"
check "shell characters are invalid" "$(yes_no valid_version 'v0.1;rm')" "no"
check "empty version is invalid" "$(yes_no valid_version '')" "no"

# --- repository name from the origin URL ---
check "https URL" "$(repo_slug https://github.com/gamingnet006/own-recipe-app.git)" "gamingnet006/own-recipe-app"
check "https URL without .git" "$(repo_slug https://github.com/gamingnet006/own-recipe-app)" "gamingnet006/own-recipe-app"
check "ssh URL in lower case" "$(repo_slug git@github.com:GamingNet006/Own-Recipe-App.git)" "gamingnet006/own-recipe-app"
check "non-GitHub URL is rejected" "$(repo_slug https://gitlab.com/a/b.git 2>/dev/null && echo ok || echo failed)" "failed"

# --- image names (CI pushes <version>-amd64 under the same name) ---
check "image name carries version and architecture" "$(image_ref gamingnet006/own-recipe-app v0.1 arm64)" "ghcr.io/gamingnet006/own-recipe-app:v0.1-arm64"

# --- CHANGELOG entry ---
changelog="$tmp/CHANGELOG.md"
printf '%s\n' '# Changelog' '' '## [v0.0-rc.10] - 2026-11-02' 'Mentions [v0.0-rc.2] in the text.' '' '## [v0.0-rc.1] - 2026-10-30' > "$changelog"
check "entry is found" "$(yes_no changelog_has v0.0-rc.1 "$changelog")" "yes"
check "missing CHANGELOG has no entry" "$(yes_no changelog_has v0.0-rc.1 "$tmp/none.md")" "no"
check "mention outside a heading does not count" "$(yes_no changelog_has v0.0-rc.2 "$changelog")" "no"
printf '%s\n' '## [v0.0-rc.10] - 2026-11-02' > "$tmp/only10.md"
check "rc.10 is not rc.1" "$(yes_no changelog_has v0.0-rc.1 "$tmp/only10.md")" "no"

# --- list lookups: token scopes (comma separated) and published tags (one per line) ---
check "scope is listed" "$(yes_no list_has 'admin:public_key, gist, repo, workflow, write:packages' write:packages)" "yes"
check "read scope is not write scope" "$(yes_no list_has 'read:packages, repo' write:packages)" "no"
check "empty list has nothing" "$(yes_no list_has '' write:packages)" "no"
tags=$(printf '%s\n' v0.0-rc.1-amd64 v0.0-rc.10-arm64)
check "published tag is found" "$(yes_no list_has "$tags" v0.0-rc.1-amd64)" "yes"
check "similar tag does not count" "$(yes_no list_has "$tags" v0.0-rc.1-arm64)" "no"

# --- argument checks (stop before touching git, GitHub or Docker) ---
check "no version is a usage error" "$(sh "$here/release.sh" >/dev/null 2>&1 && echo 0 || echo $?)" "2"
check "invalid version is a usage error" "$(sh "$here/release.sh" 'v1;x' >/dev/null 2>&1 && echo 0 || echo $?)" "2"

[ "$failures" -eq 0 ] && echo "all release tests passed" || { echo "$failures check(s) failed"; exit 1; }
