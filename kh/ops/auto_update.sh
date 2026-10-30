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

usage() {
  echo "Aufruf: kh/ops/auto_update.sh on|off|status|check|run [--scheduled]" >&2
  exit 2
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
    *) usage ;;
  esac
}

[ "${1:-}" = "--lib" ] || main "$@"
