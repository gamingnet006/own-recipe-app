#!/bin/sh
# KH: tests the logic of restore_test.sh without Docker: which recipes a backup holds, which a
# restored database holds, which backup files are missing after a restore, and the argument checks.
set -eu

here=$(cd "$(dirname "$0")" && pwd)
set -- --lib
. "$here/restore_test.sh"

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
failures=0

# Reports a failed check without stopping, so all checks run.
check() {
  if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1: expected '$3', got '$2'"; failures=$((failures + 1)); fi
}

# A self-made backup in Mealie's layout and a database as a restore would leave it.
python3 - "$tmp" <<'EOF'
import json, sqlite3, sys, zipfile
tmp = sys.argv[1]
with zipfile.ZipFile(f"{tmp}/backup.zip", "w") as z:
    z.writestr("database.json", json.dumps({"recipes": [{"slug": "kh-test-zopf"}, {"slug": "kh-test-apfelkuchen"}]}))
    z.writestr("data/recipes/1/images/original.webp", b"image")
    z.writestr("data/users/", b"")
    z.writestr("data/mealie_2026.01.01.bak.db", b"old copy")
with zipfile.ZipFile(f"{tmp}/no-database.zip", "w") as z:
    z.writestr("notes.txt", "kein Mealie-Backup")
db = sqlite3.connect(f"{tmp}/mealie.db")
db.execute("create table recipes (slug text)")
db.executemany("insert into recipes values (?)", [("kh-test-zopf",), ("kh-test-apfelkuchen",)])
db.commit()
EOF

# --- recipes: both sides sorted, so the lists compare as they are ---
check "recipes in the backup" "$(backup_recipes "$tmp/backup.zip" | tr '\n' ' ')" "kh-test-apfelkuchen kh-test-zopf "
check "recipes in the restored database" "$(restored_recipes "$tmp/mealie.db" | tr '\n' ' ')" "kh-test-apfelkuchen kh-test-zopf "
check "zip without database.json fails" "$(backup_recipes "$tmp/no-database.zip" >/dev/null 2>&1 && echo 0 || echo 1)" "1"

# --- files: every file in a folder below data/ must be back; Mealie skips loose files there on
# purpose (old database copies), and folder entries do not count ---
mkdir -p "$tmp/data/users"
check "missing file is listed" "$(missing_files "$tmp/backup.zip" "$tmp/data")" "recipes/1/images/original.webp"
mkdir -p "$tmp/data/recipes/1/images" && touch "$tmp/data/recipes/1/images/original.webp"
check "nothing missing" "$(missing_files "$tmp/backup.zip" "$tmp/data")" ""

# --- arguments: at most one backup, and it must exist ---
check "two arguments: usage" "$(sh "$here/restore_test.sh" a.zip b.zip >/dev/null 2>&1 && echo 0 || echo $?)" "2"
check "missing backup: error" "$(sh "$here/restore_test.sh" "$tmp/nope.zip" >/dev/null 2>&1 && echo 0 || echo $?)" "1"

[ "$failures" -eq 0 ] && echo "all restore tests passed" || { echo "$failures check(s) failed"; exit 1; }
