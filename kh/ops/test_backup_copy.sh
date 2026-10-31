#!/bin/sh
# KH: tests backup_copy.sh without a drive: setup and drive checks, the nightly job, a copy run and
# decrypting, with stand-ins for docker and df. With Docker it also encrypts and decrypts a real
# backup with age in the backup image.
set -eu

here=$(cd "$(dirname "$0")" && pwd)
set -- --lib
. "$here/backup_copy.sh"

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
failures=0

# Reports a failed check without stopping, so all checks run.
check() {
  if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1: expected '$3', got '$2'"; failures=$((failures + 1)); fi
}

# Prints yes/no for a command's exit status.
yes_no() {
  if "$@" >/dev/null 2>&1; then echo yes; else echo no; fi
}

KEY=age1$(printf '%058d' 0)

# --- keys, age files, the nightly job ---
check "valid key" "$(yes_no valid_key "$KEY")" "yes"
check "key too short" "$(yes_no valid_key age1abc)" "no"
check "key with capitals" "$(yes_no valid_key "AGE1$(printf '%058d' 0)")" "no"
printf 'age-encryption.org/v1\n-> X25519 x\n' > "$tmp/good.age"; printf 'PK\003\004' > "$tmp/plain.zip"
check "age file" "$(yes_no is_age_file "$tmp/good.age")" "yes"
check "not an age file" "$(yes_no is_age_file "$tmp/plain.zip")" "no"
check "cron line" "$(cron_line /srv/kh/ops)" "45 3 * * * '/srv/kh/ops/backup_copy.sh' run --scheduled >> '/srv/kh/ops/backup_copy.log' 2>&1 # kh-backup-copy"
check "agent runs the script with dash" "$(agent_plist /srv/kh/ops | grep -cF '<string>/bin/dash</string><string>/srv/kh/ops/backup_copy.sh</string><string>run</string><string>--scheduled</string>')" "1"
check "agent at 3:45" "$(agent_plist /srv/kh/ops | grep -cF '<key>Hour</key><integer>3</integer><key>Minute</key><integer>45</integer>')" "1"

# --- storing a file: compared, given the backup's time, never left half written ---
mkdir "$tmp/dest"; touch -t 202601020304 "$tmp/plain.zip"
store_file "$tmp/good.age" "$tmp/dest/a.zip.age" "$tmp/plain.zip"
check "stored" "$(cmp -s "$tmp/good.age" "$tmp/dest/a.zip.age" && echo same)" "same"
check "stored with the backup's time" "$(yes_no test "$tmp/dest/a.zip.age" -nt "$tmp/plain.zip")$(yes_no test "$tmp/plain.zip" -nt "$tmp/dest/a.zip.age")" "nono"
check "store fails without source" "$(yes_no store_file "$tmp/missing" "$tmp/dest/b.zip.age")" "no"
check "no half copy left" "$(ls -A "$tmp/dest" | tr '\n' ' ')" "a.zip.age "

# --- which backups still need a copy: the newest N without one, newest first, also with spaces ---
src="$tmp/Mein Server/backups"; mkdir -p "$src" "$tmp/have"
for day in 01 02 03; do touch -t "202601${day}0000" "$src/mealie_2026.01.$day.zip"; done
touch "$tmp/have/mealie_2026.01.02.zip.age"
check "pending" "$(pending "$src" "$tmp/have" 3 | xargs -I{} basename {} | tr '\n' ' ')" "mealie_2026.01.03.zip mealie_2026.01.01.zip "
check "pending, only the newest" "$(pending "$src" "$tmp/have" 2 | xargs -I{} basename {})" "mealie_2026.01.03.zip"

# --- the drive: present only if its folder's parent exists and lies on another disk ---
mkdir -p "$tmp/bin" "$tmp/stick" "$tmp/samedisk"
# df stand-in: everything below STUB_DRIVE lies on "/dev/stick", the rest on "/dev/internal"
printf '%s\n' '#!/bin/sh' 'echo "Filesystem 512-blocks Used Available Capacity Mounted on"' \
  'case "$2" in "$STUB_DRIVE"*) echo "/dev/stick 100 1 99 1% /drive" ;; *) echo "/dev/internal 100 1 99 1% /" ;; esac' > "$tmp/bin/df"
chmod +x "$tmp/bin/df"
export STUB_DRIVE="$tmp/stick"
check "drive ready" "$(PATH="$tmp/bin:$PATH" yes_no drive_ready "$tmp/stick/Kopien" "$src")" "yes"
check "drive missing" "$(PATH="$tmp/bin:$PATH" yes_no drive_ready "$tmp/gone/Kopien" "$src")" "no"
check "folder on the same disk" "$(PATH="$tmp/bin:$PATH" yes_no drive_ready "$tmp/samedisk/Kopien" "$src")" "no"

