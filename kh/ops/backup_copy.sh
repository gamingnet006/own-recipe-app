#!/bin/sh
# KH: copies the daily backups to a removable drive such as a USB stick (PLAN.md D32), so a copy
# survives when this machine's disk fails. With a password they are encrypted with age: only the
# public key stays here, the private key lies on the drive, locked with the password (D33). "on"
# without a folder asks for one: it also changes the place later (on a Mac: backup-ort-aendern.command).
# Usage: kh/ops/backup_copy.sh on [<folder>]|off|status|run [--scheduled]|decrypt <file.zip.age>
set -eu

# Loads helpers without running their scripts: update.sh (setting, set_env_value), backup.sh
# (prune, push, put_guide) and nightly_job.sh (schedule, report). Loaded first, so the usage, fail and main
# defined below take precedence over theirs.
load_helpers() {
  set -- --lib
  . "$(dirname "$0")/update.sh"
  . "$(dirname "$0")/backup/backup.sh"
  . "$(dirname "$0")/nightly_job.sh"
}
load_helpers

JOB_SCRIPT=backup_copy.sh
JOB_LABEL=kuechenhelfer.backup-copy  # launchd label of the nightly job on macOS
JOB_MARK='# kh-backup-copy'
JOB_HOUR=3  # a quarter of an hour after the default backup at 3:30, before the update at 4:00
JOB_MINUTE=45
# macOS lets a nightly job read removable drives only with Full Disk Access. The job runs with
# dash, which hardly anything else on a Mac starts, so that permission stays with this job.
JOB_SHELL=/bin/dash
JOB_PUSH_SETTING=KH_BACKUP_PUSH_URL  # one Uptime Kuma monitor for the backup and its copy
LOG=backup_copy.log
KEY_FILE=kuechenhelfer-schluessel.age  # the private key, locked with the password
FOLDER_NAME=Kuechenhelfer-Backups  # the folder the copies get on a drive chosen by number
# Where plugged-in drives show up: macOS, Linux desktops (/media/<user>/<name>, /run/media/<user>/<name>), by hand
DRIVE_GLOBS='/Volumes/* /media/* /media/*/* /run/media/*/* /mnt/*'
WAIT_SECONDS=120  # how long "on" waits on a Mac for the result of the first copy

usage() {
  echo "Aufruf: kh/ops/backup_copy.sh on [<ordner>]|off|status|run [--scheduled]|decrypt <datei.zip.age>" >&2
  exit 2
}

# Stops with a clear reason.
fail() {
  echo "Kopie aufs Laufwerk: $1" >&2
  exit 1
}

# Ends a copy run with a clear reason, in the log and at Uptime Kuma.
stop_run() {  # message
  report down "Kopie aufs Laufwerk: $1"
  exit 1
}

