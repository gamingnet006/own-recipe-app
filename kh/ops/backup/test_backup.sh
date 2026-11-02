#!/bin/sh
# KH: tests the backup helpers without Docker or Mealie: pruning keeps the newest
# files, newest_zip finds the latest one, an empty folder is handled, and the restore guide
# lands next to the backups.
set -eu

here=$(cd "$(dirname "$0")" && pwd)
set -- --lib
. "$here/backup.sh"

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
failures=0

# Reports a failed check without stopping, so all checks run.
check() {
  if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1: expected '$3', got '$2'"; failures=$((failures + 1)); fi
}

check "newest_zip on empty folder" "$(newest_zip "$tmp")" ""

for day in 01 02 03 04 05; do
  touch -t "202601${day}0000" "$tmp/mealie_v3_2026.01.$day.zip"
done
touch "$tmp/notes.txt"

check "newest_zip picks latest" "$(basename "$(newest_zip "$tmp")")" "mealie_v3_2026.01.05.zip"

prune "$tmp" 2
check "prune keeps 2 newest" "$(ls "$tmp"/*.zip | xargs -n 1 basename | sort | tr '\n' ' ')" "mealie_v3_2026.01.04.zip mealie_v3_2026.01.05.zip "
check "prune leaves other files" "$(ls "$tmp"/notes.txt >/dev/null && echo yes)" "yes"

prune "$tmp" 5
check "prune with fewer files than limit" "$(ls "$tmp"/*.zip | wc -l | tr -d ' ')" "2"

# the encrypted copies on a removable drive (backup_copy.sh) end in .zip.age
for day in 01 02 03; do touch -t "202601${day}0000" "$tmp/mealie_v3_2026.01.$day.zip.age"; done
prune "$tmp" 1 zip.age
check "prune by extension" "$(ls "$tmp"/*.zip.age | xargs -n 1 basename | tr '\n' ' ')" "mealie_v3_2026.01.03.zip.age "
check "prune by extension leaves zips" "$(ls "$tmp"/*.zip | wc -l | tr -d ' ')" "2"

# push: Uptime Kuma shows its push URL with an example query; pasted as is, it must not reach curl
mkdir "$tmp/bin"
printf '%s\n' '#!/bin/sh' 'printf "%s\n" "$@" > "$CURL_ARGS"' > "$tmp/bin/curl"
chmod +x "$tmp/bin/curl"
(PATH="$tmp/bin:$PATH" CURL_ARGS="$tmp/curl_args" KH_BACKUP_PUSH_URL="http://kuma:3001/api/push/abc?status=up&msg=OK&ping=" push down "kaputt")
check "push drops a pasted query" "$(grep '^http' "$tmp/curl_args")" "http://kuma:3001/api/push/abc"
check "push sends the real status" "$(grep -c '^status=down$' "$tmp/curl_args")" "1"

# the restore guide for people and for Claude lies next to the backups and is renewed when it changed
mkdir "$tmp/guide" "$tmp/dest"
printf 'neu\n' > "$tmp/guide/LIESMICH.txt"; printf 'claude\n' > "$tmp/guide/restore-guide-claude.md"
printf 'alt\n' > "$tmp/dest/LIESMICH.txt"
put_guide "$tmp/dest" "$tmp/guide"
check "guide renewed" "$(cat "$tmp/dest/LIESMICH.txt")" "neu"
check "guide for Claude" "$(cat "$tmp/dest/CLAUDE.md")" "claude"
check "missing guide reported" "$(put_guide "$tmp/dest" "$tmp/none" 2>/dev/null && echo yes || echo no)" "no"
# the real guide names both ways to the zip and the restore command
for f in LIESMICH.txt restore-guide-claude.md; do
  check "$f decrypts and restores" "$(grep -q 'backup_copy.sh decrypt' "$here/$f" && grep -q 'restore.sh <' "$here/$f" && echo yes)" "yes"
done

[ "$failures" -eq 0 ] && echo "all backup tests passed" || { echo "$failures check(s) failed"; exit 1; }
