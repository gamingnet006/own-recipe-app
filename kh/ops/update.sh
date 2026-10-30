#!/bin/sh
# KH: updates Küchenhelfer to another image (PLAN.md phase 1, D21): Mealie backup, then a file
# snapshot of the stopped database, switch and checks; on failure the old image and database return.
# Usage: ./update.sh <image>. Exit codes: 0 updated or already current, 1 failed and nothing lost
# (old version running), 2 usage error, 3 rollback failed (manual steps are printed).
set -eu

ENV_FILE=.env
# One rollback image per compose project, so a test install never replaces the real one.
ROLLBACK_TAG="${COMPOSE_PROJECT_NAME:-kuechenhelfer}:rollback"
DB_FILES="mealie.db mealie.db-wal mealie.db-shm"
POLL_SECONDS=3

usage() {
  echo "Aufruf: ./update.sh <image>" >&2
  echo "Beispiel: ./update.sh ghcr.io/gamingnet006/own-recipe-app:v0.1" >&2
  exit 2
}

# Stops before the running installation was changed.
abort() {
  echo "Update abgebrochen: $1. Die laufende Version ist unverändert." >&2
  exit 1
}

# The automatic rollback failed: says where everything for a manual restore lies.
rollback_failed() {
  echo "FEHLER: $1" >&2
  echo "Manuell wiederherstellen, im Ordner $(pwd):" >&2
  echo "  Datenbank vor dem Update: $SNAP (Dateien bei gestopptem Mealie nach $DATA kopieren)" >&2
  echo "  Einstellungen vorher:     $ENV_FILE.pre-update" >&2
  echo "  Altes Image:              $ROLLBACK_TAG" >&2
  echo "  Mealie-Backups:           $(setting KH_BACKUP_DIR ./backups)" >&2
  exit 3
}

# True for a plain image name; nothing else reaches docker or the .env file.
valid_image() {
  case "$1" in ''|*[!A-Za-z0-9._/:@-]*) return 1 ;; esac
}

# Reads one default login field of a fresh Mealie from its settings source (used by upgrade_test.sh
# and tunnel.sh, which load these helpers).
default_login() {  # field settings_file
  sed -n "s/.*$1: str = \"\(.*\)\".*/\1/p" "$2" 2>/dev/null | head -n 1
}

# Prints the value of a key from an env file (last occurrence, surrounding quotes removed).
env_value() {
  sed -n "s/^$2=//p" "$1" | tail -n 1 | sed -e 's/^"\(.*\)"$/\1/' -e "s/^'\(.*\)'$/\1/"
}

# Sets KEY=VALUE in an env file in place, so the file keeps its permissions (it holds the token).
# Every step reports failure: callers run it in `||` lists, where `set -e` does not apply.
# VALUE must not contain '|' or '&'; image names never do.
set_env_value() {
  tmp="$1.tmp"
  if grep -q "^$2=" "$1" 2>/dev/null; then
    sed "s|^$2=.*|$2=$3|" "$1" > "$tmp" || { rm -f "$tmp"; return 1; }
  else
    { cat "$1" && printf '%s=%s\n' "$2" "$3"; } > "$tmp" || { rm -f "$tmp"; return 1; }
  fi
  cat "$tmp" > "$1" && rm -f "$tmp"
}

# Reads a setting the way docker compose does: shell environment first, then .env, then default.
setting() {
  val=$(printenv "$1" || true)
  [ -n "$val" ] || val=$(env_value "$ENV_FILE" "$1")
  echo "${val:-$2}"
}

# Extracts "total" from Mealie's paginated JSON answer (empty if it is missing).
recipe_total() {
  printf '%s' "$1" | sed -n 's/.*"total":[[:space:]]*\([0-9][0-9]*\).*/\1/p'
}

# Copies the SQLite files of the stopped app into a fresh snapshot folder.
# Returns failure on any error: callers use `if !`, where `set -e` does not apply.
snapshot_db() {  # data_dir snapshot_dir
  [ -f "$1/mealie.db" ] || { echo "Datenbank fehlt: $1/mealie.db" >&2; return 1; }
  rm -rf "$2" && mkdir -p "$2" || return 1
  for f in $DB_FILES; do
    if [ -f "$1/$f" ]; then cp -p "$1/$f" "$2/" || return 1; fi
  done
}

