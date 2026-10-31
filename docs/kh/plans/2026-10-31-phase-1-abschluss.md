# Phase 1 abschließen (v0.0) · Arbeitsplan

Stand: 31.10.2026. Grundlage ist `PLAN.md`, Abschnitt 5, Phase 1. Dieser Plan ordnet die offenen Punkte. Zu jedem steht, was ich mache, was du machst und woran man sieht, dass er fertig ist. Erledigtes hake ich hier und in `PLAN.md` ab.

## Wo wir stehen

Küchenhelfer läuft seit dem 30.10. auf dem Mac mini: Tunnel `kochbuch.example.org`, tägliches Backup um 3:30, automatische Updates um 4:00. Das MacBook ist nur Entwicklungsrechner.

Für „Fertig wenn“ von Phase 1 fehlt noch:

- **Die Familie trägt von unterwegs Rezepte ein.** Es gibt noch keine Familienkonten.
- **Ein Backup ist auf einem zweiten Gerät wiederhergestellt.** Das ist noch nicht passiert.
- **`v0.0` lässt sich nur mit der Kurzanleitung auf einem frischen Pi installieren.** Es gibt weder die Anleitung noch den Pi. Laut D30 darf `v0.0` trotzdem schon erscheinen; der Pi-Test folgt.

Dazu kommen die offenen Phase-1-Aufgaben: `THIRD_PARTY_NOTICES.md`, Mealie-Teile ausblenden, Meldungen an Uptime Kuma, Restore-Test-Skript.

## Entscheidungen vom 31.10.2026

| Nr. | Frage | Antwort |
|---|---|---|
| E1 | Wohin gehen die Backups zusätzlich? | Später. Die Installation fragt künftig selbst nach dem Backup-Ort; für den Mac mini frage ich dich, sobald das steht (D32). |
| E2 | Welche Mealie-Teile blenden wir aus? | Nach meinem Ermessen: alle drei aus dem Code-Rundgang. |
| E3 | Kommen Beispielrezepte in die Familien-Installation? | Nein, die Familie startet leer (D31). |
| E4 | Erscheint `v0.0` vor dem Pi-Test? | Ja. Der Pi-Test folgt; Fehler kämen als `v0.0.1` (D30). |

## Stand (31.10.2026, nachmittags)

| Paket | Stand |
|---|---|
| 1 Restore auf dem MacBook | erledigt: Rezepte, Konten und Gruppe stimmen mit dem Mac mini überein |
| 2 Uptime Kuma | meine Seite erledigt (eingefügte Adressen mit `?status=…` funktionieren jetzt); wartet auf deine zwei Push-Monitore |
| 3 Familie startklar | Anleitung erledigt; wartet auf deine Einladungslinks |
| 4 Restore-Test-Skript | erledigt, auf MacBook und Mac mini bestanden |
| 5 Mealie-Teile ausblenden | erledigt; dabei die öffentliche Gruppe der Familie entdeckt und auf privat gestellt |
| 6 THIRD_PARTY_NOTICES.md | erledigt |
| 7 Installation | erledigt, nach Anleitung auf dem MacBook geprüft |
| 8 Release v0.0 | erledigt: Tag und beide Images veröffentlicht. Upgrade-Test von `rc.2` bestanden, für amd64 in der CI und für arm64 auf dem MacBook (in einer Wegwerf-Installation statt mit `update.sh`, damit die Entwicklungs-Installation bleibt). Der Mac mini stellt sich in der Nacht zum 1.11. um 4 Uhr um. |
| 9 Backup-Ort Mac mini | USB-Stick gewählt (D32). `kh/ops/backup_copy.sh` kopiert jede Nacht auf den Stick, wahlweise mit Passwort (D33): `v0.0.1` immer mit, `v0.0.2` mit Frage j/n. Die Windows-Dateien vom Stick liegen gesichert auf dem Mac mini. Festplattenvollzugriff für `/bin/dash` und Formatieren hast du erledigt; offen: `on` ohne Passwort |
| 10 Raspberry Pi | wartet auf den Pi |

## Reihenfolge

