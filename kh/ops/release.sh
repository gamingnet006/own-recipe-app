#!/bin/sh
# KH: publishes a release (PLAN.md phase 1, D20). Sets the git tag; CI (kh-release.yml) then builds
# amd64 and arm64, tests them and pushes <version>-amd64, <version>-arm64 and the plain multi-arch
# <version>. This script checks everything first, verifies the three tags afterwards and creates the
# GitHub release with the CHANGELOG section as its notes.
# Usage: kh/ops/release.sh <version>, e.g. v0.1 or v0.1-rc.1
set -eu

CHANGELOG=docs/kh/CHANGELOG.md
CI_WORKFLOW=kh-ci.yml
RELEASE_WORKFLOW=kh-release.yml
CI_START_TIMEOUT=300
POLL_SECONDS=10

usage() {
  echo "Aufruf: kh/ops/release.sh <version>" >&2
  echo "Beispiel: kh/ops/release.sh v0.1 (Testlauf: v0.1-rc.1)" >&2
  exit 2
}

# Stops with a clear reason.
fail() {
  echo "Release abgebrochen: $1" >&2
  exit 1
}

# Accepts vMAJOR.MINOR with optional .PATCH and -rc.N; nothing else reaches git or docker.
valid_version() {
  case "$1" in ''|*[!A-Za-z0-9.-]*) return 1 ;; esac
  printf '%s\n' "$1" | grep -Eq '^v[0-9]+\.[0-9]+(\.[0-9]+)?(-rc\.[0-9]+)?$'
}

# Turns a GitHub remote URL into "owner/repo" in lower case (GHCR names must be lower case).
repo_slug() {
  slug=$(printf '%s\n' "$1" | sed -n -e 's#^https://github\.com/##p' -e 's#^git@github\.com:##p' \
    | sed -e 's#\.git$##' | tr 'A-Z' 'a-z')
  case "$slug" in ?*/?*) echo "$slug" ;; *) return 1 ;; esac
}

# Image name in GHCR: with an arch the single-architecture image, without it the multi-arch tag.
image_ref() {  # slug version [arch]
  echo "ghcr.io/$1:$2${3:+-$3}"
}

# True if the CHANGELOG has a heading "## [version]" for this release.
changelog_has() {  # version file
  grep -q "^## \[$(printf '%s' "$1" | sed 's/\./\\./g')\]" "$2" 2>/dev/null
}

# Prints the text of the CHANGELOG section of this version without its heading and outer blank lines:
# the notes of the GitHub release (the German "Kurz gesagt" first, then the English details).
changelog_section() {  # version file
  awk -v head="## [$1]" '
    index($0, "## [") == 1 { if (on) exit; on = (index($0, head) == 1); next }
    on { lines[++n] = $0 }
    END { a = 1; while (a <= n && lines[a] == "") a++; while (n >= a && lines[n] == "") n--; for (i = a; i <= n; i++) print lines[i] }
  ' "$2"
}

# Checks everything before the first change: tools, clean main in sync with GitHub, green CI,
# CHANGELOG entry, and a Docker to verify the published tags.
preflight() {
  for tool in git gh docker; do command -v "$tool" >/dev/null || fail "$tool ist nicht installiert"; done
  docker version >/dev/null 2>&1 || fail "Docker läuft nicht (colima start)"
  git fetch --quiet --tags origin main || fail "GitHub ist nicht erreichbar"
  [ "$(git rev-parse --abbrev-ref HEAD)" = main ] || fail "es ist nicht der Zweig main ausgecheckt"
  [ -z "$(git status --porcelain)" ] || fail "es gibt nicht eingecheckte Änderungen"
  HEAD_SHA=$(git rev-parse HEAD)
  [ "$HEAD_SHA" = "$(git rev-parse origin/main)" ] || fail "main ist nicht auf dem Stand von GitHub"
  SLUG=$(repo_slug "$(git remote get-url origin)") || fail "origin ist kein GitHub-Repo"
  # gh would otherwise pick the upstream remote, i.e. Mealie's repo, for its run queries.
  export GH_REPO="$SLUG"
  changelog_has "$VERSION" "$CHANGELOG" || fail "$CHANGELOG hat keinen Abschnitt \"## [$VERSION]\""
  TAG_SHA=$(git rev-parse -q --verify "refs/tags/$VERSION^{commit}" || true)
  [ -z "$TAG_SHA" ] || [ "$TAG_SHA" = "$HEAD_SHA" ] || fail "der Tag $VERSION zeigt auf einen anderen Stand"
  ci=$(gh run list --workflow "$CI_WORKFLOW" --commit "$HEAD_SHA" --json conclusion --jq '.[0].conclusion // empty' 2>/dev/null || true)
  [ "$ci" = success ] || fail "die CI für $(git rev-parse --short HEAD) ist nicht grün (${ci:-noch kein Ergebnis})"
}

