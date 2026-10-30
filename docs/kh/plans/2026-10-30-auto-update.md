# Automatische Updates (D29) · Umsetzungsplan

> **Für ausführende Agenten:** Pflicht-Skill: superpowers:subagent-driven-development (empfohlen) oder superpowers:executing-plans, Aufgabe für Aufgabe. Schritte nutzen Checkboxen (`- [ ]`).

**Ziel:** Jede Installation holt nachts die neueste stabile Version für ihren Prozessortyp und spielt sie über `update.sh` ein; standardmäßig an, per `KH_AUTO_UPDATE` abschaltbar.

**Architektur:** Ein Skript `kh/ops/auto_update.sh` auf dem Server (Befehle `on|off|status|check|run`), gestartet von cron. Es fragt die Registry nach Tags, holt das neue Image, packt die mitgelieferten Betriebsdateien aus `/app/kh-bundle` aus und ruft das neue `update.sh` auf. Release-Images bekommen die Betriebsdateien per Dockerfile; `check_bundle.sh` prüft sie vor jedem Hochladen.

**Technik:** POSIX-sh, curl, Docker CLI und Compose, cron, GitHub Container Registry (Token- und Tag-Schnittstelle).

**Spezifikation:** `docs/kh/specs/2026-10-30-auto-update-design.md`

## Feste Vorgaben

- Nur POSIX-sh; jedes Skript läuft unter macOS-sh, Debian-dash und Alpine-ash (wie die übrigen Betriebs-Skripte). Kein `\|` in `sed` (BSD-sed kann das nicht), Muster mit `grep -E` oder `case`.
- Muster der vorhandenen Skripte: `set -eu`, `--lib` lädt nur Funktionen, Funktionen in `||`- oder `if !`-Zusammenhang geben Fehler ausdrücklich mit `return 1` zurück; Helfer aus `update.sh` wiederverwenden (`setting`, `set_env_value`, `env_value`, `valid_image`, `image_id`).
- Jede neue Datei beginnt mit 1 bis 3 Zeilen Zweck, jede Funktion hat eine Kurzbeschreibung; Code und Kommentare englisch, Meldungen an Menschen deutsch.
- Stabil heißt `^v[0-9]+\.[0-9]+(\.[0-9]+)?-(amd64|arm64)$`; `-rc` wird nie gewählt.
- Job: `0 4 * * *`, erkennbar am Kommentar `# kh-auto-update`.
- Paket im Image: `/app/kh-bundle/kh/ops/…` und `/app/kh-bundle/mealie/core/settings/settings.py`.
- `.env`: `KH_AUTO_UPDATE` (fehlt = `true`), `KH_REGISTRY_USER`, `KH_REGISTRY_TOKEN`, `KH_UPDATE_PUSH_URL`.
- Arbeitsdateien in `kh/ops`: `auto_update.log`, `.auto_update.lock/`, `.auto_update.failed`, `.auto_update.XXXXXX/`.
- Exit-Codes von `auto_update.sh`: 0 erledigt oder nichts zu tun, 1 Fehler, 2 falscher Aufruf, 3 Notfall.
- Registry: `https://<registry>/token?scope=repository:<repo>:pull&service=<registry>`, dann `https://<registry>/v2/<repo>/tags/list?n=1000` (so liefert GHCR am 30.10.2026 `{"name":…,"tags":[…]}`).
- Änderungen an Mealie-Dateien mit `KH: <Grund>` kommentieren. Keine echten Zugangsdaten in Tests; Platzhalter wie `user` und `secret`.
- Ein eigenes `DOCKER_CONFIG` nur für `docker pull`: Auf dem Mac mini liegt das Compose-Plugin in `~/.docker/cli-plugins`, und Docker ist nur über den Colima-Kontext erreichbar (`/var/run/docker.sock` fehlt).

## Review-Schwerpunkte

1. **Vorhandene Crontab:** andere Jobs bleiben erhalten, `on` zweimal ergibt genau eine Zeile, keine Crontab vorhanden ist kein Fehler (Tests in Task 2).
2. **Pfad mit Leerzeichen** (`/Users/x/Mein Server/kh/ops`): Crontab-Zeile richtig in Anführungszeichen, Einspielen klappt (Tests in Task 2 und 4).
3. **Registry nicht erreichbar oder Schlüssel abgelehnt:** `check` und `run` enden mit 1 und deutscher Meldung, nichts wird verändert (Test in Task 5 mit Registry `127.0.0.1:9`).
4. **Verwaiste Sperre** nach Absturz oder Stromausfall: Der nächste Lauf übernimmt sie, statt für immer auszusetzen (Test in Task 4).
5. **Reihenfolge der Versionen** über eine Stelle hinaus und mit `-rc`: `v0.10` > `v0.9`, `v1.0` > `v0.9.9`, `v0.1` > `v0.1-rc.3`, Tags des anderen Prozessortyps zählen nicht (Tests in Task 1).

