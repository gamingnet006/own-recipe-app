#!/bin/sh
# KH: tests the allow-list comparison of license_scan.sh with made-up package lists, without Docker or network.
set -eu

here=$(cd "$(dirname "$0")" && pwd)
set -- --lib
. "$here/license_scan.sh"

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
printf '# comment\n\nodd-pkg  metadata missing, license is MIT upstream\n' > "$tmp/exceptions.txt"
EXCEPTIONS=$tmp/exceptions.txt
failures=0

# Reports a failed check without stopping, so all checks run.
check() {
  if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1: expected '$3', got '$2'"; failures=$((failures + 1)); fi
}

# Prints yes if the one-package list passes the scan, no if it fails.
passes() {  # license
  if printf 'pkg\t%s\n' "$1" | check_licenses >/dev/null; then echo yes; else echo no; fi
}

for l in MIT "MIT License" BSD-3-Clause "BSD License" Apache-2.0 "Apache Software License" ISC MPL-2.0 \
  "Mozilla Public License 2.0 (MPL 2.0)" "Python-2.0" "PSF-2.0" "LGPL-3.0-or-later" "AGPL-3.0-only" "GPL-3.0" \
  CC0-1.0 CC-BY-4.0 CC-BY-3.0 Unlicense 0BSD BlueOak-1.0.0 Zlib "Apache-2.0 WITH LLVM-exception" \
  "(MIT OR GPL-2.0)" "GNU Library or Lesser General Public License (LGPL)" "MIT AND Zlib" "MIT/Apache-2.0"; do
  check "allowed: $l" "$(passes "$l")" yes
done
for l in "GPL-2.0-only" "CC-BY-NC-4.0" "SSPL-1.0" "BUSL-1.1" "Proprietary" "UNKNOWN" "" "MIT AND SSPL-1.0" "Elastic-2.0"; do
  check "refused: ${l:-empty}" "$(passes "$l")" no
done

check "exception lets an odd package pass" "$(printf 'Odd-Pkg\tUNKNOWN\n' | check_licenses >/dev/null && echo yes || echo no)" yes
check "summary counts" "$(printf 'a\tMIT\nb\tSSPL-1.0\nodd-pkg\t\n' | check_licenses | head -1)" "3 packages: 1 allowed, 1 by exception, 1 not allowed"
check "failure names the package and its license" "$(printf 'bad-pkg\tSSPL-1.0\n' | check_licenses | grep -c 'bad-pkg: SSPL-1.0')" 1
check "missing license is explained" "$(printf 'bad-pkg\t\n' | check_licenses | grep -c 'no license data')" 1
check "all allowed prints no list" "$(printf 'a\tMIT\n' | check_licenses | wc -l | tr -d ' ')" 1

check "empty input fails" "$(printf '' | check_licenses >/dev/null 2>&1 && echo yes || echo no)" no

# --- argument checks (stop before running any scan) ---
check "no command is a usage error" "$(sh "$here/license_scan.sh" >/dev/null 2>&1 && echo 0 || echo $?)" 2
check "unknown command is a usage error" "$(sh "$here/license_scan.sh" rust >/dev/null 2>&1 && echo 0 || echo $?)" 2

[ "$failures" -eq 0 ] && echo "all license scan tests passed" || { echo "$failures check(s) failed"; exit 1; }
