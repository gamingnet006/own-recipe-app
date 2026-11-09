# CLAUDE.md – Kochheft (vormals Küchenhelfer, Mealie-Fork)

Dieses Repo ist ein Fork von Mealie (AGPL-3.0). Mealies Entwicklungsanleitung gilt weiter und wird hier eingebunden:

@../AGENTS.md

Der Plan mit Phasen, Aufgaben und Entscheidungen steht in `PLAN.md`. Er wird nicht automatisch geladen: Lies vor jeder Aufgabe den Abschnitt der aktuellen Phase.

## Arbeitsweise

- Vor jeder Aufgabe kurz sagen, welche Dateien du anlegst oder änderst.
- In kleinen Schritten arbeiten: einen Schritt umsetzen, Tests schreiben und ausführen, kurz zusammenfassen, den nächsten Schritt nennen.
- Nichts außerhalb der Aufgabe ändern. Bei Unklarheit fragen statt raten.
- Erledigtes in `PLAN.md` abhaken, neue Entscheidungen dort in Abschnitt 2 eintragen.
- Ziele und Leitplanken nie eigenmächtig ändern.

## Code-Regeln

1. **Kein toter Code.** Nichts auf Vorrat bauen. Ungenutzte Funktionen, Importe und Dateien sofort löschen.
2. **Keine Wiederholungen.** Taucht Logik ein zweites Mal auf, wird sie eine Funktion, die überall aufgerufen wird (z. B. `parse_ingredient()`, `format_amount()`, `ask_ai()`, `transcribe()`).
3. **Erst prüfen, ob es das schon gibt:** Mealie-Funktion, dann Bibliothek, dann eigener Code. Jede neue Abhängigkeit braucht eine Begründung, einen Lizenz-Check und einen Eintrag in `docs/kh/THIRD_PARTY_NOTICES.md`.
4. **Übersichtlich bleiben.** Eine Datei, ein Thema. Funktionen meist unter etwa 40 Zeilen, sprechende Namen. Einstellungen nur über die Konfiguration, keine versteckten Zahlen im Code.
5. **Kommentare erklären den Zweck.** Jede neue Datei beginnt mit 1 bis 3 Zeilen, wofür sie da ist. Jede Funktion hat eine Kurzbeschreibung (was und warum). Nicht offensichtliche Stellen bekommen einen kurzen Randkommentar. Keine Kommentare, die nur den Code nachsagen.
6. **Sprache.** Code, Bezeichner und Kommentare auf Englisch, passend zu Mealie (D7 in `PLAN.md`); Anleitungen auf Deutsch und Englisch.
7. **Fehler verständlich melden,** nichts still verschlucken.
8. **Sicherheit.** Keine Schlüssel im Code oder Repo. Eingaben prüfen. Beim Abrufen fremder Seiten private Adressbereiche sperren und Größe sowie Zeit begrenzen. KI-Antworten nur nach festem Schema annehmen. Ausgaben escapen.
9. **Tests.** Jede Funktion mit Logik bekommt mindestens einen Test. Testdaten nur selbst geschrieben oder frei lizenziert, nie echte fremde Rezepte. KI-Aufrufe in Tests nur mit aufgezeichneten Antworten, nie mit echtem Modell oder Key (D23).
10. **Definition of Done.** Läuft, Tests grün, Kommentare da, kein toter Code, Doku angepasst, Lizenz geprüft, Kosten weiter 0 €.

## Fork-Regeln

- Unsere Funktionen liegen in eigenen Unterordnern mit dem Kürzel `kh`; die Pfade stehen nach Phase 0 in `docs/code-rundgang.md`.
- Änderungen an vorhandenem Mealie-Code klein halten und mit dem Kommentar `KH: <Grund>` markieren.
- Erzeugte Dateien nie von Hand ändern (z. B. die TypeScript-Typen aus den Schemas), sondern immer den Generator nutzen.
- Die Datenbank nur über Alembic-Migrationen ändern; vor jeder Migration ein Backup.
- Upstream: Sicherheitsfixes einzeln per `cherry-pick` übernehmen, neue Mealie-Funktionen nur nach Absprache.
- Mealies Lizenz- und Copyright-Hinweise nie entfernen.
- GitHub Actions: Nur unsere Workflows starten von selbst: `kh-ci.yml` bei jedem Push (ruft Mealies `test-backend.yml` und `test-frontend.yml` auf) und `kh-release.yml` bei Versions-Tags (baut das amd64-Image, Upgrade-Test vom vorigen Release, erst dann hochladen). Alle anderen Mealie-Workflows sind im Repo deaktiviert. Nach jedem Upstream-Abgleich neue Workflows mit `gh workflow disable <name>` abschalten.