---

### Task 1: Versionslogik

**Dateien:**
- Neu: `kh/ops/auto_update.sh`, `kh/ops/test_auto_update.sh`
- Ändern: `.github/workflows/kh-ci.yml` (Job `ops`, neuer Schritt nach „Tunnel script tests“)

**Schnittstellen:**
- Nutzt: `update.sh --lib` (geladen zuerst, dann eigene Funktionen, wie in `tunnel.sh`).
- Liefert:
  - `parse_image REF` → eine Zeile `registry repo version arch`; `return 1`, wenn kein Release-Image.
  - `is_stable_tag TAG ARCH` → 0 oder 1.
  - `version_gt A B` → 0, wenn Version A neuer als B (Versionen ohne Prozessortyp, z. B. `v0.1.2`, `v0.0-rc.2`).
  - `tags_from_json JSON` → Tags, eine pro Zeile.
  - `newest_stable TAGS ARCH CURRENT [SKIP]` → neuester stabiler Tag (mit Prozessortyp) neuer als `CURRENT`, ungleich `SKIP`; sonst keine Ausgabe.

- [ ] **Schritt 1: Tests schreiben.** Kopf wie `test_update.sh`: `here`, `tmp` mit `trap` zum Aufräumen, `failures`, `check NAME IST SOLL`, `yes_no BEFEHL…`; lädt `auto_update.sh --lib`; letzte Zeile `all auto-update tests passed` oder `N check(s) failed` mit Exit 1.

```sh
check "parse ghcr rc" "$(parse_image ghcr.io/gamingnet006/own-recipe-app:v0.0-rc.2-amd64)" "ghcr.io gamingnet006/own-recipe-app v0.0-rc.2 amd64"
check "parse patch" "$(parse_image ghcr.io/x/y:v0.1.2-arm64)" "ghcr.io x/y v0.1.2 arm64"
check "parse registry with port" "$(parse_image 127.0.0.1:5000/x/y:v1.0-amd64)" "127.0.0.1:5000 x/y v1.0 amd64"
for ref in kuechenhelfer:dev ghcr.io/x/y:latest ghcr.io/x/y:v0.1 ghcr.io/x/y:v0.1-s390x ghcr.io/x/y@sha256:0000 x/y:v0.1-amd64; do
  check "no release image: $ref" "$(yes_no parse_image "$ref")" "no"
done
check "stable" "$(yes_no is_stable_tag v0.1-amd64 amd64)" "yes"
check "stable patch" "$(yes_no is_stable_tag v0.1.3-amd64 amd64)" "yes"
check "rc is not stable" "$(yes_no is_stable_tag v0.1-rc.1-amd64 amd64)" "no"
check "other arch" "$(yes_no is_stable_tag v0.1-arm64 amd64)" "no"
check "suffix after arch" "$(yes_no is_stable_tag v0.1-amd64-old amd64)" "no"
check "v0.1 > v0.0" "$(yes_no version_gt v0.1 v0.0)" "yes"
check "v0.10 > v0.9" "$(yes_no version_gt v0.10 v0.9)" "yes"
check "v1.0 > v0.9.9" "$(yes_no version_gt v1.0 v0.9.9)" "yes"
check "v0.1.1 > v0.1" "$(yes_no version_gt v0.1.1 v0.1)" "yes"
check "v0.1 = v0.1.0" "$(yes_no version_gt v0.1 v0.1.0)$(yes_no version_gt v0.1.0 v0.1)" "nono"
check "final > rc" "$(yes_no version_gt v0.0 v0.0-rc.2)" "yes"
check "rc.3 > rc.2" "$(yes_no version_gt v0.0-rc.3 v0.0-rc.2)" "yes"
check "rc < final" "$(yes_no version_gt v0.0-rc.2 v0.0)" "no"
check "next rc > old final" "$(yes_no version_gt v0.1-rc.1 v0.0)" "yes"
check "tags from json" "$(tags_from_json '{"name":"x/y","tags":["v0.0-rc.1-amd64","v0.0-amd64","v0.0-arm64"]}' | tr '\n' ' ')" "v0.0-rc.1-amd64 v0.0-amd64 v0.0-arm64 "
check "repo name is no tag" "$(tags_from_json '{"name":"v-repo/y","tags":["v0.1-amd64"]}')" "v0.1-amd64"
check "no tags" "$(tags_from_json '{"name":"x/y","tags":null}')" ""
check "error answer" "$(tags_from_json '{"errors":[{"code":"DENIED"}]}')" ""
tags="v0.0-rc.2-amd64 v0.0-amd64 v0.1-amd64 v0.1-arm64 v0.2-rc.1-amd64 v0.10-amd64 v0.9-amd64"
check "newest stable" "$(newest_stable "$tags" amd64 v0.0-rc.2)" "v0.10-amd64"
check "already newest" "$(newest_stable "$tags" amd64 v0.10)" ""
check "skip failed" "$(newest_stable "$tags" amd64 v0.0-rc.2 v0.10-amd64)" "v0.9-amd64"
check "other arch" "$(newest_stable "$tags" arm64 v0.0)" "v0.1-arm64"
```

