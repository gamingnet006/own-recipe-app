#!/bin/sh
# KH: sets up a new Küchenhelfer install (PLAN.md phase 1, D32). Asks where the backups go and under
# which address the family opens the app, writes .env, starts everything and creates the backup key.
# Usage: kh/ops/install.sh <image>   e.g. ghcr.io/gamingnet006/own-recipe-app:v0.0-arm64
set -eu

# Loads update.sh's helpers (valid_image, set_env_value, setting, wait_healthy, create_token,
# start_backup, default_login). Loaded first, so the usage, fail and main defined below take precedence.
load_update_helpers() {
  set -- --lib
  . "$(dirname "$0")/update.sh"
}
load_update_helpers

usage() {
  echo "Aufruf: kh/ops/install.sh <image>" >&2
  echo "  zum Beispiel: kh/ops/install.sh ghcr.io/gamingnet006/own-recipe-app:v0.0-arm64" >&2
  exit 2
}

# Stops with a clear reason.
fail() {
  echo "Installation abgebrochen: $1" >&2
  exit 1
}

# Asks one question and prints the answer; Enter, or no input at all, keeps the suggestion.
ask() {  # question suggestion
  printf '%s [%s]: ' "$1" "$2" >&2
  answer=""
  IFS= read -r answer || true
  echo "${answer:-$2}"
}

# True if .env can hold the value: set_env_value writes with sed, which cannot take | and &.
storable() {  # value
  case "$1" in *'|'*|*'&'*) return 1 ;; esac
}

# Writes .env from .env.example with this install's values, readable only by the owner, because it
# will hold the backup key.
write_env() {  # image backup_dir base_url
  (umask 077 && cp .env.example .env) || return 1
  set_env_value .env KH_IMAGE "$1" && set_env_value .env KH_BACKUP_DIR "$2" \
    && set_env_value .env KH_BASE_URL "$3" && set_env_value .env KH_PUID "$(id -u)" \
    && set_env_value .env KH_PGID "$(id -g)"
}

# Warns on a Mac: Colima only shares the home folder, and a folder it cannot see silently stays
# inside its virtual machine, so the backups would not land where they should.
colima_hint() {  # folder (absolute)
  [ "$(uname -s)" = Darwin ] || return 0
  case "$1" in "$HOME"/*) return 0 ;; esac
  echo "Hinweis: Colima sieht auf dem Mac nur Ordner unter $HOME. Liegt $1 woanders, muss Colima ihn freigeben (colima start --mount), sonst landen die Backups nicht dort." >&2
}

# Starts Mealie, creates the backup key with Mealie's default login (a new install has no other
# account yet) and starts the backup service.
start_install() {
  echo "Küchenhelfer startet; beim ersten Mal lädt Docker das Image, das dauert ein paar Minuten."
  docker compose up -d --no-build mealie || fail "Küchenhelfer startet nicht (ist die Anmeldung bei ghcr.io eingerichtet?)"
  TIMEOUT=$(setting KH_UPDATE_TIMEOUT 600)
  wait_healthy || fail "Küchenhelfer wird nicht bereit; Meldungen zeigt: docker compose logs mealie"
  token=$(create_token "http://localhost:$(setting KH_PORT 9091)" "$SETTINGS" kh-backup) \
    || fail "der Backup-Schlüssel ließ sich nicht anlegen"
  set_env_value .env KH_BACKUP_API_TOKEN "$token" || fail "der Backup-Schlüssel ließ sich nicht eintragen"
  start_backup || fail "der Backup-Dienst startet nicht (docker compose build backup)"
}

main() {
  [ $# -eq 1 ] && valid_image "$1" || usage
  OPS=$(cd "$(dirname "$0")" && pwd)
  SETTINGS="$(cd "$OPS/../.." && pwd)/mealie/core/settings/settings.py"
  cd "$OPS"
  [ ! -e .env ] || fail "kh/ops/.env gibt es schon, diese Installation ist eingerichtet. Neue Versionen spielt update.sh ein."
  docker compose version >/dev/null 2>&1 || fail "Docker mit Compose fehlt oder läuft nicht"

  echo "Küchenhelfer einrichten. Enter übernimmt den Vorschlag in Klammern."
  echo "Backups liegen am sichersten auf einem anderen Laufwerk, einem Netzlaufwerk oder in einem Ordner, den ein zweites Gerät abholt. ./backups liegt auf derselben Platte wie die Rezepte."
  backups=$(ask "Ordner für die Backups" ./backups)
  echo "Die Adresse ist die, unter der ihr Küchenhelfer öffnet, mit Zugang von unterwegs z. B. https://kochbuch.example.org."
  port=${KH_PORT:-9091}
  url=$(ask "Adresse" "http://localhost:$port")
  storable "$backups" && storable "$url" || fail "bitte ohne | und & antworten"
  mkdir -p data "$backups" || fail "der Ordner $backups ließ sich nicht anlegen"
  colima_hint "$(cd "$backups" && pwd)"
  write_env "$1" "$backups" "$url" || fail "kh/ops/.env ließ sich nicht schreiben"
  start_install

  echo "Fertig: Küchenhelfer läuft, die Backups landen in $backups."
  echo "Jetzt sofort:"
  echo "  1. http://localhost:$(setting KH_PORT 9091) öffnen (von anderen Geräten im Heimnetz: IP-Adresse dieses Rechners mit :$(setting KH_PORT 9091))"
  echo "     und mit $(default_login _DEFAULT_EMAIL "$SETTINGS") und dem Passwort $(default_login _DEFAULT_PASSWORD "$SETTINGS") anmelden."
  echo "  2. Unter Profil E-Mail und Passwort ändern. Im Einrichtungs-Assistenten „Öffentlichen Zugriff aktivieren“ aus lassen."
  echo "Danach, siehe docs/kh/README.md: Familie einladen, automatische Updates, Zugang von unterwegs."
}

[ "${1:-}" = "--lib" ] || main "$@"
