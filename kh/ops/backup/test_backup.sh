#!/bin/sh
# KH: tests the backup helpers without Docker or Mealie: pruning keeps the newest
# files, newest_zip finds the latest one, and an empty folder is handled.
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

[ "$failures" -eq 0 ] && echo "all backup tests passed" || { echo "$failures check(s) failed"; exit 1; }