1. Erst die Datensicherung prüfen: Restore auf einem zweiten Gerät, Meldungen bei Fehlern.
2. Dann die Familie starten lassen. Was sie nutzt, zeigt, was wir sonst noch ausblenden.
3. Dann alles fürs Release: Restore-Test, Ausblenden, Lizenzen, Installation, `v0.0`.
4. Danach der Backup-Ort für den Mac mini und, sobald er bereitsteht, der Pi.

## Arbeitspakete

### 1 · Restore auf dem MacBook

**Warum:** „Fertig wenn“ verlangt ein wiederhergestelltes Backup auf einem zweiten Gerät. Nebenbei bekommt das MacBook eine Kopie der echten Daten zum Entwickeln.

1. Vorher sichere ich die MacBook-Daten mit einem eigenen Backup, damit nichts verloren geht.
2. Dann kopiere ich das neueste Mac-mini-Backup einmal aufs MacBook und spiele es mit `restore.sh` ein.
3. Zum Schluss vergleiche ich Rezepte und Konten mit dem Mac mini.

**Dateien:** keine, nur eine Notiz in `PLAN.md`.

**Fertig, wenn:** Rezeptzahl und Konten auf dem MacBook stimmen mit dem Mac mini überein.

### 2 · Meldungen an Uptime Kuma

**Warum:** Scheitert ein Backup oder ein Update, soll es jemand merken. Uptime Kuma läuft schon auf dem Mac mini.

**Ich:** Vorher prüfe ich, welche Adresse der Backup-Container erreicht. Die Meldung soll im Haus bleiben und nicht über Cloudflare laufen. Dann schreibe ich dir die genauen Schritte auf.

**Du:**

- Lege in Uptime Kuma zwei Monitore vom Typ „Push“ an: „Küchenhelfer Backup“ und „Küchenhelfer Update“, jeweils mit 25 Stunden Intervall.
- Trag beide Adressen per nano in die `.env` des Mac mini ein: `KH_BACKUP_PUSH_URL` und `KH_UPDATE_PUSH_URL`.
- Die Anmeldung bei Uptime Kuma machst du selbst.

**Ich danach:** Probe-Backup und Probelauf.

**Fertig, wenn:** Beide Monitore zeigen grün.

### 3 · Familie startklar

**Konten (D31):** Die Familie bekommt einen Einladungslink. Du erzeugst ihn in Küchenhelfer und schickst ihn herum.

- Jede Person legt ihr Konto selbst an, mit eigenem Passwort und ohne Admin-Rechte.
- Das geht, obwohl die Selbstregistrierung aus ist: Mit Einladung ist sie erlaubt (`mealie/routes/users/registration.py:24`).
- Das Passwort kennt nur die Person selbst.

**Ich:** Ich schreibe zwei kurze Anleitungen auf Deutsch und Englisch in `docs/kh/`.

- Für dich: Link erzeugen.
- Für die Familie: Link öffnen, Konto anlegen, „Angemeldet bleiben“, zum Home-Bildschirm hinzufügen.

**Du:** Link erzeugen und verschicken.

**Fertig, wenn:** Das erste Familienmitglied hat unterwegs ein Rezept eingetragen. Das ist der erste Teil von „Fertig wenn“.

### 4 · Restore-Test-Skript

**Warum:** Ein Backup ist erst etwas wert, wenn es sich wiederherstellen lässt. Bisher prüfe ich das von Hand.

- `kh/ops/restore_test.sh [backup.zip]` startet eine Wegwerf-Installation auf Port 9191, wie der Upgrade-Test.
- Dort spielt es das Backup ein und vergleicht die Rezeptzahl in der Datenbank mit dem Inhalt des Backups. Danach räumt es auf.
- Es nutzt die vorhandenen Helfer aus `upgrade_test.sh` und `restore.sh`.
- Wann es von selbst läuft, legen wir mit dem Backup-Ort fest (Paket 9); bis dahin startet man es von Hand.

**Fertig, wenn:** Die Tests sind grün, und ein echter Lauf mit dem Mac-mini-Backup hat bestanden.

### 5 · Mealie-Teile ausblenden (Stufe 1)

Vorschlag aus dem Code-Rundgang (E2):

