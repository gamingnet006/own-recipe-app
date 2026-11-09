#!/bin/sh
# KH: keeps Kochheft on the newest stable release (PLAN.md D29): a nightly job (cron, on macOS
# launchd) asks the registry, installs the ops files shipped in the new image and switches with update.sh.
# Usage: kh/ops/auto_update.sh on|off|status|check|run [--scheduled]
set -eu

# Loads helpers without running their scripts: update.sh (setting, set_env_value), backup.sh
# (push to Uptime Kuma), check_bundle.sh (bundle_problems, BUNDLE) and nightly_job.sh (schedule,
# note, report). Loaded first, so the usage, fail and main defined below take precedence over theirs.
load_helpers() {
  set -- --lib
  . "$(dirname "$0")/update.sh"
  . "$(dirname "$0")/backup/backup.sh"
  . "$(dirname "$0")/check_bundle.sh"
  . "$(dirname "$0")/nightly_job.sh"
}
load_helpers

JOB_SCRIPT=auto_update.sh
JOB_LABEL=kuechenhelfer.auto-update  # launchd label of the nightly job on macOS
JOB_MARK='# kh-auto-update'
JOB_HOUR=4  # after the default backup at 3:30
JOB_MINUTE=0
JOB_PUSH_SETTING=KH_UPDATE_PUSH_URL
LOG=auto_update.log
FAILED=.auto_update.failed
LOCK=.auto_update.lock

usage() {
  echo "Aufruf: kh/ops/auto_update.sh on|off|status|check|run [--scheduled]" >&2
  exit 2
}

# Stops with a clear reason; this run changed nothing.
fail() {
  echo "Automatische Updates: $1" >&2
  exit 1
}

# Prints the path of FILE in the app's data folder (kh/ there), the one place the container and this script share.
kh_data_file() {  # name
  echo "$(setting KH_DATA_DIR ./data)/kh/$1"
}

# Prints the switch: the app's checkbox (data/kh/auto_update.json, {"enabled": true|false}) if the file says one,
# else KH_AUTO_UPDATE from .env, else true. No jq on the servers, so a tiny sed.
auto_update_switch() {
  box=$(sed -nE 's/.*"enabled"[[:space:]]*:[[:space:]]*(true|false).*/\1/p' "$(kh_data_file auto_update.json)" 2>/dev/null || true)
  echo "${box:-$(setting KH_AUTO_UPDATE true)}"
}

# True unless the switch says off (false, 0, no, off; any case). Missing means on (D29).
auto_update_enabled() {
  case "$(auto_update_switch | tr '[:upper:]' '[:lower:]')" in
    false|0|no|off) return 1 ;;
  esac
  return 0
}

# Leaves one line for the app's admin page: date | up or down | what happened | running version.
write_status() {
  file=$(kh_data_file auto_update_status.txt)
  ref=$(setting KH_IMAGE kuechenhelfer:dev)
  { mkdir -p "$(dirname "$file")" \
    && printf '%s | %s | %s | %s\n' "$(date '+%Y-%m-%d %H:%M')" "${LAST_RESULT:-up}" "${LAST_NOTE:-}" "${ref##*:}" > "$file"; } \
    || echo "Automatische Updates: der Stand ließ sich nicht nach $file schreiben" >&2
}

# Switches automatic updates on: the setting in .env plus the nightly job.
turn_on() {
  [ -f "$ENV_FILE" ] || fail "$(pwd)/$ENV_FILE fehlt (Vorlage: .env.example)"
  set_env_value "$ENV_FILE" KH_AUTO_UPDATE true || fail "$ENV_FILE ließ sich nicht schreiben"
  rm -f "$(kh_data_file auto_update.json)"  # the command line is the last word, the app's checkbox must not contradict it
  schedule_job "$(pwd)" || fail "der nächtliche Job ließ sich nicht eintragen"
  echo "Automatische Updates an: jede Nacht um 4 Uhr, nur stabile Versionen."
}

# Switches automatic updates off: only the setting in .env. The nightly job stays and exits at once while the
# switch says off, so the app's checkbox can switch updates on again later (a removed job would ignore it).
turn_off() {
  [ -f "$ENV_FILE" ] || fail "$(pwd)/$ENV_FILE fehlt (Vorlage: .env.example)"
  set_env_value "$ENV_FILE" KH_AUTO_UPDATE false || fail "$ENV_FILE ließ sich nicht schreiben"
  rm -f "$(kh_data_file auto_update.json)"
  echo "Automatische Updates aus. Von Hand geht es weiter mit: kh/ops/auto_update.sh check, dann run."
}

