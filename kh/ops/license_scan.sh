#!/bin/sh
# KH: lists the licenses of all Python and npm runtime packages and fails when one is not on the
# allow-list (PLAN.md section 9, point 10). Reasons for odd metadata live in license_exceptions.txt.
# Usage: kh/ops/license_scan.sh py|npm|all
#   py   scans the Python environment of $KH_PYTHON (default python3), e.g. after `uv sync --no-dev`
#   npm  runs `pnpm licenses list --prod` in frontend/ (needs `pnpm install` first)
set -eu

here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/../.." && pwd)
EXCEPTIONS=${KH_LICENSE_EXCEPTIONS:-$here/license_exceptions.txt}

# Reads "name<TAB>license" lines on stdin, prints a summary and every package whose license is
# neither on the allow-list nor named in the exceptions file. Returns 1 if any is not allowed
# or if the list is empty (a failed scan must not look like a clean one).
# A license string is reduced to lowercase letters and digits and matched by prefix, so
# "Apache-2.0", "Apache License 2.0" and "Apache Software License" all count as one family.
# "A OR B" passes if one side does, "A AND B" only if both do; "WITH ..." clauses are ignored.
check_licenses() {
  awk -F'\t' -v exfile="$EXCEPTIONS" '
    BEGIN {
      n = split("mit bsd newbsd simplifiedbsd 0bsd apache isc mpl mozilla psf python lgpl gnulesser agpl gnuaffero gpl3 gplv3 gnugeneralpubliclicensev3 cc0 ccby3 ccby4 unlicense blueoak zlib wtfpl publicdomain", ok, " ")
      while ((getline line < exfile) > 0) {
        if (line ~ /^[ \t]*(#|$)/) continue
        split(line, f, /[ \t]+/); excepted[tolower(f[1])] = 1
      }
    }
    function one_ok(s,   k, i) {
      sub(/ with .*/, "", s); k = s; gsub(/[^a-z0-9]/, "", k)
      for (i = 1; i <= n; i++) if (index(k, ok[i]) == 1) return 1
      return 0
    }
    function and_ok(s,   parts, m, i) {
      m = split(s, parts, / and /)
      for (i = 1; i <= m; i++) if (!one_ok(parts[i])) return 0
      return 1
    }
    function lic_ok(s,   parts, m, i) {
      s = tolower(s); sub(/library or lesser/, "lesser", s); gsub(/[()]/, " ", s); gsub(/[ \t]+/, " ", s); gsub(/;|\//, " or ", s)
      m = split(s, parts, / or /)
      for (i = 1; i <= m; i++) if (and_ok(parts[i])) return 1
      return 0
    }
    NF < 2 { next }
    { total++
      if (lic_ok($2)) good++
      else if (excepted[tolower($1)]) viaex++
      else { bad++; msg = msg "  " $1 ": " ($2 == "" ? "(no license data)" : $2) "\n" } }
    END {
      if (!total) { print "No packages found: the scan input was empty, so nothing was checked" > "/dev/stderr"; exit 1 }
      printf "%d packages: %d allowed, %d by exception, %d not allowed\n", total, good, viaex, bad
      if (bad) {
        printf "Not allowed (fix the package, or add it with a reason to license_exceptions.txt):\n%s", msg
        exit 1
      }
    }'
}

# Prints "name<TAB>license" for every package installed in the environment of $KH_PYTHON.
python_licenses() {
  "${KH_PYTHON:-python3}" - <<'PY'
from importlib.metadata import distributions

seen = {}
for dist in distributions():
    meta = dist.metadata
    name = meta["Name"]
    if not name or name.lower() == "mealie":
        continue
    # Newest metadata first: SPDX expression, then trove classifiers, then the free-text field.
    lic = meta.get("License-Expression") or ""
    if not lic:
        classes = [c.rsplit(" :: ", 1)[-1] for c in meta.get_all("Classifier") or [] if c.startswith("License ::")]
        lic = " OR ".join(c for c in classes if c != "OSI Approved")
    if not lic:
        text = (meta.get("License") or "").strip()
        lic = text if text and "\n" not in text and len(text) <= 100 else ""
    seen[name.lower()] = f"{name}\t{lic}"
print("\n".join(sorted(seen.values())))
PY
}

# Prints "name<TAB>license" for every production dependency of the frontend.
npm_licenses() {
  (cd "$root/frontend" && pnpm licenses list --json --prod) | node -e '
    const groups = JSON.parse(require("fs").readFileSync(0, "utf8"));
    if (groups.error) { console.error("pnpm failed: " + groups.error.message); process.exit(1); }
    const rows = new Set();
    for (const list of Object.values(groups)) for (const p of list) rows.add(`${p.name}\t${p.license || ""}`);
    console.log([...rows].sort().join("\n"));'
}

usage() { echo "Usage: kh/ops/license_scan.sh py|npm|all" >&2; exit 2; }

# Sourcing with --lib (the tests do) loads the functions without running a scan.
[ "${1:-}" = "--lib" ] && return 0 2>/dev/null
[ $# -eq 1 ] || usage
case $1 in py|npm|all) ;; *) usage ;; esac
status=0
case $1 in py|all) echo "Python:"; python_licenses | check_licenses || status=1 ;; esac
case $1 in npm|all) echo "npm:"; npm_licenses | check_licenses || status=1 ;; esac
exit $status
