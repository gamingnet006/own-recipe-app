#!/bin/sh
# KH: switches access from outside through the Cloudflare Tunnel on or off (PLAN.md phase 1, D27).
# "on" starts it only if self sign-up is off, no account still uses Mealie's well-known default
# e-mail and every group and household is private, so recipes never go public by accident.
# Usage: kh/ops/tunnel.sh on|off|status
set -eu

CONNECT_TIMEOUT=60
POLL=3

# Loads update.sh's helpers (setting, health_status, default_login) without running it.
# Loaded first, so the usage, fail and main defined below take precedence over update.sh's own.
load_update_helpers() {
  set -- --lib
  . "$(dirname "$0")/update.sh"
}
load_update_helpers

usage() {
  echo "Aufruf: kh/ops/tunnel.sh on|off|status" >&2
  exit 2
}

# Stops with a clear reason; the tunnel stays off.
fail() {
  echo "Tunnel nicht gestartet: $1" >&2
  exit 1
}

# True if Mealie lets strangers create accounts (compact JSON of /api/app/about).
signup_open() {  # about_json
  printf '%s' "$1" | grep -q '"allowSignup":true'
}

# True if an account in the admin user list still has this e-mail (compact JSON, any case).
email_in_use() {  # users_json email
  printf '%s' "$1" | grep -Fqi "\"email\":\"$2\""
}

# True if a group or household in an admin list lets strangers browse its recipes (compact JSON of
# /api/admin/groups or /api/admin/households).
public_found() {  # admin_list_json
  printf '%s' "$1" | grep -Eq '"private(Group|Household)":false'
}

# True if the value contains a space, e.g. the whole install command was pasted instead of only the key.
has_space() {  # value
  case "$1" in *" "*) return 0 ;; esac
  return 1
}

# True once cloudflared reports a working connection to Cloudflare.
tunnel_connected() {  # logs
  printf '%s' "$1" | grep -q "Registered tunnel connection"
}

# Checks that the install is safe to go online; no login is attempted, so nobody gets locked out.
check_safe() {
  tunnel_token=$(setting KH_TUNNEL_TOKEN '')
  [ -n "$tunnel_token" ] || fail "KH_TUNNEL_TOKEN fehlt in .env (Cloudflare: Networking, Tunnels)"
  ! has_space "$tunnel_token" \
    || fail "KH_TUNNEL_TOKEN enthält Leerzeichen: nur die lange Zeichenkette nach --token eintragen, nicht den ganzen Befehl"
  token=$(setting KH_BACKUP_API_TOKEN '')
  [ -n "$token" ] || fail "KH_BACKUP_API_TOKEN fehlt in .env (wird für die Prüfung der Konten gebraucht)"
  [ "$(health_status)" = healthy ] || fail "der Küchenhelfer läuft nicht oder ist nicht bereit"
  url="http://localhost:$(setting KH_PORT 9091)"
  about=$(curl -fsS -m 10 "$url/api/app/about") || fail "Mealie antwortet nicht"
  ! signup_open "$about" || fail "die Selbstregistrierung ist an"
  users=$(curl -fsS -m 10 -H "Authorization: Bearer $token" "$url/api/admin/users?page=1&perPage=-1") \
    || fail "die Kontenliste ist nicht abrufbar (gehört KH_BACKUP_API_TOKEN einem Admin?)"
  email=$(default_login _DEFAULT_EMAIL "$SETTINGS")
  [ -n "$email" ] || fail "Mealies Standard-E-Mail ist nicht lesbar ($SETTINGS)"
  ! email_in_use "$users" "$email" \
    || fail "ein Konto nutzt noch die Standard-E-Mail $email. In Mealie unter Profil E-Mail und Passwort ändern"
  groups=$(curl -fsS -m 10 -H "Authorization: Bearer $token" "$url/api/admin/groups?page=1&perPage=-1") \
    || fail "die Gruppenliste ist nicht abrufbar"
  ! public_found "$groups" || fail "eine Gruppe ist öffentlich. In Mealie unter Gruppeneinstellungen „Private Gruppe“ einschalten"
  households=$(curl -fsS -m 10 -H "Authorization: Bearer $token" "$url/api/admin/households?page=1&perPage=-1") \
    || fail "die Haushaltsliste ist nicht abrufbar"
  ! public_found "$households" \
    || fail "ein Haushalt ist öffentlich. In Mealie unter Haushaltskonfiguration „Privater Haushalt“ einschalten"
}

# Starts cloudflared and waits until it is connected; stops it again if it never connects.
turn_on() {
  check_safe
  docker compose --profile tunnel up -d tunnel >/dev/null 2>&1 || fail "der Tunnel-Container startet nicht"
  waited=0
  until tunnel_connected "$(docker compose --profile tunnel logs tunnel 2>&1)"; do
    if [ "$waited" -ge "$CONNECT_TIMEOUT" ]; then
      docker compose --profile tunnel rm -sf tunnel >/dev/null 2>&1 || true
      fail "keine Verbindung zu Cloudflare (stimmt KH_TUNNEL_TOKEN?)"
    fi
    sleep "$POLL"
    waited=$((waited + POLL))
  done
  base=$(setting KH_BASE_URL '')
  echo "Tunnel läuft: Der Küchenhelfer ist jetzt von unterwegs erreichbar${base:+ unter $base}."
  case "$base" in https://*) ;; *) echo "Hinweis: KH_BASE_URL in .env auf die Tunnel-Adresse setzen (https://...)." ;; esac
}

turn_off() {
  docker compose --profile tunnel rm -sf tunnel >/dev/null 2>&1 || true
  echo "Tunnel aus: Der Küchenhelfer ist nur noch im Heimnetz erreichbar."
}

show_status() {
  if [ -n "$(docker compose --profile tunnel ps -q tunnel 2>/dev/null)" ] \
    && tunnel_connected "$(docker compose --profile tunnel logs tunnel 2>&1)"; then
    echo "Tunnel: an"
  else
    echo "Tunnel: aus"
  fi
}

main() {
  cd "$(dirname "$0")"
  SETTINGS="../../mealie/core/settings/settings.py"
  [ $# -eq 1 ] || usage
  case "$1" in
    on) turn_on ;;
    off) turn_off ;;
    status) show_status ;;
    *) usage ;;
  esac
}

[ "${1:-}" = "--lib" ] || main "$@"