# Shows the switch, the nightly job, the running version, a remembered failed version and the log.
show_status() {
  if auto_update_enabled; then echo "Automatische Updates: an"; else echo "Automatische Updates: aus"; fi
  if job_scheduled; then
    echo "Nächtlicher Job: eingetragen (4 Uhr)"
  else
    echo "Nächtlicher Job: nicht eingetragen (kh/ops/auto_update.sh on)"
  fi
  echo "Laufende Version: $(setting KH_IMAGE kuechenhelfer:dev)"
  failed=$(failed_tag)
  [ -z "$failed" ] || echo "Fehlgeschlagen und nachts übersprungen: $failed"
  [ ! -f "$LOG" ] || { echo "Letzte Einträge im Log:"; tail -n 5 "$LOG"; }
}

# Takes the run lock (a directory, created atomically). A lock whose process is gone (crash,
# power cut) is taken over, so one bad night never stops all later ones.
# ponytail: a lock without pid file counts as stale; two runs in the same instant could both start.
take_lock() {  # dir
  if ! mkdir "$1" 2>/dev/null; then
    holder=$(cat "$1/pid" 2>/dev/null || true)
    if [ -n "$holder" ] && kill -0 "$holder" 2>/dev/null; then return 1; fi
    rm -rf "$1" && mkdir "$1" 2>/dev/null || return 1
  fi
  echo $$ > "$1/pid" || return 1
}

release_lock() {  # dir
  rm -rf "$1"
}

# Copies the unpacked ops files over the install (the folder above kh/); everything the bundle
# does not contain (.env, data, backups, logs) stays as it is.
install_bundle() {  # staging root
  cp -R "$1/." "$2/"
}

# Prints a docker config.json that logs in to REGISTRY, so one pull can use the read-only
# token without touching the user's own docker login or keychain.
docker_auth_json() {  # registry user token
  printf '{"auths":{"%s":{"auth":"%s"}}}\n' "$1" "$(printf '%s:%s' "$2" "$3" | base64 | tr -d '\n')"
}

# Remembers a version whose update failed; the nightly run skips it until a newer one exists.
mark_failed() {  # tag
  echo "$1" > "$FAILED"
}

# Prints the remembered failed version, if any.
failed_tag() {
  cat "$FAILED" 2>/dev/null || true
}

clear_failed() {
  rm -f "$FAILED"
}

# Turns update.sh's exit code into the result: success clears a remembered failure, 3 means the
# rollback failed too (a person must look), 4 means update.sh stopped before changing anything
# (the next night tries again), anything else marks the version as failed.
finish_update() {  # rc tag
  case "$1" in
    0) clear_failed; report up "Aktualisiert auf $2"; return 0 ;;
    3) report down "NOTFALL: Update auf $2 und Rückfall gescheitert, siehe Meldungen von update.sh"; return 3 ;;
    4) report down "Update auf $2 abgebrochen, nichts geändert; nächste Nacht neuer Versuch"; return 1 ;;
    *) mark_failed "$2"; report down "Update auf $2 fehlgeschlagen, die bisherige Version läuft weiter"; return 1 ;;
  esac
}

# Prints the image tags of REPO. Logs in only when user and token are set; secrets reach curl
# on stdin (-K -), so they never show up in the process list.
registry_tags() {  # registry repo user token
  scope="https://$1/token?scope=repository:$2:pull&service=$1"
  if [ -n "$3" ]; then
    answer=$(printf 'user = "%s:%s"\n' "$3" "$4" | curl -fs -m 30 -K - "$scope") || answer=""
  else
    answer=$(curl -fs -m 30 "$scope") || answer=""
  fi
  bearer=$(printf '%s\n' "$answer" | sed -n 's/.*"token":"\([^"]*\)".*/\1/p')
  [ -n "$bearer" ] || { echo "Registry $1 nicht erreichbar oder Anmeldung abgelehnt" >&2; return 1; }
  list=$(printf 'header = "Authorization: Bearer %s"\n' "$bearer" \
    | curl -fs -m 30 -K - "https://$1/v2/$2/tags/list?n=1000") \
    || { echo "Registry $1: die Versionsliste ist nicht abrufbar" >&2; return 1; }
  tags_from_json "$list"
}

