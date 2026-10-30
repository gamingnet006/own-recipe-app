#!/bin/sh
# KH: tests auto_update.sh without network or Docker: release-image names, stable tags,
# version order, the registry's tag list and the choice of the next version.
set -eu

here=$(cd "$(dirname "$0")" && pwd)
set -- --lib
. "$here/auto_update.sh"

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
failures=0

# Reports a failed check without stopping, so all checks run.
check() {
  if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1: expected '$3', got '$2'"; failures=$((failures + 1)); fi
}

# Prints yes/no for a command's exit status.
yes_no() {
  if "$@" >/dev/null 2>&1; then echo yes; else echo no; fi
}

# Copies auto_update.sh and the scripts it loads into DIR, a kh/ops folder of a test install.
copy_scripts() {  # dir
  mkdir -p "$1/backup"
  cp "$here/auto_update.sh" "$here/update.sh" "$here/check_bundle.sh" "$1/"
  cp "$here/backup/backup.sh" "$1/backup/"
}

# --- release-image names (only released installs update themselves) ---
check "parse ghcr rc" "$(parse_image ghcr.io/gamingnet006/own-recipe-app:v0.0-rc.2-amd64)" "ghcr.io gamingnet006/own-recipe-app v0.0-rc.2 amd64"
check "parse patch" "$(parse_image ghcr.io/x/y:v0.1.2-arm64)" "ghcr.io x/y v0.1.2 arm64"
check "parse registry with port" "$(parse_image 127.0.0.1:5000/x/y:v1.0-amd64)" "127.0.0.1:5000 x/y v1.0 amd64"
for ref in kuechenhelfer:dev ghcr.io/x/y:latest ghcr.io/x/y:v0.1 ghcr.io/x/y:v0.1-s390x ghcr.io/x/y@sha256:0000 x/y:v0.1-amd64; do
  check "no release image: $ref" "$(yes_no parse_image "$ref")" "no"
done

# --- stable tags ---
check "stable" "$(yes_no is_stable_tag v0.1-amd64 amd64)" "yes"
check "stable patch" "$(yes_no is_stable_tag v0.1.3-amd64 amd64)" "yes"
check "rc is not stable" "$(yes_no is_stable_tag v0.1-rc.1-amd64 amd64)" "no"
check "other arch" "$(yes_no is_stable_tag v0.1-arm64 amd64)" "no"
check "suffix after arch" "$(yes_no is_stable_tag v0.1-amd64-old amd64)" "no"

# --- version order ---
check "v0.1 > v0.0" "$(yes_no version_gt v0.1 v0.0)" "yes"
check "v0.10 > v0.9" "$(yes_no version_gt v0.10 v0.9)" "yes"
check "v1.0 > v0.9.9" "$(yes_no version_gt v1.0 v0.9.9)" "yes"
check "v0.1.1 > v0.1" "$(yes_no version_gt v0.1.1 v0.1)" "yes"
check "v0.1 = v0.1.0" "$(yes_no version_gt v0.1 v0.1.0)$(yes_no version_gt v0.1.0 v0.1)" "nono"
check "final > rc" "$(yes_no version_gt v0.0 v0.0-rc.2)" "yes"
check "rc.3 > rc.2" "$(yes_no version_gt v0.0-rc.3 v0.0-rc.2)" "yes"
check "rc < final" "$(yes_no version_gt v0.0-rc.2 v0.0)" "no"
check "next rc > old final" "$(yes_no version_gt v0.1-rc.1 v0.0)" "yes"

# --- the registry's tag list (compact JSON as GHCR returns it) ---
check "tags from json" "$(tags_from_json '{"name":"x/y","tags":["v0.0-rc.1-amd64","v0.0-amd64","v0.0-arm64"]}' | tr '\n' ' ')" "v0.0-rc.1-amd64 v0.0-amd64 v0.0-arm64 "
check "repo name is no tag" "$(tags_from_json '{"name":"v-repo/y","tags":["v0.1-amd64"]}')" "v0.1-amd64"
check "no tags" "$(tags_from_json '{"name":"x/y","tags":null}')" ""
check "error answer" "$(tags_from_json '{"errors":[{"code":"DENIED"}]}')" ""

# --- choosing the next version ---
tags="v0.0-rc.2-amd64 v0.0-amd64 v0.1-amd64 v0.1-arm64 v0.2-rc.1-amd64 v0.10-amd64 v0.9-amd64"
check "newest stable" "$(newest_stable "$tags" amd64 v0.0-rc.2)" "v0.10-amd64"
check "already newest" "$(newest_stable "$tags" amd64 v0.10)" ""
check "skip failed" "$(newest_stable "$tags" amd64 v0.0-rc.2 v0.10-amd64)" "v0.9-amd64"
check "other arch" "$(newest_stable "$tags" arm64 v0.0)" "v0.1-arm64"

