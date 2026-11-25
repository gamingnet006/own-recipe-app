#!/bin/sh
# KH: tests the logic of release.sh without git pushes, GitHub or Docker: version check,
# repo name from the remote URL, image names, CHANGELOG entry and argument checks.
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

# --- image names (CI pushes <version>-amd64, <version>-arm64 and the plain multi-arch <version>) ---
check "image name carries version and architecture" "$(image_ref gamingnet006/own-recipe-app v0.1 arm64)" "ghcr.io/gamingnet006/own-recipe-app:v0.1-arm64"
check "image name without architecture is the multi-arch tag" "$(image_ref gamingnet006/own-recipe-app v0.1)" "ghcr.io/gamingnet006/own-recipe-app:v0.1"

# --- multi-arch check, with a fake docker that prints $FAKE_INSPECT ---
mkdir -p "$tmp/bin"
printf '%s\n' '#!/bin/sh' 'printf "%s\n" "$FAKE_INSPECT"' > "$tmp/bin/docker"
chmod +x "$tmp/bin/docker"
both=$(printf '%s\n' 'Manifests:' '  Platform:    linux/amd64' '  Platform:    linux/arm64')
check "both platforms are found" "$(PATH="$tmp/bin:$PATH" FAKE_INSPECT="$both" yes_no has_both_platforms x)" "yes"
check "one platform is not enough" "$(PATH="$tmp/bin:$PATH" FAKE_INSPECT='  Platform:    linux/amd64' yes_no has_both_platforms x)" "no"

# --- CHANGELOG entry ---
changelog="$tmp/CHANGELOG.md"
printf '%s\n' '# Changelog' '' '## [v0.0-rc.10] - 2026-11-02' 'Mentions [v0.0-rc.2] in the text.' '' '## [v0.0-rc.1] - 2026-10-30' > "$changelog"
check "entry is found" "$(yes_no changelog_has v0.0-rc.1 "$changelog")" "yes"
check "missing CHANGELOG has no entry" "$(yes_no changelog_has v0.0-rc.1 "$tmp/none.md")" "no"
check "mention outside a heading does not count" "$(yes_no changelog_has v0.0-rc.2 "$changelog")" "no"
printf '%s\n' '## [v0.0-rc.10] - 2026-11-02' > "$tmp/only10.md"
check "rc.10 is not rc.1" "$(yes_no changelog_has v0.0-rc.1 "$tmp/only10.md")" "no"
printf '%s\n' '## [v0.2] - 2026-11-03' '' '**Kurz gesagt:**' '- Neu' '' '- New' '' '## [v0.1] - 2026-11-01' '- Old' > "$tmp/notes.md"
check "release notes are the section body" "$(changelog_section v0.2 "$tmp/notes.md")" "$(printf '%s\n' '**Kurz gesagt:**' '- Neu' '' '- New')"
check "release notes of the last section" "$(changelog_section v0.1 "$tmp/notes.md")" "- Old"

# --- argument checks (stop before touching git, GitHub or Docker) ---
check "no version is a usage error" "$(sh "$here/release.sh" >/dev/null 2>&1 && echo 0 || echo $?)" "2"
check "invalid version is a usage error" "$(sh "$here/release.sh" 'v1;x' >/dev/null 2>&1 && echo 0 || echo $?)" "2"

[ "$failures" -eq 0 ] && echo "all release tests passed" || { echo "$failures check(s) failed"; exit 1; }