`TAGS` ist eine Liste mit Leerzeichen oder Zeilenumbrüchen.

- [ ] **Schritt 2: Tests laufen lassen, sie scheitern**

Run: `sh kh/ops/test_auto_update.sh`
Expected: `FAIL` bei allen Prüfungen mit „yes“ und erwarteter Ausgabe (Funktionen fehlen), Exit 1.

- [ ] **Schritt 3: Funktionen in `kh/ops/auto_update.sh` umsetzen**

Grundgerüst: Kopfkommentar (Zweck, Aufruf), `set -eu`, `load_update_helpers` wie in `tunnel.sh`, `usage` (Exit 2, Text „Aufruf: kh/ops/auto_update.sh on|off|status|check|run [--scheduled]“), `main` nur mit Aufruf-Prüfung, `--lib`-Wächter.
- `parse_image`: `@` ablehnen; Tag = Teil nach dem letzten `:` hinter dem letzten `/`; Registry = erstes Pfadstück, nur gültig, wenn es `.` oder `:` enthält; Prozessortyp per `case` (`*-amd64`, `*-arm64`); Version = Tag ohne `-<arch>`, geprüft mit `grep -Eq '^v[0-9]+\.[0-9]+(\.[0-9]+)?(-rc\.[0-9]+)?$'`.
- `version_gt`: in awk `vX.Y[.Z][-rc.N]` zerlegen in X, Y, Z (fehlend 0) und R (fertige Version: sehr groß, sonst N); X, Y, Z, R nacheinander numerisch vergleichen.
- `tags_from_json`: erst den Inhalt von `"tags":[…]` herausschneiden, dann an Kommas trennen und Anführungszeichen entfernen.

- [ ] **Schritt 4: Tests laufen lassen, sie sind grün**

Run: `sh kh/ops/test_auto_update.sh && for i in debian:bookworm-slim alpine:3.22; do docker run --rm -v "$PWD/kh/ops":/ops:ro "$i" sh -c 'cd /ops && sh test_auto_update.sh' | tail -1; done`
Expected: dreimal `all auto-update tests passed`.

- [ ] **Schritt 5: CI-Schritt eintragen** in `kh-ci.yml`: `- name: Auto-update script tests` mit `run: sh kh/ops/test_auto_update.sh`.

- [ ] **Schritt 6: Commit**

```bash
git add kh/ops/auto_update.sh kh/ops/test_auto_update.sh .github/workflows/kh-ci.yml
git commit -m "Auto-update: version logic for stable releases (D29)"
```

### Task 2: Schalter und nächtlicher Job (`on`, `off`, `status`)

**Dateien:** Ändern `kh/ops/auto_update.sh`, `kh/ops/test_auto_update.sh`, `kh/ops/.env.example`, `.gitignore`

**Schnittstellen:**
- Liefert: `auto_update_enabled` (0 = an; aus nur bei `false`, `0`, `no`, `off`, Groß- und Kleinschreibung egal), `cron_line OPS_DIR`, `crontab_with CURRENT LINE`, `crontab_without CURRENT`; Konstanten `CRON_MARK='# kh-auto-update'`, `LOG=auto_update.log`, `FAILED=.auto_update.failed`; Befehle `on`, `off`, `status`.

- [ ] **Schritt 1: Tests schreiben**

