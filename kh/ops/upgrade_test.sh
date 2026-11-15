#!/bin/sh
# KH: upgrade test (PLAN.md phase 1, D23). Installs the old image in a throwaway folder, adds the
# self-made test recipes and image, updates to the new image with update.sh and checks that recipes
# and image are unchanged. Usage: kh/ops/upgrade_test.sh <old-image> <new-image>
#   or (CI): kh/ops/upgrade_test.sh --previous-release <tag> <image-name> <new-image>
set -eu

TEST_PROJECT=kh-upgrade-test
TEST_PORT=${KH_TEST_PORT:-9191}

# Loads update.sh's helpers (valid_image, setting, set_env_value, wait_healthy, create_token).
# Loaded first, so the usage, fail and main defined below take precedence over update.sh's own.
load_update_helpers() {
  set -- --lib
  . "$(dirname "$0")/update.sh"
}
load_update_helpers

usage() {
  echo "Aufruf: kh/ops/upgrade_test.sh <altes-image> <neues-image>" >&2
  echo "   oder: kh/ops/upgrade_test.sh --previous-release <tag> <image-name> <neues-image>" >&2
  exit 2
}

# Stops the test with a clear reason; the throwaway install is removed on exit.
fail() {
  echo "Upgrade-Test FEHLGESCHLAGEN: $1" >&2
  exit 1
}

# Prints the tags that are older than the current one; the list comes newest first.
older_releases() {  # current_tag tags
  printf '%s\n' "$2" | awk -v current="$1" 'found && NF { print } $0 == current { found = 1 }'
}

# Content of one recipe (Mealie JSON on stdin) as one line; timestamps are left out.
recipe_fingerprint() {
  python3 -c '
import json, sys
r = json.load(sys.stdin)
parts = [r["name"], r.get("description") or "", str(r.get("recipeServings")),
         str(r.get("recipeYieldQuantity")), r.get("recipeYield") or "", r.get("image") or ""]
parts += [i.get("display") or i.get("note") or "" for i in r.get("recipeIngredient") or []]
parts += [s.get("text") or "" for s in r.get("recipeInstructions") or []]
print(" | ".join(parts))'
}

# Prints one field of a JSON object on stdin, or the whole value when no field is given.
json_field() {
  python3 -c 'import json, sys; v = json.load(sys.stdin); print(v[sys.argv[1]] if len(sys.argv) > 1 else v)' "$@"
}

# Copies this checkout's ops files into the throwaway folder, with its own .env and data folders.
prepare_install() {  # old_image
  mkdir -p "$WORK/ops/data" "$WORK/ops/backups"
  cp "$OPS/docker-compose.yml" "$OPS/update.sh" "$WORK/ops/"
  cp -R "$OPS/backup" "$WORK/ops/backup"
  printf '%s\n' "KH_IMAGE=$1" "KH_PORT=$TEST_PORT" "KH_DATA_DIR=./data" "KH_BACKUP_DIR=./backups" \
    "KH_PUID=$(id -u)" "KH_PGID=$(id -g)" "KH_BACKUP_API_TOKEN=" > "$WORK/ops/.env"
}

# Adds the self-made test recipes, gives the first one the test image and prints the slugs.
seed_recipes() {
  first=""
  for file in "$TESTDATA"/recipe-*.json; do
    payload=$(python3 -c 'import json, sys; print(json.dumps({"data": open(sys.argv[1], encoding="utf-8").read()}))' "$file")
    answer=$(curl -fsS -m 60 -X POST "$URL/api/recipes/create/html-or-json" -H "$AUTH" \
      -H "Content-Type: application/json" -d "$payload") || return 1
    slug=$(printf '%s' "$answer" | json_field) || return 1
    echo "$slug"
    [ -n "$first" ] || first=$slug
  done
  curl -fsS -m 30 -X PUT "$URL/api/recipes/$first/image" -H "$AUTH" \
    -F "image=@$TESTDATA/test-image.png" -F extension=png >/dev/null
}

# What must survive the update: the fingerprint of every test recipe and the image checksum.
data_state() {  # slugs
  for slug in $1; do
    recipe=$(curl -fsS -m 30 -H "$AUTH" "$URL/api/recipes/$slug") || return 1
    printf '%s' "$recipe" | recipe_fingerprint || return 1
  done
  first=$(printf '%s\n' "$1" | head -n 1)
  recipe=$(curl -fsS -m 30 -H "$AUTH" "$URL/api/recipes/$first") || return 1
  id=$(printf '%s' "$recipe" | json_field id) || return 1
  curl -fsS -m 30 -o "$WORK/image.webp" "$URL/api/media/recipes/$id/images/original.webp" || return 1
  python3 -c 'import hashlib, sys; print("image", hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest())' "$WORK/image.webp"
}