- **Teilen-Links:** Das sind öffentliche Links auf einzelne Rezepte, die jeder ohne Anmeldung öffnen kann. Laut Leitplanke sind sie standardmäßig aus.
  - Ein Schalter in der `.env`, standardmäßig aus.
  - Dann blendet das Frontend den Menüpunkt aus, und das Backend lehnt neue Links und das Öffnen ab.
  - Dafür gibt es je eine `KH:`-Stelle.
- **Ankündigungen:** Das sind Mealie-Hinweise mit Links zur Mealie-Doku. Mealie hat dafür schon einen Schalter in den Gruppeneinstellungen (`show_announcements`).
  - Für neue Installationen setze ich ihn standardmäßig auf aus.
  - Für die Familie schalte ich ihn ab.
- **Explore-Seiten:** Neue Gruppen sind schon privat, weil `private_group` standardmäßig an ist. Ich prüfe das nur und sichere es mit einem Test ab.

Die Tabellen bleiben bis Phase 8.

**Entwurf (31.10.2026, nach dem Lesen des Codes):**

- **Schalter:** `KH_SHARE_LINKS` (Standard `false`), gelesen von `KhSettings` in `mealie/kh/features/settings.py`. Mealies `settings.py` bleibt unverändert.
- **Backend:** `GET /api/kh/features` meldet die Schalter (`mealie/kh/features/routes.py`, eingehängt über `mealie/kh/__init__.py` in `mealie/routes/__init__.py`).
  - Ist der Schalter aus, antwortet die öffentliche Rezeptansicht per Token (`GET /api/recipes/shared/{token}`) mit 404.
  - Die Vorschau-Seite `/g/{gruppe}/shared/r/{token}` zeigt dann keine Rezeptdaten mehr.
- **Was bleibt:** Das Erzeugen von Tokens und die Zip-Route bleiben. Mealies Rezept-Download legt dafür selbst einen Token an, der 30 Tage gilt; der Token wird nirgends angezeigt.
- **Frontend:** Ein eigener Nuxt-Layer `frontend/kh/` (D26) mit dem Plugin `kh-features.client.ts`, nach dem Vorbild von Mealies `app-info.client.ts`. Das Rezeptmenü lässt „Teilen“ weg, solange der Schalter aus ist.
- **Ankündigungen:** Neue Gruppen bekommen `show_announcements = false`, geändert in Modell und Schema. Für die Familie schalte ich sie über die API ab.
- **Explore:** keine Änderung. Ein Test sichert ab, dass eine neue Gruppe privat ist und ihre Explore-Seiten 404 liefern.
- **Mealies Tests:** Sie nutzen Teilen-Links und schalten sie deshalb in `tests/conftest.py` ein. Unsere Tests in `tests/kh/features/` prüfen beide Stellungen.

Jede Änderung an Mealies Dateien trägt einen `KH:`-Kommentar.

**Fertig, wenn:** Die Tests sind grün, und auf dem MacBook ist alles im Browser geprüft.

### 6 · THIRD_PARTY_NOTICES.md

**Inhalt:** Darin stehen alle Fremdteile, die wir zu Mealie dazunehmen, jeweils mit Version, Lizenz und Quelle:

- Mealie selbst (AGPL-3.0)
- `cloudflared` für den Tunnel
- das Alpine-Image des Backup-Dienstes mit `curl`, `unzip`, `tzdata` und BusyBox
- die GitHub Actions der CI

Mealies eigene Abhängigkeiten stehen in Mealies Paketlisten; darauf verweise ich.

**Prüfung:** Lizenzen prüfe ich an der Quelle, also an der Lizenzdatei oder der Paketangabe im Image, nicht aus dem Gedächtnis.

**Ort:** `docs/kh/THIRD_PARTY_NOTICES.md`, wie der CHANGELOG wegen D17.

**Fertig, wenn:** Jede Abhängigkeit aus Compose-Datei, Dockerfiles und Workflows steht drin.

### 7 · Installation: Skript, das fragt, und Kurzanleitung (Deutsch und Englisch)

**Installationsskript (D32):** `kh/ops/install.sh` legt die `.env` an und fragt dabei nur, was sich nicht von selbst ergibt:

- Wo die Backups liegen sollen, mit dem Hinweis, dass ein anderes Laufwerk oder ein zweites Gerät sicherer ist als die eigene Platte.
- Unter welcher Adresse Küchenhelfer erreichbar ist.

Den Prozessortyp, also welches Image passt, sowie Benutzer-ID und Gruppe ermittelt es selbst. Die Ordner `data` und `backups` legt es an, weil Colima unter macOS 12 das nicht kann. Schlüssel fragt es nicht ab; die trägt man selbst ein.

**Kurzanleitung:** Sie kommt in `docs/kh/README.md`. Dort steht bisher noch „Planung, kein Programmcode“.

- **Voraussetzungen:** Docker mit Compose, also Docker Desktop, Colima auf dem Mac oder Docker Engine auf Linux und Pi OS 64-Bit.
- **Anmeldung bei ghcr.io:** mit dem Lese-Schlüssel, solange die Images privat sind.
- **Betriebsdateien holen:** am besten aus dem Release-Image, dann braucht man keinen Zugriff aufs Repo. Das prüfe ich noch.
- **`install.sh` ausführen und erster Start:**
  - Das Standard-Konto sofort ändern.
  - Den API-Schlüssel für Backups eintragen.
- **Optional:** Tunnel, automatische Updates (`auto_update.sh on`), Uptime Kuma.
- **Updates, Zurückspielen, Restore-Test:** Dazu der Hinweis, dass Hintergrund-Jobs auf macOS `/usr/local/bin` im PATH brauchen.

**Prüfung:** Ich installiere streng nach Anleitung auf dem MacBook in einen leeren Ordner, mit eigenem Port, und räume danach auf. Was hakt, korrigiere ich in der Anleitung.

**Fertig, wenn:**

- Die Tests für `install.sh` sind grün.
- Die Probe-Installation läuft, ohne dass ich etwas außerhalb der Anleitung tun musste.

### 8 · Release v0.0

**Vorher:** Die Pakete 1 bis 7 sind erledigt, die CI ist grün, und der CHANGELOG hat einen Abschnitt `v0.0`. Den Arbeitszweig führe ich erst nach deinem Okay in `main` zusammen.

**Ablauf:**

1. `kh/ops/release.sh v0.0` baut arm64 auf dem MacBook und setzt den Tag.
2. Die CI baut amd64 und macht den Upgrade-Test von `v0.0-rc.2`. Erst danach lädt sie hoch.

**Danach:**

- Der Mac mini wechselt in der nächsten Nacht um 4 Uhr von selbst auf `v0.0`. Das ist der erste echte Lauf der automatischen Updates; ich prüfe ihn am Morgen.
- Das MacBook aktualisiere ich mit `update.sh` auf `v0.0-arm64`. Das ist dasselbe Image wie für den Pi.

**Fertig, wenn:**

- Der Tag ist gesetzt.
- Beide Images sind hochgeladen.
- CHANGELOG und Anleitung sind da.
- Der Mac mini läuft mit `v0.0`.

### 9 · Backup-Ort für den Mac mini (D32)

Wenn `install.sh` steht, frage ich dich, wohin die Backups des Mac mini zusätzlich sollen. Zur Wahl stehen zum Beispiel das MacBook, eine USB-Platte am Mac mini oder der Speicher der Fritzbox. Danach legen wir fest, wann der Restore-Test von selbst läuft.

### 10 · Raspberry Pi (wartet auf den Pi)

- **T8:** offizielles Image starten, Zeit und RAM messen.
- **Frische Installation:** nur mit der Kurzanleitung. Das ist der letzte Teil von „Fertig wenn“.
- **Später der Umzug vom Mac mini auf den Pi:** Backup, Restore, und der Tunnel läuft nur auf einem Gerät (D27, D28).

## Was ich dabei nicht mache

- Passwörter, Schlüssel und Push-Adressen fasse ich nicht an: nicht ansehen, nicht eintragen, nicht ins Repo legen. Das machst du per nano; ich prüfe nur, ob etwas eingetragen ist.
- An der Datenbank des Mac mini ändere ich nichts direkt. Entwickelt wird nur auf dem MacBook.
- Familienmitglieder schreibe ich nicht an; die Einladung verschickst du.
