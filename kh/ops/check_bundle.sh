#!/bin/sh
# KH: checks that a release image carries the ops files auto_update.sh installs and nothing
# private (D29); release.sh and kh-release.yml run it before an image is uploaded.
# Usage: kh/ops/check_bundle.sh <image>
set -eu

BUNDLE=/app/kh-bundle

usage() {
  echo "Aufruf: kh/ops/check_bundle.sh <image>" >&2
  exit 2
}

# Prints one line per problem in a bundle listing (file paths below the bundle, one per line):
# a missing file auto_update.sh, the nightly copy (backup_copy.sh), the backup image with its restore
# guide or a new install (install.sh) needs, or a secret, data or working file that must stay local.
bundle_problems() {  # listing
  for f in kh/ops/update.sh kh/ops/auto_update.sh kh/ops/check_bundle.sh kh/ops/nightly_job.sh kh/ops/backup_copy.sh \
    kh/ops/install.sh kh/ops/backup/backup.sh kh/ops/backup/Dockerfile kh/ops/backup/LIESMICH.txt kh/ops/backup/restore-guide-claude.md \
    kh/ops/docker-compose.yml mealie/core/settings/settings.py; do
    printf '%s\n' "$1" | grep -qxF "$f" || echo "$f fehlt"
  done
  printf '%s\n' "$1" \
    | grep -E '^kh/ops/(\.env|\.env\..*|data/.*|backups/.*|data\.pre-update/.*|\.upgrade-test\..*|\.restore-test\..*|auto_update\.log|\.auto_update\..*|backup_copy\.log|\.backup_copy\..*)$' \
    | grep -vxF kh/ops/.env.example \
    | sed 's/$/ darf nicht ins Image/'
}

main() {
  [ $# -eq 1 ] || usage
  listing=$(docker run --rm --entrypoint sh "$1" -c "cd $BUNDLE && find . -type f") \
    || { echo "Im Image $1 fehlen die Betriebsdateien ($BUNDLE)" >&2; exit 1; }
  problems=$(bundle_problems "$(printf '%s\n' "$listing" | sed 's|^\./||')")
  [ -z "$problems" ] || { printf '%s\n' "$problems" >&2; exit 1; }
  echo "Betriebsdateien im Image in Ordnung"
}

[ "${1:-}" = "--lib" ] || main "$@"
