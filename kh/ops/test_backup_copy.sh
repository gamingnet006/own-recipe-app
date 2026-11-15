#!/bin/sh
# KH: tests backup_copy.sh without a drive: setup and drive checks, choosing and switching the place
# (also on a Mac and by double-click), the nightly job, a copy run and decrypting, with stand-ins for
# docker, df and launchctl. With Docker it also encrypts and decrypts a real backup with age in the
# backup image.
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
check "pending" "$(pending "$src" "$tmp/have" 3 .age | xargs -I{} basename {} | tr '\n' ' ')" "mealie_2026.01.03.zip mealie_2026.01.01.zip "
check "pending, only the newest" "$(pending "$src" "$tmp/have" 2 .age | xargs -I{} basename {})" "mealie_2026.01.03.zip"
check "pending, plain copies" "$(pending "$src" "$tmp/have" 3 "" | xargs -I{} basename {} | tr '\n' ' ')" "mealie_2026.01.03.zip mealie_2026.01.02.zip mealie_2026.01.01.zip "

# --- the drive: present only if its folder's parent exists and lies on another disk ---
mkdir -p "$tmp/bin" "$tmp/stick" "$tmp/samedisk"
# df stand-in, named like macOS: everything below STUB_DRIVE lies on the stick "/dev/disk4s1",
# below STUB_VOLUME on another volume of the internal disk (like macOS's Recovery), the rest on it
printf '%s\n' '#!/bin/sh' 'echo "Filesystem 512-blocks Used Available Capacity Mounted on"' \
  'case "$2" in "$STUB_DRIVE"*) echo "/dev/disk4s1 100 1 ${STUB_FREE:-99} 1% /drive" ;;' \
  '  "${STUB_VOLUME:-/none}"*) echo "/dev/disk3s5 100 1 99 1% /volume" ;; *) echo "/dev/disk3s1 100 1 99 1% /" ;; esac' > "$tmp/bin/df"
chmod +x "$tmp/bin/df"
export STUB_DRIVE="$tmp/stick"
check "drive ready" "$(PATH="$tmp/bin:$PATH" yes_no drive_ready "$tmp/stick/Kopien" "$src")" "yes"
check "drive missing" "$(PATH="$tmp/bin:$PATH" yes_no drive_ready "$tmp/gone/Kopien" "$src")" "no"
check "folder on the same disk" "$(PATH="$tmp/bin:$PATH" yes_no drive_ready "$tmp/samedisk/Kopien" "$src")" "no"
check "folder on another volume of the same disk" \
  "$(export STUB_VOLUME="$tmp/samedisk"; PATH="$tmp/bin:$PATH" yes_no drive_ready "$tmp/samedisk/Kopien" "$src")" "no"
# One disk, whatever volume or partition: macOS, Linux disks, SD cards and NVMe; network shares stay
for pair in /dev/disk3s3s1:/dev/disk3 /dev/disk2s1:/dev/disk2 /dev/sdb1:/dev/sdb /dev/mmcblk0p2:/dev/mmcblk0 \
  /dev/nvme0n1p3:/dev/nvme0n1 //admin@nas/share://admin@nas/share; do
  check "whole disk of ${pair%%:/*}" "$(whole_disk "${pair%%:/*}")" "${pair#*:}"
done

# --- choosing a place: the plugged-in drives, how to prepare one, then a number or a folder ---
# Under $vol only KH-Stick is a drive; Intern lies on this machine's disk, Recovery on another volume
# of it, Verweis is a link to the stick, and Ordner a folder on it, not a drive of its own.
vol="$tmp/vol"; mkdir -p "$vol/KH-Stick/Ordner" "$vol/Intern" "$vol/Recovery"; ln -s "$vol/KH-Stick" "$vol/Verweis"
# Runs the choice with the drives under $vol; the answer comes from stdin, the dialog goes to stderr.
choose() {
  (cd "$tmp" && export STUB_DRIVE="$vol/KH-Stick" STUB_VOLUME="$vol/Recovery" \
    && DRIVE_GLOBS="$vol/* $vol/*/*" PATH="$tmp/bin:$PATH" choose_folder "$src")
}
check "drives: only the plugged-in one" "$(export STUB_DRIVE="$vol/KH-Stick" STUB_VOLUME="$vol/Recovery"
  DRIVE_GLOBS="$vol/* $vol/*/*" PATH="$tmp/bin:$PATH" drives "$src")" "$vol/KH-Stick"
