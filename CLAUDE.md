# CLAUDE.md – Küchenhelfer (Mealie-Fork)

Dieses Repo ist ein Fork von Mealie (AGPL-3.0). Mealies Entwicklungsanleitung gilt weiter und wird hier eingebunden:

@AGENTS.md

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
3. **Erst prüfen, ob es das schon gibt:** Mealie-Funktion, dann Bibliothek, dann eigener Code. Jede neue Abhängigkeit braucht eine Begründung, einen Lizenz-Check und einen Eintrag in `THIRD_PARTY_NOTICES.md`.
4. **Übersichtlich bleiben.** Eine Datei, ein Thema. Funktionen meist unter etwa 40 Zeilen, sprechende Namen. Einstellungen nur über die Konfiguration, keine versteckten Zahlen im Code.
5. **Kommentare erklären den Zweck.** Jede neue Datei beginnt mit 1 bis 3 Zeilen, wofür sie da ist. Jede Funktion hat eine Kurzbeschreibung (was und warum). Nicht offensichtliche Stellen bekommen einen kurzen Randkommentar. Keine Kommentare, die nur den Code nachsagen.
6. **Sprache.** Code, Bezeichner und Kommentare auf Englisch, passend zu Mealie (D7 in `PLAN.md`); Anleitungen auf Deutsch und Englisch.
7. **Fehler verständlich melden,** nichts still verschlucken.
8. **Sicherheit.** Keine Schlüssel im Code oder Repo. Eingaben prüfen. Beim Abrufen fremder Seiten private Adressbereiche sperren und Größe sowie Zeit begrenzen. KI-Antworten nur nach festem Schema annehmen. Ausgaben escapen.
9. **Tests.** Jede Funktion mit Logik bekommt mindestens einen Test. Testdaten nur selbst geschrieben oder frei lizenziert, nie echte fremde Rezepte.
10. **Definition of Done.** Läuft, Tests grün, Kommentare da, kein toter Code, Doku angepasst, Lizenz geprüft, Kosten weiter 0 €.

## Fork-Regeln

- Unsere Funktionen liegen in eigenen Unterordnern mit dem Kürzel `kh`; die Pfade stehen nach Phase 0 in `docs/code-rundgang.md`.
- Änderungen an vorhandenem Mealie-Code klein halten und mit dem Kommentar `KH: <Grund>` markieren.
- Erzeugte Dateien nie von Hand ändern (z. B. die TypeScript-Typen aus den Schemas), sondern immer den Generator nutzen.
- Die Datenbank nur über Alembic-Migrationen ändern; vor jeder Migration ein Backup.
- Upstream: Sicherheitsfixes einzeln per `cherry-pick` übernehmen, neue Mealie-Funktionen nur nach Absprache.
- Mealies Lizenz- und Copyright-Hinweise nie entfernen.

## Phasen-Regeln

- Jede Phase endet mit einem eigenständig installierbaren Release (Tag, Images, Kurzanleitung). Details in `PLAN.md` Abschnitt 5.
- Neue Funktionen kommen in `kh/<funktion>/`. Fertigen Code früherer Phasen nur für Fehlerbehebungen ändern, jeweils mit Test.
- Spätere Phasen docken an Erweiterungspunkte an (Listen oder Einhängepunkte), statt früheren Code umzubauen.
- API, Funktionen und Datenformate früherer Phasen bleiben kompatibel; Migrationen nur additiv.
- Die Tests aller Phasen müssen grün bleiben. Vor jedem Release ein Upgrade-Test vom vorherigen Tag.

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

<!-- In Phase 0 aus Mealies Taskfile und AGENTS.md übernehmen: einrichten, starten, Tests, Lint, Typen erzeugen, Migration anlegen, Docker-Image bauen. Keine Befehle erfinden. -->
