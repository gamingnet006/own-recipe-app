#!/bin/sh
# KH: keeps Küchenhelfer on the newest stable release (PLAN.md D29): a nightly cron job asks the
# registry, installs the ops files shipped in the new image and switches with update.sh.
# Usage: kh/ops/auto_update.sh on|off|status|check|run [--scheduled]
set -eu

# Loads update.sh's helpers (setting, set_env_value, image_id) without running it.
# Loaded first, so the usage and main defined below take precedence over update.sh's own.
load_update_helpers() {
  set -- --lib
  . "$(dirname "$0")/update.sh"
}
load_update_helpers

CRON_MARK='# kh-auto-update'
LOG=auto_update.log
FAILED=.auto_update.failed

usage() {
  echo "Aufruf: kh/ops/auto_update.sh on|off|status|check|run [--scheduled]" >&2
  exit 2
}

# Stops with a clear reason; this run changed nothing.
fail() {
  echo "Automatische Updates: $1" >&2
  exit 1
}

# True unless KH_AUTO_UPDATE says off (false, 0, no, off; any case). Missing means on (D29).
auto_update_enabled() {
  case "$(setting KH_AUTO_UPDATE true | tr '[:upper:]' '[:lower:]')" in
    false|0|no|off) return 1 ;;
  esac
  return 0
}

# Prints the crontab line for the nightly run at 4:00, after the default backup at 3:30.
cron_line() {  # ops_dir (absolute)
  echo "0 4 * * * '$1/auto_update.sh' run --scheduled >> '$1/$LOG' 2>&1 $CRON_MARK"
}

# Prints a crontab without our line, then LINE: other jobs stay, ours exists exactly once.
crontab_with() {  # current line
  crontab_without "$1"
  echo "$2"
}

# Prints a crontab without our line.
crontab_without() {  # current
  [ -z "$1" ] || printf '%s\n' "$1" | grep -vF "$CRON_MARK" || true
}

# Switches automatic updates on: the setting in .env plus the nightly cron job.
turn_on() {
  [ -f "$ENV_FILE" ] || fail "$(pwd)/$ENV_FILE fehlt (Vorlage: .env.example)"
  set_env_value "$ENV_FILE" KH_AUTO_UPDATE true || fail "$ENV_FILE ließ sich nicht schreiben"
  # Read before the pipe: a crontab that empties itself on writing would lose the other jobs.
  current=$(crontab -l 2>/dev/null || true)
  crontab_with "$current" "$(cron_line "$(pwd)")" | crontab - \
    || fail "der nächtliche Job ließ sich nicht eintragen (crontab)"
  echo "Automatische Updates an: jede Nacht um 4 Uhr, nur stabile Versionen."
}

# Switches automatic updates off: the setting in .env and the cron job; other jobs stay.
turn_off() {
  [ -f "$ENV_FILE" ] || fail "$(pwd)/$ENV_FILE fehlt (Vorlage: .env.example)"
  set_env_value "$ENV_FILE" KH_AUTO_UPDATE false || fail "$ENV_FILE ließ sich nicht schreiben"
  current=$(crontab -l 2>/dev/null || true)
  crontab_without "$current" | crontab - \
    || fail "der nächtliche Job ließ sich nicht austragen (crontab)"
  echo "Automatische Updates aus. Von Hand geht es weiter mit: kh/ops/auto_update.sh check, dann run."
}

# Shows the switch, the cron job, the running version, a remembered failed version and the log.
show_status() {
  if auto_update_enabled; then echo "Automatische Updates: an"; else echo "Automatische Updates: aus"; fi
  if crontab -l 2>/dev/null | grep -qF "$CRON_MARK"; then
    echo "Nächtlicher Job: eingetragen (4 Uhr)"
  else
    echo "Nächtlicher Job: nicht eingetragen (kh/ops/auto_update.sh on)"
  fi
  echo "Laufende Version: $(setting KH_IMAGE kuechenhelfer:dev)"
  [ ! -s "$FAILED" ] || echo "Fehlgeschlagen und nachts übersprungen: $(cat "$FAILED")"
  [ ! -f "$LOG" ] || { echo "Letzte Einträge im Log:"; tail -n 5 "$LOG"; }
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
  cd "$(dirname "$0")"
  [ $# -ge 1 ] || usage
  case "$1" in
    on) [ $# -eq 1 ] || usage; turn_on ;;
    off) [ $# -eq 1 ] || usage; turn_off ;;
    status) [ $# -eq 1 ] || usage; show_status ;;
    *) usage ;;
  esac
}

[ "${1:-}" = "--lib" ] || main "$@"
