#!/bin/sh
# KH: measures this machine (architecture, CPU cores, RAM) and proposes a profile (P7.4, PLAN.md section 8).
# With --audio <file> and a running Whisper service it also times one transcription of your own recording of
# about 1 minute and says how the time compares to the length of the recording.
# Usage: kh/ops/hardware_test.sh [--audio <file> [--seconds <length>] [--url <whisper url>]]
set -eu

# Thresholds of the proposal (see PLAN.md section 8): under 4 GB or up to 4 cores is "leicht"; "normal" needs
# 8 GB; "stark" is Apple Silicon with 16 GB or 8 cores and more.
LIGHT_RAM_MB=4096
NORMAL_RAM_MB=7000  # a machine sold with 8 GB reports a little less
STRONG_APPLE_RAM_MB=16384
LIGHT_MAX_CORES=4
STRONG_MIN_CORES=8
# Transcription speed: up to 1 is faster than the recording, over 3 is too slow to wait for
REALTIME_FACTOR=1
SLOW_FACTOR=3
WHISPER_TIMEOUT=1800

# Loads update.sh's helpers (setting) without running it.
load_update_helpers() {
  set -- --lib
  . "$(dirname "$0")/update.sh"
}
load_update_helpers

usage() {
  echo "Aufruf: kh/ops/hardware_test.sh [--audio <datei> [--seconds <länge>] [--url <whisper-adresse>]]" >&2
  exit 2
}

# RAM in MB from the text of /proc/meminfo (kB).
ram_mb_from_meminfo() {  # meminfo_text
  printf '%s\n' "$1" | awk '/^MemTotal:/ { print int($2 / 1024) }'
}

# RAM in MB from bytes (macOS: sysctl hw.memsize).
ram_mb_from_bytes() {  # bytes
  echo $(($1 / 1048576))
}

# This machine's RAM in MB, or nothing if it cannot be read.
detect_ram_mb() {
  if [ -r /proc/meminfo ]; then
    ram_mb_from_meminfo "$(cat /proc/meminfo)"
  elif command -v sysctl >/dev/null 2>&1; then
    ram_mb_from_bytes "$(sysctl -n hw.memsize)"
  fi
}

# This machine's CPU cores.
detect_cores() {
  if command -v nproc >/dev/null 2>&1; then nproc; else sysctl -n hw.ncpu; fi
}

# The profile that fits: leicht for little RAM or few cores (a Raspberry Pi), stark for Apple Silicon with
# plenty of RAM or many cores, else normal. Stark also needs the RAM of normal.
propose_profile() {  # os arch cores ram_mb
  if [ "$4" -lt "$LIGHT_RAM_MB" ] || [ "$3" -le "$LIGHT_MAX_CORES" ] || [ "$4" -lt "$NORMAL_RAM_MB" ]; then
    echo leicht
  elif [ "$3" -ge "$STRONG_MIN_CORES" ] || { [ "$1" = Darwin ] && [ "$2" = arm64 ] && [ "$4" -ge "$STRONG_APPLE_RAM_MB" ]; }; then
    echo stark
  else
    echo normal
  fi
}

# The Whisper model a profile uses; the same table as PROFILE_MODELS in mealie/kh/drafts/whisper.py.
model_for_profile() {  # profile
  case "$1" in
    leicht) echo tiny ;;
    normal | lokal) echo base ;;
    stark) echo small ;;
    *) return 1 ;;
  esac
}

# The model to test: KH_WHISPER_MODEL if set (as the app does), else the profile's; fails for an unknown profile.
chosen_model() {  # profile
  model=$(setting KH_WHISPER_MODEL "")
  if [ -n "$model" ]; then echo "$model"; else model_for_profile "$1"; fi
}

