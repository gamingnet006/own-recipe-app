# Automatische Updates (D29) · Design

Stand 30.10.2026, im Chat freigegeben (Ansatz A: nächtlicher Job auf dem Server, Betriebsdateien im Image).

## Ziel

- Jede Installation hält sich selbst mit **stabilen Releases** aktuell: standardmäßig an, per Schalter abschaltbar.
- Stabil heißt: Tag `vX.Y` oder `vX.Y.Z` ohne `-rc` (Phasen-Releases und Fehlerbehebungen), je Prozessortyp als `<version>-amd64` oder `<version>-arm64`.
- Jedes Update läuft durch dasselbe Sicherheitsnetz wie ein Update von Hand: `update.sh` (Backup, Datenbank-Schnappschuss, Prüfung, Rückfall).
- Läuft auf Mac, Linux und Raspberry Pi; Windows folgt später (D28).

## Nicht-Ziele (später oder nie)

- Häkchen in den Admin-Einstellungen der App: Phase 8 (Erststart-Assistent, Betrieb).
- Zeitplanung unter Windows: wenn Windows getestet wird.
- Updates bei jedem Push oder auf Release-Kandidaten (`-rc`): nie automatisch.
- Wählbare Uhrzeit: fest 4:00 Uhr, nach dem Standard-Backup um 3:30 Uhr.

## Bausteine

| Baustein | Aufgabe |
|---|---|
| `kh/ops/auto_update.sh` (neu) | Befehle `on`, `off`, `status`, `check`, `run`; Logik für Versionen, Registry, Paket mit Betriebsdateien, Sperre |
| `kh/ops/test_auto_update.sh` (neu) | Tests ohne Netz und ohne Docker, in macOS-sh, dash und ash; läuft in der CI |
| `kh/ops/check_bundle.sh` (neu) | prüft ein Image: Betriebsdateien vorhanden, keine `.env`, keine Daten; genutzt von `release.sh` und `kh-release.yml` |
| `kh/ops/update.sh` (erweitert) | nach erfolgreichem Wechsel Backup-Dienst neu bauen und starten, Tunnel neu erstellen, falls er läuft |
| `docker/Dockerfile` (Mealie, `KH:`-Kommentar) | kopiert `kh/ops` und `mealie/core/settings/settings.py` nach `/app/kh-bundle/` |
| `.dockerignore`, `.gitignore` | halten `.env`, Daten, Backups, Logs und Arbeitsdateien aus Image und Repo |
| `kh/ops/.env.example` | neuer Abschnitt mit den Schaltern unten |

## Einstellungen (`.env`)

```
# --- Automatische Updates (D29) ---
KH_AUTO_UPDATE=true      # false: keine automatischen Updates
KH_REGISTRY_USER=        # nur solange die Images privat sind: GitHub-Name
KH_REGISTRY_TOKEN=       # dazu ein GitHub-Schlüssel, der nur Pakete lesen darf (read:packages)
KH_UPDATE_PUSH_URL=      # optional: Uptime-Kuma-Push-URL für das Ergebnis jeder Nacht
```

Fehlt `KH_AUTO_UPDATE`, gilt `true`. Registry und Repository kommen aus `KH_IMAGE`, nirgends sonst her; so fragt jede Installation genau dort, woher ihr laufendes Image stammt.

## Befehle

- `on`: setzt `KH_AUTO_UPDATE=true` und trägt den nächtlichen Job in die Crontab des Benutzers ein (eine Zeile, erkennbar am Kommentar `# kh-auto-update`, ersetzt eine vorhandene). Gehört künftig zur Installation.
- `off`: setzt `KH_AUTO_UPDATE=false` und entfernt die Zeile.
- `status`: Schalter, Job eingetragen ja/nein, laufende Version, letzte Zeilen des Logs, gemerkte fehlerhafte Version.
- `check`: Schritte 4 bis 6 von `run` ohne Änderung, auch bei ausgeschaltetem Schalter; nennt Schalter, laufende Version, die Version, die `run` nehmen würde (oder „nichts Neueres“), und eine gemerkte fehlerhafte Version.
- `run`: der ganze Ablauf von Hand; versucht auch eine gemerkte fehlerhafte Version noch einmal.
- `run --scheduled`: derselbe Ablauf für den nächtlichen Job; überspringt eine gemerkte fehlerhafte Version.

