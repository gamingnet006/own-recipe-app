#!/bin/sh
# KH: tests the host-side parts of update.sh without Docker: reading and editing .env,
# reading the recipe total, the database snapshot and its restore, and argument checks.
set -eu

here=$(cd "$(dirname "$0")" && pwd)
set -- --lib
. "$here/update.sh"

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
failures=0

# Reports a failed check without stopping, so all checks run.
check() {
  if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1: expected '$3', got '$2'"; failures=$((failures + 1)); fi
}

# --- .env reading and editing ---
ENV_FILE="$tmp/.env"
printf '%s\n' 'KH_IMAGE=old:1' 'KH_BACKUP_CRON=30 3 * * *' 'KH_QUOTED="with space"' 'KH_EMPTY=' > "$ENV_FILE"
chmod 600 "$ENV_FILE"

check "env_value reads a value" "$(env_value "$ENV_FILE" KH_IMAGE)" "old:1"
check "env_value keeps spaces and stars" "$(env_value "$ENV_FILE" KH_BACKUP_CRON)" "30 3 * * *"
check "env_value strips quotes" "$(env_value "$ENV_FILE" KH_QUOTED)" "with space"
check "env_value of a missing key is empty" "$(env_value "$ENV_FILE" KH_MISSING)" ""

check "set_env_value replaces a line" "$(set_env_value "$ENV_FILE" KH_IMAGE ghcr.io/x/y:v0.1 && env_value "$ENV_FILE" KH_IMAGE)" "ghcr.io/x/y:v0.1"
check "set_env_value leaves one line per key" "$(grep -c '^KH_IMAGE=' "$ENV_FILE")" "1"
check "set_env_value keeps other lines" "$(env_value "$ENV_FILE" KH_BACKUP_CRON)" "30 3 * * *"
check "set_env_value appends a missing key" "$(set_env_value "$ENV_FILE" KH_PORT 9092 && env_value "$ENV_FILE" KH_PORT)" "9092"
check "set_env_value keeps the file private" "$(ls -l "$ENV_FILE" | cut -c1-10)" "-rw-------"
check "set_env_value fails on a missing .env" "$(set_env_value "$tmp/missing.env" KH_IMAGE x:1 2>/dev/null && echo ok || echo failed)" "failed"

check "setting prefers the shell environment" "$(export KH_PORT=7777; setting KH_PORT 9091)" "7777"
check "setting falls back to .env" "$(setting KH_PORT 9091)" "9092"
check "setting falls back to the default" "$(setting KH_MISSING dflt)" "dflt"
check "setting treats an empty value as unset" "$(setting KH_EMPTY dflt)" "dflt"

# --- recipe total from Mealie's paginated answer ---
check "recipe_total reads total" "$(recipe_total '{"page":1,"per_page":1,"total":7,"total_pages":7,"items":[]}')" "7"
check "recipe_total ignores total_pages" "$(recipe_total '{"total_pages":3,"total":0}')" "0"
check "recipe_total of an error answer is empty" "$(recipe_total '{"detail":"Not authenticated"}')" ""

# --- database snapshot and restore ---
data="$tmp/data"
snap="$tmp/data.pre-update"
mkdir -p "$data"
check "snapshot fails without a database" "$(snapshot_db "$data" "$snap" 2>/dev/null && echo ok || echo failed)" "failed"
touch "$tmp/a-file"
echo v0 > "$data/mealie.db"
check "snapshot fails when its folder cannot be created" "$(snapshot_db "$data" "$tmp/a-file/snap" 2>/dev/null && echo ok || echo failed)" "failed"

echo v1 > "$data/mealie.db"
echo wal1 > "$data/mealie.db-wal"
mkdir -p "$snap"
echo stale > "$snap/mealie.db-shm"
check "snapshot copies the database" "$(snapshot_db "$data" "$snap" && cat "$snap/mealie.db")" "v1"
check "snapshot copies the journal" "$(cat "$snap/mealie.db-wal")" "wal1"
check "snapshot drops files of an older snapshot" "$([ -e "$snap/mealie.db-shm" ] && echo present || echo gone)" "gone"

echo v2-migrated > "$data/mealie.db"
rm "$data/mealie.db-wal"
echo shm2 > "$data/mealie.db-shm"
check "restore brings the old database back" "$(restore_db "$snap" "$data" && cat "$data/mealie.db")" "v1"
check "restore brings the old journal back" "$(cat "$data/mealie.db-wal")" "wal1"
check "restore removes journal files of the new version" "$([ -e "$data/mealie.db-shm" ] && echo present || echo gone)" "gone"
check "restore fails without a snapshot" "$(restore_db "$tmp/nothing" "$data" 2>/dev/null && echo ok || echo failed)" "failed"
check "failed restore leaves the data alone" "$(cat "$data/mealie.db")" "v1"
check "restore fails when the data folder is unusable" "$(restore_db "$snap" "$tmp/a-file/data" 2>/dev/null && echo ok || echo failed)" "failed"

# --- rollback image name: one per compose project, so a test install never touches the real one ---
check "rollback tag of the default project" "$(env -u COMPOSE_PROJECT_NAME sh -c 'set -- --lib; . "$0"; echo "$ROLLBACK_TAG"' "$here/update.sh")" "kuechenhelfer:rollback"
check "rollback tag follows COMPOSE_PROJECT_NAME" "$(COMPOSE_PROJECT_NAME=kh-upgrade-test sh -c 'set -- --lib; . "$0"; echo "$ROLLBACK_TAG"' "$here/update.sh")" "kh-upgrade-test:rollback"

# --- argument checks (stop before touching Docker) ---
check "no image is a usage error" "$(sh "$here/update.sh" >/dev/null 2>&1 && echo 0 || echo $?)" "2"
check "an invalid image name is a usage error" "$(sh "$here/update.sh" 'bad|image' >/dev/null 2>&1 && echo 0 || echo $?)" "2"
check "two images are a usage error" "$(sh "$here/update.sh" a:1 b:2 >/dev/null 2>&1 && echo 0 || echo $?)" "2"

[ "$failures" -eq 0 ] && echo "all update tests passed" || { echo "$failures check(s) failed"; exit 1; }
