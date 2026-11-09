# Kochheft backups: helping someone get their recipes back

This folder holds backups of Kochheft, a family cookbook (a fork of Mealie). Whoever started
you here most likely lost the machine that ran it and wants the recipes back. The person may not
be technical: go step by step, say what each command does before running it, and check the
result after each step. `LIESMICH.txt` (German) has the same steps for people.

## What is here

- `*.zip.age`: daily backups, encrypted with age (https://age-encryption.org) to the key in
  `kuechenhelfer-schluessel.age`, which is itself locked with a password the family chose.
- `*.zip`: daily backups without encryption, each a normal Mealie backup: `database.json` with
  all tables, `data/` with photos and files.
- The file name ends in the UTC time `YYYY.MM.DD.HH.MM.SS`; the newest is usually the right one.

## Restore

1. Install Kochheft from the private GitHub repo `gamingnet006/own-recipe-app`
   (`docs/kh/README.md`, section "Install (English)"). It needs Docker with Compose, and while
   the images are private a `docker login ghcr.io` with a token that may read packages. Prefer
   the newest release: Mealie's restore builds the schema up to the backup's migration, so a
   newer version restores older backups, but an older version cannot read newer ones.
2. In the install folder (the one holding `kh/`):
   - encrypted: `kh/ops/backup_copy.sh decrypt "<this folder>/<name>.zip.age"`; age asks for the
     password in the terminal, and the zip lands in the install's backup folder (`KH_BACKUP_DIR`
     in `kh/ops/.env`, default `kh/ops/backups`). On a Mac run it in a terminal on the machine
     itself, not over SSH, where macOS hides removable drives.
   - plain: copy the zip into that backup folder.
3. `docker compose -f kh/ops/docker-compose.yml run --rm --no-deps backup restore.sh <name>.zip`
   (without a name it lists the backups it sees). This replaces all data of that install, so
   confirm with the person first.
4. `docker compose -f kh/ops/docker-compose.yml restart mealie`, so the database migrates to the
   running version. Then the person logs in with their old account and checks a few recipes.

## Rules

- Never ask for the password in the chat and never write it into a file: the person types it
  when age asks. Without it the encrypted backups cannot be opened, and nobody can reset it.
- Work on copies: never delete, move or rename anything in this folder, least of all
  `kuechenhelfer-schluessel.age`.
- A backup holds every account and the backup service's API key in plain text: keep decrypted
  copies out of shared or public places, and delete them once the restore worked.
- If Kochheft cannot be installed, `age -d -i kuechenhelfer-schluessel.age -o backup.zip
  <name>.zip.age` opens an encrypted backup, and `database.json` can be read directly.
