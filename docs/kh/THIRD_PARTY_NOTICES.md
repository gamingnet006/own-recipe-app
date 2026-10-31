# Third-party notices – Küchenhelfer

Küchenhelfer is a fork of [Mealie](https://github.com/mealie-recipes/mealie) and, like Mealie, licensed under the AGPL-3.0 (PLAN.md D2). This file lists the third-party software that Küchenhelfer adds to Mealie or ships with it, with the reason it is needed.

Mealie's own dependencies come with Mealie, each under its own license. They are listed in Mealie's package files:

- backend: `pyproject.toml` and `uv.lock`
- frontend: `frontend/package.json` and `frontend/pnpm-lock.yaml`
- base images: `docker/Dockerfile`

All licenses below were checked at the source on 2026-10-31, from the license data on GitHub and the package data inside the images. Every entry has an OSI-approved license; there is no source-available server part (PLAN.md section 9, item 4).

**Deutsch:** Diese Datei nennt alle fremden Teile, die Küchenhelfer zu Mealie dazunimmt oder mitliefert, mit Lizenz und Grund. Mealies eigene Abhängigkeiten stehen in Mealies Paketlisten.

## Shipped with every installation

| Component | Version | License | Source | Why |
|---|---|---|---|---|
| Mealie | v3.29.0 | AGPL-3.0 | [mealie-recipes/mealie](https://github.com/mealie-recipes/mealie) | The app itself; Küchenhelfer is a fork of it (D1). |
| cloudflared | 2026.10.1 | Apache-2.0 | image `cloudflare/cloudflared`, [cloudflare/cloudflared](https://github.com/cloudflare/cloudflared) | Tunnel for access from outside without an open router port (D14, D27). The `tunnel` service only starts with `kh/ops/tunnel.sh on`. |
| distroless base image (Debian 13) | as pinned by cloudflared 2026.10.1 | Debian packages under their own licenses | `gcr.io/distroless/base-debian13`, the base of the cloudflared image | Comes with cloudflared. |
| Alpine Linux | 3.22 | see the package list below | image `alpine:3.22` | Small base for the backup service (`kh/ops/backup/Dockerfile`, D20, D21). |

### Packages in the backup image

The backup image is built on each machine from `alpine:3.22` with `apk add --no-cache curl unzip tzdata age`. It needs curl for Mealie's API and Uptime Kuma, unzip to check backups, tzdata for the backup time, and age to encrypt the copies on a removable drive (`kh/ops/backup_copy.sh`, D32). The other packages come with Alpine or with these four.

Patch versions can differ a little between builds. The list below is from the build on 2026-10-31. To see the exact list on your machine:

```bash
docker run --rm --entrypoint apk kuechenhelfer-backup:dev list --installed
```

| Package | Version | License |
|---|---|---|
| curl, libcurl | 8.14.1 | curl (MIT-style) |
| unzip | 6.0 | Info-ZIP license (apk lists it as "custom") |
| tzdata | 2026e | Public domain |
| age (age, age-keygen) | 1.2.1 | BSD-3-Clause, [FiloSottile/age](https://github.com/FiloSottile/age) |
| BusyBox (busybox, busybox-binsh, ssl_client; provides `sh` and `crond`) | 1.37.0 | GPL-2.0-only |
| musl | 1.2.5 | MIT |
| musl-utils | 1.2.5 | MIT AND BSD-2-Clause AND GPL-2.0-or-later |
| OpenSSL (libcrypto3, libssl3) | 3.5.9 | Apache-2.0 |
| ca-certificates-bundle | 20261020 | MPL-2.0 AND MIT |
| zlib | 1.3.2 | Zlib |
| zstd-libs | 1.5.7 | BSD-3-Clause OR GPL-2.0-or-later |
| brotli-libs | 1.1.1 | MIT |
| c-ares | 1.34.9 | MIT |
| nghttp2-libs | 1.69.0 | MIT |
| libidn2 | 2.3.7 | GPL-2.0-or-later OR LGPL-3.0-or-later |
| libunistring | 1.3 | GPL-2.0-or-later OR LGPL-3.0-or-later |
| libpsl | 0.21.5 | MIT |
| alpine-baselayout, alpine-baselayout-data | 3.7.0 | GPL-2.0-only |
| apk-tools, libapk2 | 2.14.12 | GPL-2.0-only |
| scanelf (pax-utils) | 1.3.8 | GPL-2.0-only |
| alpine-keys | 2.5 | MIT |
| alpine-release | 3.22.7 | MIT |

## Used only for building and releasing (not shipped)

| Component | Version | License | Used in | Why |
|---|---|---|---|---|
| actions/checkout | v6 | MIT | `.github/workflows/kh-ci.yml`, `kh-release.yml` | Gets the code for tests and the release build. |
| docker/setup-buildx-action | v4 | Apache-2.0 | `kh-release.yml` | Sets up the image build. |
| docker/build-push-action | v7 | Apache-2.0 | `kh-release.yml` | Builds the amd64 image. |
| docker/login-action | v4 | Apache-2.0 | `kh-release.yml` | Logs in to the GitHub Container Registry to push the image. |

## Not part of Küchenhelfer

Docker, Docker Compose, Colima, Uptime Kuma, the Cloudflare service and Google Gemini (with a key from Google AI Studio, D35) are installed or used by whoever runs Küchenhelfer, under their own terms. Which data goes to which service is listed in the table „Was geht wohin“ in [README.md](README.md).
