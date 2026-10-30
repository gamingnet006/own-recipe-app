#!/bin/sh
# KH: tests the logic of upgrade_test.sh without Docker: which older releases come into
# question, the recipe fingerprint that is compared before and after, the default login
# lookup and the argument checks.
set -eu

here=$(cd "$(dirname "$0")" && pwd)
set -- --lib
. "$here/upgrade_test.sh"

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
failures=0

# Reports a failed check without stopping, so all checks run.
check() {
  if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1: expected '$3', got '$2'"; failures=$((failures + 1)); fi
}

# --- older releases: tags newest first, the ones after the current tag ---
tags=$(printf '%s\n' v0.1-rc.1 v0.0 v0.0-rc.1)
check "newest tag: all older ones" "$(older_releases v0.1-rc.1 "$tags" | tr '\n' ' ')" "v0.0 v0.0-rc.1 "
check "middle tag: only older ones" "$(older_releases v0.0 "$tags" | tr '\n' ' ')" "v0.0-rc.1 "
check "oldest tag: none" "$(older_releases v0.0-rc.1 "$tags")" ""
check "unknown tag: none" "$(older_releases v9.9 "$tags")" ""
check "dots are not wildcards" "$(older_releases v0x0 "$tags")" ""

# --- recipe fingerprint from Mealie's recipe JSON (fields as Mealie v3.29.0 returns them) ---
recipe='{"id":"3a50ee8e-5378-4f1a-9c3c-b111019b94c0","slug":"kh-test-hefezopf","name":"KH Test Hefezopf",
"description":"Testrezept","recipeServings":1.0,"recipeYieldQuantity":0.0,"recipeYield":"","image":"LgsQ",
"recipeIngredient":[{"display":"500 g Weizenmehl","note":"500 g Weizenmehl","originalText":null,"quantity":0.0},
{"display":"1 Ei","note":"1 Ei","originalText":null,"quantity":0.0}],
"recipeInstructions":[{"text":"Teig kneten.","title":"","summary":""},{"text":"Backen.","title":"","summary":""}],
"dateUpdated":"2026-10-30T11:00:00+00:00","updatedAt":"2026-10-30T11:00:00+00:00"}'
check "fingerprint holds the content" "$(printf '%s' "$recipe" | recipe_fingerprint)" \
  "KH Test Hefezopf | Testrezept | 1.0 | 0.0 |  | LgsQ | 500 g Weizenmehl | 1 Ei | Teig kneten. | Backen."
changed=$(printf '%s' "$recipe" | sed 's/1 Ei/2 Eier/' | recipe_fingerprint || true)
check "a changed ingredient changes the fingerprint" "$([ "$changed" = "$(printf '%s' "$recipe" | recipe_fingerprint)" ] && echo same || echo different)" "different"
touched=$(printf '%s' "$recipe" | sed 's/2026-10-30T11:00/2026-10-31T09:30/g' | recipe_fingerprint || true)
check "timestamps do not count" "$([ "$touched" = "$(printf '%s' "$recipe" | recipe_fingerprint)" ] && echo same || echo different)" "same"

# --- default login of a fresh Mealie, read from its settings source ---
settings="$tmp/settings.py"
printf '%s\n' '    _DEFAULT_EMAIL: str = "placeholder@example.invalid"' '    _DEFAULT_PASSWORD: str = "placeholder-password"' > "$settings"
check "default e-mail" "$(default_login _DEFAULT_EMAIL "$settings")" "placeholder@example.invalid"
check "default password" "$(default_login _DEFAULT_PASSWORD "$settings")" "placeholder-password"
check "missing field is empty" "$(default_login _DEFAULT_GROUP "$settings")" ""

# --- argument checks (stop before touching Docker) ---
check "no images is a usage error" "$(sh "$here/upgrade_test.sh" >/dev/null 2>&1 && echo 0 || echo $?)" "2"
check "usage explains upgrade_test.sh, not update.sh" "$(sh "$here/upgrade_test.sh" 2>&1 | grep -c "upgrade_test.sh" || true)" "2"
check "one image is a usage error" "$(sh "$here/upgrade_test.sh" a:1 >/dev/null 2>&1 && echo 0 || echo $?)" "2"
check "incomplete --previous-release is a usage error" "$(sh "$here/upgrade_test.sh" --previous-release v0.1 a >/dev/null 2>&1 && echo 0 || echo $?)" "2"
check "invalid image name is a usage error" "$(sh "$here/upgrade_test.sh" 'a:1' 'b|c' >/dev/null 2>&1 && echo 0 || echo $?)" "2"

[ "$failures" -eq 0 ] && echo "all upgrade tests passed" || { echo "$failures check(s) failed"; exit 1; }