```sh
ENV_FILE="$tmp/.env"; : > "$ENV_FILE"; unset KH_AUTO_UPDATE
check "on when missing" "$(yes_no auto_update_enabled)" "yes"
for v in true TRUE 1 yes; do printf 'KH_AUTO_UPDATE=%s\n' "$v" > "$ENV_FILE"; check "on: $v" "$(yes_no auto_update_enabled)" "yes"; done
for v in false FALSE 0 no off; do printf 'KH_AUTO_UPDATE=%s\n' "$v" > "$ENV_FILE"; check "off: $v" "$(yes_no auto_update_enabled)" "no"; done
check "cron line" "$(cron_line /srv/kh/ops)" "0 4 * * * '/srv/kh/ops/auto_update.sh' run --scheduled >> '/srv/kh/ops/auto_update.log' 2>&1 # kh-auto-update"
check "cron line with space" "$(cron_line '/Users/x/Mein Server/kh/ops')" "0 4 * * * '/Users/x/Mein Server/kh/ops/auto_update.sh' run --scheduled >> '/Users/x/Mein Server/kh/ops/auto_update.log' 2>&1 # kh-auto-update"
line=$(cron_line /srv/kh/ops); other=$(printf 'MAILTO=""\n5 * * * * /usr/bin/true')
check "empty crontab" "$(crontab_with "" "$line")" "$line"
check "keeps other jobs" "$(crontab_with "$other" "$line")" "$(printf '%s\n%s' "$other" "$line")"
check "on twice, one line" "$(crontab_with "$(crontab_with "$other" "$line")" "$line" | grep -c 'kh-auto-update')" "1"
check "off keeps other jobs" "$(crontab_without "$(crontab_with "$other" "$line")")" "$other"
check "usage without command" "$(sh "$here/auto_update.sh" >/dev/null 2>&1 && echo 0 || echo $?)" "2"
check "usage unknown command" "$(sh "$here/auto_update.sh" start >/dev/null 2>&1 && echo 0 || echo $?)" "2"
```

- [ ] **Schritt 2: Tests laufen lassen, die neuen scheitern** (`sh kh/ops/test_auto_update.sh`, Exit 1).

- [ ] **Schritt 3: Umsetzen.** `on`: `.env` muss existieren (sonst `abort`), `set_env_value .env KH_AUTO_UPDATE true`, `crontab -l 2>/dev/null || true` lesen, `crontab_with … | crontab -`, Meldung „Automatische Updates an: jede Nacht um 4 Uhr“. `off`: `false` setzen, `crontab_without … | crontab -`, Meldung. `status`: Schalter, Job eingetragen ja/nein, `KH_IMAGE`, Inhalt von `.auto_update.failed`, `tail -n 5 auto_update.log`. Der Pfad in der Crontab-Zeile ist das absolute `kh/ops`.
`.env.example`: Abschnitt „--- Automatische Updates (D29) ---“ mit den vier Schlüsseln und Kommentaren wie in der Spezifikation (Schlüssel leer, `KH_AUTO_UPDATE=true`).
`.gitignore` (KH-Block): `kh/ops/auto_update.log` und `kh/ops/.auto_update.*`.

- [ ] **Schritt 4: Tests in sh, dash und ash grün** (Befehl aus Aufgabe 1, Schritt 4).

- [ ] **Schritt 5: Commit** `git commit -m "Auto-update: switch and nightly cron job (on, off, status)"` mit den vier Dateien.

### Task 3: Betriebsdateien im Image

**Dateien:**
- Neu: `kh/ops/check_bundle.sh`
- Ändern: `docker/Dockerfile` (Stufe `production`, direkt vor `ENTRYPOINT`), `.dockerignore`, `kh/ops/release.sh` (`main`, nach Schritt 1), `.github/workflows/kh-release.yml` (nach „Build amd64 image“), `kh/ops/test_auto_update.sh`

**Schnittstellen:**
- Liefert: `bundle_problems LISTING` in `check_bundle.sh` (eine deutsche Zeile pro Problem, leer = in Ordnung) und den Aufruf `sh kh/ops/check_bundle.sh IMAGE` (Exit 0, 1 oder 2).
- Pflicht im Paket: `kh/ops/update.sh`, `kh/ops/auto_update.sh`, `kh/ops/docker-compose.yml`, `mealie/core/settings/settings.py`.
- Verboten: `kh/ops/.env`, `kh/ops/.env.*` außer `kh/ops/.env.example`, alles unter `kh/ops/data/`, `kh/ops/backups/`, `kh/ops/data.pre-update/`, `kh/ops/.upgrade-test.*`, `kh/ops/auto_update.log`, `kh/ops/.auto_update.*`.