# --- a copy run in a test install, with stand-ins for docker and df ---
# docker stand-in: the encrypting run prints an age header and the backup; key making writes the
# key pair and decrypting the backup into the backup folder (/backups-dest); STUB_DOCKER_RC fails it
printf '%s\n' '#!/bin/sh' 'echo "$*" >> "$DOCKER_CALLS"' '[ "${STUB_DOCKER_RC:-0}" -eq 0 ] || exit "$STUB_DOCKER_RC"' \
  'case "$*" in' \
  '  *"-T backup"*) printf "age-encryption.org/v1\n"; cat ;;' \
  '  *age-keygen*) echo "$STUB_KEY" > "$STUB_BACKUPS/.copy-key.pub"; echo locked > "$STUB_BACKUPS/.copy-key.age" ;;' \
  '  *"age -d"*) tail -n +2 "$STUB_BACKUPS/.decrypt-in.age" > "$STUB_BACKUPS/.decrypt-out.zip" ;;' \
  'esac' > "$tmp/bin/docker"
chmod +x "$tmp/bin/docker"
ops="$tmp/inst/kh/ops"; mkdir -p "$ops/backup" "$ops/backups"
cp "$here/backup_copy.sh" "$here/update.sh" "$here/nightly_job.sh" "$ops/"; cp "$here/backup/backup.sh" "$ops/backup/"
stick="$tmp/stick/Kuechenhelfer-Backups"
printf 'KH_BACKUP_KEEP=2\nKH_BACKUP_COPY_DIR=%s\nKH_BACKUP_COPY_KEY=%s\n' "$stick" "$KEY" > "$ops/.env"
echo locked-key > "$ops/backups/$KEY_FILE"
for day in 01 02 03; do echo "backup $day" > "$ops/backups/mealie_2026.01.$day.zip"; touch -t "202601${day}0000" "$ops/backups/mealie_2026.01.$day.zip"; done
# Runs backup_copy.sh in the test install with the stand-ins; prints its output, then "exit N".
copy() {
  rc=0
  out=$(cd "$ops" && PATH="$tmp/bin:$PATH" DOCKER_CALLS="$tmp/docker_calls" STUB_BACKUPS="$ops/backups" STUB_KEY="$KEY" \
    sh ./backup_copy.sh "$@" 2>&1) || rc=$?
  printf '%s\nexit %s\n' "$out" "$rc"
}
res=$(copy run)
check "run: exit 0" "$(printf '%s\n' "$res" | tail -1)" "exit 0"
check "run: reports" "$(printf '%s\n' "$res" | grep -c 'OK: 2 neu, 2 auf dem Laufwerk')" "1"
check "run: copies the newest" "$(LC_ALL=C ls "$stick" | tr '\n' ' ')" "LIESMICH.txt $KEY_FILE mealie_2026.01.02.zip.age mealie_2026.01.03.zip.age "
check "run: copy is the encrypted backup" "$(tail -n +2 "$stick/mealie_2026.01.03.zip.age")" "backup 03"
check "run: key on the drive" "$(cat "$stick/$KEY_FILE")" "locked-key"
check "run: logged" "$(grep -c 'OK: 2 neu' "$ops/backup_copy.log")" "1"
check "run: working folder gone" "$(ls -A "$ops" | grep -c '^\.backup_copy\.')" "0"
check "run again: nothing new" "$(copy run | grep -c 'OK: 0 neu, 2 auf dem Laufwerk')" "1"
echo "backup 04" > "$ops/backups/mealie_2026.01.04.zip"
check "run: encryption fails" "$(STUB_DOCKER_RC=1 copy run | tail -1)" "exit 1"
check "run: no half copy" "$(ls -A "$stick" | grep -c '04')" "0"
echo other-key > "$stick/$KEY_FILE"
check "run: other key on the drive" "$(copy run | grep -c 'anderer Schlüssel')" "1"
echo locked-key > "$stick/$KEY_FILE"
mv "$tmp/stick" "$tmp/stick-away"
check "run: drive missing" "$(copy run | grep -c 'Laufwerk fehlt')" "1"
check "run: drive missing, nothing created" "$(yes_no test -e "$stick")" "no"
mv "$tmp/stick-away" "$tmp/stick"
printf 'KH_BACKUP_COPY_DIR=%s\n' "$stick" > "$ops/.env"
check "run: not set up" "$(copy run | grep -c 'nicht eingerichtet')" "1"

