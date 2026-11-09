# Third-party notices – Kochheft

Kochheft is a fork of [Mealie](https://github.com/mealie-recipes/mealie) and, like Mealie, licensed under the AGPL-3.0 (PLAN.md D2). This file lists the third-party software that Kochheft adds to Mealie or ships with it, with the reason it is needed.

Mealie's own dependencies come with Mealie, each under its own license. They are listed in Mealie's package files:

- backend: `pyproject.toml` and `uv.lock`
- frontend: `frontend/package.json` and `frontend/pnpm-lock.yaml`
- base images: `docker/Dockerfile`

All licenses below were checked at the source on 2026-10-31, from the license data on GitHub and the package data inside the images. Every entry has an OSI-approved license; there is no source-available server part (PLAN.md section 9, item 4).

**Deutsch:** Diese Datei nennt alle fremden Teile, die Kochheft zu Mealie dazunimmt oder mitliefert, mit Lizenz und Grund. Mealies eigene Abhängigkeiten stehen in Mealies Paketlisten.

## Shipped with every installation

| Component | Version | License | Source | Why |
|---|---|---|---|---|
| Mealie | v3.29.0 | AGPL-3.0 | [mealie-recipes/mealie](https://github.com/mealie-recipes/mealie) | The app itself; Kochheft is a fork of it (D1). |
| cloudflared | 2026.10.1 | Apache-2.0 | image `cloudflare/cloudflared`, [cloudflare/cloudflared](https://github.com/cloudflare/cloudflared) | Tunnel for access from outside without an open router port (D14, D27). The `tunnel` service only starts with `kh/ops/tunnel.sh on`. |
| distroless base image (Debian 13) | as pinned by cloudflared 2026.10.1 | Debian packages under their own licenses | `gcr.io/distroless/base-debian13`, the base of the cloudflared image | Comes with cloudflared. |
| speaches | 0.8.3 (`-cpu` image) | MIT | image `ghcr.io/speaches-ai/speaches`, [speaches-ai/speaches](https://github.com/speaches-ai/speaches) | OpenAI-compatible Whisper server for own audio and video files (P7.3). The `whisper` service only starts with `docker compose --profile whisper up -d whisper`. The image (amd64 and arm64) brings faster-whisper and CTranslate2 (MIT) and an Ubuntu 24.04 base. |
| faster-whisper models `tiny`, `base`, `small` | as published by Systran | MIT | [Systran on Hugging Face](https://huggingface.co/Systran), loaded by the `whisper` service on first use | CTranslate2 conversions of OpenAI's Whisper models (MIT). Downloaded once at runtime, not part of the image. |
| vosk-browser | 0.0.8 | Apache-2.0 | [npm](https://www.npmjs.com/package/vosk-browser), [ccoreilly/vosk-browser](https://github.com/ccoreilly/vosk-browser) | Speech recognition in the browser (WebAssembly build of Vosk) for the voice commands in cook mode (P7.5). Loaded only when the user switches the commands on. Brings uuid 9.0.0 (MIT). |
| Vosk model `vosk-model-small-de-0.15` | 0.15 | Apache-2.0 (file COPYING in the model) | [alphacephei.com/vosk/models](https://alphacephei.com/vosk/models), Alpha Cephei Inc. | Small German speech model for the voice commands (P7.5). Downloaded at image build from the ZIP with a pinned SHA-256, repacked as `.tar.gz` and served by the app itself under `/kh-models/`, so the browser never contacts a third party. About 45 MB in the image; loaded by the device on first use only. Built by the `voice-model` stage of `docker/Dockerfile`. |
| Alpine Linux | 3.22 | see the package list below | image `alpine:3.22` | Small base for the backup service (`kh/ops/backup/Dockerfile`, D20, D21). |
| Bundeslebensmittelschlüssel (BLS) | 4.0 (2025) | CC BY 4.0 | [blsdb.de](https://www.blsdb.de/assets/uploads/BLS_4_0_2025_DE.zip), Max Rubner-Institut | Nutrition values per 100 g in `mealie/kh/nutrition/data/bls.csv` (D44). Citation: Max Rubner-Institut (2025): Bundeslebensmittelschlüssel (BLS), Version 4.0 – Deutsche Nährstoffdatenbank. Karlsruhe. DOI 10.25826/Data20251217-134202-0. Changed: reduced to 9 values, salt computed from sodium × 2.5. Built by `mealie/kh/nutrition/build_bls.py` from the ZIP with a pinned SHA-256. |

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

## Not part of Kochheft

Docker, Docker Compose, Colima, Uptime Kuma, the Cloudflare service and Google Gemini (with a key from Google AI Studio, D35) are installed or used by whoever runs Kochheft, under their own terms. Which data goes to which service is listed in the table „Was geht wohin“ in [README.md](README.md).