# Waits for the release run of this tag in CI (builds, tests and pushes both images and the plain
# tag) and fails if it failed.
wait_for_ci() {
  run_id=""
  waited=0
  while [ -z "$run_id" ]; do
    run_id=$(gh run list --workflow "$RELEASE_WORKFLOW" --branch "$VERSION" --json databaseId \
      --jq '.[0].databaseId // empty' 2>/dev/null || true)
    [ -n "$run_id" ] && break
    [ "$waited" -lt "$CI_START_TIMEOUT" ] || fail "die CI hat den Release-Lauf nicht gestartet"
    sleep "$POLL_SECONDS"
    waited=$((waited + POLL_SECONDS))
  done
  gh run watch "$run_id" --exit-status --interval 30 >/dev/null 2>&1 \
    || fail "Build oder Upgrade-Test in der CI sind fehlgeschlagen, es wurde nichts veröffentlicht (Details: gh run view $run_id --log-failed)"
}

# Logs in to ghcr.io with the gh token for the checks (the package may be private); the token is
# never shown or kept.
ghcr_login() {
  gh auth token | docker login ghcr.io -u "${SLUG%%/*}" --password-stdin >/dev/null 2>&1 \
    || fail "die Anmeldung bei ghcr.io ist fehlgeschlagen"
  trap 'docker logout ghcr.io >/dev/null 2>&1' EXIT
}

# True if the registry has the image with both platforms (amd64 and arm64).
has_both_platforms() {  # image
  out=$(docker buildx imagetools inspect "$1" 2>/dev/null) || return 1
  printf '%s\n' "$out" | grep -q 'Platform: *linux/amd64' && printf '%s\n' "$out" | grep -q 'Platform: *linux/arm64'
}

main() {
  cd "$(dirname "$0")/../.."
  [ $# -eq 1 ] || usage
  valid_version "$1" || usage
  VERSION=$1
  preflight

  echo "1/4 Git-Tag $VERSION setzen und hochladen (startet den Release-Lauf in der CI)"
  if [ -z "$TAG_SHA" ]; then
    git tag -a "$VERSION" -m "Release $VERSION" && git push --quiet origin "$VERSION" \
      || fail "der Tag ließ sich nicht hochladen"
  else
    echo "Tag $VERSION gibt es schon für diesen Stand, setze fort."
  fi

  echo "2/4 Auf Build (amd64 und arm64) und Upgrade-Tests der CI warten (etwa 15 Minuten)"
  wait_for_ci

  echo "3/4 Veröffentlichte Tags prüfen"
  ghcr_login
  for arch in amd64 arm64; do
    docker buildx imagetools inspect "$(image_ref "$SLUG" "$VERSION" "$arch")" >/dev/null 2>&1 \
      || fail "in GHCR fehlt $(image_ref "$SLUG" "$VERSION" "$arch")"
  done
  has_both_platforms "$(image_ref "$SLUG" "$VERSION")" \
    || fail "$(image_ref "$SLUG" "$VERSION") fehlt oder enthält nicht beide Plattformen"
  echo "4/4 GitHub-Release mit den Neuerungen aus $CHANGELOG anlegen"
  if gh release view "$VERSION" >/dev/null 2>&1; then
    echo "GitHub-Release $VERSION gibt es schon."
  else
    case "$VERSION" in *-rc*) pre=--prerelease ;; *) pre="" ;; esac
    changelog_section "$VERSION" "$CHANGELOG" \
      | gh release create "$VERSION" --verify-tag --title "Kochheft $VERSION" --notes-file - $pre >/dev/null \
      || fail "das GitHub-Release ließ sich nicht anlegen (die Images sind veröffentlicht; von Hand: gh release create $VERSION)"
  fi
  echo "Release fertig:"
  echo "  $(image_ref "$SLUG" "$VERSION")  (für alle Geräte: Raspberry Pi, Mac, PC, Server)"
  echo "  $(image_ref "$SLUG" "$VERSION" arm64)  und  $(image_ref "$SLUG" "$VERSION" amd64)  (je Architektur, für bestehende Installationen)"
}

[ "${1:-}" = "--lib" ] || main "$@"