# --- on: drive check, key on first use, nightly job (cron stand-in), first copy ---
printf '%s\n' '#!/bin/sh' 'case "$1" in -l) cat "$CRONTAB_FILE" 2>/dev/null || exit 1 ;; -) cat > "$CRONTAB_FILE" ;; esac' > "$tmp/bin/crontab"
printf '%s\n' '#!/bin/sh' 'echo Linux' > "$tmp/bin/uname"
chmod +x "$tmp/bin/crontab" "$tmp/bin/uname"
export CRONTAB_FILE="$tmp/crontab"
# A new key needs a new folder: the copies in the old one stay readable with the old key.
rm -f "$ops/backups/$KEY_FILE"; new="$tmp/stick/Neu"
printf 'KH_BACKUP_KEEP=2\n' > "$ops/.env"
check "on: drive missing" "$(copy on "$tmp/gone/Kopien" | tail -1)" "exit 1"
res=$(copy on "$new")
check "on: exit 0" "$(printf '%s\n' "$res" | tail -1)" "exit 0"
check "on: key made" "$(env_value "$ops/.env" KH_BACKUP_COPY_KEY) $(cat "$ops/backups/$KEY_FILE")" "$KEY locked"
check "on: folder set" "$(env_value "$ops/.env" KH_BACKUP_COPY_DIR)" "$new"
check "on: nightly job" "$(grep -c "backup_copy.sh' run --scheduled" "$CRONTAB_FILE")" "1"
check "on: first copy" "$(printf '%s\n' "$res" | grep -c 'OK: 2 neu, 2 auf dem Laufwerk')" "1"
calls=$(grep -c age-keygen "$tmp/docker_calls")
copy on "$new" >/dev/null
check "on again: same key" "$(grep -c age-keygen "$tmp/docker_calls")" "$calls"
check "off" "$(copy off | tail -1) $(grep -c kh-backup-copy "$CRONTAB_FILE")" "exit 0 0"

# --- decrypt: into the backup folder, where restore.sh finds it ---
res=$(copy decrypt "$new/mealie_2026.01.04.zip.age")
check "decrypt: result exists already" "$(printf '%s\n' "$res" | grep -c 'liegt schon')" "1"
mv "$ops/backups/mealie_2026.01.04.zip" "$tmp/04.zip"
res=$(copy decrypt "$new/mealie_2026.01.04.zip.age")
check "decrypt: exit 0" "$(printf '%s\n' "$res" | tail -1)" "exit 0"
check "decrypt: backup back" "$(cat "$ops/backups/mealie_2026.01.04.zip")" "backup 04"
check "decrypt: temporary files gone" "$(ls -A "$ops/backups" | grep -c '^\.decrypt')" "0"
rm -f "$ops/backups/mealie_2026.01.04.zip"
check "decrypt: wrong password" "$(STUB_DOCKER_RC=1 copy decrypt "$new/mealie_2026.01.04.zip.age" | tail -1) $(ls -A "$ops/backups" | grep -cE '04|^\.decrypt')" "exit 1 0"
check "decrypt: not a copy" "$(copy decrypt "$tmp/04.zip" | tail -1)" "exit 1"

# --- with Docker: real age in the backup image ---
if docker info >/dev/null 2>&1; then
  image=kuechenhelfer-backup:copy-test
  docker build -q -t "$image" "$here/backup" >/dev/null
  in_backup() { docker run --rm -i "$image" "$@"; }  # the backup image without compose
  identity=$(docker run --rm "$image" age-keygen 2>/dev/null)
  pub=$(printf '%s\n' "$identity" | docker run --rm -i "$image" age-keygen -y)
  (cd "$here" && git archive --format=zip HEAD backup) > "$tmp/real.zip"
  encrypt "$pub" < "$tmp/real.zip" > "$tmp/real.zip.age"
  check "real: age file" "$(yes_no is_age_file "$tmp/real.zip.age")" "yes"
  docker run --rm -i -e ID="$identity" "$image" sh -c 'printf "%s\n" "$ID" > /tmp/id && age -d -i /tmp/id' < "$tmp/real.zip.age" > "$tmp/back.zip"
  check "real: decrypted equals backup" "$(cmp -s "$tmp/real.zip" "$tmp/back.zip" && echo same)" "same"
  check "real: broken backup refused" "$(printf 'no zip' | yes_no encrypt "$pub")" "no"
  docker image rm -f "$image" >/dev/null 2>&1 || true
else
  echo "skip real age round trip: no Docker"
fi

[ "$failures" -eq 0 ] && echo "all backup copy tests passed" || { echo "$failures check(s) failed"; exit 1; }