Crontab-Zeile: `0 4 * * * '<ops>/auto_update.sh' run --scheduled >> '<ops>/auto_update.log' 2>&1 # kh-auto-update` mit dem absoluten Pfad `<ops>` von `kh/ops`.

Exit-Codes: 0 erledigt oder nichts zu tun, 1 Fehler (alte Version läuft weiter), 2 falscher Aufruf, 3 Notfall (Rückfall gescheitert).

## Ablauf von `run`

1. **PATH ergänzen** um `/usr/local/bin` und `/opt/homebrew/bin`: cron und SSH ohne Terminal kennen auf macOS sonst `docker` nicht.
2. **Sperre** `kh/ops/.auto_update.lock` (Ordner mit PID). Läuft schon ein Lauf, endet dieser sofort; eine Sperre ohne lebenden Prozess wird übernommen.
3. **Schalter**: `KH_AUTO_UPDATE=false` → „aus“ ins Log, Ende.
4. **Laufendes Image** aus `KH_IMAGE` zerlegen in Registry, Repository, Version und Prozessortyp. Kein Release-Image (zum Beispiel `kuechenhelfer:dev` auf dem Entwicklungs-Mac) → „Entwicklungs-Image, keine automatischen Updates“, Ende.
5. **Versionsliste** über die Registry-Schnittstelle (`/token`, dann `/v2/<repo>/tags/list`), mit Anmeldung nur wenn `KH_REGISTRY_USER` und `KH_REGISTRY_TOKEN` gesetzt sind. Fehler → Meldung, Ende vor jeder Änderung.
6. **Auswahl**: neueste stabile Version für den eigenen Prozessortyp, die neuer ist als die laufende. Mit `--scheduled` wird eine Version aus `.auto_update.failed` übersprungen. Nichts Neueres → „aktuell (vX.Y)“, Ende.
7. **Herunterladen** des neuen Images. Mit Zugangsdaten über ein eigenes, nur für diesen Lauf angelegtes Docker-Konfigurationsverzeichnis (`DOCKER_CONFIG`), das am Ende gelöscht wird; nichts landet im Schlüsselbund.
8. **Betriebsdateien auspacken**: `docker create`, `docker cp <id>:/app/kh-bundle/. <arbeitsordner>`, `docker rm`. Fehlt darin `kh/ops/update.sh` → „Image ohne Betriebsdateien“, Ende vor jeder Änderung.
9. **Einspielen** in den Installationsordner (zwei Ebenen über `kh/ops`, wie bei `git archive`): vorhandene Dateien werden ersetzt; `.env`, `data`, `backups` und Logs liegen nicht im Paket und bleiben unberührt.
10. **`kh/ops/update.sh <neues Image>`** aus dem frisch eingespielten Stand.
11. **Ergebnis** ins Log und, falls gesetzt, an Uptime Kuma (dieselbe `push`-Funktion wie beim Backup). Arbeitsordner und Sperre werden immer entfernt.

Nach einem fehlgeschlagenen Update bleiben die neuen Betriebsdateien liegen. Das ist eine geprüfte Kombination: Der Upgrade-Test in der CI startet das alte Image mit den neuen Betriebsdateien, bevor er aktualisiert.

## Erweiterung von `update.sh`

Nach einem erfolgreichen Wechsel (vor `exit 0`) ein Schritt „Begleitdienste aktualisieren“:

- `docker compose up -d --build backup`, damit der Backup-Dienst zum Release passt (ersetzt den Hinweis in der Installationsanleitung).
- Gibt es den Tunnel-Container: `docker compose --profile tunnel up -d tunnel`.

Scheitert dieser Schritt, gibt es eine Warnung, aber kein Rückfall: Die App läuft dann schon in der neuen Version.

Bricht `update.sh` ab, bevor es etwas geändert hat (zum Beispiel ist Mealie nicht bereit oder das Backup scheitert), endet es mit Exit 4 statt 1. So unterscheidet `auto_update.sh` ein vorübergehendes Problem von einer Version, die nach dem Wechsel gescheitert ist.

## Fehlerfälle