- [ ] **Schritt 1: Tests schreiben** (in `test_auto_update.sh`, `check_bundle.sh --lib` laden)

```sh
ok=$(printf '%s\n' kh/ops/update.sh kh/ops/auto_update.sh kh/ops/docker-compose.yml kh/ops/.env.example mealie/core/settings/settings.py)
check "complete bundle" "$(bundle_problems "$ok")" ""
check "update.sh missing" "$(bundle_problems "$(printf '%s\n' "$ok" | grep -v update.sh)" | grep -c 'kh/ops/update.sh')" "1"
for bad in kh/ops/.env kh/ops/.env.pre-update kh/ops/data/mealie.db kh/ops/backups/a.zip kh/ops/auto_update.log kh/ops/.auto_update.failed; do
  check "forbidden: $bad" "$(yes_no test -n "$(bundle_problems "$(printf '%s\n%s' "$ok" "$bad")")")" "yes"
done
```

- [ ] **Schritt 2: Tests scheitern** (`sh kh/ops/test_auto_update.sh`).

- [ ] **Schritt 3: `check_bundle.sh` umsetzen.** `main IMAGE`: `docker run --rm --entrypoint sh IMAGE -c 'cd /app/kh-bundle && find . -type f'`, führendes `./` entfernen, `bundle_problems`; bei Problemen auf stderr und Exit 1, sonst „Betriebsdateien im Image in Ordnung“.

- [ ] **Schritt 4: Dockerfile, `.dockerignore`, Release-Prüfung**
  - Dockerfile, mit Kommentar `# KH: ship the ops files with every image, so auto_update.sh can install the matching compose file and scripts without git on the server (D29).`: `COPY kh/ops /app/kh-bundle/kh/ops` und `COPY mealie/core/settings/settings.py /app/kh-bundle/mealie/core/settings/settings.py`.
  - `.dockerignore`, KH-Block: `kh/ops/.env`, `kh/ops/.env.*`, `!kh/ops/.env.example`, `kh/ops/data`, `kh/ops/data.pre-update`, `kh/ops/backups`, `kh/ops/.upgrade-test.*`, `kh/ops/auto_update.log`, `kh/ops/.auto_update.*`.
  - `release.sh` nach `build_arm64`: `sh kh/ops/check_bundle.sh "$arm64" || fail "das arm64-Image hat keine vollständigen Betriebsdateien oder enthält private Dateien"`.
  - `kh-release.yml` nach dem Build: Schritt `Check ops bundle` mit `run: sh kh/ops/check_bundle.sh "$IMAGE:$TAG-amd64"`.

- [ ] **Schritt 5: Tests grün in sh, dash und ash; Probe mit echtem Build-Kontext** (der Arbeitsordner auf dem Mac enthält eine echte `.env` und `data/`):

```bash
printf 'FROM busybox:1.37\nCOPY kh/ops /app/kh-bundle/kh/ops\nCOPY mealie/core/settings/settings.py /app/kh-bundle/mealie/core/settings/settings.py\n' | docker build -q -t kh-bundle-probe -f - . && sh kh/ops/check_bundle.sh kh-bundle-probe; docker rmi kh-bundle-probe >/dev/null
```

Expected: `Betriebsdateien im Image in Ordnung`. Danach dieselbe Probe ohne den `.dockerignore`-Block: Sie muss „darf nicht ins Image“ melden. Den Block danach wiederherstellen.

- [ ] **Schritt 6: Commit** `git commit -m "Release images carry the ops files; check_bundle.sh guards every upload (D29)"` mit allen Dateien der Aufgabe.

### Task 4: Bausteine für einen Lauf

**Dateien:** Ändern `kh/ops/auto_update.sh`, `kh/ops/test_auto_update.sh`

**Schnittstellen:**
- Liefert:
  - `take_lock DIR` (0 = erhalten, legt `DIR/pid` mit `$$` an; 1 = ein lebender Prozess hält sie; übernimmt, wenn der Prozess nicht mehr lebt oder `pid` fehlt) und `release_lock DIR`.
  - `install_bundle STAGING ROOT`: kopiert den Inhalt von `STAGING` über `ROOT`; Fehler gibt 1 zurück.
  - `docker_auth_json REGISTRY USER TOKEN`.
  - `mark_failed TAG`, `failed_tag`, `clear_failed` auf der Datei `$FAILED`.

- [ ] **Schritt 1: Tests schreiben**