# The server's full model name for a size like "small" or an already full name; as whisper_model() in whisper.py.
whisper_model_name() {  # size_or_name
  case "$1" in */*) echo "$1" ;; *) echo "Systran/faster-whisper-$1" ;; esac
}

# Length of a recording in whole seconds: the given value, else ffprobe's.
audio_seconds() {  # file given_seconds
  length=$2
  if [ -z "$length" ] && command -v ffprobe >/dev/null 2>&1; then
    length=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$1")
  fi
  [ -n "$length" ] || { echo "Länge der Aufnahme unbekannt: ffprobe fehlt, gib sie mit --seconds <Sekunden> an." >&2; return 1; }
  awk -v s="$length" 'BEGIN { printf "%d\n", s + 0.5 }'
}

# What the time of one transcription means, as a sentence.
speed_verdict() {  # audio_seconds transcription_seconds
  awk -v a="$1" -v t="$2" -v ok="$REALTIME_FACTOR" -v slow="$SLOW_FACTOR" 'BEGIN {
    f = t / a
    if (f <= ok) text = "schneller als die Aufnahme dauert, das Profil passt."
    else if (f <= slow) text = "Die Umwandlung dauert länger als die Aufnahme, aber noch brauchbar im Hintergrund."
    else text = "zu langsam, nimm das nächstkleinere Profil oder Modell."
    printf "Faktor %.2f: %s\n", f, text
  }'
}

# Times one transcription of FILE on the Whisper server at URL; prints the seconds. Fails on an error answer (-f).
time_transcription() {  # url model file
  curl -sf -o /dev/null -w '%{time_total}' --max-time "$WHISPER_TIMEOUT" \
    -F "file=@$3" -F "model=$(whisper_model_name "$2")" -F language=de "$1/v1/audio/transcriptions"
}

# The measurement: reachability, the model's download, the timed run and the verdict.
measure_audio() {  # file seconds url model
  curl -sf --max-time 5 "$3/health" >/dev/null || { echo "Whisper unter $3 nicht erreichbar: läuft der Dienst (docker compose --profile whisper up -d whisper)?" >&2; return 1; }
  length=$(audio_seconds "$1" "$2") || return 1
  curl -s -o /dev/null --max-time "$WHISPER_TIMEOUT" -X POST "$3/v1/models/$(whisper_model_name "$4")" || true
  echo "Umwandlung mit dem Modell $4, $length s Aufnahme ..."
  took=$(time_transcription "$3" "$4" "$1") \
    || { echo "Die Umwandlung bei $3 ist fehlgeschlagen (Fehlerantwort des Servers): Modell und Dienst prüfen." >&2; return 1; }
  echo "Dauer: $took s. $(speed_verdict "$length" "$took")"
}

main() {
  cd "$(dirname "$0")"
  audio="" seconds="" url=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --audio) [ $# -ge 2 ] || usage; audio=$2; shift 2 ;;
      --seconds) [ $# -ge 2 ] || usage; seconds=$2; shift 2 ;;
      --url) [ $# -ge 2 ] || usage; url=$2; shift 2 ;;
      *) usage ;;
    esac
  done
  os=$(uname -s) arch=$(uname -m) cores=$(detect_cores) ram=$(detect_ram_mb)
  [ -n "$ram" ] || { echo "Arbeitsspeicher nicht lesbar." >&2; exit 1; }
  profile=$(propose_profile "$os" "$arch" "$cores" "$ram")
  echo "System: $os $arch, $cores Prozessorkerne, $((ram / 1024)) GB Arbeitsspeicher"
  echo "Vorschlag: KH_PROFILE=$profile (Whisper-Modell $(model_for_profile "$profile"))"
  if [ -n "$audio" ]; then
    [ -f "$audio" ] || { echo "Datei nicht gefunden: $audio" >&2; exit 1; }
    profile_set=$(setting KH_PROFILE leicht)
    model=$(chosen_model "$profile_set") \
      || { echo "KH_PROFILE=$profile_set ist ungültig (leicht, normal, stark oder lokal)." >&2; exit 1; }
    measure_audio "$audio" "$seconds" "${url:-http://localhost:$(setting KH_WHISPER_PORT 8000)}" "$model"
  fi
}

[ "${1:-}" = "--lib" ] || main "$@"