# Prints an absolute path; the script changes into kh/ops before it uses one.
abs_path() {  # path
  case "$1" in /*) echo "$1" ;; *) echo "$(pwd)/$1" ;; esac
}

# True for an age public key: age1 and 58 more lowercase letters or digits.
valid_key() {  # key
  printf '%s\n' "$1" | grep -Eqx 'age1[0-9a-z]{58}'
}

# True if FILE starts like an age file.
is_age_file() {  # file
  [ "$(head -n 1 "$1" 2>/dev/null)" = "age-encryption.org/v1" ]
}

# Prints the disk a path lies on: df's device as one whole disk (whole_disk).
disk_of() {  # path
  whole_disk "$(df -P "$1" 2>/dev/null | awk 'NR == 2 { print $1 }')"
}

# Prints the whole disk of a device: volumes and partitions of one disk count as that disk, so a
# Mac's Recovery volume (/dev/disk3s5 next to the data on /dev/disk3s1) is no drive of its own.
# Other names, such as network shares, stay as they are.
# ponytail: a plain partition next to a Mac's APFS container (Boot Camp) still counts as another disk.
whole_disk() {  # device
  printf '%s\n' "$1" | sed -E -e 's#^(/dev/disk[0-9]+)s.*#\1#' \
    -e 's#^(/dev/(mmcblk[0-9]+|nvme[0-9]+n[0-9]+))p[0-9]+$#\1#' -e 's#^(/dev/(sd|hd|vd|xvd)[a-z]+)[0-9]+$#\1#'
}

# True if the drive is plugged in: the folder's parent exists and lies on another disk than the
# backups. Without the drive there is nothing, or an empty folder on this machine's own disk.
drive_ready() {  # folder source
  [ -d "$(dirname "$1")" ] || return 1
  drive=$(disk_of "$(dirname "$1")")
  [ -n "$drive" ] && [ "$drive" != "$(disk_of "$2")" ]
}

# True for a plugged-in drive: a folder with a disk of its own (so not a folder on a drive), not a
# link like macOS's "Macintosh HD", and not the disk the backups lie on.
is_drive() {  # folder source
  [ -d "$1" ] && [ ! -L "$1" ] || return 1
  own_disk=$(disk_of "$1")
  [ -n "$own_disk" ] && [ "$own_disk" != "$(disk_of "$(dirname "$1")")" ] && [ "$own_disk" != "$(disk_of "$2")" ]
}

# Prints the plugged-in drives under DRIVE_GLOBS, one per line.
drives() {  # source
  for candidate in $DRIVE_GLOBS; do
    ! is_drive "$candidate" "$1" || echo "$candidate"
  done
}

# Prints the free space on the drive of PATH as df shows it, e.g. 57Gi.
free_space() {  # path
  df -Ph "$1" 2>/dev/null | awk 'NR == 2 { print $4 }'
}

# Explains a failed write to the drive; on macOS that is usually the missing Full Disk Access.
no_access() {  # path
  if on_mac; then
    echo "kein Zugriff auf $1. macOS: /bin/dash braucht Festplattenvollzugriff (docs/kh/README.md)"
  else
    echo "kein Zugriff auf $1"
  fi
}

# Copies SRC to DEST under a temporary name, compares the copy and renames it only then, so a copy
# cut off halfway never carries the final name. The file gets REF's time: pruning goes by it.
store_file() {  # src dest [ref]
  part="$(dirname "$2")/.$(basename "$2").part"
  cp "$1" "$part" 2>/dev/null && cmp -s "$1" "$part" && touch -r "${3:-$1}" "$part" && mv "$part" "$2" \
    || { rm -f "$part"; return 1; }
}

# Prints the newest N backups in SOURCE that FOLDER has no copy of yet (named like the backup plus
# SUFFIX), newest first.
pending() {  # source folder n suffix
  ls -1t "$1"/*.zip 2>/dev/null | head -n "$3" | while read -r zip; do
    [ -f "$2/$(basename "$zip")$4" ] || echo "$zip"
  done
}

# Runs a command in the backup service's image, which has age and unzip; without a terminal, so
# stdin and stdout carry the data.
in_backup() {  # command...
  docker compose run --rm --no-deps -T backup "$@"
}

# Runs a command in the backup image with a terminal, so age can ask for the password.
in_backup_tty() {  # command...
  docker compose run --rm --no-deps backup "$@"
}

# Reads a backup zip on stdin, checks it and prints it encrypted for KEY.
encrypt() {  # key
  in_backup sh -c 'f=$(mktemp) && cat > "$f" && unzip -tq "$f" >/dev/null && age -r "$1" "$f"; rc=$?; rm -f "$f"; exit "$rc"' sh "$1"
}

# Puts the locked key on the drive if it is missing there. Never replaces a different key: the
# copies made with it could no longer be opened.
put_key() {  # local_key folder
  if [ -f "$2/$KEY_FILE" ]; then
    cmp -s "$1" "$2/$KEY_FILE" \
      || stop_run "auf dem Laufwerk liegt ein anderer Schlüssel; für einen neuen Schlüssel einen neuen Ordner nehmen"
  else
    store_file "$1" "$2/$KEY_FILE" || stop_run "$(no_access "$2")"
  fi
}

# One copy run: checks setup and drive, puts key and the restore guide (backup.sh's put_guide)
# there, copies the backups that have no copy yet (encrypted, or as they are with
# KH_BACKUP_COPY_KEY=none), then keeps the newest KH_BACKUP_KEEP copies on the drive.
run_cmd() {  # [--scheduled]
  case "${1:-}" in "") ;; --scheduled) SCHEDULED=1 ;; *) usage ;; esac
  dir=$(setting KH_BACKUP_COPY_DIR "")
  key=$(setting KH_BACKUP_COPY_KEY "")
  src=$(setting KH_BACKUP_DIR ./backups)
  keep=$(setting KH_BACKUP_KEEP 14)
  suffix=.age
  [ "$key" != none ] || suffix=""
  # plain copies need only the folder, encrypted ones also the public and the locked private key
  [ -n "$dir" ] && { [ -z "$suffix" ] || { valid_key "$key" && [ -f "$src/$KEY_FILE" ]; }; } \
    || stop_run "nicht eingerichtet, zuerst: kh/ops/backup_copy.sh on <ordner>"
  drive_ready "$dir" "$src" || stop_run "Laufwerk fehlt: $(dirname "$dir") ist nicht da oder liegt auf der eigenen Platte"
  [ -d "$dir" ] || mkdir "$dir" 2>/dev/null || stop_run "$(no_access "$dir")"
  [ -z "$suffix" ] || put_key "$src/$KEY_FILE" "$dir"
  put_guide "$dir" backup || stop_run "$(no_access "$dir")"
  WORK=$(mktemp -d ./.backup_copy.XXXXXX) || stop_run "Arbeitsordner fehlt"
  trap 'rm -rf "$WORK"' EXIT
  pending "$src" "$dir" "$keep" "$suffix" > "$WORK/list"
  new=0
  while read -r zip; do
    copy="$zip"
    if [ -n "$suffix" ]; then
      copy="$WORK/copy"
      encrypt "$key" < "$zip" > "$copy" && is_age_file "$copy" \
        || stop_run "$(basename "$zip") ließ sich nicht verschlüsseln (Backup beschädigt? Fehlt age im Backup-Image: docker compose build backup)"
    fi
    store_file "$copy" "$dir/$(basename "$zip")$suffix" "$zip" || stop_run "$(no_access "$dir")"
    new=$((new + 1))
  done < "$WORK/list"
  prune "$dir" "$keep" "zip$suffix"
  report up "Kopie aufs Laufwerk OK: $new neu, $(ls -1 "$dir"/*.zip"$suffix" 2>/dev/null | wc -l | tr -d ' ') auf dem Laufwerk"
}

# Makes a key pair in the backup image: age asks twice for the password and locks the private key
# with it, which lands in SOURCE; prints the public key. The open private key never touches a disk.
make_key() {  # source
  rm -f "$1/.copy-key.pub" "$1/.copy-key.age"
  echo "Gleich fragt age zweimal nach dem Passwort für die Kopien (Enter passphrase, Confirm passphrase)." >&2
  echo "Ohne dieses Passwort lässt sich keine Kopie mehr öffnen: gut merken oder sicher aufschreiben." >&2
  in_backup_tty sh -c 'key=$(age-keygen 2>/dev/null) &&
    printf "%s\n" "$key" | age-keygen -y > /backups-dest/.copy-key.pub &&
    printf "%s\n" "$key" | age -p -a -o /backups-dest/.copy-key.age &&
    { chown "$KH_PUID:$KH_PGID" /backups-dest/.copy-key.pub /backups-dest/.copy-key.age 2>/dev/null || true; }' >&2 \
    || return 1
  pub=$(cat "$1/.copy-key.pub" 2>/dev/null) && valid_key "$pub" && mv "$1/.copy-key.age" "$1/$KEY_FILE" || return 1
  rm -f "$1/.copy-key.pub"
  echo "$pub"
}

# Asks whether the copies get a password; prints "none" for no, nothing for yes.
ask_password() {
  echo "Kopien mit Passwort verschlüsseln? Ohne Passwort kann jeder mit dem Laufwerk die Backups lesen" >&2
  printf "und mit dem Backup-Schlüssel darin in die App (docs/kh/README.md, Stick verloren). (j/n) " >&2
  read -r answer || answer=""
  case "$answer" in
    j*|J*|y*|Y*) ;;
    n*|N*) echo none ;;
    *) return 1 ;;
  esac
}

# Explains how to prepare a drive for the copies, shown before the choice.
drive_guide() {
  echo "So bereitest du ein Laufwerk vor:"
  echo "  1. USB-Stick oder Festplatte als exFAT formatieren und benennen, z. B. KH-Backup"
  echo "     (Mac: Festplattendienstprogramm, „Löschen“). Achtung: Das löscht alles darauf."
  echo "  2. An diesen Rechner stecken, dann steht es unten in der Liste."
  if on_mac; then
    echo "  3. Einmal pro Mac: /bin/dash braucht Festplattenvollzugriff (docs/kh/README.md)."
  else
    echo "  3. Ohne Desktop hängt Linux es nicht selbst ein: dauerhaft einhängen, z. B. über /etc/fstab."
  fi
  echo "Ein Ordner geht auch, etwa auf einem Netzlaufwerk, aber nicht auf der eigenen Platte: Geht sie"
  echo "kaputt, wären Backups und Kopien zugleich weg. Am alten Ort bleiben die Kopien liegen."
}

# Asks where the copies go: shows the place now, how to prepare a drive and the plugged-in drives,
# then reads a number from the list or a folder with its full path. Prints the folder; fails on
# anything else. A typed drive gets FOLDER_NAME, like one chosen by number.
choose_folder() {  # source
  list=$(drives "$1")
  {
    echo "Backup-Ort ändern: Wohin kommen die nächtlichen Kopien der Backups?"
    echo "Bisher: $(setting KH_BACKUP_COPY_DIR "kein Ort eingerichtet")"
    echo
    drive_guide
    echo
    if [ -z "$list" ]; then echo "Eingesteckte Laufwerke: keines gefunden."; else echo "Eingesteckte Laufwerke:"; fi
    n=0
    printf '%s\n' "$list" | grep . | while IFS= read -r d; do
      n=$((n + 1)); echo "  $n) $(basename "$d"), frei: $(free_space "$d")"
    done
    printf "Nummer oder Ordner mit vollem Pfad (leer lassen: abbrechen): "
  } >&2
  read -r answer || answer=""
  case "$answer" in
    /*) if is_drive "${answer%/}" "$1"; then echo "${answer%/}/$FOLDER_NAME"; else echo "$answer"; fi ;;
    ""|0*|*[!0-9]*) return 1 ;;
    *) picked=$(printf '%s\n' "$list" | sed -n "${answer}p"); [ -n "$picked" ] && echo "$picked/$FOLDER_NAME" ;;
  esac
}

# Prints how many lines the log has, 0 without one.
log_lines() {
  if [ -f "$LOG" ]; then wc -l < "$LOG" | tr -d ' '; else echo 0; fi
}

# Waits up to WAIT_SECONDS for the copy the nightly job was just started for: its result is the
# first dated line (note) after the log's first BEFORE lines. Shows it, or where to look later.
wait_first_copy() {  # before
  waited=0
  while :; do
    result=$(tail -n +"$(($1 + 1))" "$LOG" 2>/dev/null | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2} ' | head -n 1)
    [ -z "$result" ] || { echo "$result"; return 0; }
    [ "$waited" -lt "$WAIT_SECONDS" ] || break
    sleep 2
    waited=$((waited + 2))
  done
  echo "Die erste Kopie läuft noch. Ergebnis später: kh/ops/backup_copy.sh status"
}

# Switches the copy on: checks the drive, asks once whether the copies get a password and then
# makes the key, enters the nightly job and starts the first copy. On macOS the first copy runs as
# the nightly job, which may read the drive; "on" waits for its result. Switching to another folder
# works the same way and keeps the password choice and the key.
turn_on() {  # folder (absolute)
  [ -f "$ENV_FILE" ] || fail "$(pwd)/$ENV_FILE fehlt (Vorlage: .env.example)"
  src=$(setting KH_BACKUP_DIR ./backups)
  drive_ready "$1" "$src" \
    || fail "$(dirname "$1") fehlt oder liegt auf derselben Platte wie $src: Laufwerk einstecken und einen Ordner darauf angeben, z. B. /Volumes/KH-Backup/Kuechenhelfer-Backups"
  key=$(setting KH_BACKUP_COPY_KEY "")
  [ -n "$key" ] || key=$(ask_password) || fail "Antwort j oder n erwartet"
  if [ "$key" != none ] && { ! valid_key "$key" || [ ! -f "$src/$KEY_FILE" ]; }; then
    key=$(make_key "$src") || fail "der Schlüssel ließ sich nicht anlegen (im Terminal aufrufen, über SSH mit ssh -t)"
  fi
  set_env_value "$ENV_FILE" KH_BACKUP_COPY_KEY "$key" || fail "$ENV_FILE ließ sich nicht schreiben"
  set_env_value "$ENV_FILE" KH_BACKUP_COPY_DIR "$1" || fail "$ENV_FILE ließ sich nicht schreiben"
  schedule_job "$(pwd)" || fail "der nächtliche Job ließ sich nicht eintragen"
  echo "Kopie aufs Laufwerk an: jede Nacht um $JOB_HOUR:$JOB_MINUTE Uhr nach $1."
  if on_mac; then
    before=$(log_lines)
    launchctl kickstart "gui/$(id -u)/$JOB_LABEL" || fail "die erste Kopie ließ sich nicht starten"
    echo "Die erste Kopie läuft ..."
    wait_first_copy "$before"
  else
    run_cmd
  fi
}

# Switches the copy off; settings, key and the copies on the drive stay.
turn_off() {
  unschedule_job || fail "der nächtliche Job ließ sich nicht austragen"
  echo "Kopie aufs Laufwerk aus. Wieder an: kh/ops/backup_copy.sh on <ordner>"
}

# Shows folder, key, nightly job and the last log entries. It does not look at the drive: over SSH,
# macOS hides removable drives; the nightly job's log tells how the copies went.
show_status() {
  dir=$(setting KH_BACKUP_COPY_DIR "")
  echo "Ordner: ${dir:-nicht eingerichtet (kh/ops/backup_copy.sh on <ordner>)}"
  key=$(setting KH_BACKUP_COPY_KEY "")
  if [ "$key" = none ]; then
    echo "Verschlüsselung: aus (ohne Passwort)"
  elif valid_key "$key"; then
    echo "Verschlüsselung: an (mit Passwort)"
  else
    echo "Verschlüsselung: noch nicht gewählt"
  fi
  if job_scheduled; then
    echo "Nächtlicher Job: eingetragen ($JOB_HOUR:$JOB_MINUTE Uhr)"
  else
    echo "Nächtlicher Job: nicht eingetragen"
  fi
  [ ! -f "$LOG" ] || { echo "Letzte Einträge im Log:"; tail -n 5 "$LOG"; }
}

# Decrypts a copy into the backup folder, where restore.sh finds it; age asks for the password.
# While that backup is still here, it only compares the two: a check of the copy. Takes the key
# next to the copy, or this machine's own.
decrypt_cmd() {  # file.zip.age (absolute)
  case "$1" in *.zip.age) ;; *) fail "keine Kopie (.zip.age): $1" ;; esac
  [ -f "$1" ] || fail "nicht gefunden: $1"
  src=$(setting KH_BACKUP_DIR ./backups)
  name=$(basename "$1" .age)
  keyfile="$(dirname "$1")/$KEY_FILE"
  [ -f "$keyfile" ] || keyfile="$src/$KEY_FILE"
  [ -f "$keyfile" ] || fail "kein Schlüssel ($KEY_FILE) neben der Kopie und keiner in $src"
  cp "$keyfile" "$src/.decrypt-key.age" && cp "$1" "$src/.decrypt-in.age" || fail "$(no_access "$1")"
  rc=0
  in_backup_tty sh -c 'age -d -i /backups-dest/.decrypt-key.age -o /backups-dest/.decrypt-out.zip /backups-dest/.decrypt-in.age &&
    unzip -tq /backups-dest/.decrypt-out.zip >/dev/null &&
    { chown "$KH_PUID:$KH_PGID" /backups-dest/.decrypt-out.zip 2>/dev/null || true; }' || rc=1
  rm -f "$src/.decrypt-key.age" "$src/.decrypt-in.age"
  out="$src/.decrypt-out.zip"
  [ "$rc" -eq 0 ] && [ -f "$out" ] || { rm -f "$out"; fail "Entschlüsseln fehlgeschlagen (falsches Passwort?)"; }
  if [ -e "$src/$name" ]; then
    cmp -s "$out" "$src/$name" && rc=0 || rc=1
    rm -f "$out"
    [ "$rc" -eq 0 ] || fail "die Kopie weicht vom Backup $src/$name ab"
    echo "Kopie geprüft: stimmt mit dem Backup $src/$name überein."
    return 0
  fi
  mv "$out" "$src/$name" || { rm -f "$out"; fail "$src/$name ließ sich nicht anlegen"; }
  echo "Entschlüsselt: $src/$name"
  echo "Wiederherstellen: docker compose -f kh/ops/docker-compose.yml run --rm --no-deps backup restore.sh $name"
}

main() {
  # cron, launchd and SSH on macOS do not find docker otherwise; appended, so the caller's PATH still wins
  PATH="$PATH:/usr/local/bin:/opt/homebrew/bin"
  export PATH
  [ $# -ge 1 ] || usage
  path=$(abs_path "${2:-}")
  cd "$(dirname "$0")"
  case "$1" in
    on)
      [ $# -le 2 ] || usage
      [ $# -eq 2 ] || path=$(choose_folder "$(setting KH_BACKUP_DIR ./backups)") \
        || fail "nichts geändert (eine Nummer aus der Liste oder einen Ordner mit vollem Pfad angeben)"
      turn_on "$path" ;;
    off) [ $# -eq 1 ] || usage; turn_off ;;
    status) [ $# -eq 1 ] || usage; show_status ;;
    run) [ $# -le 2 ] || usage; shift; run_cmd "$@" ;;
    decrypt) [ $# -eq 2 ] || usage; decrypt_cmd "$path" ;;
    *) usage ;;
  esac
}

[ "${1:-}" = "--lib" ] || main "$@"
