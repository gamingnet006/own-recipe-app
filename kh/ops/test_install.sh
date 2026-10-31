#!/bin/sh
# KH: tests install.sh without Docker: questions with their suggestions, the .env it writes, the hint
# about folders Colima cannot see on a Mac, answers .env cannot store, and an existing .env stays.
set -eu

here=$(cd "$(dirname "$0")" && pwd)
set -- --lib
. "$here/install.sh"

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
failures=0

# Reports a failed check without stopping, so all checks run.
check() {
  if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1: expected '$3', got '$2'"; failures=$((failures + 1)); fi
}

# Prints yes or no for a test command, so checks can compare it.
yes_no() {
  if "$@" >/dev/null 2>&1; then echo yes; else echo no; fi
}

# --- ask: Enter keeps the suggestion ---
check "empty answer keeps the suggestion" "$(printf '\n' | ask "Ordner" ./backups 2>/dev/null)" "./backups"
check "answer replaces the suggestion" "$(printf '/mnt/usb/backups\n' | ask "Ordner" ./backups 2>/dev/null)" "/mnt/usb/backups"
check "no input at all keeps the suggestion" "$(ask "Ordner" ./backups </dev/null 2>/dev/null)" "./backups"

# --- storable: .env values are written with sed, which cannot take | and & ---
check "plain path is storable" "$(yes_no storable /mnt/usb/backups)" "yes"
check "| is not storable" "$(yes_no storable 'a|b')" "no"
check "& is not storable" "$(yes_no storable 'Tom & Jerry')" "no"

# --- write_env: this install's values on top of .env.example, readable only by the owner ---
mkdir "$tmp/ops" && cp "$here/.env.example" "$tmp/ops/"
(cd "$tmp/ops" && write_env example/image:v1 /mnt/usb/backups https://kochbuch.example.org)
for pair in KH_IMAGE=example/image:v1 KH_BACKUP_DIR=/mnt/usb/backups KH_BASE_URL=https://kochbuch.example.org \
  "KH_PUID=$(id -u)" "KH_PGID=$(id -g)" KH_SHARE_LINKS=false; do
  check "env ${pair%%=*}" "$(env_value "$tmp/ops/.env" "${pair%%=*}")" "${pair#*=}"
done
check "env readable only by the owner" "$(ls -l "$tmp/ops/.env" | cut -c1-10)" "-rw-------"

# --- colima_hint: Docker on a Mac (Colima) only sees folders below the home folder ---
mkdir "$tmp/bin"
printf '%s\n' '#!/bin/sh' 'echo "${STUB_UNAME:-Linux}"' > "$tmp/bin/uname"
chmod +x "$tmp/bin/uname"
hint_lines() {  # system folder
  (export PATH="$tmp/bin:$PATH" STUB_UNAME="$1"; colima_hint "$2" 2>&1 | grep -c Colima || true)
}
check "mac, folder outside home: hint" "$(hint_lines Darwin /Volumes/USB/backups)" "1"
check "mac, folder in home: no hint" "$(hint_lines Darwin "$HOME/kuechenhelfer/kh/ops/backups")" "0"
check "linux: no hint" "$(hint_lines Linux /mnt/usb/backups)" "0"

# --- fail: a .env this run wrote is removed again, so install.sh can simply run again ---
mkdir "$tmp/retry" && echo "KH_IMAGE=new" > "$tmp/retry/.env"
(cd "$tmp/retry" && CREATED_ENV=1 && fail "Probe") >/dev/null 2>&1 || true
check "failure after writing .env removes it" "$(ls -A "$tmp/retry")" ""
echo "KH_IMAGE=old" > "$tmp/retry/.env"
(cd "$tmp/retry" && fail "Probe") >/dev/null 2>&1 || true
check "failure before writing keeps an existing .env" "$(cat "$tmp/retry/.env")" "KH_IMAGE=old"

# --- main: one image, and an existing install is never touched ---
check "no image: usage" "$(sh "$here/install.sh" >/dev/null 2>&1 && echo 0 || echo $?)" "2"
check "two arguments: usage" "$(sh "$here/install.sh" a/b:1 c/d:2 >/dev/null 2>&1 && echo 0 || echo $?)" "2"
mkdir -p "$tmp/inst/kh/ops" && cp "$here/install.sh" "$here/update.sh" "$here/.env.example" "$tmp/inst/kh/ops/"
echo "KH_IMAGE=mine" > "$tmp/inst/kh/ops/.env"
check "existing .env: stops" "$(sh "$tmp/inst/kh/ops/install.sh" example/image:v1 </dev/null >/dev/null 2>&1 && echo 0 || echo $?)" "1"
check "existing .env stays as it was" "$(cat "$tmp/inst/kh/ops/.env")" "KH_IMAGE=mine"

[ "$failures" -eq 0 ] && echo "all install tests passed" || { echo "$failures check(s) failed"; exit 1; }