```sh
lock="$tmp/lock"
check "take lock" "$(yes_no take_lock "$lock")$(cat "$lock/pid")" "yes$$"
check "held by live process" "$(yes_no take_lock "$lock")" "no"
sh -c 'exit 0' & dead=$!; wait "$dead"; echo "$dead" > "$lock/pid"
check "stale lock taken over" "$(yes_no take_lock "$lock")" "yes"
release_lock "$lock"; check "lock released" "$(yes_no test -e "$lock")" "no"
root="$tmp/Mein Server"; mkdir -p "$root/kh/ops/data" "$tmp/stage/kh/ops"
echo secret-placeholder > "$root/kh/ops/.env"; echo db > "$root/kh/ops/data/mealie.db"; echo old > "$root/kh/ops/update.sh"
echo new > "$tmp/stage/kh/ops/update.sh"; echo added > "$tmp/stage/kh/ops/new.sh"
install_bundle "$tmp/stage" "$root"
check "file replaced" "$(cat "$root/kh/ops/update.sh")" "new"
check "file added" "$(cat "$root/kh/ops/new.sh")" "added"
check ".env untouched" "$(cat "$root/kh/ops/.env")" "secret-placeholder"
check "data untouched" "$(cat "$root/kh/ops/data/mealie.db")" "db"
check "auth json" "$(docker_auth_json ghcr.io user secret)" '{"auths":{"ghcr.io":{"auth":"dXNlcjpzZWNyZXQ="}}}'
FAILED="$tmp/failed"; mark_failed v0.1-amd64
check "failed tag" "$(failed_tag)" "v0.1-amd64"
clear_failed; check "failed cleared" "$(failed_tag)" ""
```

- [ ] **Schritt 2: Tests scheitern.**
- [ ] **Schritt 3: Umsetzen** (`take_lock` mit `mkdir` als atomarer Sperre; lebt der Prozess, prüft `kill -0`; `install_bundle` mit `cp -R "$1/." "$2/"`; Base64 mit `base64 | tr -d '\n'`).
- [ ] **Schritt 4: Tests grün in sh, dash und ash.**
- [ ] **Schritt 5: Commit** `git commit -m "Auto-update: lock, bundle install, registry auth and failed-version marker"`

### Task 5: Befehle `check` und `run`

**Dateien:** Ändern `kh/ops/auto_update.sh`, `kh/ops/test_auto_update.sh`

**Schnittstellen:**
- Nutzt: alles aus den Aufgaben 1 bis 4; `push` aus `backup/backup.sh --lib`. Vor den eigenen Funktionen laden, damit das eigene `fail` gilt.
- Liefert:
  - `registry_tags REGISTRY REPO USER TOKEN`: Tags pro Zeile; bei Netz- oder Anmeldefehler `return 1` mit „Registry REGISTRY nicht erreichbar oder Anmeldung abgelehnt“.
  - `pull_image REF REGISTRY USER TOKEN`: mit Zugangsdaten über temporäres `DOCKER_CONFIG` (umask 077, `config.json` aus `docker_auth_json`) und `DOCKER_HOST` aus `docker context inspect --format '{{.Endpoints.docker.Host}}'`, danach Ordner löschen; ohne Zugangsdaten einfaches `docker pull -q`.
  - `extract_bundle REF STAGING`: `docker create`, `docker cp ID:/app/kh-bundle/. STAGING`, `docker rm`, dann `bundle_problems` auf der Dateiliste; bei Problemen `return 1`.
  - `note MSG`: Zeile `YYYY-MM-DD HH:MM MSG`; ohne `--scheduled` zusätzlich an `$LOG` angehängt.
  - `report up|down MSG`: `note` und in einer Subshell `KH_BACKUP_PUSH_URL=$(setting KH_UPDATE_PUSH_URL "")`, dann `push`.
  - `finish_update RC TAG`: wertet den Rückgabewert von `update.sh` aus. 0 → `clear_failed`, `report up`, `return 0`; 3 → `report down "NOTFALL: …"`, `return 3`; jeder andere → `mark_failed TAG`, `report down`, `return 1`.
  - Befehle `check` und `run [--scheduled]`.
- Ablauf `run` und Exit-Codes: genau nach der Spezifikation, Abschnitt „Ablauf von `run`“ und „Fehlerfälle“; der Exit-Code von `run` ist der von `finish_update`. Sperre und Arbeitsordner werden immer entfernt (`trap`). `main` ergänzt `PATH` um `/usr/local/bin:/opt/homebrew/bin` und wechselt nach `kh/ops`.

