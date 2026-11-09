#!/bin/sh
# KH: tests the decisions of hardware_test.sh without measuring anything: reading RAM, the profile proposal at
# its thresholds, the model per profile and the verdict on a measured transcription.
set -eu

here=$(cd "$(dirname "$0")" && pwd)
set -- --lib
. "$here/hardware_test.sh"

failures=0

# Reports a failed check without stopping, so all checks run.
check() {
  if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1: expected '$3', got '$2'"; failures=$((failures + 1)); fi
}

# --- RAM from /proc/meminfo (kB) and from sysctl hw.memsize (bytes), in MB ---
check "meminfo 8 GB" "$(ram_mb_from_meminfo 'MemTotal:        8165432 kB
MemFree:         1000000 kB')" "7974"
check "memsize 16 GB" "$(ram_mb_from_bytes 17179869184)" "16384"

# --- profile proposal: os arch cores ram_mb ---
check "Raspberry Pi 5, 8 GB, 4 cores" "$(propose_profile Linux aarch64 4 8000)" "leicht"
check "old laptop, 2 GB" "$(propose_profile Linux x86_64 8 2000)" "leicht"
check "3.9 GB is under the limit" "$(propose_profile Linux x86_64 8 3900)" "leicht"
check "4 cores are still light" "$(propose_profile Linux x86_64 4 16000)" "leicht"
check "5 cores, 6 GB too little for normal" "$(propose_profile Linux x86_64 6 6000)" "leicht"
check "mini PC 6 cores, 8 GB" "$(propose_profile Linux x86_64 6 8000)" "normal"
check "intel mac 6 cores, 16 GB" "$(propose_profile Darwin x86_64 6 16384)" "normal"
check "apple silicon 8 cores, 8 GB" "$(propose_profile Darwin arm64 8 8192)" "stark"
check "apple silicon 16 GB" "$(propose_profile Darwin arm64 10 16384)" "stark"
check "8 cores, 8 GB, x86" "$(propose_profile Linux x86_64 8 8192)" "stark"
check "8 cores but only 4 GB" "$(propose_profile Linux x86_64 8 4096)" "leicht"

# --- the Whisper model of a profile (same table as PROFILE_MODELS in mealie/kh/drafts/whisper.py) ---
check "model leicht" "$(model_for_profile leicht)" "tiny"
check "model normal" "$(model_for_profile normal)" "base"
check "model stark" "$(model_for_profile stark)" "small"
check "model lokal" "$(model_for_profile lokal)" "base"
check "model of an unknown profile" "$(model_for_profile turbo || true)" ""

# --- verdict: audio seconds, transcription seconds ---
check "faster than real time" "$(speed_verdict 60 30)" "Faktor 0.50: schneller als die Aufnahme dauert, das Profil passt."
check "slower than real time" "$(speed_verdict 60 120)" "Faktor 2.00: Die Umwandlung dauert länger als die Aufnahme, aber noch brauchbar im Hintergrund."
check "much slower" "$(speed_verdict 60 300)" "Faktor 5.00: zu langsam, nimm das nächstkleinere Profil oder Modell."

# --- seconds: from --seconds, else ffprobe, else a request to pass --seconds ---
check "seconds given" "$(audio_seconds nofile 61.7)" "62"
check "no seconds and no ffprobe" "$(PATH=/nonexistent audio_seconds nofile '' 2>&1 || true)" "Länge der Aufnahme unbekannt: ffprobe fehlt, gib sie mit --seconds <Sekunden> an."

# --- the measurement with a stand-in curl: health and model download answer, the timed run reports 30 s ---
stub=$(mktemp -d)
trap 'rm -rf "$stub"' EXIT
cat >"$stub/curl" <<'STUB'
#!/bin/sh
case "$*" in
  *time_total*failing.test*) exit 22 ;;  # curl -f: the server answered with an error status
  *time_total*) printf '30.2' ;;
  *unreachable*) exit 7 ;;
esac
STUB
chmod +x "$stub/curl"
echo audio >"$stub/memo.m4a"
out=$(PATH="$stub:$PATH" measure_audio "$stub/memo.m4a" 60 http://whisper.test base)
check "measurement reports the time and the verdict" "$out" "Umwandlung mit dem Modell base, 60 s Aufnahme ...
Dauer: 30.2 s. Faktor 0.50: schneller als die Aufnahme dauert, das Profil passt."
check "unreachable Whisper stops" "$(PATH="$stub:$PATH" measure_audio "$stub/memo.m4a" 60 http://unreachable.test base >/dev/null 2>&1 && echo ok || echo stop)" "stop"

check "a failing request is an error, not a verdict" "$(PATH="$stub:$PATH" measure_audio "$stub/memo.m4a" 60 http://failing.test base 2>&1 || true)" "Umwandlung mit dem Modell base, 60 s Aufnahme ...
Die Umwandlung bei http://failing.test ist fehlgeschlagen (Fehlerantwort des Servers): Modell und Dienst prüfen."

# --- KH_WHISPER_MODEL wins over the profile's model; a bad KH_PROFILE is explained ---
check "profile model" "$(chosen_model stark)" "small"
check "KH_WHISPER_MODEL wins" "$(KH_WHISPER_MODEL=medium chosen_model stark)" "medium"
check "full model names stay" "$(whisper_model_name small) $(whisper_model_name org/own)" "Systran/faster-whisper-small org/own"
check "bad profile is explained" "$(KH_PROFILE=foo sh "$here/hardware_test.sh" --audio "$stub/memo.m4a" 2>&1 >/dev/null | tail -1)" "KH_PROFILE=foo ist ungültig (leicht, normal, stark oder lokal)."

# --- arguments ---
check "unknown option" "$(sh "$here/hardware_test.sh" --nope >/dev/null 2>&1 && echo ok || echo stop)" "stop"

[ "$failures" -eq 0 ] || { echo "$failures Prüfung(en) fehlgeschlagen"; exit 1; }
echo "Alle Prüfungen bestanden"
