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
- **Kopie auf einen USB-Stick** (D32): Jede Nacht um 3:45 Uhr kommen die neuen Backups verschlüsselt auf ein zweites Laufwerk, zum Beispiel einen USB-Stick mit exFAT. Öffnen lassen sie sich nur mit deinem Passwort, das nirgends gespeichert wird. Vergisst du es, sind die Kopien verloren.
  1. Am Mac braucht der nächtliche Job einmal Festplattenvollzugriff, sonst sperrt macOS den Stick: Systemeinstellungen → Sicherheit & Datenschutz → Datenschutz → Festplattenvollzugriff → „+“ → ⇧⌘G → `/bin/dash`. Außer diesem Job startet nichts `dash`.
  2. Stick einstecken und einschalten, über SSH mit `ssh -t`: `kh/ops/backup_copy.sh on /Volumes/<Stick>/Kuechenhelfer-Backups`. Beim ersten Mal fragt age zweimal nach dem Passwort. Am Pi muss der Stick eingehängt sein, zum Beispiel über `/etc/fstab`.
  3. Stand prüfen: `kh/ops/backup_copy.sh status`. Fehlt der Stick, schreibt der Job nichts und meldet es, mit `KH_BACKUP_PUSH_URL` auch an Uptime Kuma.
  - Zurückholen: `kh/ops/backup_copy.sh decrypt <Stick>/Kuechenhelfer-Backups/<backup>.zip.age` fragt nach dem Passwort und legt das Backup in den Backup-Ordner; danach `restore.sh <backup>.zip` wie unter „Alltag“. Am Mac im Terminal am Gerät selbst aufrufen, nicht über SSH. Dieselben Schritte stehen in `LIESMICH.txt` auf dem Stick.

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
- **Copy to a USB stick** (D32): every night at 3:45 am the new backups go, encrypted, to a second drive such as a USB stick with exFAT. Only your password opens them; it is stored nowhere. If you forget it, the copies are lost.
  1. On a Mac the nightly job needs Full Disk Access once, or macOS locks the stick: System Preferences → Security & Privacy → Privacy → Full Disk Access → "+" → ⇧⌘G → `/bin/dash`. Nothing but this job starts `dash`.
  2. Plug in the stick and switch the copy on, over SSH with `ssh -t`: `kh/ops/backup_copy.sh on /Volumes/<stick>/Kuechenhelfer-Backups`. The first time, age asks for the password twice. On a Pi the stick must be mounted, for example through `/etc/fstab`.
  3. Check: `kh/ops/backup_copy.sh status`. Without the stick the job writes nothing and reports it, with `KH_BACKUP_PUSH_URL` also to Uptime Kuma.
  - Bring one back: `kh/ops/backup_copy.sh decrypt <stick>/Kuechenhelfer-Backups/<backup>.zip.age` asks for the password and puts the backup into the backup folder; then `restore.sh <backup>.zip` as under "Day to day". On a Mac run it in the Terminal on the machine itself, not over SSH. `LIESMICH.txt` on the stick has the same steps.

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