| Situation | Verhalten | Meldung |
|---|---|---|
| Schalter aus | nichts | Log „aus“ |
| Entwicklungs-Image | nichts | Log |
| Registry nicht erreichbar, Anmeldung falsch oder Schlüssel abgelaufen | Ende vor jeder Änderung | Log, Uptime Kuma „down“ |
| nichts Neueres | nichts | Log, Uptime Kuma „up“ |
| Image ohne Betriebsdateien | Ende vor jeder Änderung | Log, „down“ |
| `update.sh` bricht vor jeder Änderung ab (Exit 4), etwa weil Mealie gerade nicht bereit ist oder das Backup scheitert | nichts geändert, nichts gemerkt; die nächste Nacht versucht dieselbe Version noch einmal | Log, „down“ |
| neue Version scheitert, `update.sh` springt zurück (Exit 1) | alte Version läuft weiter; Version wird in `.auto_update.failed` gemerkt; nachts erst wieder versucht, wenn es eine neuere gibt | Log, „down“ |
| Rückfall gescheitert (Exit 3) | Notfall, nichts weiter tun | Log „NOTFALL“, „down“, Exit 3 |
| zweiter Lauf gleichzeitig | endet sofort | Log |
| Erfolg | gemerkte fehlerhafte Version wird gelöscht | Log, „up“ mit neuer Version |

## Versionen vergleichen

`vX.Y` gilt als `vX.Y.0`. Verglichen wird Zahl für Zahl; bei gleicher Zahl ist die fertige Version neuer als ihr Release-Kandidat (`v0.0` > `v0.0-rc.2`). Kandidaten für ein Update sind nur stabile Tags; das laufende Image darf ein Kandidat sein (der Mac mini läuft gerade mit `v0.0-rc.2`).

## Sicherheit

- Quelle ist nur das Repository aus `KH_IMAGE`. Neue Tags entstehen nur über `release.sh` und `kh-release.yml`, nach Tests und Upgrade-Test.
- Der Schlüssel darf nur lesen (`read:packages`), steht nur in der `.env` (Rechte 600) und gilt nur für die Dauer eines Laufs in Docker.
- Die Skripte aus dem Image laufen auf dem Server mit denselben Rechten wie ein Update von Hand; sie sind so vertrauenswürdig wie das Image selbst.
- `.dockerignore` hält `.env`, Daten und Backups auch aus lokalen Builds heraus; `check_bundle.sh` prüft jedes Release-Image vor dem Hochladen.

## Tests

- `test_auto_update.sh` mit selbst geschriebenen Beispieldaten: Image-Name zerlegen, stabile Tags erkennen, Versionen vergleichen (auch `-rc`), neueste Version wählen, fehlerhafte Version nur mit `--scheduled` überspringen, Tag-Liste aus der Registry-Antwort lesen, Crontab-Zeile setzen, ersetzen und entfernen, Schalter lesen, Aufruf-Fehler und Exit-Codes. In der CI im Job „ops“.
- `check_bundle.sh` in `kh-release.yml` (amd64) und in `release.sh` (arm64), jeweils vor dem Hochladen.
- Von Hand: auf dem Mac mini `check` (erwartet bis `v0.0`: „nichts Neueres“), der erste echte Lauf mit Release `v0.0`.

## Einführung

1. Code, Tests, Dockerfile, `.dockerignore`, Doku; CI grün.
2. Mac mini: neue Betriebsdateien wie bisher per `git archive` einspielen, `KH_REGISTRY_USER` und `KH_REGISTRY_TOKEN` in die `.env` (den Schlüssel legst du bei GitHub an), `auto_update.sh on`, `check`.
3. `PLAN.md`: D29, Aufgabe in Phase 1, Häkchen in der App als Aufgabe in Phase 8; Installationsanleitung: `auto_update.sh on` als Schritt. `CHANGELOG.md` unter „Unreleased“.

## Später

- Ein gemeinsamer Tag für amd64 und arm64 (Phase 8): Dann zerlegt Schritt 4 Tags ohne Prozessortyp; bis dahin bleibt der Typ Teil des Tags.
- Häkchen in der App (Phase 8) liest und schreibt denselben Schalter `KH_AUTO_UPDATE`.