# Puts the snapshot back and removes journal files the new version left behind.
restore_db() {  # snapshot_dir data_dir
  [ -f "$1/mealie.db" ] || { echo "Schnappschuss fehlt: $1/mealie.db" >&2; return 1; }
  for f in $DB_FILES; do
    rm -f "$2/$f" || return 1
    if [ -f "$1/$f" ]; then cp -p "$1/$f" "$2/" || return 1; fi
  done
}

# Container ID of the mealie service, also while it is restarting.
container_id() {
  docker compose ps -a -q mealie 2>/dev/null
}

# Image ID behind an image name; fails if the image is not on this machine.
image_id() {
  docker image inspect -f '{{.Id}}' "$1" 2>/dev/null
}

# Image ID the mealie container was created from.
running_image_id() {
  docker inspect -f '{{.Image}}' "$(container_id)" 2>/dev/null
}

# Health status of the mealie container (healthy, starting, unhealthy or empty).
health_status() {
  docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{end}}' "$(container_id)" 2>/dev/null || true
}

# Starts mealie from the given image and never builds: heavy builds do not run on the Pi.
start_mealie() {
  KH_IMAGE="$1" docker compose up -d --no-build mealie
}

# Waits until mealie is healthy; stops early when it reports unhealthy or crashes.
wait_healthy() {
  waited=0
  while [ "$waited" -lt "$TIMEOUT" ]; do
    state=$(docker inspect -f '{{.State.Status}} {{.RestartCount}}' "$(container_id)" 2>/dev/null || true)
    case "$(health_status)" in
      healthy) return 0 ;;
      unhealthy) echo "Mealie meldet sich als nicht gesund" >&2; return 1 ;;
    esac
    case "$state" in
      exited*|dead*|*" "[1-9]*) echo "Mealie stürzt beim Start ab" >&2; return 1 ;;
    esac
    sleep "$POLL_SECONDS"
    waited=$((waited + POLL_SECONDS))
  done
  echo "Mealie ist nach $TIMEOUT Sekunden nicht bereit" >&2
  return 1
}

# Counts the recipes visible to the admin token; fewer after the switch means data was lost.
count_recipes() {
  json=$(curl -fsS -m 30 -H "Authorization: Bearer $TOKEN" "$URL/api/recipes?page=1&perPage=1") || return 1
  total=$(recipe_total "$json")
  [ -n "$total" ] && echo "$total"
}

# Checks the switched installation: the new image runs and no recipe is missing.
verify_switch() {  # new_id recipes_before
  [ "$(running_image_id)" = "$1" ] || { echo "Es läuft nicht das neue Image" >&2; return 1; }
  after=$(count_recipes) || { echo "Rezepte sind nach dem Wechsel nicht abrufbar" >&2; return 1; }
  [ "$after" -ge "$2" ] || { echo "Nach dem Wechsel fehlen Rezepte ($after statt $2)" >&2; return 1; }
}

# Starts the old image again. If its name now points to another image (rebuilt locally),
# .env is pinned to the rollback tag so later starts do not pick up the failed version.
start_old() {  # old_id
  [ "$(image_id "$OLD_REF")" = "$1" ] || set_env_value "$ENV_FILE" KH_IMAGE "$ROLLBACK_TAG" || return 1
  start_mealie "$(setting KH_IMAGE kuechenhelfer:dev)" >/dev/null 2>&1 && wait_healthy
}

# Brings back the old image and the database snapshot after a failed switch, then exits 1.
roll_back() {  # old_id recipes_before
  echo "Update fehlgeschlagen. Letzte Meldungen der neuen Version:" >&2
  docker compose logs --tail 15 mealie >&2 2>/dev/null || true
  echo "Stelle die alte Version wieder her …" >&2
  docker compose stop mealie >/dev/null 2>&1 || true
  restore_db "$SNAP" "$DATA" || rollback_failed "Datenbank-Schnappschuss ließ sich nicht zurückspielen"
  cp "$ENV_FILE.pre-update" "$ENV_FILE" || rollback_failed "Einstellungen ließen sich nicht zurückspielen"
  start_old "$1" || rollback_failed "Die alte Version startet nicht"
  after=$(count_recipes) || rollback_failed "Die alte Version liefert keine Rezepte"
  [ "$after" -eq "$2" ] || echo "Warnung: $after Rezepte statt $2 wie vor dem Update" >&2
  echo "Die alte Version läuft wieder, die Daten sind wie vor dem Update." >&2
  exit 1
}

