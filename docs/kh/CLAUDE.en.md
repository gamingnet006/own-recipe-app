# CLAUDE.md – Küchenhelfer (Mealie fork) · English version

> English translation of `.claude/CLAUDE.md`. If the two differ, the German file is authoritative.

This repo is a fork of Mealie (AGPL-3.0). Mealie's development guide still applies and is included here:

@../../AGENTS.md

The plan with phases, tasks and decisions lives in `PLAN.md` (English: `PLAN.en.md`) in the repo root. It is not loaded automatically: read the section of the current phase before every task.

## Way of working

- Before each task, briefly state which files you will create or change.
- Work in small steps: implement one step, write and run tests, summarize briefly, name the next step.
- Change nothing outside the task. When unclear, ask instead of guessing.
- Tick off finished items in `PLAN.md` and record new decisions in section 2.
- Never change goals or guardrails on your own.

## Code rules

1. **No dead code.** Build nothing in advance. Delete unused functions, imports and files immediately.
2. **No repetition.** If logic appears a second time, it becomes a function called everywhere (e.g. `parse_ingredient()`, `format_amount()`, `ask_ai()`, `transcribe()`).
3. **Check first whether it already exists:** Mealie function, then library, then own code. Every new dependency needs a reason, a license check and an entry in `THIRD_PARTY_NOTICES.md`.
4. **Stay readable.** One file, one topic. Functions mostly under about 40 lines, descriptive names. Settings only through configuration, no hidden numbers in code.
5. **Comments explain the purpose.** Every new file starts with 1 to 3 lines on what it is for. Every function has a short description (what and why). Non-obvious spots get a short margin comment. No comments that merely restate the code.
6. **Language.** Code, identifiers and comments in English, matching Mealie (D7 in `PLAN.md`); guides in German and English.
7. **Report errors clearly,** never swallow them silently.
8. **Security.** No keys in code or repo. Validate input. When fetching external pages, block private address ranges and limit size and time. Accept AI answers only against a fixed schema. Escape output.
9. **Tests.** Every function with logic gets at least one test. Test data only self-written or freely licensed, never real third-party recipes. AI calls in tests only with recorded answers, never with a real model or key (D23).
10. **Definition of Done.** Runs, tests green, comments in place, no dead code, docs updated, license checked, cost still €0.

## Fork rules

- Our features live in their own subfolders with the prefix `kh`; the paths are documented in `docs/code-rundgang.md` after phase 0.
- Keep changes to existing Mealie code small and mark them with the comment `KH: <reason>`.
- Never edit generated files by hand (e.g. TypeScript types generated from schemas); always use the generator.
- Change the database only through Alembic migrations; take a backup before every migration.
- Upstream: take security fixes individually via `cherry-pick`, new Mealie features only after agreement.
- Never remove Mealie's license and copyright notices.
- GitHub Actions: only our workflows trigger on their own: `kh-ci.yml` on every push (calls Mealie's `test-backend.yml` and `test-frontend.yml`) and `kh-release.yml` on version tags (builds the amd64 image). All other Mealie workflows are disabled in the repo. After every upstream sync, disable new workflows with `gh workflow disable <name>`.

## Phase rules

- Every phase ends with a release that can be installed on its own (tag, images, short guide). Details in `PLAN.md` section 5.
- New features go into `kh/<feature>/`. Change finished code from earlier phases only for bug fixes, each with a test.
- Later phases plug into extension points (lists or hooks) instead of rebuilding earlier code.
- APIs, functions and data formats of earlier phases stay compatible; migrations are additive only.
- Tests of all phases must stay green. Before every release, run an upgrade test from the previous tag.

## Credentials

- Never put credentials, passwords, tokens or keys into the repo, not even in examples or tests. Only placeholders in `.env.example`; `.env` is listed in `.gitignore`.

## Develop on the Mac, run on the Raspberry Pi

- Everything runs in Docker; assume nothing Mac-specific.
- Build images for `linux/arm64` and `linux/amd64` (Raspberry Pi, Apple Silicon, Intel machines). Heavy builds such as the frontend only in CI, never on the Pi.
- Write file names and import paths with exact casing: macOS forgives mistakes, Linux does not.
- Containers that need to reach services on the host (e.g. Ollama) use `host.docker.internal`; on Linux only with `extra_hosts: ["host.docker.internal:host-gateway"]` in Compose.
- Fix the user ID inside the container so file permissions on volumes also work on the Pi.
- Test Pi-like: start containers with limits (about 2 CPUs, 2 GB RAM). At the end of every phase, check on the real Pi (64-bit OS, data on SSD instead of SD card).
- On the Mac, Ollama runs natively (with GPU there, without GPU in a Docker container); on the Pi the profile `leicht` (light) applies.

## Guardrails (short version, details in `PLAN.md`)

- Everything free, no subscriptions.
- No third-party recipes, texts or photos in the repo; ship no video downloader.
- No telemetry; everything that leaves the house is listed in the README table "What goes where".

## Commands

Everything runs in Docker (Colima on the Mac, at least 4 CPUs and 6 GB RAM: `colima start --cpu 4 --memory 6`). All commands from the repo root; run and verified in phases 0 and 1 unless marked otherwise.

```bash
# Build and start Küchenhelfer (Mealie and the backup service from kh/ops), then http://localhost:9091
docker compose -f kh/ops/docker-compose.yml up -d --build
# Pi-like limits for the running container
docker update --cpus 2 --memory 2g --memory-swap 2g kuechenhelfer-mealie-1
# Stop
docker compose -f kh/ops/docker-compose.yml down
# Back up now; list backups or restore one (--no-deps: do not restart Mealie)
docker compose -f kh/ops/docker-compose.yml run --rm --no-deps backup backup.sh
docker compose -f kh/ops/docker-compose.yml run --rm --no-deps backup restore.sh [file.zip]
# Update to another image: backup, database snapshot, checks, roll back on failure
kh/ops/update.sh <image>
# Publish a release (Mac only): build arm64, set the tag, CI builds amd64, push arm64
kh/ops/release.sh <version>
# Tests of the ops scripts (also run in CI)
sh kh/ops/backup/test_backup.sh && sh kh/ops/test_update.sh && sh kh/ops/test_release.sh

# Backend tests (same as `task py:test`); LDAP, Postgres and long-running tests are skipped
docker run --rm -v "$PWD":/app -w /app -e UV_PROJECT_ENVIRONMENT=/venv -e UV_LINK_MODE=copy \
  ghcr.io/astral-sh/uv:python3.14-bookworm-slim sh -c "apt-get update -qq && \
  apt-get install -qq -y --no-install-recommends build-essential libsasl2-dev libldap2-dev libssl-dev >/dev/null && \
  uv sync --frozen --quiet && uv run --frozen pytest -n 4 --dist loadfile -p no:cacheprovider"

# Frontend tests (like Mealie's CI: install, `nuxt prepare`, `test:ci`); the tests also read mealie/repos/seed
docker run --rm -v "$PWD":/src:ro node:24 sh -c "mkdir -p /work/mealie/repos && cp -r /src/frontend /work/frontend && \
  cp -r /src/mealie/repos/seed /work/mealie/repos/ && cd /work/frontend && rm -rf node_modules .nuxt && \
  npm install -g pnpm@11 && CI=true pnpm install --frozen-lockfile && pnpm nuxt prepare && pnpm test:ci"
```

According to Mealie's `AGENTS.md`, not yet tried in our Docker setup: lint `task py:lint` and `task ui:lint`, generate types `task dev:generate`, create a migration `task py:migrate -- "description"`.