check "choose: a number picks the drive" "$(printf '1\n' | choose 2>"$tmp/dialog")" "$vol/KH-Stick/Kuechenhelfer-Backups"
check "choose: the drive with name and free space" "$(grep -c '1) KH-Stick, frei: 99' "$tmp/dialog")" "1"
check "choose: where the copies go now" "$(grep -c 'Bisher: kein Ort eingerichtet' "$tmp/dialog")" "1"
check "choose: how to prepare a drive" "$(grep -c 'exFAT' "$tmp/dialog")" "1"
check "choose: a folder" "$(printf '/srv/kopien\n' | choose 2>/dev/null)" "/srv/kopien"
check "choose: a drive typed in gets the folder" "$(printf '%s/\n' "$vol/KH-Stick" | choose 2>/dev/null)" "$vol/KH-Stick/Kuechenhelfer-Backups"
for answer in "" 0 2 x Kopien; do
  check "choose: '$answer' is no choice" "$(printf '%s\n' "$answer" | yes_no choose)" "no"
done
check "choose: no drive plugged in" \
  "$(printf '\n' | (cd "$tmp" && DRIVE_GLOBS="$tmp/leer/*" PATH="$tmp/bin:$PATH" choose_folder "$src") 2>&1 | grep -c 'keines gefunden')" "1"

# --- waiting for the first copy the nightly job makes on a Mac: its first dated log line ---
printf '2026-11-01 03:45 Kopie aufs Laufwerk OK: 0 neu, 6 auf dem Laufwerk\n' > "$tmp/wait.log"
check "wait: no result yet" "$(cd "$tmp" && LOG=wait.log WAIT_SECONDS=0 wait_first_copy 1)" \
  "Die erste Kopie läuft noch. Ergebnis später: kh/ops/backup_copy.sh status"
printf 'Warnung ohne Datum\n2026-11-02 06:00 Kopie aufs Laufwerk OK: 2 neu, 2 auf dem Laufwerk\n' >> "$tmp/wait.log"
check "wait: the result" "$(cd "$tmp" && LOG=wait.log WAIT_SECONDS=0 wait_first_copy 1)" \
  "2026-11-02 06:00 Kopie aufs Laufwerk OK: 2 neu, 2 auf dem Laufwerk"

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
cp "$here/backup_copy.sh" "$here/update.sh" "$here/nightly_job.sh" "$ops/"
cp "$here/backup/backup.sh" "$here/backup/LIESMICH.txt" "$here/backup/restore-guide-claude.md" "$ops/backup/"
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
check "run: copies the newest" "$(LC_ALL=C ls "$stick" | tr '\n' ' ')" "CLAUDE.md LIESMICH.txt $KEY_FILE mealie_2026.01.02.zip.age mealie_2026.01.03.zip.age "
check "run: the restore guide on the drive" "$(cmp -s "$ops/backup/LIESMICH.txt" "$stick/LIESMICH.txt" && cmp -s "$ops/backup/restore-guide-claude.md" "$stick/CLAUDE.md" && echo same)" "same"
check "run: copy is the encrypted backup" "$(tail -n +2 "$stick/mealie_2026.01.03.zip.age")" "backup 03"
check "run: key on the drive" "$(cat "$stick/$KEY_FILE")" "locked-key"
check "run: logged" "$(grep -c 'OK: 2 neu' "$ops/backup_copy.log")" "1"
check "run: working folder gone" "$(ls -A "$ops" | grep -c '^\.backup_copy\.')" "0"
check "run again: nothing new" "$(copy run | grep -c 'OK: 0 neu, 2 auf dem Laufwerk')" "1"
echo "backup 04" > "$ops/backups/mealie_2026.01.04.zip"
check "run: encryption fails" "$(STUB_DOCKER_RC=1 copy run | tail -1)" "exit 1"
check "run: no half copy" "$(ls -A "$stick" | grep -c '04')" "0"
check "run: room is made before copying (a full drive recovers)" "$(ls "$stick" | grep -c 'zip.age$')" "1"
echo other-key > "$stick/$KEY_FILE"
check "run: other key on the drive" "$(copy run | grep -c 'anderer Schlüssel')" "1"
echo locked-key > "$stick/$KEY_FILE"
# a drive that refuses the write: "full" when nothing is free, else "no access" (not as root: it ignores modes)
if [ "$(id -u)" -ne 0 ]; then
  chmod 555 "$stick"
  check "run: full drive says so" "$(STUB_FREE=0 copy run | grep -c 'Laufwerk voll')" "1"
  check "run: refused write with space left says no access" "$(copy run | grep -c 'kein Zugriff')" "1"
  chmod 755 "$stick"
fi
mv "$tmp/stick" "$tmp/stick-away"
check "run: drive missing" "$(copy run | grep -c 'Laufwerk fehlt')" "1"
check "run: drive missing, nothing created" "$(yes_no test -e "$stick")" "no"
mv "$tmp/stick-away" "$tmp/stick"
printf 'KH_BACKUP_COPY_DIR=%s\n' "$stick" > "$ops/.env"
check "run: not set up" "$(copy run | grep -c 'nicht eingerichtet')" "1"

# --- without a password: the backups go to the drive as they are ---
plain="$tmp/stick/Ohne"
printf 'KH_BACKUP_KEEP=2\nKH_BACKUP_COPY_DIR=%s\nKH_BACKUP_COPY_KEY=none\n' "$plain" > "$ops/.env"
calls=$(wc -l < "$tmp/docker_calls" | tr -d ' ')
mkdir -p "$plain"; echo "alte Anleitung" > "$plain/LIESMICH.txt"  # a drive set up before the guide changed
res=$(copy run)
check "plain: exit 0" "$(printf '%s\n' "$res" | tail -1)" "exit 0"
check "plain: copies the newest as they are" "$(LC_ALL=C ls "$plain" | tr '\n' ' ')" "CLAUDE.md LIESMICH.txt mealie_2026.01.03.zip mealie_2026.01.04.zip "
check "plain: copy equals the backup, with its time" "$(cmp -s "$ops/backups/mealie_2026.01.04.zip" "$plain/mealie_2026.01.04.zip" && echo same) $(yes_no test "$ops/backups/mealie_2026.01.04.zip" -nt "$plain/mealie_2026.01.04.zip")" "same no"
check "plain: no key, no docker" "$(yes_no test -e "$plain/$KEY_FILE") $(wc -l < "$tmp/docker_calls" | tr -d ' ')" "no $calls"
check "plain: an old guide is renewed" "$(cmp -s "$ops/backup/LIESMICH.txt" "$plain/LIESMICH.txt" && echo renewed)" "renewed"
check "plain: run again, nothing new" "$(copy run | grep -c 'OK: 0 neu, 2 auf dem Laufwerk')" "1"

# --- on: drive check, the password question, key on first use, nightly job (cron stand-in), first copy ---
printf '%s\n' '#!/bin/sh' 'case "$1" in -l) cat "$CRONTAB_FILE" 2>/dev/null || exit 1 ;; -) cat > "$CRONTAB_FILE" ;; esac' > "$tmp/bin/crontab"
# uname stand-in: Linux unless STUB_UNAME says Darwin
printf '%s\n' '#!/bin/sh' 'echo "${STUB_UNAME:-Linux}"' > "$tmp/bin/uname"
chmod +x "$tmp/bin/crontab" "$tmp/bin/uname"
export CRONTAB_FILE="$tmp/crontab"
# A new key needs a new folder: the copies in the old one stay readable with the old key.
rm -f "$ops/backups/$KEY_FILE"; new="$tmp/stick/Neu"
printf 'KH_BACKUP_KEEP=2\n' > "$ops/.env"
check "on: drive missing" "$(copy on "$tmp/gone/Kopien" | tail -1)" "exit 1"
check "on: answer neither j nor n" "$(printf 'vielleicht\n' | copy on "$new" | tail -1) $(env_value "$ops/.env" KH_BACKUP_COPY_KEY)" "exit 1 "
res=$(printf 'j\n' | copy on "$new")
check "on: exit 0" "$(printf '%s\n' "$res" | tail -1)" "exit 0"
check "on: key made" "$(env_value "$ops/.env" KH_BACKUP_COPY_KEY) $(cat "$ops/backups/$KEY_FILE")" "$KEY locked"
check "on: folder set" "$(env_value "$ops/.env" KH_BACKUP_COPY_DIR)" "$new"
check "on: nightly job" "$(grep -c "backup_copy.sh' run --scheduled" "$CRONTAB_FILE")" "1"
check "on: first copy" "$(printf '%s\n' "$res" | grep -c 'OK: 2 neu, 2 auf dem Laufwerk')" "1"
calls=$(grep -c age-keygen "$tmp/docker_calls")
copy on "$new" >/dev/null
check "on again: same key" "$(grep -c age-keygen "$tmp/docker_calls")" "$calls"
check "off" "$(copy off | tail -1) $(grep -c kh-backup-copy "$CRONTAB_FILE")" "exit 0 0"
printf 'KH_BACKUP_KEEP=2\n' > "$ops/.env"
res=$(printf 'n\n' | copy on "$tmp/stick/OhneNeu")
check "on without password" "$(printf '%s\n' "$res" | tail -1) $(env_value "$ops/.env" KH_BACKUP_COPY_KEY) $(printf '%s\n' "$res" | grep -c 'OK: 2 neu')" "exit 0 none 1"
check "status without password" "$(copy status | grep -c 'ohne Passwort')" "1"
check "on again keeps it" "$(copy on "$tmp/stick/OhneNeu" | tail -1) $(env_value "$ops/.env" KH_BACKUP_COPY_KEY)" "exit 0 none"

# --- on without a folder: the guided switch; the key stays, the old place keeps its copies ---
res=$(printf '%s\n' "$tmp/stick/Weg" | copy on)
check "switch: exit 0" "$(printf '%s\n' "$res" | tail -1)" "exit 0"
check "switch: no password question" "$(printf '%s\n' "$res" | grep -c 'mit Passwort verschlüsseln')" "0"
check "switch: new place, same key" "$(env_value "$ops/.env" KH_BACKUP_COPY_DIR) $(env_value "$ops/.env" KH_BACKUP_COPY_KEY)" "$tmp/stick/Weg none"
check "switch: first copy with the guide" "$(LC_ALL=C ls "$tmp/stick/Weg" | tr '\n' ' ')" "CLAUDE.md LIESMICH.txt mealie_2026.01.03.zip mealie_2026.01.04.zip "
check "switch: the old place keeps its copies" "$(ls "$tmp/stick/OhneNeu" | grep -c '\.zip$')" "2"
res=$(printf '\n' | copy on)
check "switch: no answer changes nothing" \
  "$(printf '%s\n' "$res" | tail -1) $(printf '%s\n' "$res" | grep -c 'nichts geändert') $(env_value "$ops/.env" KH_BACKUP_COPY_DIR)" \
  "exit 1 1 $tmp/stick/Weg"

# --- on a Mac the first copy runs as the nightly job, and "on" shows its result ---
# launchctl stand-in: logs its calls; kickstart runs the nightly job right away, into its log
printf '%s\n' '#!/bin/sh' 'echo "$*" >> "$LAUNCHCTL_LOG"' \
  'case "$1" in kickstart) cd "$STUB_OPS" && sh ./backup_copy.sh run --scheduled >> backup_copy.log 2>&1 ;; esac' > "$tmp/bin/launchctl"
chmod +x "$tmp/bin/launchctl"
res=$(printf '%s\n' "$tmp/stick/Mac" | (export STUB_UNAME=Darwin HOME="$tmp/home" LAUNCHCTL_LOG="$tmp/launchctl" STUB_OPS="$ops"; copy on))
check "mac switch: exit 0" "$(printf '%s\n' "$res" | tail -1)" "exit 0"
check "mac switch: nightly job entered and started" "$(grep -c '^bootstrap' "$tmp/launchctl") $(grep -c '^kickstart' "$tmp/launchctl")" "1 1"
check "mac switch: shows the first copy's result" "$(printf '%s\n' "$res" | grep -c 'OK: 2 neu, 2 auf dem Laufwerk')" "1"

# --- decrypt: into the backup folder, where restore.sh finds it ---
# While the backup is still here, decrypt checks the copy against it and changes nothing.
res=$(copy decrypt "$new/mealie_2026.01.04.zip.age")
check "decrypt: copy matches the backup here" "$(printf '%s\n' "$res" | grep -c 'stimmt mit dem Backup') $(printf '%s\n' "$res" | tail -1)" "1 exit 0"
echo changed > "$ops/backups/mealie_2026.01.04.zip"
res=$(copy decrypt "$new/mealie_2026.01.04.zip.age")
check "decrypt: copy differs from the backup here" "$(printf '%s\n' "$res" | grep -c 'weicht') $(printf '%s\n' "$res" | tail -1) $(cat "$ops/backups/mealie_2026.01.04.zip")" "1 exit 1 changed"
check "decrypt: check leaves no files" "$(ls -A "$ops/backups" | grep -c '^\.decrypt')" "0"
mv "$ops/backups/mealie_2026.01.04.zip" "$tmp/04.zip"
res=$(copy decrypt "$new/mealie_2026.01.04.zip.age")
check "decrypt: exit 0" "$(printf '%s\n' "$res" | tail -1)" "exit 0"
check "decrypt: backup back" "$(cat "$ops/backups/mealie_2026.01.04.zip")" "backup 04"
check "decrypt: temporary files gone" "$(ls -A "$ops/backups" | grep -c '^\.decrypt')" "0"
rm -f "$ops/backups/mealie_2026.01.04.zip"
check "decrypt: wrong password" "$(STUB_DOCKER_RC=1 copy decrypt "$new/mealie_2026.01.04.zip.age" | tail -1) $(ls -A "$ops/backups" | grep -cE '04|^\.decrypt')" "exit 1 0"
check "decrypt: not a copy" "$(copy decrypt "$tmp/04.zip" | tail -1)" "exit 1"

# --- the double-click file: runs "backup_copy.sh on" next to it, also through a link ---
check "double-click file is executable" "$(yes_no test -x "$here/backup-ort-aendern.command")" "yes"
dc="$tmp/dc/kh/ops"; mkdir -p "$dc" "$tmp/desk"
cp "$here/backup-ort-aendern.command" "$dc/"
printf '%s\n' '#!/bin/sh' 'echo "backup_copy.sh $*"' > "$dc/backup_copy.sh"; chmod +x "$dc/backup_copy.sh"
ln -s "$dc/backup-ort-aendern.command" "$tmp/desk/Backup-Ort ändern.command"
ln -s ../dc/kh/ops/backup-ort-aendern.command "$tmp/desk/relativ.command"
for f in "$dc/backup-ort-aendern.command" "$tmp/desk/Backup-Ort ändern.command" "$tmp/desk/relativ.command"; do
  check "double-click: $(basename "$f")" "$(sh "$f" < /dev/null | head -n 1)" "backup_copy.sh on"
done

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
