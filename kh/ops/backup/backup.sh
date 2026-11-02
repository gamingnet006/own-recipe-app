#!/bin/sh
# KH: daily backup through Mealie's own backup API (D21). Mealie writes the zip
# into its data folder; this script checks it, copies it to the second location with the
# restore guide, prunes old copies and reports to Uptime Kuma. `backup.sh --lib` only loads functions.
set -eu

SRC=/backups-src    # Mealie's data/backups folder
DEST=/backups-dest  # second storage location
GUIDE_DIR=/usr/local/share/kuechenhelfer  # the restore guide inside the backup image
# The restore guide for people and for Claude, as file here:name next to the backups. Claude's part has another
# name in the repo, so Claude Code working on the repo never takes it for its own instructions.
GUIDE_FILES="LIESMICH.txt:LIESMICH.txt restore-guide-claude.md:CLAUDE.md"
API="${KH_MEALIE_URL:-http://mealie:9000}"

# Sends status up/down to the Uptime Kuma push URL, if one is configured. A query pasted along
# with the URL is dropped: with a second status, Uptime Kuma would count every report as down.
push() {
  [ -n "${KH_BACKUP_PUSH_URL:-}" ] || return 0
  curl -fsS -m 10 -G "${KH_BACKUP_PUSH_URL%%\?*}" --data-urlencode "status=$1" --data-urlencode "msg=$2" >/dev/null \
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

# Keeps the newest N files ending in EXT (default zip) in a folder and deletes the older ones.
prune() {  # folder n [ext]
  ls -1t "$1"/*."${3:-zip}" 2>/dev/null | tail -n +"$(($2 + 1))" | while read -r old; do
    rm -f "$old"
  done
}

# Puts the restore guide next to the backups in FOLDER, or renews it there when it changed, so
# whoever finds the backups later knows how to get the recipes back.
put_guide() {  # folder guide_dir
  for pair in $GUIDE_FILES; do
    from="$2/${pair%%:*}" to="$1/${pair#*:}"
    cmp -s "$from" "$to" || cp "$from" "$to" || return 1
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
  # a missing guide never costs the backup, it only warns
  put_guide "$DEST" "$GUIDE_DIR" || echo "Warnung: Anleitung zum Wiederherstellen nicht abgelegt" >&2
  prune "$DEST" "${KH_BACKUP_KEEP:-14}"
  prune "$SRC" "${KH_BACKUP_KEEP_LOCAL:-3}"
  echo "Backup OK: $(basename "$created")"
  push up "OK $(basename "$created")"
}

[ "${1:-}" = "--lib" ] || main