- [ ] **Schritt 1: Tests schreiben** (ohne Netz und Docker: das Skript in eine Testinstallation kopieren)

```sh
inst="$tmp/inst/kh/ops"; mkdir -p "$inst/backup"
cp "$here/auto_update.sh" "$here/update.sh" "$here/check_bundle.sh" "$inst/"; cp "$here/backup/backup.sh" "$inst/backup/"
run_au() { (cd "$inst" && sh ./auto_update.sh "$@" 2>&1); }
printf 'KH_AUTO_UPDATE=false\nKH_IMAGE=ghcr.io/x/y:v0.0-amd64\n' > "$inst/.env"
check "switch off" "$(run_au run | grep -c 'aus')" "1"
check "switch off logged" "$(grep -c 'aus' "$inst/auto_update.log")" "1"
printf 'KH_IMAGE=kuechenhelfer:dev\n' > "$inst/.env"
check "dev image" "$(run_au run --scheduled | grep -c 'Entwicklungs-Image')" "1"
printf 'KH_IMAGE=127.0.0.1:9/x/y:v0.0-amd64\n' > "$inst/.env"
check "registry down: exit" "$( (cd "$inst" && sh ./auto_update.sh check >/dev/null 2>&1) && echo 0 || echo $?)" "1"
check "registry down: message" "$(run_au check | grep -c 'nicht erreichbar')" "1"
check "registry down: run exit" "$( (cd "$inst" && sh ./auto_update.sh run --scheduled >/dev/null 2>&1) && echo 0 || echo $?)" "1"
check "registry down: nothing marked" "$(yes_no test -e "$inst/.auto_update.failed")" "no"
check "lock removed" "$(yes_no test -e "$inst/.auto_update.lock")" "no"
check "bad option" "$( (cd "$inst" && sh ./auto_update.sh run --nightly >/dev/null 2>&1) && echo 0 || echo $?)" "2"
report() { echo "$1" >> "$tmp/reports"; }   # stub: records up/down instead of pushing
FAILED="$tmp/failed2"; : > "$tmp/reports"
check "update ok" "$(finish_update 0 v0.1-amd64 && echo 0 || echo $?)$(failed_tag)" "0"
check "update failed" "$(finish_update 1 v0.1-amd64 && echo 0 || echo $?)$(failed_tag)" "1v0.1-amd64"
check "ok clears marker" "$(finish_update 0 v0.1-amd64 >/dev/null; failed_tag)" ""
check "rollback failed" "$(finish_update 3 v0.1-amd64 && echo 0 || echo $?)" "3"
check "reports" "$(tr '\n' ' ' < "$tmp/reports")" "up down up down "
```

- [ ] **Schritt 2: Tests scheitern.**
- [ ] **Schritt 3: Umsetzen** wie bei den Schnittstellen. `check` zeigt Schalter, laufendes Image, gemerkte fehlerhafte Version und die Entscheidung („würde aktualisieren auf REF“, „nichts Neueres“ oder „Entwicklungs-Image“).
- [ ] **Schritt 4: Tests grün in sh, dash und ash.**
- [ ] **Schritt 5: Commit** `git commit -m "Auto-update: check and run commands"`

### Task 6: `update.sh` aktualisiert die Begleitdienste

**Dateien:** Ändern `kh/ops/update.sh` (neue Funktion, Aufruf direkt vor dem erfolgreichen `exit 0` in `main`, Kopfkommentar ergänzen), `kh/ops/upgrade_test.sh` (`run_test`, Schritt 4/4)

**Schnittstellen:**
- Liefert: `refresh_companions` in `update.sh`:
  - `docker compose build backup && docker compose up -d --no-deps backup`. Nie `up --build` mit Abhängigkeiten, sonst baut Compose auch das Mealie-Image neu.
  - Läuft ein Tunnel-Container (`docker compose --profile tunnel ps -q tunnel`): `docker compose --profile tunnel up -d --no-deps tunnel`.
  - Fehler gibt nur eine deutsche Warnung auf stderr, immer `return 0`.

- [ ] **Schritt 1: Test schreiben.** In `upgrade_test.sh` nach dem Datenvergleich: `[ -n "$(docker compose ps -q backup)" ] || fail "der Backup-Dienst läuft nach dem Update nicht"`.
- [ ] **Schritt 2: Test scheitert**

