#!/bin/sh
# KH: restore test (PLAN.md phase 1, D21). Restores a backup with restore.sh into a throwaway install
# that runs the same image as this one, then checks that every recipe and file of the backup is back.
# Usage: kh/ops/restore_test.sh [backup.zip]   (without an argument: the newest backup)
set -eu

# Loads the helpers of upgrade_test.sh (prepare_install, cleanup, and update.sh's setting,
# wait_healthy, image_id, create_token) and backup.sh (newest_zip). Loaded first, so the usage, fail and
# main defined below take precedence.
load_helpers() {
  set -- --lib
  . "$(dirname "$0")/upgrade_test.sh"
  . "$(dirname "$0")/backup/backup.sh"
}
load_helpers
TEST_PROJECT=kh-restore-test

usage() {
  echo "Aufruf: kh/ops/restore_test.sh [backup.zip]" >&2
  exit 2
}

# Stops the test with a clear reason; the throwaway install is removed on exit.
fail() {
  echo "Restore-Test FEHLGESCHLAGEN: $1" >&2
  exit 1
}

# Absolute path of a file, so it stays valid after changing the folder.
abs_path() {
  echo "$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
}

# Slugs of the recipes in a Mealie backup, sorted, one per line; fails without database.json.
backup_recipes() {  # zip
  python3 -c '
import json, sys, zipfile
tables = json.loads(zipfile.ZipFile(sys.argv[1]).read("database.json"))
print("\n".join(sorted(r["slug"] for r in tables["recipes"])))' "$1"
}

# Slugs of the recipes in a restored database, sorted, one per line; opened read-only.
restored_recipes() {  # mealie.db
  python3 -c '
import pathlib, sqlite3, sys
db = sqlite3.connect(pathlib.Path(sys.argv[1]).absolute().as_uri() + "?mode=ro", uri=True)
print("\n".join(sorted(slug for (slug,) in db.execute("select slug from recipes"))))' "$1"
}

# Files from the folders of the backup's data folder (recipe images, avatars) that are missing in a
# data folder. Mealie restores those folders completely, but of the loose files only .secret.
missing_files() {  # zip data_dir
  python3 -c '
import os, sys, zipfile
names = zipfile.ZipFile(sys.argv[1]).namelist()
files = [n[len("data/"):] for n in names if n.startswith("data/") and not n.endswith("/")]
files = [f for f in files if "/" in f]
print("\n".join(f for f in files if not os.path.isfile(os.path.join(sys.argv[2], f))))' "$1" "$2"
}

# Restores the backup into a throwaway install and compares recipes and files with the backup.
run_test() {  # zip image
  image_id "$2" >/dev/null || fail "das Image $2 ist nicht auf diesem Rechner"
  expected=$(backup_recipes "$1") || fail "$(basename "$1") ist kein lesbares Mealie-Backup"
  # Inside the ops folder, not the system temp folder: Colima only mounts folders below the home directory.
  WORK=$(mktemp -d "$OPS/.restore-test.XXXXXX")
  trap cleanup EXIT
  export COMPOSE_PROJECT_NAME="$TEST_PROJECT"
  prepare_install "$2"
  cp "$1" "$WORK/ops/backups/"
  cd "$WORK/ops"
  URL="http://localhost:$TEST_PORT"
  TIMEOUT=$(setting KH_UPDATE_TIMEOUT 600)

  echo "1/3 Wegwerf-Installation starten: $2"
  docker compose up -d --no-build mealie >/dev/null 2>&1 || fail "die Wegwerf-Installation startet nicht"
  wait_healthy || fail "die Wegwerf-Installation wird nicht bereit"
  token=$(create_token "$URL" "$SETTINGS" kh-restore-test) || fail "auf der Wegwerf-Installation ließ sich kein API-Token anlegen"
  set_env_value .env KH_BACKUP_API_TOKEN "$token" || fail "der API-Token ließ sich nicht eintragen"

  echo "2/3 Backup mit restore.sh einspielen: $(basename "$1")"
  out=$(docker compose run --rm --no-deps backup restore.sh "$(basename "$1")" 2>&1) \
    || fail "restore.sh hat das Backup nicht eingespielt: $(printf '%s\n' "$out" | tail -n 1)"

  echo "3/3 Rezepte und Dateien vergleichen"
  actual=$(restored_recipes data/mealie.db) || fail "die wiederhergestellte Datenbank ist nicht lesbar"
  [ "$expected" = "$actual" ] || fail "die Rezepte nach dem Restore weichen vom Backup ab"
  missing=$(missing_files "$1" data) || fail "die wiederhergestellten Dateien sind nicht lesbar"
  [ -z "$missing" ] || fail "nach dem Restore fehlen Dateien, z. B. $(printf '%s\n' "$missing" | head -n 1)"
  echo "Restore-Test bestanden: $(basename "$1"), Rezepte: $(printf '%s\n' "$expected" | sed '/^$/d' | wc -l | tr -d ' '), alle Dateien da"
}

main() {
  [ $# -le 1 ] || usage
  OPS=$(cd "$(dirname "$0")" && pwd)
  SETTINGS="$(cd "$OPS/../.." && pwd)/mealie/core/settings/settings.py"
  if [ $# -eq 1 ]; then
    [ -f "$1" ] || fail "Backup nicht gefunden: $1"
    zip=$(abs_path "$1")
  fi
  cd "$OPS"
  if [ $# -eq 0 ]; then
    zip=$(newest_zip "$(setting KH_BACKUP_DIR ./backups)")
    [ -n "$zip" ] || fail "kein Backup in $(setting KH_BACKUP_DIR ./backups) gefunden"
    zip=$(abs_path "$zip")
  fi
  image=$(setting KH_IMAGE "")
  [ -n "$image" ] || fail "KH_IMAGE fehlt in kh/ops/.env"
  run_test "$zip" "$image"
}

[ "${1:-}" = "--lib" ] || main "$@"
