#!/bin/sh
# KH: restores a backup from the second location through Mealie's API (D21).
# Without an argument it lists the available backups. Mealie only accepts a backup
# made with the same database version, so after a failed update start the old image first.
set -eu

set -- --lib "$@"
. /usr/local/bin/backup.sh
shift

if [ $# -eq 0 ]; then
  echo "Vorhandene Backups am zweiten Ort (neuestes zuerst):"
  ls -1t "$DEST"/*.zip 2>/dev/null | xargs -n 1 basename 2>/dev/null || echo "  keine"
  echo "Wiederherstellen: restore.sh <dateiname.zip>"
  exit 0
fi

name=$(basename "$1")
file="$DEST/$name"
[ -f "$file" ] || fail "Backup nicht gefunden: $name"
[ -n "${KH_BACKUP_API_TOKEN:-}" ] || fail "KH_BACKUP_API_TOKEN fehlt in kh/ops/.env"
unzip -tq "$file" >/dev/null || fail "Backup ist beschädigt: $name"

auth="Authorization: Bearer $KH_BACKUP_API_TOKEN"
curl -fsS -m "${KH_BACKUP_TIMEOUT:-300}" -X POST -H "$auth" -F "archive=@$file" "$API/api/admin/backups/upload" >/dev/null \
  || fail "Hochladen zu Mealie fehlgeschlagen"
curl -fsS -m "${KH_BACKUP_TIMEOUT:-300}" -X POST -H "$auth" "$API/api/admin/backups/$name/restore" >/dev/null \
  || fail "Mealie hat das Backup abgelehnt (andere Datenbank-Version?)"
echo "Wiederhergestellt: $name"