# Reads all settings and checks the running installation before anything changes.
preflight() {
  docker compose version >/dev/null 2>&1 || abort "docker compose ist nicht installiert"
  [ -f "$ENV_FILE" ] || abort "$(pwd)/$ENV_FILE fehlt (Vorlage: .env.example)"
  TOKEN=$(setting KH_BACKUP_API_TOKEN "")
  [ -n "$TOKEN" ] || abort "KH_BACKUP_API_TOKEN fehlt in .env"
  URL="http://localhost:$(setting KH_PORT 9091)"
  DATA=$(setting KH_DATA_DIR ./data)
  SNAP="${DATA%/}.pre-update"
  TIMEOUT=$(setting KH_UPDATE_TIMEOUT 600)
  case "$TIMEOUT" in ''|*[!0-9]*) abort "KH_UPDATE_TIMEOUT muss eine Zahl (Sekunden) sein" ;; esac
  OLD_REF=$(setting KH_IMAGE kuechenhelfer:dev)
  old_id=$(running_image_id) || abort "der Küchenhelfer läuft nicht, bitte zuerst starten"
  [ "$(health_status)" = healthy ] || abort "der Küchenhelfer ist gerade nicht bereit"
}

main() {
  cd "$(dirname "$0")"
  [ $# -eq 1 ] || usage
  valid_image "$1" || usage
  new_ref=$1
  preflight

  echo "1/4 Neue Version holen: $new_ref"
  if ! docker pull "$new_ref" 2>/dev/null; then
    image_id "$new_ref" >/dev/null || abort "das Image $new_ref gibt es weder in der Registry noch hier"
    echo "Nicht in der Registry, nehme das Image von diesem Rechner."
  fi
  new_id=$(image_id "$new_ref")
  [ "$new_id" != "$old_id" ] || { echo "Läuft bereits mit dieser Version, nichts zu tun."; exit 0; }
  before=$(count_recipes) || abort "die Rezepte sind nicht abrufbar (stimmt KH_BACKUP_API_TOKEN?)"

  echo "2/4 Backup über Mealie"
  # --no-deps: otherwise compose recreates mealie whenever .env names another image than the running one.
  docker compose run --rm --no-deps backup backup.sh || abort "das Backup ist fehlgeschlagen"

  echo "3/4 Datenbank-Schnappschuss bei gestopptem Mealie"
  docker tag "$old_id" "$ROLLBACK_TAG" || abort "das alte Image ließ sich nicht sichern"
  docker compose stop mealie >/dev/null || abort "Mealie ließ sich nicht stoppen"
  rm -f "$ENV_FILE.pre-update"
  if ! { snapshot_db "$DATA" "$SNAP" && cp "$ENV_FILE" "$ENV_FILE.pre-update" \
    && set_env_value "$ENV_FILE" KH_IMAGE "$new_ref"; }; then
    [ ! -f "$ENV_FILE.pre-update" ] || cp "$ENV_FILE.pre-update" "$ENV_FILE"
    start_old "$old_id" || rollback_failed "Die alte Version startet nach dem Schnappschuss nicht"
    abort "Schnappschuss oder Einstellungen ließen sich nicht schreiben"
  fi

  echo "4/4 Neue Version starten und prüfen (höchstens $TIMEOUT Sekunden)"
  if start_mealie "$new_ref" && wait_healthy && verify_switch "$new_id" "$before"; then
    echo "Update fertig: $new_ref läuft, alle $before Rezepte sind da."
    echo "Für den Notfall bleiben bis zum nächsten Update: $SNAP und das Image $ROLLBACK_TAG"
    exit 0
  fi
  roll_back "$old_id" "$before"
}

[ "${1:-}" = "--lib" ] || main "$@"
