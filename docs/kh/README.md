# own-recipe-app (working name: Küchenhelfer)

A free, self-hosted family recipe app and website, based on a fork of [Mealie](https://github.com/mealie-recipes/mealie) (AGPL-3.0). Runs in Docker on a Raspberry Pi, a Mac or any Linux machine.

**Deutsch:** Eine kostenlose, selbst gehostete Rezept-App und Webseite für die Familie, auf Basis eines Mealie-Forks. Läuft in Docker auf einem Raspberry Pi, einem Mac oder einem Linux-Rechner. Die Kurzanleitung steht direkt unten, die englische Fassung danach.

**Status:** phase 1 (`v0.0`): runs for the family with backups, automatic updates and access from outside. Every phase ends with a release that can be installed on its own (D15).

- Plan: [PLAN.md](../../PLAN.md) (Deutsch, authoritative) · [PLAN.en.md](../../PLAN.en.md)
- Rules for development: [CLAUDE.md](../../.claude/CLAUDE.md) · [CLAUDE.en.md](CLAUDE.en.md)
- Changes: [CHANGELOG.md](CHANGELOG.md) · Licenses: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)
- Family accounts: [Deutsch](familienkonten.md) · [English](familienkonten.en.md)

No credentials, passwords or keys are ever stored in this repo; configuration uses placeholders in `kh/ops/.env.example`.

---

## Installieren

### Voraussetzungen

- **Ein Rechner, der dauernd läuft:**
  - Raspberry Pi 4 oder 5 mit Raspberry Pi OS 64-Bit, die Daten auf einer SSD statt auf der SD-Karte.
  - Ein Mac oder ein Linux-Rechner.
  - Windows mit Docker Desktop (WSL2) ist noch nicht getestet.