# --- switch in .env (missing means on) ---
ENV_FILE="$tmp/.env"; : > "$ENV_FILE"; unset KH_AUTO_UPDATE
check "on when missing" "$(yes_no auto_update_enabled)" "yes"
for v in true TRUE 1 yes; do printf 'KH_AUTO_UPDATE=%s\n' "$v" > "$ENV_FILE"; check "on: $v" "$(yes_no auto_update_enabled)" "yes"; done
for v in false FALSE 0 no off; do printf 'KH_AUTO_UPDATE=%s\n' "$v" > "$ENV_FILE"; check "off: $v" "$(yes_no auto_update_enabled)" "no"; done

# --- nightly cron job (other jobs of the user stay untouched) ---
check "cron line" "$(cron_line /srv/kh/ops)" "0 4 * * * '/srv/kh/ops/auto_update.sh' run --scheduled >> '/srv/kh/ops/auto_update.log' 2>&1 # kh-auto-update"
check "cron line with space" "$(cron_line '/Users/x/Mein Server/kh/ops')" "0 4 * * * '/Users/x/Mein Server/kh/ops/auto_update.sh' run --scheduled >> '/Users/x/Mein Server/kh/ops/auto_update.log' 2>&1 # kh-auto-update"
line=$(cron_line /srv/kh/ops); other=$(printf 'MAILTO=""\n5 * * * * /usr/bin/true')
check "empty crontab" "$(crontab_with "" "$line")" "$line"
check "keeps other jobs" "$(crontab_with "$other" "$line")" "$(printf '%s\n%s' "$other" "$line")"
check "on twice, one line" "$(crontab_with "$(crontab_with "$other" "$line")" "$line" | grep -c 'kh-auto-update')" "1"
check "off keeps other jobs" "$(crontab_without "$(crontab_with "$other" "$line")")" "$other"

# --- on/off against a stand-in crontab (tests never touch the real one) ---
onoff="$tmp/onoff/kh/ops"; mkdir -p "$tmp/bin"
copy_scripts "$onoff"
printf 'KH_AUTO_UPDATE=false\n' > "$onoff/.env"
printf '%s\n' '#!/bin/sh' 'case "$1" in -l) cat "$CRONTAB_FILE" 2>/dev/null || exit 1 ;; -) cat > "$CRONTAB_FILE" ;; esac' > "$tmp/bin/crontab"
chmod +x "$tmp/bin/crontab"
export CRONTAB_FILE="$tmp/crontab"
printf '%s\n' '5 * * * * /usr/bin/true' > "$CRONTAB_FILE"
PATH="$tmp/bin:$PATH" sh "$onoff/auto_update.sh" on >/dev/null
check "on sets the switch" "$(env_value "$onoff/.env" KH_AUTO_UPDATE)" "true"
check "on adds the job, keeps the other" "$(grep -c . "$CRONTAB_FILE") $(grep -c "/onoff/kh/ops/auto_update.sh' run --scheduled" "$CRONTAB_FILE")" "2 1"
PATH="$tmp/bin:$PATH" sh "$onoff/auto_update.sh" on >/dev/null
check "on twice, one job" "$(grep -c 'kh-auto-update' "$CRONTAB_FILE")" "1"
PATH="$tmp/bin:$PATH" sh "$onoff/auto_update.sh" off >/dev/null
check "off clears the switch" "$(env_value "$onoff/.env" KH_AUTO_UPDATE)" "false"
check "off leaves the other job" "$(cat "$CRONTAB_FILE")" "5 * * * * /usr/bin/true"
rm -f "$CRONTAB_FILE"
check "on without any crontab" "$(PATH="$tmp/bin:$PATH" sh "$onoff/auto_update.sh" on >/dev/null 2>&1 && grep -c 'kh-auto-update' "$CRONTAB_FILE")" "1"

# --- ops files inside the image (check_bundle.sh) ---
. "$here/check_bundle.sh"
ok=$(printf '%s\n' kh/ops/update.sh kh/ops/auto_update.sh kh/ops/docker-compose.yml kh/ops/.env.example mealie/core/settings/settings.py)
check "complete bundle" "$(bundle_problems "$ok")" ""
check "update.sh missing" "$(bundle_problems "$(printf '%s\n' "$ok" | grep -vx kh/ops/update.sh)")" "kh/ops/update.sh fehlt"
for bad in kh/ops/.env kh/ops/.env.pre-update kh/ops/data/mealie.db kh/ops/backups/a.zip kh/ops/data.pre-update/mealie.db kh/ops/.upgrade-test.x1/ops/.env kh/ops/auto_update.log kh/ops/.auto_update.failed; do
  check "forbidden: $bad" "$(bundle_problems "$(printf '%s\n%s' "$ok" "$bad")")" "$bad darf nicht ins Image"