# Pulls REF. With user and token it uses a throwaway docker config for this one pull, so the
# user's own docker login, keychain and compose plugin stay untouched; DOCKER_HOST keeps the
# current context (on a Mac with Colima there is no /var/run/docker.sock).
pull_image() {  # ref registry user token
  if [ -z "$3" ]; then docker pull -q "$1" >/dev/null; return; fi
  host=$(docker context inspect --format '{{.Endpoints.docker.Host}}') || return 1
  cfg=$(mktemp -d) || return 1
  (umask 077 && docker_auth_json "$2" "$3" "$4" > "$cfg/config.json") || { rm -rf "$cfg"; return 1; }
  rc=0
  DOCKER_HOST="$host" DOCKER_CONFIG="$cfg" docker pull -q "$1" >/dev/null || rc=$?
  rm -rf "$cfg"
  return "$rc"
}

# Copies the ops files out of the new image into STAGING and checks them like check_bundle.sh.
extract_bundle() {  # ref staging
  cid=$(docker create "$1") || return 1
  rc=0
  docker cp "$cid:$BUNDLE/." "$2" >/dev/null 2>&1 || rc=1
  docker rm "$cid" >/dev/null 2>&1 || true
  [ "$rc" -eq 0 ] || { echo "Im Image $1 fehlen die Betriebsdateien ($BUNDLE)" >&2; return 1; }
  problems=$(bundle_problems "$(cd "$2" && find . -type f | sed 's|^\./||')")
  [ -z "$problems" ] || { printf '%s\n' "$problems" >&2; return 1; }
}

# Shows what run would do and changes nothing; works with the switch off too.
check_cmd() {
  if auto_update_enabled; then echo "Automatische Updates: an"; else echo "Automatische Updates: aus"; fi
  ref=$(setting KH_IMAGE kuechenhelfer:dev)
  echo "Laufende Version: $ref"
  parts=$(parse_image "$ref") || { echo "Entwicklungs-Image, keine automatischen Updates."; return 0; }
  set -- $parts  # registry repo version arch
  failed=$(failed_tag)
  [ -z "$failed" ] || echo "Fehlgeschlagen und nachts übersprungen: $failed"
  tags=$(registry_tags "$1" "$2" "$(setting KH_REGISTRY_USER "")" "$(setting KH_REGISTRY_TOKEN "")") || exit 1
  next=$(newest_stable "$tags" "$4" "$3")
  if [ -n "$next" ]; then echo "Würde aktualisieren auf $1/$2:$next"; else echo "Nichts Neueres als $3."; fi
}

# One update run (spec D29, "Ablauf von run"): switch, version list, newest stable release, pull,
# ops files from the image, update.sh. Returns 0 done or nothing to do, 1 failed, 3 emergency.
run_cmd() {  # [--scheduled]
  case "${1:-}" in "") ;; --scheduled) SCHEDULED=1 ;; *) usage ;; esac
  take_lock "$LOCK" || { note "Ein anderer Lauf ist noch aktiv, dieser endet."; return 0; }
  WORK=""
  trap 'write_status; release_lock "$LOCK"; [ -z "$WORK" ] || rm -rf "$WORK"' EXIT
  auto_update_enabled || { note "Automatische Updates sind aus (KH_AUTO_UPDATE), nichts zu tun."; return 0; }
  ref=$(setting KH_IMAGE kuechenhelfer:dev)
  parts=$(parse_image "$ref") || { note "Entwicklungs-Image $ref, keine automatischen Updates."; return 0; }
  set -- $parts  # registry repo version arch
  user=$(setting KH_REGISTRY_USER "")
  token=$(setting KH_REGISTRY_TOKEN "")
  tags=$(registry_tags "$1" "$2" "$user" "$token") \
    || { report down "Versionsliste nicht abrufbar, nichts geändert"; return 1; }
  skip=""
  [ "$SCHEDULED" = 0 ] || skip=$(failed_tag)
  next=$(newest_stable "$tags" "$4" "$3" "$skip")
  [ -n "$next" ] || { report up "Aktuell ($3), nichts zu tun"; return 0; }
  new="$1/$2:$next"
  note "Neue Version: $new"
  pull_image "$new" "$1" "$user" "$token" || { report down "Herunterladen von $new fehlgeschlagen, nichts geändert"; return 1; }
  WORK=$(mktemp -d ./.auto_update.XXXXXX) || { report down "Arbeitsordner fehlt, nichts geändert"; return 1; }
  extract_bundle "$new" "$WORK" || { report down "Betriebsdateien in $new unvollständig, nichts geändert"; return 1; }
  install_bundle "$WORK" ../.. || { report down "Betriebsdateien ließen sich nicht einspielen"; return 1; }
  rc=0
  sh ./update.sh "$new" || rc=$?
  finish_update "$rc" "$next"
}