- **Docker mit Compose:**
  - Auf dem Pi und unter Linux: [Docker Engine](https://docs.docker.com/engine/install/).
  - Auf dem Mac: [Colima](https://github.com/abiosoft/colima), zum Beispiel `brew install colima docker docker-compose`, dann `colima start --cpu 2 --memory 4`. Docker Desktop geht auch.
- **Auf dem Mac außerdem:**
  - Ruhezustand aus.
  - Automatische Anmeldung an.
  - Colima startet beim Anmelden (`brew services start colima`).
- **Speicher:** etwa 1 GB freier Arbeitsspeicher. Küchenhelfer selbst braucht rund 250 MB.

### 1. Bei ghcr.io anmelden

Das ist nur nötig, solange die Images privat sind.

1. Lege bei GitHub einen Schlüssel an: Settings → Developer settings → Personal access tokens → Tokens (classic). Setz nur das Häkchen bei `read:packages`.
2. Melde dich an:

   ```bash
   docker login ghcr.io -u DEIN-GITHUB-NAME
   ```

   Als Passwort fügst du den Schlüssel ein.

### 2. Betriebsdateien holen

Die Dateien kommen aus dem Release-Image. Die zweite Zeile wählt das passende Image für den Prozessor: `arm64` für Pi und Apple Silicon, `amd64` für Intel und AMD.

```bash
mkdir -p ~/kuechenhelfer && cd ~/kuechenhelfer
image=ghcr.io/gamingnet006/own-recipe-app:v0.0-$(docker version -f '{{.Server.Arch}}')
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD":/out --entrypoint sh "$image" -c 'cp -R /app/kh-bundle/. /out/'
```

### 3. Einrichten und starten

```bash
kh/ops/install.sh "$image"
```

Das Skript fragt zwei Dinge:

- **Wohin die Backups sollen:** Am sichersten ist ein anderes Laufwerk, ein Netzlaufwerk oder ein Ordner, den ein zweites Gerät abholt.
- **Unter welcher Adresse ihr Küchenhelfer öffnet.**

Danach startet es alles, legt den Schlüssel für die Backups an und zeigt die erste Anmeldung an. Das tägliche Backup läuft um 3:30 Uhr.

### 4. Erste Anmeldung

1. Öffne die angezeigte Adresse und melde dich mit dem Standard-Konto an, das `install.sh` nennt.
2. Ändere sofort unter **Profil** E-Mail und Passwort.
3. Erscheint Mealies Einrichtungs-Assistent, lass **Öffentlichen Zugriff aktivieren** aus.

### 5. Familie einladen

Jede Person bekommt einen Einladungslink und legt ihr Konto selbst an, siehe [familienkonten.md](familienkonten.md).

### 6. Automatische Updates

Jede Nacht um 4 Uhr holt Küchenhelfer die neueste stabile Version und spielt sie mit Backup und Rückfall ein (D29).

1. Trag den Lese-Schlüssel aus Schritt 1 in `kh/ops/.env` ein, zum Beispiel mit `nano kh/ops/.env`: `KH_REGISTRY_USER` (dein GitHub-Name) und `KH_REGISTRY_TOKEN` (der Schlüssel).
2. Schalte die Updates ein und prüf den Stand:

   ```bash
   kh/ops/auto_update.sh on
   kh/ops/auto_update.sh status
   ```

### 7. KI einrichten (Gemini)

Eine KI liest Fotos, Screenshots, Texte und Links ohne Rezeptdaten. Links mit Rezeptdaten gehen auch ohne sie. Küchenhelfer nutzt dafür Google Gemini mit einem kostenlosen Schlüssel (D35). Ein Google-Konto genügt, eine Kreditkarte nicht.

1. Melde dich in [Google AI Studio](https://aistudio.google.com) an und leg unter **Get API key** einen Schlüssel an. Hinterleg dort **kein Bezahlkonto**. Ohne Bezahlkonto entstehen keine Kosten; ist das Tageskontingent aufgebraucht, meldet Küchenhelfer „Kontingent für heute aufgebraucht“.
2. Öffne in Küchenhelfer **Profil → Gruppen-Einstellungen → KI-Anbieter-Einstellungen → Anbieter erstellen** und trag ein:
   - **Anbietername:** zum Beispiel `Gemini`
   - **Basis-URL:** `https://generativelanguage.googleapis.com/v1beta/openai/`
   - **API-Key:** der Schlüssel aus AI Studio
   - **Modell:** ein Flash-Modell, genau so geschrieben, wie AI Studio es anzeigt
   - **Supports images** anhaken
3. Prüf die Verbindung mit **Test Connection** und speichere. Wähl den Anbieter dann als **Standard-Anbieter** und als **Bildanbieter**.

Im Gratis-Angebot darf Google eingereichte Texte, Fotos und Screenshots nutzen (siehe „Was geht wohin“). Der Schlüssel liegt in Küchenhelfers Datenbank und damit in jedem Backup.

### Rezept hinzufügen

Neue Rezepte kommen über **Erstellen → Rezept hinzufügen**; auch Mealies Import-Seiten führen dorthin. Selbst eintippen geht weiter über den zweiten Eintrag im Menü **Erstellen**.

- **Link:** Adresse einfügen. Hat die Seite Rezeptdaten, liest Küchenhelfer sie ohne KI, sonst liest die KI die Seite.
- **Text:** Rezepttext einfügen, zum Beispiel aus einer Nachricht.
- **Foto oder Screenshot:** Kamera oder Mediathek. Ein Rezept auf mehreren Seiten bekommt alle Fotos zusammen, bis zu fünf.

Danach wartet das Rezept als Entwurf unter **Entwürfe (n)** und ist nach ein paar Sekunden erkannt. Jeder im Haushalt sieht alle Entwürfe und darf sie übernehmen. In der Prüfansicht steht das Original neben dem Ergebnis, am Handy untereinander:

- **Übernehmen** speichert das Rezept, **Übernehmen und bearbeiten** öffnet es gleich zum Ändern.
- **Verwerfen** löscht den Entwurf samt Original.
- Gibt es das Rezept vielleicht schon (gleicher Link, ähnlicher Titel oder dieselben Zutaten), steht oben ein Hinweis mit Link. Gelöscht wird nie etwas von selbst.
- Ging die Erkennung schief, steht der Grund dabei, mit **Neu versuchen**.

Am gespeicherten Rezept zeigt ein Abzeichen, woher es kam, mit **Original ansehen**.

### Optional

- **Zugang von unterwegs** (Cloudflare Tunnel, D27):
  1. Leg in Cloudflare Zero Trust unter Networks → Tunnels einen Tunnel an, mit Route auf `http://mealie:9000`.
  2. Trag seinen Schlüssel als `KH_TUNNEL_TOKEN` und die öffentliche Adresse als `KH_BASE_URL` ein.
  3. Starte ihn mit `kh/ops/tunnel.sh on`. Das Skript geht nur online, wenn Selbstregistrierung aus ist, das Standard-Konto geändert ist und alle Gruppen und Haushalte privat sind.
- **Meldungen an Uptime Kuma:** Lege zwei Monitore vom Typ „Push“ an und trag ihre Adressen ein, mit Hinweisen in `kh/ops/.env.example`.
  - `KH_BACKUP_PUSH_URL`: mit `host.docker.internal` statt `localhost`, weil das Backup im Container läuft.
  - `KH_UPDATE_PUSH_URL`
  - Danach `docker compose -f kh/ops/docker-compose.yml up -d backup`.
- **Backup prüfen:** `kh/ops/restore_test.sh` spielt das neueste Backup in eine Wegwerf-Installation ein und vergleicht Rezepte und Dateien.
- **Kopie auf einen USB-Stick** (D32): Jede Nacht um 3:45 Uhr kommen die neuen Backups auf ein zweites Laufwerk, zum Beispiel einen USB-Stick mit exFAT. Beim Einrichten wählst du, ob sie ein Passwort bekommen (D33). Mit Passwort sind sie verschlüsselt, und das Passwort wird nirgends gespeichert: Vergisst du es, sind die Kopien verloren. Ohne Passwort sind es normale Mealie-Backups.
  1. Am Mac braucht der nächtliche Job einmal Festplattenvollzugriff, sonst sperrt macOS den Stick: Systemeinstellungen → Sicherheit & Datenschutz → Datenschutz → Festplattenvollzugriff → „+“ → ⇧⌘G → `/bin/dash`. Auf einem Mac startet sonst kaum etwas `dash`, die Freigabe bleibt also bei diesem Job.
  2. Stick einstecken und einschalten, über SSH mit `ssh -t`: `kh/ops/backup_copy.sh on /Volumes/<Stick>/Kuechenhelfer-Backups`. Beim ersten Mal fragt das Skript „Kopien mit Passwort verschlüsseln? (j/n)“; bei „j“ fragt age zweimal nach dem Passwort. Am Pi muss der Stick eingehängt sein, zum Beispiel über `/etc/fstab`.
  3. Stand prüfen: `kh/ops/backup_copy.sh status`. Fehlt der Stick, schreibt der Job nichts und meldet es, mit `KH_BACKUP_PUSH_URL` auch an Uptime Kuma.
  4. Mit Passwort zur Probe eine Kopie öffnen: `kh/ops/backup_copy.sh decrypt <Stick>/Kuechenhelfer-Backups/<backup>.zip.age`. Solange dasselbe Backup noch auf diesem Rechner liegt, vergleicht der Befehl nur und meldet, ob die Kopie stimmt.
  - Zurückholen: Mit Passwort fragt `kh/ops/backup_copy.sh decrypt <Stick>/Kuechenhelfer-Backups/<backup>.zip.age` danach und legt das Backup in den Backup-Ordner; am Mac im Terminal am Gerät selbst aufrufen, nicht über SSH. Ohne Passwort die `.zip` vom Stick nach `kh/ops/backups` kopieren. Danach `restore.sh <backup>.zip` wie unter „Alltag“. Dieselben Schritte stehen in `LIESMICH.txt` auf dem Stick.
  - Stick ohne Passwort verloren: Wer ihn hat, kommt mit dem Backup-Schlüssel darin in die App. Lösch dann in Küchenhelfer unter Profil → API-Tokens den Token des Backup-Dienstes (bei neuen Installationen `kh-backup`), leg einen neuen an, trag ihn als `KH_BACKUP_API_TOKEN` in `kh/ops/.env` ein und führ `docker compose -f kh/ops/docker-compose.yml up -d backup` aus. Lösch zuletzt `kh/ops/data/.secret` und starte Mealie neu (`docker compose -f kh/ops/docker-compose.yml restart mealie`); danach melden sich alle einmal neu an. Auch der KI-Schlüssel steckt im Backup: Leg in Google AI Studio einen neuen an, trag ihn unter Gruppen-Einstellungen → KI-Anbieter ein und lösch den alten in AI Studio.

### Alltag

```bash
# Update von Hand: Backup, Wechsel, Prüfung, bei Fehler zurück
kh/ops/update.sh ghcr.io/gamingnet006/own-recipe-app:<version>-<arm64|amd64>
# Backup sofort, vorhandene Backups anzeigen, eines wiederherstellen
docker compose -f kh/ops/docker-compose.yml run --rm --no-deps backup backup.sh
docker compose -f kh/ops/docker-compose.yml run --rm --no-deps backup restore.sh [datei.zip]
# Stoppen und wieder starten
docker compose -f kh/ops/docker-compose.yml down
docker compose -f kh/ops/docker-compose.yml up -d
```

Auf dem Mac brauchen eigene Hintergrund-Jobs (cron, launchd) `/usr/local/bin` im PATH, sonst finden sie `docker` nicht. `auto_update.sh` ergänzt das selbst.

### Was geht wohin

Was Küchenhelfer heute nach draußen schickt. Telemetrie gibt es keine.

| Funktion | Was wird gesendet | An wen | Abschalten |
|---|---|---|---|
| Link einlesen | Abruf der Seite und ihres Rezeptbilds | die jeweilige Webseite | – |
| KI: Text, Foto, Screenshot oder Link ohne Rezeptdaten auslesen; Mealies KI-Zutatenerkennung, wenn man sie wählt | der Text, die Bilder oder der Inhalt der Seite; im Gratis-Angebot darf Google sie nutzen | Google Gemini, nur mit eingetragenem Schlüssel (D35) | KI-Anbieter in den Gruppen-Einstellungen löschen |
| Zugang von unterwegs | gesamter Verkehr zur Web-App; Cloudflare kann ihn lesen, weil HTTPS dort endet | Cloudflare (Tunnel, D27) | `kh/ops/tunnel.sh off` |
| Automatische Updates | Abruf der Versionsliste und der neuen Images, mit dem Lese-Schlüssel, solange das Repo privat ist; beim Erneuern des Backup-Dienstes das Alpine-Basisimage und Pakete | GitHub (ghcr.io), Docker Hub, Alpine-Paketspiegel (D29) | `kh/ops/auto_update.sh off` |
| Mealies Versionsprüfung | nur die Frage nach der neuesten Mealie-Version, wenn ein Admin die Verwaltung öffnet | GitHub (api.github.com) | – |
| Backups und Kopie | alle Daten, auch der KI-Schlüssel | dein Backup-Ordner und, falls eingerichtet, der USB-Stick; verschlüsselt, wenn beim Einrichten ein Passwort gewählt wurde (D32, D33) | `kh/ops/backup_copy.sh off` für die Kopie |
| Meldungen | ob Backup, Kopie und Update geklappt haben | dein Uptime Kuma | Push-Adressen in `kh/ops/.env` leer lassen |

---

## Install (English)

### Requirements

- **A machine that is always on:**
  - Raspberry Pi 4 or 5 with Raspberry Pi OS 64-bit, with the data on an SSD instead of the SD card.
  - A Mac or a Linux machine.
  - Windows with Docker Desktop (WSL2) is not tested yet.
- **Docker with Compose:**
  - On the Pi and on Linux: [Docker Engine](https://docs.docker.com/engine/install/).
  - On a Mac: [Colima](https://github.com/abiosoft/colima), for example `brew install colima docker docker-compose`, then `colima start --cpu 2 --memory 4`. Docker Desktop works too.
- **On a Mac also:**
  - Sleep off.
  - Automatic login on.
  - Colima starts at login (`brew services start colima`).
- **Memory:** about 1 GB of free RAM. Küchenhelfer itself needs around 250 MB.

### 1. Log in to ghcr.io

This is only needed while the images are private.

1. Create a key on GitHub: Settings → Developer settings → Personal access tokens → Tokens (classic). Tick only `read:packages`.
2. Log in:

   ```bash
   docker login ghcr.io -u YOUR-GITHUB-NAME
   ```

   Paste the key as the password.

### 2. Get the ops files

The files come from the release image. The second line picks the image for your CPU: `arm64` for the Pi and Apple Silicon, `amd64` for Intel and AMD.

```bash
mkdir -p ~/kuechenhelfer && cd ~/kuechenhelfer
image=ghcr.io/gamingnet006/own-recipe-app:v0.0-$(docker version -f '{{.Server.Arch}}')
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD":/out --entrypoint sh "$image" -c 'cp -R /app/kh-bundle/. /out/'
```

### 3. Set up and start

```bash
kh/ops/install.sh "$image"
```

The script asks two things:

- **Where the backups go:** safest on another drive, a network drive or a folder a second device collects.
- **Under which address you open Küchenhelfer.**

It then starts everything, creates the key for the backups and shows the first login. The daily backup runs at 3:30 am.

### 4. First login

1. Open the address shown and log in with the default account that `install.sh` names.
2. Change e-mail and password right away under **Profile**.
3. If Mealie's setup wizard appears, leave **Enable public access** off.

### 5. Invite the family

Each person gets an invite link and creates their own account, see [familienkonten.en.md](familienkonten.en.md).

### 6. Automatic updates

Every night at 4 am Küchenhelfer fetches the newest stable version and installs it with a backup and a rollback (D29).

1. Put the read key from step 1 into `kh/ops/.env`, for example with `nano kh/ops/.env`: `KH_REGISTRY_USER` (your GitHub name) and `KH_REGISTRY_TOKEN` (the key).
2. Switch the updates on and check the state:

   ```bash
   kh/ops/auto_update.sh on
   kh/ops/auto_update.sh status
   ```

### 7. Set up AI (Gemini)

An AI reads photos, screenshots, texts and links without recipe data. Links with recipe data work without it. Küchenhelfer uses Google Gemini with a free key for this (D35). A Google account is enough, no credit card.

1. Sign in to [Google AI Studio](https://aistudio.google.com) and create a key under **Get API key**. Do **not** add a billing account there. Without one nothing costs money; when the daily quota is used up, Küchenhelfer says "Today's AI quota is used up".
2. In Küchenhelfer open **Profile → Group Settings → AI Provider Settings → Create Provider** and enter:
   - **Provider Name:** for example `Gemini`
   - **Base URL:** `https://generativelanguage.googleapis.com/v1beta/openai/`
   - **API Key:** the key from AI Studio
   - **Model:** a Flash model, written exactly as AI Studio shows it
   - tick **Supports images**
3. Check the connection with **Test Connection** and save. Then choose the provider as **Default Provider** and as **Image Provider**.

On the free tier Google may use the texts, photos and screenshots handed in (see "What goes where"). The key is stored in Küchenhelfer's database and so in every backup.

### Add a recipe

New recipes come in through **Create → Add recipe**; Mealie's import pages lead there too. Typing a recipe yourself still works through the second entry in the **Create** menu.

- **Link:** paste the address. If the page has recipe data, Küchenhelfer reads it without AI, otherwise the AI reads the page.
- **Text:** paste the recipe text, for example from a message.
- **Photo or screenshot:** camera or photo library. A recipe on several pages gets all its photos together, up to five.

The recipe then waits as a draft under **Drafts (n)** and is recognized after a few seconds. Everyone in the household sees all drafts and may save them. The review shows the original next to the result, one below the other on a phone:

- **Save** stores the recipe, **Save and edit** opens it right away for changes.
- **Discard** deletes the draft with its original.
- If the recipe may exist already (same link, similar title or the same ingredients), a hint with a link is shown on top. Nothing is ever deleted by itself.
- If the recognition went wrong, the reason is shown, with **Try again**.

A badge on the saved recipe shows where it came from, with **View original**.

### Optional

- **Access from outside** (Cloudflare Tunnel, D27):
  1. Create a tunnel in Cloudflare Zero Trust under Networks → Tunnels, with a route to `http://mealie:9000`.
  2. Put its key into `KH_TUNNEL_TOKEN` and the public address into `KH_BASE_URL`.
  3. Start it with `kh/ops/tunnel.sh on`. The script only goes online when self sign-up is off, the default account is changed and every group and household is private.
- **Reports to Uptime Kuma:** create two monitors of type "Push" and put their addresses in, with hints in `kh/ops/.env.example`.
  - `KH_BACKUP_PUSH_URL`: with `host.docker.internal` instead of `localhost`, because the backup runs in a container.
  - `KH_UPDATE_PUSH_URL`
  - Then run `docker compose -f kh/ops/docker-compose.yml up -d backup`.
- **Check a backup:** `kh/ops/restore_test.sh` restores the newest backup into a throwaway install and compares recipes and files.
- **Copy to a USB stick** (D32): every night at 3:45 am the new backups go to a second drive such as a USB stick with exFAT. When you set it up, you choose whether they get a password (D33). With a password they are encrypted and the password is stored nowhere: if you forget it, the copies are lost. Without one they are normal Mealie backups.
  1. On a Mac the nightly job needs Full Disk Access once, or macOS locks the stick: System Preferences → Security & Privacy → Privacy → Full Disk Access → "+" → ⇧⌘G → `/bin/dash`. Hardly anything else on a Mac starts `dash`, so the permission stays with this job.
  2. Plug in the stick and switch the copy on, over SSH with `ssh -t`: `kh/ops/backup_copy.sh on /Volumes/<stick>/Kuechenhelfer-Backups`. The first time, the script asks "Kopien mit Passwort verschlüsseln? (j/n)" (encrypt the copies with a password?); with "j", age asks for the password twice. On a Pi the stick must be mounted, for example through `/etc/fstab`.
  3. Check: `kh/ops/backup_copy.sh status`. Without the stick the job writes nothing and reports it, with `KH_BACKUP_PUSH_URL` also to Uptime Kuma.
  4. With a password, open a copy as a test: `kh/ops/backup_copy.sh decrypt <stick>/Kuechenhelfer-Backups/<backup>.zip.age`. While the same backup is still on this machine, the command only compares and reports whether the copy is right.
  - Bring one back: with a password, `kh/ops/backup_copy.sh decrypt <stick>/Kuechenhelfer-Backups/<backup>.zip.age` asks for it and puts the backup into the backup folder; on a Mac run it in the Terminal on the machine itself, not over SSH. Without a password, copy the `.zip` from the stick into `kh/ops/backups`. Then `restore.sh <backup>.zip` as under "Day to day". `LIESMICH.txt` on the stick has the same steps.
  - Lost a stick without a password: whoever has it gets into the app with the backup key inside. Then delete the backup service's token in Küchenhelfer under Profile → API Tokens (`kh-backup` on new installs), create a new one, put it into `kh/ops/.env` as `KH_BACKUP_API_TOKEN` and run `docker compose -f kh/ops/docker-compose.yml up -d backup`. Finally delete `kh/ops/data/.secret` and restart Mealie (`docker compose -f kh/ops/docker-compose.yml restart mealie`); everyone then logs in once more. The AI key is in the backup too: create a new one in Google AI Studio, enter it under Group Settings → AI Providers and delete the old one in AI Studio.

### Day to day

```bash
# Update by hand: backup, switch, check, roll back on failure
kh/ops/update.sh ghcr.io/gamingnet006/own-recipe-app:<version>-<arm64|amd64>
# Backup right now, list backups, restore one
docker compose -f kh/ops/docker-compose.yml run --rm --no-deps backup backup.sh
docker compose -f kh/ops/docker-compose.yml run --rm --no-deps backup restore.sh [file.zip]
# Stop and start again
docker compose -f kh/ops/docker-compose.yml down
docker compose -f kh/ops/docker-compose.yml up -d
```

On a Mac, your own background jobs (cron, launchd) need `/usr/local/bin` in PATH, or they do not find `docker`. `auto_update.sh` adds it itself.

### What goes where

What Küchenhelfer sends out today. There is no telemetry.

| Feature | What is sent | To whom | Switch off |
|---|---|---|---|
| Read a link | fetching the page and its recipe picture | the website in question | – |
| AI: read a text, photo, screenshot or a link without recipe data; Mealie's AI ingredient parser when chosen | the text, the pictures or the page's content; on the free tier Google may use them | Google Gemini, only with a key entered (D35) | delete the AI provider in the group settings |
| Access from outside | all traffic to the web app; Cloudflare can read it because HTTPS ends there | Cloudflare (tunnel, D27) | `kh/ops/tunnel.sh off` |
| Automatic updates | requests for the version list and the new images, with the read key while the repo is private; when the backup service is rebuilt, the Alpine base image and packages | GitHub (ghcr.io), Docker Hub, Alpine package mirrors (D29) | `kh/ops/auto_update.sh off` |
| Mealie's version check | only the question for the newest Mealie version, when an admin opens the admin pages | GitHub (api.github.com) | – |
| Backups and copy | all data, the AI key included | your backup folder and, if set up, the USB stick; encrypted when a password was chosen during setup (D32, D33) | `kh/ops/backup_copy.sh off` for the copy |
| Reports | whether backup, copy and update worked | your Uptime Kuma | leave the push addresses in `kh/ops/.env` empty |
