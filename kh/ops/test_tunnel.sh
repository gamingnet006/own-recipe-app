#!/bin/sh
# KH: tests the safety checks of tunnel.sh without Docker or Cloudflare: is self sign-up open,
# does an account still use the default e-mail, is cloudflared connected, and argument checks.
set -eu

here=$(cd "$(dirname "$0")" && pwd)
set -- --lib
. "$here/tunnel.sh"

failures=0

# Reports a failed check without stopping, so all checks run.
check() {
  if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1: expected '$3', got '$2'"; failures=$((failures + 1)); fi
}

# Prints yes/no for a command's exit status.
yes_no() {
  if "$@" >/dev/null 2>&1; then echo yes; else echo no; fi
}

# --- self sign-up (compact JSON as Mealie's /api/app/about returns it) ---
check "sign-up off" "$(yes_no signup_open '{"production":true,"version":"develop","allowSignup":false,"allowPasswordLogin":true}')" "no"
check "sign-up on" "$(yes_no signup_open '{"production":true,"version":"develop","allowSignup":true,"allowPasswordLogin":true}')" "yes"
check "error answer counts as not open" "$(yes_no signup_open '{"detail":"Not Found"}')" "no"

# --- default e-mail in the admin user list (compact JSON as /api/admin/users returns it) ---
users='{"page":1,"per_page":-1,"total":2,"total_pages":1,"items":[{"username":"oma","fullName":"Oma","email":"oma@example.invalid","admin":false},{"username":"admin","fullName":"Admin","email":"Placeholder@Example.invalid","admin":true}],"next":null,"previous":null}'
check "default e-mail still in use" "$(yes_no email_in_use "$users" placeholder@example.invalid)" "yes"
check "e-mail changed" "$(yes_no email_in_use "$users" someone-else@example.invalid)" "no"
check "partial e-mail does not count" "$(yes_no email_in_use "$users" ma@example.invalid)" "no"

# --- public groups and households (compact JSON as /api/admin/groups and /api/admin/households return it) ---
groups='{"page":1,"per_page":-1,"total":2,"items":[{"name":"Home","preferences":{"privateGroup":true,"showAnnouncements":false}},{"name":"Gäste","preferences":{"privateGroup":false}}]}'
check "public group found" "$(yes_no public_found "$groups")" "yes"
check "all groups private" "$(yes_no public_found "$(printf '%s' "$groups" | sed 's/"privateGroup":false/"privateGroup":true/')")" "no"
check "public household found" "$(yes_no public_found '{"items":[{"name":"Family","preferences":{"privateHousehold":false,"recipePublic":true}}]}')" "yes"
check "recipePublic alone is no public household" "$(yes_no public_found '{"items":[{"preferences":{"privateHousehold":true,"recipePublic":true}}]}')" "no"

# --- tunnel key (the dashboard shows it inside an install command; only the key belongs in .env) ---
check "plain key passes" "$(yes_no has_space 'eyJhIjoiMDAwIiwidCI6IjExMSIsInMiOiIyMjIifQ==')" "no"
check "pasted install command is caught" "$(yes_no has_space 'docker run cloudflare/cloudflared:latest tunnel --no-autoupdate run --token eyJhIjoiMDAwIn0=')" "yes"

# --- cloudflared connection (log lines as cloudflared prints them) ---
check "connected" "$(yes_no tunnel_connected 'INF Starting tunnel tunnelID=x
INF Registered tunnel connection connIndex=0 connection=abc event=0 ip=198.41.200.13 location=fra08 protocol=quic')" "yes"
check "not connected yet" "$(yes_no tunnel_connected 'INF Starting tunnel tunnelID=x
ERR Failed to fetch features, default to disable error="lookup cfd-features.argotunnel.com"')" "no"

# --- argument checks (stop before touching Docker) ---
check "no command is a usage error" "$(sh "$here/tunnel.sh" >/dev/null 2>&1 && echo 0 || echo $?)" "2"
check "unknown command is a usage error" "$(sh "$here/tunnel.sh" start >/dev/null 2>&1 && echo 0 || echo $?)" "2"
check "usage explains tunnel.sh" "$(sh "$here/tunnel.sh" 2>&1 | grep -c "tunnel.sh" || true)" "1"

[ "$failures" -eq 0 ] && echo "all tunnel tests passed" || { echo "$failures check(s) failed"; exit 1; }