# Removes the throwaway install, its containers and its rollback image.
cleanup() {
  if [ -d "$WORK/ops" ]; then (cd "$WORK/ops" && docker compose down -v --remove-orphans >/dev/null 2>&1) || true; fi
  docker rmi "$TEST_PROJECT:rollback" >/dev/null 2>&1 || true
  rm -rf "$WORK" 2>/dev/null || true
}

# Runs one upgrade from old to new image in a throwaway install.
run_test() {  # old_image new_image
  image_id "$1" >/dev/null || docker pull "$1" >/dev/null 2>&1 || fail "das alte Image $1 ist nicht verfügbar"
  image_id "$2" >/dev/null || fail "das neue Image $2 ist nicht auf diesem Rechner"
  # Inside the checkout, not the system temp folder: Docker on the Mac (Colima) only mounts folders
  # below the home directory, so a /var/folders path would silently get an empty data folder.
  WORK=$(mktemp -d "$OPS/.upgrade-test.XXXXXX")
  trap cleanup EXIT
  export COMPOSE_PROJECT_NAME="$TEST_PROJECT"
  prepare_install "$1"
  cd "$WORK/ops"
  URL="http://localhost:$TEST_PORT"
  TIMEOUT=$(setting KH_UPDATE_TIMEOUT 600)

  echo "1/4 Alte Version starten: $1"
  docker compose up -d --no-build mealie >/dev/null 2>&1 || fail "die alte Version startet nicht"
  wait_healthy || fail "die alte Version wird nicht bereit"
  token=$(create_token "$URL" "$SETTINGS" kh-upgrade-test) || fail "auf der Testinstallation ließ sich kein API-Token anlegen"
  set_env_value .env KH_BACKUP_API_TOKEN "$token"
  AUTH="Authorization: Bearer $token"

  echo "2/4 Testrezepte und Testbild anlegen"
  slugs=$(seed_recipes) || fail "die Testrezepte ließen sich nicht anlegen"
  before=$(data_state "$slugs") || fail "die Daten vor dem Update sind nicht lesbar"
  docker compose build backup >/dev/null 2>&1 || fail "das Backup-Image ließ sich nicht bauen"

  echo "3/4 Update mit update.sh auf $2"
  ./update.sh "$2" || fail "update.sh hat das Update nicht geschafft"

  echo "4/4 Rezepte und Bild vergleichen"
  after=$(data_state "$slugs") || fail "die Daten nach dem Update sind nicht lesbar"
  if [ "$before" != "$after" ]; then
    printf 'Vorher:\n%s\nNachher:\n%s\n' "$before" "$after" >&2
    fail "Rezepte oder Bild haben sich beim Update verändert"
  fi
  [ -n "$(docker compose ps -q backup)" ] || fail "der Backup-Dienst läuft nach dem Update nicht"
  echo "Upgrade-Test bestanden: $1 -> $2 ($(printf '%s\n' "$slugs" | wc -l | tr -d ' ') Rezepte, Bild unverändert)"
}

# CI: tests the upgrade from the newest older release that has an image for this machine.
from_previous_release() {  # tag image_name new_image
  arch=$(docker version -f '{{.Server.Arch}}' 2>/dev/null) || fail "Docker läuft nicht"
  olders=$(older_releases "$1" "$(git -C "$REPO" tag --list 'v*' --sort=-creatordate)")
  if [ -z "$olders" ]; then
    echo "Erstes Release, es gibt nichts zum Vergleichen: der Upgrade-Test entfällt."
    return
  fi
  for older in $olders; do
    if docker pull "$2:$older-$arch" >/dev/null 2>&1; then
      run_test "$2:$older-$arch" "$3"
      return
    fi
    echo "Kein Image $older-$arch, versuche das nächstältere Release."
  done
  # an unreachable registry must not let a release through untested
  fail "kein Image eines früheren Releases ladbar ($olders): Registry oder Anmeldung prüfen"
}

main() {
  REPO=$(cd "$(dirname "$0")/../.." && pwd)
  OPS="$REPO/kh/ops"
  TESTDATA="$OPS/testdata"
  SETTINGS="$REPO/mealie/core/settings/settings.py"
  if [ "${1:-}" = --previous-release ]; then
    [ $# -eq 4 ] && valid_image "$2" && valid_image "$3" && valid_image "$4" || usage
    from_previous_release "$2" "$3" "$4"
  else
    [ $# -eq 2 ] && valid_image "$1" && valid_image "$2" || usage
    run_test "$1" "$2"
  fi
}

[ "${1:-}" = "--lib" ] || main "$@"
