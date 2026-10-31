# Changelog – Küchenhelfer

Notable changes per release. Every release is a git tag with the app image in GHCR as
`ghcr.io/gamingnet006/own-recipe-app:<version>-arm64` (Raspberry Pi, Apple Silicon) and
`<version>-amd64` (Intel/AMD), published with `kh/ops/release.sh`. That script refuses a version without its own `## [version]` section here.

## [Unreleased]

- Access from outside through a Cloudflare Tunnel (`kh/ops/tunnel.sh on|off|status`); it only starts
  if self sign-up is off and no account still uses Mealie's default e-mail.
- Logins stay valid for 30 days without opening the app (`KH_TOKEN_TIME`; Mealie's default is 48 hours).
- `tunnel.sh` rejects a pasted install command right away and asks for the key alone.
- Mealie's RAM is capped (`KH_MEMORY_LIMIT`, default 2 GB), so it can share a machine with other services.
- Automatic updates to stable releases (`kh/ops/auto_update.sh on|off|status|check|run`): on by default,
  nightly at 4 am, always through `update.sh`. Release images carry the ops files (`/app/kh-bundle`).
- `update.sh` also refreshes the backup service and a running tunnel after a successful switch.
- `update.sh` exits with 4 (was 1) when it stops before changing anything, so the nightly update
  tries the same version again instead of skipping it.
- On macOS the nightly update is a LaunchAgent instead of a cron job: macOS lets `crontab` write
  only with Full Disk Access, which SSH sessions lack.
- Uptime Kuma push URLs work when pasted with the example query Uptime Kuma shows
  (`?status=up&msg=OK&ping=`); before, every report counted as down.
- The backup service reaches Uptime Kuma on the same machine as `host.docker.internal`, also on Linux.
- Restore test (`kh/ops/restore_test.sh [backup.zip]`): restores the newest or the given backup with
  `restore.sh` into a throwaway install running the same image and checks that every recipe and file is back.
- Share links are off by default (`KH_SHARE_LINKS=false`): the recipe menu shows no "Share", and public
  recipe pages by token answer 404. Recipe downloads keep working.
- New groups show no Mealie announcements (links to Mealie's docs); the switch in the group settings stays.
- Küchenhelfer's own code starts: backend in `mealie/kh/`, frontend as the Nuxt layer `frontend/kh/` (D26);
  `GET /api/kh/features` tells the frontend which switches are on.
- `tunnel.sh on` also refuses to go online while a group or household is public, so recipes never
  become readable without login by accident.
- New installs: `kh/ops/install.sh <image>` asks where the backups go (D32) and under which address the
  app opens, writes `.env`, starts everything and creates the backup key. Release images carry it.
- Install guide in German and English in `docs/kh/README.md`; family accounts by invite link in
  `docs/kh/familienkonten.md` (D31).

## [v0.0-rc.2] - 2026-10-30

Second release candidate, to try out the upgrade test in CI. Not meant for the family yet.

- Upgrade test (D23): the release workflow installs the previous release with self-made test
  recipes and a test image, updates with `update.sh` and compares; only then the amd64 image is
  pushed. Also runs by hand: `kh/ops/upgrade_test.sh <old-image> <new-image>`.
- `update.sh`: the rollback image is named after the compose project, so a test install never
  replaces the rollback image of the real one.

## [v0.0-rc.1] - 2026-10-30

First release candidate, to try out the release pipeline. Not meant for the family yet:
phase 1 is not finished (no tunnel, no install guide, not tried on the Pi).

- Base: Mealie v3.29.0, brought in through the `upstream` remote; Mealie's code is unchanged.
- `kh/ops`: one compose setup for Mac and Pi; `.env.example` holds placeholders only.
- Backup service: daily backup through Mealie's backup API, copy to a second location,
  retention, restore, optional Uptime Kuma notification.
- `update.sh`: update to another image with backup, database snapshot, health and recipe
  checks, and automatic rollback.
- CI: Mealie's backend and frontend tests plus tests of the ops scripts; release images for
  amd64 (CI) and arm64 (Mac).
