# Changelog – Küchenhelfer

Notable changes per release. Every release is a git tag with the app image in GHCR as
`ghcr.io/gamingnet006/own-recipe-app:<version>-arm64` (Raspberry Pi, Apple Silicon) and
`<version>-amd64` (Intel/AMD), published with `kh/ops/release.sh`. That script refuses a version without its own `## [version]` section here.

## [Unreleased]

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