## Phasen-Regeln

- Jede Phase endet mit einem eigenständig installierbaren Release (Tag, Images, Kurzanleitung). Details in `PLAN.md` Abschnitt 5.
- Neue Funktionen kommen in `kh/<funktion>/`. Fertigen Code früherer Phasen nur für Fehlerbehebungen ändern, jeweils mit Test.
- Spätere Phasen docken an Erweiterungspunkte an (Listen oder Einhängepunkte), statt früheren Code umzubauen.
- API, Funktionen und Datenformate früherer Phasen bleiben kompatibel; Migrationen nur additiv.
- Die Tests aller Phasen müssen grün bleiben. Vor jedem Release ein Upgrade-Test vom vorherigen Tag (läuft automatisch in `kh-release.yml`, Testdaten in `kh/ops/testdata/`).

## Zugangsdaten

- Nie Zugangsdaten, Passwörter, Tokens oder Keys ins Repo, auch nicht in Beispielen oder Tests. Nur Platzhalter in `.env.example`; `.env` steht in `.gitignore`.

## Entwickeln auf dem Mac, Betrieb auf dem Raspberry Pi

- Alles läuft in Docker; nichts Mac-Spezifisches voraussetzen.
- Images für `linux/arm64` und `linux/amd64` bauen (Raspberry Pi, Apple Silicon, Intel-Rechner). Schwere Builds wie das Frontend nur in der CI, nie auf dem Pi.
- Dateinamen und Importpfade mit exakter Groß- und Kleinschreibung schreiben: macOS verzeiht Fehler, Linux nicht.
- Container, die Dienste auf dem Host erreichen sollen (z. B. Ollama), nutzen `host.docker.internal`; unter Linux nur mit `extra_hosts: ["host.docker.internal:host-gateway"]` in Compose.
- Benutzer-ID im Container festlegen, damit Dateirechte auf Volumes auch auf dem Pi stimmen.
- Pi-ähnlich testen: Container mit Limits starten (etwa 2 CPUs, 2 GB RAM). Am Ende jeder Phase auf dem echten Pi prüfen (64-Bit-System, Daten auf SSD statt SD-Karte).
- Auf dem Mac läuft Ollama nativ (dort mit GPU, im Docker-Container ohne); auf dem Pi gilt das Profil `leicht`.

## Leitplanken (Kurzfassung, Details in `PLAN.md`)

- Alles kostenlos, keine Abos.
- Keine fremden Rezepte, Texte oder Fotos ins Repo; keinen Video-Downloader mitliefern.
- Keine Telemetrie; was das Haus verlässt, steht in der README-Tabelle „Was geht wohin“.

## Befehle

Alles läuft in Docker (Colima auf dem Mac, mindestens 4 CPUs und 6 GB RAM: `colima start --cpu 4 --memory 6`). Alle Befehle aus dem Repo-Hauptordner; ausgeführt und geprüft in Phase 0 und 1, sofern nicht anders markiert.

