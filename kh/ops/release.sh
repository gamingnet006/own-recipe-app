#!/bin/sh
# KH: publishes a release (PLAN.md phase 1, D20). Builds the arm64 image on this Mac from the
# committed source, sets the git tag (CI builds amd64, kh-release.yml) and pushes arm64, so GHCR
# holds <version>-amd64 and <version>-arm64. Usage: kh/ops/release.sh <version>, e.g. v0.1 or v0.1-rc.1
set -eu

DOCKERFILE=docker/Dockerfile
TARGET=production
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

# Image name in GHCR for one architecture; CI pushes amd64 under the same scheme.
image_ref() {  # slug version arch
  echo "ghcr.io/$1:$2-$3"
}

# True if the CHANGELOG has a heading "## [version]" for this release.
changelog_has() {  # version file
  grep -q "^## \[$(printf '%s' "$1" | sed 's/\./\\./g')\]" "$2" 2>/dev/null
}

# True if a list (comma separated like GitHub's scope header, or one item per line) has the item.
list_has() {  # list item
  printf '%s\n' "$1" | tr ',' '\n' | sed 's/^ *//; s/ *$//' | grep -Fqx "$2"
}

# Checks everything before the first change: tools, clean main in sync with GitHub, green CI,
# CHANGELOG entry, token scope and an Apple Silicon Docker for the arm64 build.
preflight() {
  for tool in git gh docker; do command -v "$tool" >/dev/null || fail "$tool ist nicht installiert"; done
  [ "$(docker version -f '{{.Server.Arch}}' 2>/dev/null)" = arm64 ] \
    || fail "Docker läuft nicht oder nicht auf arm64 (colima start; der arm64-Build braucht Apple Silicon)"
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
  scopes=$(gh api -i /user 2>/dev/null | tr -d '\r' | sed -n 's/^[Xx]-[Oo][Aa]uth-[Ss]copes: //p')
  list_has "$scopes" write:packages \
    || fail "dem GitHub-Login fehlt write:packages (gh auth refresh -h github.com -s write:packages)"
}

# Builds the arm64 image from exactly the committed source, so no local file can end up in it.
build_arm64() {  # image log
  git archive --format=tar HEAD | docker build -f "$DOCKERFILE" --target "$TARGET" \
    --build-arg COMMIT="$HEAD_SHA" \
    --label org.opencontainers.image.source="https://github.com/$SLUG" \
    --label org.opencontainers.image.version="$VERSION" -t "$1" - > "$2" 2>&1
}

# Waits for the release run of this tag in CI (it pushes the amd64 image) and fails if it failed.
# arm64 is pushed only afterwards, so the first push of a new package always comes from CI.
wait_for_ci() {
  run_id=""
  waited=0
  while [ -z "$run_id" ]; do
    run_id=$(gh run list --workflow "$RELEASE_WORKFLOW" --branch "$VERSION" --json databaseId \
      --jq '.[0].databaseId // empty' 2>/dev/null || true)
    [ -n "$run_id" ] && break
    [ "$waited" -lt "$CI_START_TIMEOUT" ] || fail "die CI hat den amd64-Build nicht gestartet"
    sleep "$POLL_SECONDS"
    waited=$((waited + POLL_SECONDS))
  done
  gh run watch "$run_id" --exit-status --interval 30 >/dev/null 2>&1 \
    || fail "der amd64-Build in der CI ist fehlgeschlagen (Details: gh run view $run_id --log-failed)"
}

# Pushes the arm64 image with the gh token for this one push; the token is never shown or kept.
push_arm64() {  # image log
  gh auth token | docker login ghcr.io -u "${SLUG%%/*}" --password-stdin >/dev/null 2>&1 \
    || fail "die Anmeldung bei ghcr.io ist fehlgeschlagen"
  trap 'docker logout ghcr.io >/dev/null 2>&1' EXIT
  docker push "$1" >> "$2" 2>&1
}

# Tags of the app package in GHCR, one per line.
published_tags() {
  gh api "/user/packages/container/${SLUG#*/}/versions" --paginate \
    --jq '.[].metadata.container.tags[]' 2>/dev/null
}

main() {
  cd "$(dirname "$0")/../.."
  [ $# -eq 1 ] || usage
  valid_version "$1" || usage
  VERSION=$1
  preflight
  arm64=$(image_ref "$SLUG" "$VERSION" arm64)
  log=$(mktemp)

  echo "1/4 arm64-Image auf diesem Mac bauen (etwa 6 Minuten, noch wird nichts veröffentlicht)"
  build_arm64 "$arm64" "$log" || fail "der arm64-Build ist fehlgeschlagen (Protokoll: $log)"

  echo "2/4 Git-Tag $VERSION setzen und hochladen (startet den amd64-Build in der CI)"
  if [ -z "$TAG_SHA" ]; then
    git tag -a "$VERSION" -m "Release $VERSION" && git push --quiet origin "$VERSION" \
      || fail "der Tag ließ sich nicht hochladen"
  else
    echo "Tag $VERSION gibt es schon für diesen Stand, setze fort."
  fi

  echo "3/4 Auf den amd64-Build der CI warten (etwa 10 Minuten)"
  wait_for_ci

  echo "4/4 arm64-Image hochladen und prüfen"
  push_arm64 "$arm64" "$log" || fail "das Hochladen ist fehlgeschlagen (Protokoll: $log)"
  tags=$(published_tags) || fail "die veröffentlichten Tags sind nicht abrufbar"
  for arch in amd64 arm64; do
    list_has "$tags" "$VERSION-$arch" || fail "in GHCR fehlt $(image_ref "$SLUG" "$VERSION" "$arch")"
  done
  rm -f "$log"
  echo "Release fertig:"
  echo "  $(image_ref "$SLUG" "$VERSION" arm64)  (Raspberry Pi, Mac mit Apple Silicon)"
  echo "  $(image_ref "$SLUG" "$VERSION" amd64)  (PC und Server mit Intel/AMD)"
}

[ "${1:-}" = "--lib" ] || main "$@"
