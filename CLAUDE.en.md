# CLAUDE.md – Küchenhelfer (Mealie fork) · English version

> English translation of `CLAUDE.md`. If the two differ, `CLAUDE.md` (German) is authoritative.

This repo is a fork of Mealie (AGPL-3.0). Mealie's development guide still applies and is included here:

@AGENTS.md

The plan with phases, tasks and decisions lives in `PLAN.md` (English: `PLAN.en.md`). It is not loaded automatically: read the section of the current phase before every task.

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
9. **Tests.** Every function with logic gets at least one test. Test data only self-written or freely licensed, never real third-party recipes.
10. **Definition of Done.** Runs, tests green, comments in place, no dead code, docs updated, license checked, cost still €0.

## Fork rules

- Our features live in their own subfolders with the prefix `kh`; the paths are documented in `docs/code-rundgang.md` after phase 0.
- Keep changes to existing Mealie code small and mark them with the comment `KH: <reason>`.
- Never edit generated files by hand (e.g. TypeScript types generated from schemas); always use the generator.
- Change the database only through Alembic migrations; take a backup before every migration.
- Upstream: take security fixes individually via `cherry-pick`, new Mealie features only after agreement.
- Never remove Mealie's license and copyright notices.

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

<!-- In phase 0, take these from Mealie's Taskfile and AGENTS.md: set up, start, tests, lint, generate types, create migration, build Docker image. Do not invent commands. -->