```bash
# Neue Installation einrichten: fragt Backup-Ort und Adresse, schreibt .env, startet, legt den Backup-Schlüssel an (docs/kh/README.md)
kh/ops/install.sh <image>
# Kochheft bauen und starten (Mealie und Backup-Dienst aus kh/ops), danach http://localhost:9091
docker compose -f kh/ops/docker-compose.yml up -d --build
# Pi-ähnliche Grenzen für den laufenden Container
docker update --cpus 2 --memory 2g --memory-swap 2g kuechenhelfer-mealie-1
# Stoppen
docker compose -f kh/ops/docker-compose.yml down
# Backup sofort; Backups anzeigen oder eines wiederherstellen (--no-deps: Mealie nicht neu starten)
docker compose -f kh/ops/docker-compose.yml run --rm --no-deps backup backup.sh
docker compose -f kh/ops/docker-compose.yml run --rm --no-deps backup restore.sh [datei.zip]
# Update auf ein anderes Image: Backup, Datenbank-Schnappschuss, Prüfung, bei Fehler zurück; danach Backup-Dienst und Tunnel erneuern
kh/ops/update.sh <image>
# Zugang von unterwegs (Cloudflare Tunnel) ein- und ausschalten; "on" prüft vorher Registrierung und Standard-Konto
kh/ops/tunnel.sh on|off|status
# Automatische Updates (nur stabile Releases, nachts um 4 Uhr): an, aus, Stand, Probelauf, sofort
kh/ops/auto_update.sh on|off|status|check|run
# Kopie der Backups auf einen USB-Stick, nachts um 3:45 Uhr; "on" fragt beim ersten Mal, ob mit Passwort (dann mit age
# verschlüsselt), ohne Ordner fragt es nach dem Ort (so lässt er sich auch später wechseln, am Mac per Doppelklick auf
# kh/ops/backup-ort-aendern.command), "decrypt" öffnet eine verschlüsselte Kopie. Am Mac mini mit echtem Stick in Betrieb
kh/ops/backup_copy.sh on [<ordner>]|off|status|run|decrypt <datei.zip.age>
# Passendes Profil vorschlagen; mit --audio <datei> (etwa 1 Minute) auch die Whisper-Geschwindigkeit messen (Phase 7)
sh kh/ops/hardware_test.sh [--audio <datei> [--seconds <länge>]]
# Release veröffentlichen (nur auf dem Mac): arm64 bauen, Tag setzen, CI baut amd64, arm64 hochladen
kh/ops/release.sh <version>
# Upgrade-Test von Hand: alte Version mit Testrezepten, Update, Vergleich (Wegwerf-Installation auf Port 9191)
kh/ops/upgrade_test.sh <altes-image> <neues-image>
# Restore-Test: neuestes oder angegebenes Backup mit restore.sh in eine Wegwerf-Installation einspielen, Rezepte und Dateien vergleichen (Port 9191)
kh/ops/restore_test.sh [backup.zip]
# Tests der Betriebs-Skripte (laufen auch in der CI)
sh kh/ops/backup/test_backup.sh && sh kh/ops/test_update.sh && sh kh/ops/test_release.sh && sh kh/ops/test_upgrade.sh && sh kh/ops/test_restore.sh && sh kh/ops/test_install.sh && sh kh/ops/test_tunnel.sh && sh kh/ops/test_auto_update.sh && sh kh/ops/test_backup_copy.sh && sh kh/ops/test_hardware_test.sh

# Backend-Tests (entspricht `task py:test`); LDAP-, Postgres- und Langläufer-Tests werden übersprungen
docker run --rm -v "$PWD":/app -w /app -e UV_PROJECT_ENVIRONMENT=/venv -e UV_LINK_MODE=copy \
  ghcr.io/astral-sh/uv:python3.14-bookworm-slim sh -c "apt-get update -qq && \
  apt-get install -qq -y --no-install-recommends build-essential libsasl2-dev libldap2-dev libssl-dev >/dev/null && \
  uv sync --frozen --quiet && uv run --frozen pytest -n 4 --dist loadfile -p no:cacheprovider"

# Frontend-Tests (wie Mealies CI: install, `nuxt prepare`, `test:ci`); die Tests lesen auch mealie/repos/seed
docker run --rm -v "$PWD":/src:ro node:24 sh -c "mkdir -p /work/mealie/repos && cp -r /src/frontend /work/frontend && \
  cp -r /src/mealie/repos/seed /work/mealie/repos/ && cd /work/frontend && rm -rf node_modules .nuxt && \
  npm install -g pnpm@11 && CI=true pnpm install --frozen-lockfile && pnpm nuxt prepare && pnpm test:ci"
```

Laut Mealies `AGENTS.md`, in unserer Docker-Variante noch nicht erprobt: Lint `task py:lint` und `task ui:lint`, Typen erzeugen `task dev:generate`, Migration anlegen `task py:migrate -- "Beschreibung"`.
