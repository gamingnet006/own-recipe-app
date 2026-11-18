#!/bin/sh
# KH: tests the host-side parts of update.sh without Docker: reading and editing .env,
# reading the recipe total, the database snapshot and its restore, the exit code of an abort
# and argument checks.
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
check "set_env_value keeps & | and backslash (v1.1)" "$(set_env_value "$ENV_FILE" KH_BACKUP_COPY_DIR /alt && set_env_value "$ENV_FILE" KH_BACKUP_COPY_DIR '/Volumes/R&D | Stick\a' && env_value "$ENV_FILE" KH_BACKUP_COPY_DIR)" '/Volumes/R&D | Stick\a'
check "set_env_value fails on a missing .env" "$(set_env_value "$tmp/missing.env" KH_IMAGE x:1 2>/dev/null && echo ok || echo failed)" "failed"
# Some editors save without a final newline; appending must not glue the new key to the last line.
printf 'KH_A=1\nKH_LAST=placeholder' > "$tmp/nonl.env"
(set_env_value "$tmp/nonl.env" KH_NEW yes)  # subshell: set_env_value uses a global $tmp
check "append keeps a last line without newline" "$(env_value "$tmp/nonl.env" KH_LAST)" "placeholder"
check "append after a last line without newline" "$(env_value "$tmp/nonl.env" KH_NEW)" "yes"

check "setting prefers the shell environment" "$(export KH_PORT=7777; setting KH_PORT 9091)" "7777"
check "setting falls back to .env" "$(setting KH_PORT 9091)" "9092"
check "setting falls back to the default" "$(setting KH_MISSING dflt)" "dflt"
check "setting treats an empty value as unset" "$(setting KH_EMPTY dflt)" "dflt"

# --- recipe total from Mealie's paginated answer ---
check "recipe_total reads total" "$(recipe_total '{"page":1,"per_page":1,"total":7,"total_pages":7,"items":[]}')" "7"
check "recipe_total ignores total_pages" "$(recipe_total '{"total_pages":3,"total":0}')" "0"
check "recipe_total of an error answer is empty" "$(recipe_total '{"detail":"Not authenticated"}')" ""

# --- json_string: string fields of Mealie's login and API token answers (create_token needs no python3) ---
check "json_string reads access_token" "$(json_string access_token '{"access_token":"eyJ.a.b","token_type":"bearer"}')" "eyJ.a.b"
check "json_string reads token" "$(json_string token '{"name":"kh-backup","id":3,"token":"eyJ.c.d","createdAt":"2026-10-31"}')" "eyJ.c.d"
check "json_string token is not access_token or token_type" "$(json_string token '{"access_token":"eyJ.a.b","token_type":"bearer"}')" ""
check "json_string with space after colon" "$(json_string token '{"token": "eyJ.e.f"}')" "eyJ.e.f"
check "json_string of a missing field is empty" "$(json_string token '{"detail":"Unauthorized"}')" ""

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

# --- an abort before any change exits 4, so auto_update.sh tries the same version again ---
# A copy without .env stops in the preflight, with or without Docker on this machine.
mkdir "$tmp/install" && cp "$here/update.sh" "$tmp/install/"
check "an abort before any change exits 4" "$(sh "$tmp/install/update.sh" example/image:v1 >/dev/null 2>&1 && echo 0 || echo $?)" "4"

# --- a signal after the switch rolls back (the old version must not stay down), a clean finish disarms it ---
check "a TERM after arming runs the rollback with both values" "$(sh -c 'set -- --lib; . "$0"; roll_back() { echo "rollback $1 $2"; exit 1; }; arm_rollback_trap sha256:old 7; kill -TERM $$; sleep 1' "$here/update.sh")" "rollback sha256:old 7"
check "disarming removes the traps" "$(sh -c 'set -- --lib; . "$0"; arm_rollback_trap a 1; disarm_rollback_trap; trap' "$here/update.sh")" ""

# --- old images after a successful update: all of the repository except the new and the rollback one (v1.2.1) ---
list='ghcr.io/x/app:v1.2 sha256:new
ghcr.io/x/app:v1.1 sha256:old
ghcr.io/x/app:v1.0 sha256:older
ghcr.io/x/app:<none> sha256:dangling'
check "stale_images lists only images that are neither kept nor untagged" "$(echo "$list" | stale_images sha256:new sha256:old)" "ghcr.io/x/app:v1.0"
check "stale_images keeps everything that is kept" "$(echo "$list" | stale_images sha256:new sha256:old sha256:older)" ""
check "image_repo strips the tag" "$(image_repo ghcr.io/x/app:v1.2)" "ghcr.io/x/app"
check "image_repo keeps a registry port" "$(image_repo localhost:5000/app:v1)" "localhost:5000/app"
check "image_repo of a name without tag is empty" "$(image_repo localhost:5000/app)" ""

# --- free space of Docker's disk from df -Pk, checked before an update (v1.2.1) ---
df_out='Filesystem     1024-blocks     Used Available Capacity Mounted on
overlay           30830592 19504128   9646080      67% /'
check "free_gb reads the available whole gigabytes" "$(echo "$df_out" | free_gb)" "9"
check "free_gb of a full disk is 0" "$(printf 'Filesystem 1024-blocks Used Available Capacity Mounted on\noverlay 30830592 30830592 0 100%% /\n' | free_gb)" "0"
check "free_gb of no answer is empty" "$(echo "" | free_gb)" ""

# --- argument checks (stop before touching Docker) ---
check "no image is a usage error" "$(sh "$here/update.sh" >/dev/null 2>&1 && echo 0 || echo $?)" "2"
check "an invalid image name is a usage error" "$(sh "$here/update.sh" 'bad|image' >/dev/null 2>&1 && echo 0 || echo $?)" "2"
check "two images are a usage error" "$(sh "$here/update.sh" a:1 b:2 >/dev/null 2>&1 && echo 0 || echo $?)" "2"

[ "$failures" -eq 0 ] && echo "all update tests passed" || { echo "$failures check(s) failed"; exit 1; }