# Splits a release image name into "registry repo version arch". Fails for anything else
# (local dev images, digests, other tags), so only released installs update themselves.
parse_image() {  # ref
  case "$1" in *@*) return 1 ;; esac
  name=${1%:*}
  tag=${1##*:}
  [ "$name" != "$1" ] || return 1
  case "$tag" in */*) return 1 ;; esac  # that colon was a registry port, there is no tag
  registry=${name%%/*}
  repo=${name#*/}
  [ "$repo" != "$name" ] || return 1
  case "$registry" in *.*|*:*) ;; *) return 1 ;; esac
  case "$tag" in *-amd64) arch=amd64 ;; *-arm64) arch=arm64 ;; *) return 1 ;; esac
  version=${tag%-"$arch"}
  printf '%s\n' "$version" | grep -Eq '^v[0-9]+\.[0-9]+(\.[0-9]+)?(-rc\.[0-9]+)?$' || return 1
  echo "$registry $repo $version $arch"
}

# True if TAG is a stable release for ARCH: vX.Y or vX.Y.Z with the arch suffix, never -rc.
is_stable_tag() {  # tag arch
  printf '%s\n' "$1" | grep -Eq "^v[0-9]+\.[0-9]+(\.[0-9]+)?-$2\$"
}

# True if version A is newer than B (vX.Y[.Z][-rc.N]; a final release beats its candidates).
version_gt() {  # a b
  awk -v a="$1" -v b="$2" '
    function key(v,   p, n, rc) {
      sub(/^v/, "", v)
      rc = 999999  # no -rc: newer than every candidate of the same version
      if (index(v, "-rc.")) { rc = substr(v, index(v, "-rc.") + 4) + 0; v = substr(v, 1, index(v, "-rc.") - 1) }
      n = split(v, p, ".")
      return sprintf("%09d%09d%09d%09d", p[1], p[2], (n > 2 ? p[3] : 0), rc)
    }
    BEGIN { exit !(key(a) > key(b)) }'
}

# Prints the tags from the registry's tag list answer, one per line (no jq on the servers).
tags_from_json() {  # json
  printf '%s\n' "$1" | sed -n 's/.*"tags":\[\([^]]*\)\].*/\1/p' | tr ',' '\n' | tr -d '" '
}

# Prints the newest stable tag for ARCH that is newer than CURRENT, leaving out SKIP
# (a version that failed before); prints nothing when there is none.
newest_stable() {  # tags arch current [skip]
  best=""
  for t in $1; do
    is_stable_tag "$t" "$2" || continue
    [ "$t" != "${4:-}" ] || continue
    version_gt "${t%-"$2"}" "$3" || continue
    [ -z "$best" ] || version_gt "${t%-"$2"}" "${best%-"$2"}" || continue
    best=$t
  done
  [ -z "$best" ] || echo "$best"
}

main() {
  # cron, launchd and SSH on macOS do not find docker otherwise; appended, so the caller's PATH still wins
  PATH="$PATH:/usr/local/bin:/opt/homebrew/bin"
  export PATH
  cd "$(dirname "$0")"
  [ $# -ge 1 ] || usage
  case "$1" in
    on) [ $# -eq 1 ] || usage; turn_on ;;
    off) [ $# -eq 1 ] || usage; turn_off ;;
    status) [ $# -eq 1 ] || usage; show_status ;;
    check) [ $# -eq 1 ] || usage; check_cmd ;;
    run) [ $# -le 2 ] || usage; shift; run_cmd "$@" ;;
    *) usage ;;
  esac
}

# Exit right after main: an update replaces this very file in place, and the shell must not
# read on into the new version (the braces are parsed in full before they run).
[ "${1:-}" = "--lib" ] || { main "$@"; exit; }