done

# --- run lock (a crash or power cut must not stop all later nights) ---
lock="$tmp/lock"
check "take lock" "$(yes_no take_lock "$lock")$(cat "$lock/pid")" "yes$$"
check "held by live process" "$(yes_no take_lock "$lock")" "no"
sh -c 'exit 0' & dead=$!; wait "$dead"; echo "$dead" > "$lock/pid"
check "stale lock taken over" "$(yes_no take_lock "$lock")" "yes"
release_lock "$lock"
check "lock released" "$(yes_no test -e "$lock")" "no"

# --- installing the unpacked ops files (.env and data stay) ---
root="$tmp/Mein Server"; mkdir -p "$root/kh/ops/data" "$tmp/stage/kh/ops"
echo secret-placeholder > "$root/kh/ops/.env"; echo db > "$root/kh/ops/data/mealie.db"; echo old > "$root/kh/ops/update.sh"
echo new > "$tmp/stage/kh/ops/update.sh"; echo added > "$tmp/stage/kh/ops/new.sh"
install_bundle "$tmp/stage" "$root"
check "file replaced" "$(cat "$root/kh/ops/update.sh")" "new"
check "file added" "$(cat "$root/kh/ops/new.sh")" "added"
check ".env untouched" "$(cat "$root/kh/ops/.env")" "secret-placeholder"
check "data untouched" "$(cat "$root/kh/ops/data/mealie.db")" "db"

# --- registry login for one pull, and the remembered failed version ---
check "auth json" "$(docker_auth_json ghcr.io user secret)" '{"auths":{"ghcr.io":{"auth":"dXNlcjpzZWNyZXQ="}}}'
FAILED="$tmp/failed"; mark_failed v0.1-amd64
check "failed tag" "$(failed_tag)" "v0.1-amd64"
clear_failed
check "failed cleared" "$(failed_tag)" ""

# --- check and run without network or Docker, in a copied test install ---
inst="$tmp/inst/kh/ops"
copy_scripts "$inst"
run_au() { (cd "$inst" && sh ./auto_update.sh "$@" 2>&1); }
printf 'KH_AUTO_UPDATE=false\nKH_IMAGE=ghcr.io/x/y:v0.0-amd64\n' > "$inst/.env"
check "switch off" "$(run_au run | grep -c 'aus')" "1"
check "switch off logged" "$(grep -c 'aus' "$inst/auto_update.log")" "1"
printf 'KH_IMAGE=kuechenhelfer:dev\n' > "$inst/.env"
check "dev image" "$(run_au run --scheduled | grep -c 'Entwicklungs-Image')" "1"
printf 'KH_IMAGE=127.0.0.1:9/x/y:v0.0-amd64\n' > "$inst/.env"
check "registry down: exit" "$( (cd "$inst" && sh ./auto_update.sh check >/dev/null 2>&1) && echo 0 || echo $?)" "1"
check "registry down: message" "$(run_au check | grep -c 'nicht erreichbar')" "1"
check "registry down: run exit" "$( (cd "$inst" && sh ./auto_update.sh run --scheduled >/dev/null 2>&1) && echo 0 || echo $?)" "1"
check "registry down: nothing marked" "$(yes_no test -e "$inst/.auto_update.failed")" "no"
check "lock removed" "$(yes_no test -e "$inst/.auto_update.lock")" "no"
check "bad option" "$( (cd "$inst" && sh ./auto_update.sh run --nightly >/dev/null 2>&1) && echo 0 || echo $?)" "2"

# --- result of update.sh (0 updated, 1 failed and old version back, 3 rollback failed) ---
report() { echo "$1" >> "$tmp/reports"; }   # stub: records up/down instead of pushing
FAILED="$tmp/failed2"; : > "$tmp/reports"
check "update ok" "$(finish_update 0 v0.1-amd64 && echo 0 || echo $?)$(failed_tag)" "0"
check "update failed" "$(finish_update 1 v0.1-amd64 && echo 0 || echo $?)$(failed_tag)" "1v0.1-amd64"
check "ok clears marker" "$(finish_update 0 v0.1-amd64 >/dev/null; failed_tag)" ""
check "rollback failed" "$(finish_update 3 v0.1-amd64 && echo 0 || echo $?)" "3"
check "reports" "$(tr '\n' ' ' < "$tmp/reports")" "up down up down "

# --- argument checks ---
check "usage without command" "$(sh "$here/auto_update.sh" >/dev/null 2>&1 && echo 0 || echo $?)" "2"
check "usage unknown command" "$(sh "$here/auto_update.sh" start >/dev/null 2>&1 && echo 0 || echo $?)" "2"

[ "$failures" -eq 0 ] && echo "all auto-update tests passed" || { echo "$failures check(s) failed"; exit 1; }
