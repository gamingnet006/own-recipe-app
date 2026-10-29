#!/bin/sh
# KH: daily backup through Mealie's own backup API (D21). Mealie writes the zip
# into its data folder; this script checks it, copies it to the second location,
# prunes old copies and reports to Uptime Kuma. `backup.sh --lib` only loads functions.
set -eu

SRC=/backups-src    # Mealie's data/backups folder
DEST=/backups-dest  # second storage location
API="${KH_MEALIE_URL:-http://mealie:9000}"

# Sends status up/down to the Uptime Kuma push URL, if one is configured.
push() {
  [ -n "${KH_BACKUP_PUSH_URL:-}" ] || return 0
  curl -fsS -m 10 -G "$KH_BACKUP_PUSH_URL" --data-urlencode "status=$1" --data-urlencode "msg=$2" >/dev/null \
    || echo "Warnung: Meldung an Uptime Kuma fehlgeschlagen" >&2
}

# Reports an error clearly (log and Uptime Kuma) and stops.
fail() {
  echo "Backup FEHLER: $1" >&2
  push down "$1"
  exit 1
}

# Prints the newest zip file in a folder, or nothing if there is none.
newest_zip() {
  ls -1t "$1"/*.zip 2>/dev/null | head -n 1
}

# Keeps the newest N zip files in a folder and deletes the older ones.
prune() {
  ls -1t "$1"/*.zip 2>/dev/null | tail -n +"$(($2 + 1))" | while read -r old; do
    rm -f "$old"
  done
}

# Asks Mealie to write a new backup zip into its data folder.
create_backup() {
  curl -fsS -m "${KH_BACKUP_TIMEOUT:-300}" -X POST \
    -H "Authorization: Bearer $KH_BACKUP_API_TOKEN" "$API/api/admin/backups" >/dev/null
}

main() {
  [ -n "${KH_BACKUP_API_TOKEN:-}" ] || fail "KH_BACKUP_API_TOKEN fehlt in kh/ops/.env"
  before=$(newest_zip "$SRC")
  create_backup || fail "Mealie hat kein Backup erstellt (läuft Mealie, stimmt der Token?)"
  created=$(newest_zip "$SRC")
  [ -n "$created" ] && [ "$created" != "$before" ] || fail "Kein neues Backup in $SRC gefunden"
  unzip -tq "$created" >/dev/null || fail "Backup ist beschädigt: $(basename "$created")"
  copy="$DEST/$(basename "$created")"
  cp "$created" "$copy" || fail "Kopie an den zweiten Ort fehlgeschlagen"
  unzip -tq "$copy" >/dev/null || fail "Kopie am zweiten Ort ist beschädigt"
  chown "${KH_PUID:-1000}:${KH_PGID:-1000}" "$copy" 2>/dev/null || true  # readable for the host user
  prune "$DEST" "${KH_BACKUP_KEEP:-14}"
  prune "$SRC" "${KH_BACKUP_KEEP_LOCAL:-3}"
  echo "Backup OK: $(basename "$created")"
  push up "OK $(basename "$created")"
}

[ "${1:-}" = "--lib" ] || main