Run: `kh/ops/upgrade_test.sh ghcr.io/gamingnet006/own-recipe-app:v0.0-rc.2-arm64 kuechenhelfer:dev`
Expected: `Upgrade-Test FEHLGESCHLAGEN: der Backup-Dienst läuft nach dem Update nicht` (Exit 1). Die echte Installation und ihr `kuechenhelfer:rollback` bleiben unberührt.

- [ ] **Schritt 3: `refresh_companions` umsetzen** und nach „Update fertig“ aufrufen.
- [ ] **Schritt 4: Upgrade-Test bestanden** (derselbe Befehl, Expected: `Upgrade-Test bestanden: …`); dazu `sh kh/ops/test_update.sh` und `sh kh/ops/test_upgrade.sh` grün.
- [ ] **Schritt 5: Commit** `git commit -m "update.sh refreshes the backup service and the tunnel after a switch"`

### Task 7: Doku, CI, Abschluss im Repo

**Dateien:** Ändern `.claude/CLAUDE.md` und `docs/kh/CLAUDE.en.md` (Befehle: `kh/ops/auto_update.sh on|off|status|check|run`; `&& sh kh/ops/test_auto_update.sh` in der Testkette), `docs/kh/CHANGELOG.md` (Unreleased), `PLAN.md` und `PLAN.en.md` (Phase 1: Notiz zur Aufgabe D29; Installationsanleitung: Hinweis auf `docker compose up -d --build backup` streichen, `kh/ops/auto_update.sh on` und den Lese-Schlüssel ergänzen).

- [ ] **Schritt 1: Doku ändern** wie oben.
- [ ] **Schritt 2: Alles prüfen**

Run: `sh kh/ops/backup/test_backup.sh && sh kh/ops/test_update.sh && sh kh/ops/test_release.sh && sh kh/ops/test_upgrade.sh && sh kh/ops/test_tunnel.sh && sh kh/ops/test_auto_update.sh && (cd kh/ops && docker compose config -q)`, dazu `test_auto_update.sh` in dash und ash.
Expected: alle `… passed`, `compose config` ohne Ausgabe.

- [ ] **Schritt 3: Commit, Push, CI**

```bash
git add .claude/CLAUDE.md docs/kh/CLAUDE.en.md docs/kh/CHANGELOG.md PLAN.md PLAN.en.md
git commit -m "Docs: automatic updates (D29)"
git push origin main
```

Expected: `kh-ci` für den Commit grün (Job „KH ops scripts“ mit „Auto-update script tests“).

### Task 8: Einführung auf dem Mac mini

**Dateien:** keine im Repo außer der Notiz in `PLAN.md`/`PLAN.en.md`; Gedächtnisnotiz `mac-mini-server.md`.

- [ ] **Schritt 1: Betriebsdateien einspielen** (`.env` und Daten liegen nicht im Archiv):

```bash
git archive HEAD kh/ops mealie/core/settings/settings.py | ssh admin@mac-mini 'tar -x -C ~/homelab/kuechenhelfer'
```

- [ ] **Schritt 2: Lese-Schlüssel (macht der Admin).** GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token (classic): Name „Küchenhelfer Mac mini“, nur `read:packages`. In die `.env` des Mac mini eintragen, nie in den Chat: `KH_REGISTRY_USER=gamingnet006` und `KH_REGISTRY_TOKEN=…`.

```bash
ssh -t admin@mac-mini 'nano ~/homelab/kuechenhelfer/kh/ops/.env'
```

- [ ] **Schritt 3: Einschalten und prüfen** (per SSH, mit `PATH`):
  - `kh/ops/auto_update.sh on`: Danach steht in `crontab -l` genau eine Zeile `# kh-auto-update`.
  - `check`: Expected „nichts Neueres“ bei laufendem `v0.0-rc.2-amd64`, ohne Fehler. Das beweist auch, dass der Schlüssel für die Tag-Liste reicht.
  - Zum Herunterladen mit Schlüssel und Colima-Kontext: `sh -c 'set -- --lib; . ./auto_update.sh; pull_image ghcr.io/gamingnet006/own-recipe-app:v0.0-rc.2-amd64 ghcr.io "$(setting KH_REGISTRY_USER "")" "$(setting KH_REGISTRY_TOKEN "")"'`, Expected Exit 0.
  - `status` zeigt an, Job ja und Version `v0.0-rc.2-amd64`.

- [ ] **Schritt 4: Notizen.** In `PLAN.md`/`PLAN.en.md` bei der D29-Aufgabe vermerken, dass sie auf dem Mac mini eingeschaltet ist und der erste echte Lauf mit `v0.0` kommt; Gedächtnisnotiz ergänzen; committen und pushen.
