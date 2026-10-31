# Küchenhelfer – Plan (fusion version) · English version

> English translation of `PLAN.md`. If the two differ, `PLAN.md` (German) is authoritative.

As of: 29 Oct 2026 · Working name "Küchenhelfer" ("kitchen helper"; check the name before publishing, T7)
Mockup: https://claude.ai/artifact/3STTwHpXE6DXtPGUoKQoPr

A free, self-hosted recipe system based on a Mealie fork: checked import (link, text, photo, video), duplicate warning, quantities in the step text that scale along, nutrition values, allergens, cooking mode with timers and voice commands, a PDF family cookbook and automatic backups. Everything lives in one repo and can be published so others can use it the same way.

> **For Claude Code:** This file is the working basis. Work through the phases in order, tick off finished items (`- [x]`), record new decisions in section 2 and never silently change goals or guardrails.

---

## 1. Guardrails

1. **Free:** no subscriptions, no paid components (section 10).
2. **Legally clean:** section 9.
3. **One repo with everything:** code, Docker setup, docs and tests, reproducibly installable.
4. **Fusion:** Mealie's code is the base. We keep what fits, remove what we don't need, and rebuild what we want different, without compromise.
5. **Don't build anything twice:** first check whether Mealie or a library can already do it.
6. **Check before saving:** no AI result lands in the collection unchecked.
7. **Weak hardware and fully local** must work (profiles, section 8).
8. **Code rules** in `.claude/CLAUDE.md` apply to everything.
9. **Every phase installable on its own:** the end of each phase is a release that can be installed and run without later phases (D15).
10. **Later never changes earlier:** new phases add instead of rebuilding finished code; the tests of all earlier phases stay green (D15).

**Non-goals:** public recipe database · paid tiers · app store apps (the web app is enough) · bundled video downloader · desktop app (postponed).

---

## 2. Decisions

| No. | Decision | Status |
|---|---|---|
| D1 | Base is Mealie, as a fork pinned to a fixed version | decided |
| D2 | The whole project is AGPL-3.0; Mealie's license and copyright notices stay | decided |
| D3 | replaced by D11 | – |
| D4 | Own review view, directly inside the app | decided |
| D5 | Instagram/TikTok: description and screenshot are the default; video download only as an optional plug-in, off by default, not shipped in the repo | proposal, please confirm |
| D6 | AI: local first (Ollama, Whisper), free cloud only as a fallback and only with the user's own key. From phase 2 via Mealie's AI provider management (Ollama on the Mac or own key, D25); profiles follow in phase 7 | decided |
| D7 | Code, identifiers and comments in English (matches Mealie); guides in German and English | decided |
| D8 | Tech = Mealie's stack: FastAPI, SQLAlchemy, Alembic, Nuxt 4, Vue 3, TypeScript | decided |
| D9 | Project name | open (T7) |
| D10 | Desktop app and iOS app in the store | postponed |
| D11 | Fusion instead of add-on containers, with a code walkthrough in phase 0 as checkpoint | decided |
| D12 | Develop on the MacBook, run on a Raspberry Pi or server: everything in Docker, images for arm64 and amd64 | decided |
| D13 | Order: the family uses the fork from phase 1; dependent features come one after another; what only outsiders need (name, first-run wizard, profiles) comes last. No feature is dropped | decided |
| D14 | Reachability from outside the home (HTTPS, tunnel) is a task in phase 1 | decided |
| D15 | Every phase ends with a release that installs on its own (tag, images, short guide); new phases are additive and don't change finished code of earlier phases (rules in section 5). For this, amd64/arm64 images and `update.sh` already come in phase 1 | decided |
| D16 | Code, docs and plan live in the private repo `gamingnet006/own-recipe-app` (own repo, Mealie via `upstream`, no GitHub fork); never credentials, passwords or keys in the repo, only placeholders in `.env.example` | decided |
| D17 | Our rules live in `.claude/CLAUDE.md`, our README in `docs/kh/` until phase 8; Mealie's `CLAUDE.md`, `README.md` and `.gitignore` stay unchanged (eng review) | decided |
| D18 | Drafts in their own `kh` table; only approval creates a Mealie recipe (eng review) | decided |
| D19 | Quantities in step text: text unchanged, links in a `kh` side table based on `ingredient_references` (eng review) | decided |
| D20 | Build arm64 images on the Mac and push to GHCR while the repo is private; amd64 in CI (eng review). Implementation: the app image is published as `<version>-arm64` (Pi, Apple Silicon) and `<version>-amd64` (PC); one shared tag follows once CI builds both architectures itself (phase 8). Each device builds the small backup image itself from the release checkout (seconds, not a heavy build) | decided |
| D21 | Backups via Mealie's backup API; on failure `update.sh` restores image and database from the pre-update backup (eng review). Implementation: the database comes from a file snapshot taken right before the switch while Mealie is stopped; this also works when the new version has already migrated the database. The Mealie backup at the second location stays as an extra safety net | decided |
| D22 | Access from outside: self sign-up off, tunnel provider listed in "What goes where" (eng review) | decided |
| D23 | Automatic upgrade test in CI; AI calls in tests only with recorded answers (eng review). Implementation: `kh-release.yml` tests the upgrade from the previous release before the amd64 image is pushed; if the test fails, nothing is published | decided |
| D24 | Our migrations as an Alembic branch `kh` (`mealie/kh/alembic/versions/`); Mealie starts with `"heads"` instead of `"head"` (`init_db.py:119`) so Mealie updates need no merge migrations (code walkthrough) | decided |
| D25 | AI connection from phase 2 via Mealie's existing AI provider management (admin, per group) instead of `.env`; D6 stays the same in substance (code walkthrough) | decided |
| D26 | Frontend extensions as a Nuxt layer `frontend/kh/` with one `extends` line in `nuxt.config.ts` (code walkthrough) | decided |
| D27 | Access from outside through a Cloudflare Tunnel at `kochbuch.example.org` (domain at Cloudflare, paid until 3 Jul 2027). Deliberately without Cloudflare Access to keep it simple for the family; a login stays valid for 30 days (`TOKEN_TIME=720`). `tunnel.sh` starts the tunnel only if self sign-up is off, no account still uses the default e-mail and every group and household is private (the last one since 2026-10-31). Access can be added at any time | decided |
| D28 | Runs wherever Docker runs: Raspberry Pi, old and new Macs, Linux, Windows (Docker Desktop with WSL2, not tested yet). Whoever installs it chooses where; images exist for arm64 and amd64, the ops scripts are POSIX sh. Until the radio alarm clock's Pi is ready, Küchenhelfer runs on the Mac mini (Intel, macOS 12, Colima, `KH_MEMORY_LIMIT=768m`); development stays on the MacBook. Moving to the Pi after development via backup and restore; the tunnel only ever runs on one machine | decided |
| D29 | Automatic updates: every install fetches the newest stable version (tags `vX.Y` or `vX.Y.Z` without `-rc`) for its CPU type at 4 am and installs it through `update.sh` (backup, snapshot, checks, rollback). On by default, switch `KH_AUTO_UPDATE` in `.env` (`kh/ops/auto_update.sh on|off|status|check|run`); the checkbox in the app comes in phase 8. The ops files ship inside the image (`/app/kh-bundle`), no git on the server. If `update.sh` stops before changing anything, the next night tries the same version again; only a version that failed after the switch is skipped. Design: `docs/kh/specs/2026-10-30-auto-update-design.md` | decided |
| D30 | `v0.0` may be released before the Pi is ready. The install on a fresh Pi from phase 1's "done when" follows later; bugs it finds ship as `v0.0.1` (2026-10-31) | decided |
| D31 | No sample recipes as starting data; the family starts with an empty recipe list. Family accounts come from an invite link: each person creates their own account without admin rights and sets their own password (2026-10-31) | decided |
| D32 | The install asks where backups should go. The second location for the Mac mini is decided afterwards; until then its backups sit on the same disk as the database (2026-10-31). Chosen: a USB stick; set up as soon as it is plugged in (2026-10-31). Built as `kh/ops/backup_copy.sh`: a copy to the stick every night at 3:45 am (D33). Set up on the Mac mini: Full Disk Access for `/bin/dash`, the stick as exFAT `KH-Backup`, `backup_copy.sh on` without a password; the first copy (3 backups) matches the originals (2026-10-31) | decided |
| D33 | Copies that leave the machine get a password if wanted (age); `backup_copy.sh on` asks once, j/n. What matters for the choice: a Mealie backup holds the backup service's API key in plain text, so an open stick opens the app. With a password the private key lies locked on the stick, the password nowhere, and Mealie's `.secret` may go along; after a restore everyone stays logged in. The Mac mini goes without a password: it is too much hassle, and the data is not sensitive. The guide says what to do if the stick gets lost. Shipped as `v0.0.1` (always with a password) and `v0.0.2` (the j/n question); fixes from the Pi test (D30) come as the next patch version (2026-10-31) | decided |
| D34 | No local AI of our own for now: no Ollama or Whisper running all the time, neither on the MacBook (it should not have to stay on) nor on the Mac mini (too weak). The AI comes through Mealie's AI provider settings (D25) with an own key at a provider with a free tier; which one is settled at the start of phase 2. This turns the order from D6 (local first) around for now (2026-10-31) | decided |

---

## 3. Architecture

One application (our Mealie fork) plus a backup container; AI and Whisper are interchangeable extra services.

```text
Phone · iPad · Browser  (web app, installable as an app)
        │
Küchenhelfer = Mealie fork  (backend FastAPI · frontend Nuxt)
  ├─ Intake · review view · duplicates · plausibility
  ├─ Quantities: parser · serving calculator · nutrition · allergens · substitutions
  ├─ Cooking mode: timers · voice commands · offline
  ├─ Sharing and output: shortcut · Telegram · PDF
  ├─ Operations: first run · system check · profiles
  └─ Database (SQLite; Postgres optional) + images
        │
        ├─ AI service       OpenAI-compatible: Ollama local or free cloud
        └─ Whisper service  OpenAI-compatible, local
Backup container → second storage location → push message to Uptime Kuma
```

**Fork rules**

1. Our features live in their own subfolders with the prefix `kh`; the exact paths are set by the code walkthrough in phase 0.
2. Changes to Mealie's existing code stay small; each carries the comment `KH: <reason>` so it can be found during upstream syncs.
3. Upstream: the remote `upstream` points to Mealie. Always take security fixes individually (`cherry-pick`), new features only when needed, sync every three months.
4. Remove in two stages: first hide UI and routes, drop database tables later via migration.
5. New name and logo; "based on Mealie", license and copyright stay; source code link in the UI (AGPL).

---

## 4. Features and order

Principle (D13): the family uses it as early as possible; what builds on something comes after it; what only outsiders need comes last. No feature is dropped, it only comes later.

| Feature | Priority | Source | Phase |
|---|---|---|---|
| Daily backups with restore test and notification | Must | new (container) | 1 |
| Reachability from outside (HTTPS, tunnel) | Must | new (operations) | 1 |
| Images for amd64/arm64 per release, `update.sh` | Must | new | 1 |
| Sample recipes (self-written, freely licensed) | Could | new | 1 |
| Intake: link, text, photo | Must | rework: Mealie's import and AI import produce a draft | 2 |
| Review view with the original alongside | Must | new | 2 |
| Duplicate warning | Must | new | 2 |
| Provenance badge (source, author, checked) | Should | new | 2 |
| German ingredient parser | Must | rework (Mealie's parser) | 3 |
| Serving calculator with quantities in the text, three ways | Must | rework (Mealie's scaling) | 3 |
| Plausibility warnings | Should | new | 3 |
| Cooking mode with clickable timers, also with a locked phone | Should | rework (Mealie's cooking mode) | 4 |
| Voice commands (next, back, timer) | Should | new (Vosk in the browser) | 4 |
| Screen stays on, offline recipes | Should | Mealie has "screen on", offline new | 4 |
| PDF recipe card and PDF family cookbook | Should | new | 5 |
| Sharing via shortcut | Should | new | 5 |
| Migration from other apps | Should | Mealie (migrations exist) + guide | 5 |
| Convection converter, menu schedule | Could | new | 5 |
| Nutrition (BLS, "approx.") | Must | new | 6 |
| Allergen tags and family profile | Should | new | 6 |
| Own substitution rules | Should | new | 6 |
| Intake: video (Whisper) | Must | rework (existing AI import) | 7 |
| Telegram bot | Should | new | 7 |
| Profiles: light, normal, strong, local; hardware test | Must | new (configuration) | 7 |
| Name, logo | Must | new | 8 |
| First-run wizard, system check | Should | new | 8 |
| Meal plan, shopping list | Later | Mealie (exists) | – |
| Note field "Next time" | Later | Mealie notes | – |

---

## 5. Phases

A phase is only done when its "Done when" is met. The family uses the fork from phase 1 (v0.0); the first version with the review view (v0.1) is the end of phase 2. After v1.0 a feature freeze applies so maintenance stays manageable.

**Phase rules (D15)**

1. **One release per phase.** Every phase ends with a Git tag (`v0.0`, `v0.1`, …), finished images in the GitHub Container Registry, a `CHANGELOG.md` entry and a short guide. Whoever installs tag `v0.0` gets exactly the features of phase 1, fully working.
2. **Phases build on each other.** A release contains its phase and all earlier ones (`v0.2` = phases 1 to 3). Individual later features that are heavy or send data outside (video, Telegram, Open Food Facts) can additionally be switched off in `.env`.
3. **Additive instead of rebuilding.** New features go into their own folder `kh/<feature>/` (backend and frontend). Finished code from earlier phases is only changed for bug fixes, each with a test.
4. **Plan extension points.** Where later phases will clearly hook in (hints in the review view, intake paths, display of quantities), the earlier phase builds a simple list or hook that later phases register into. Only where this plan already foresees it, nothing in advance.
5. **Stable interfaces.** API routes, functions and data formats of earlier phases stay compatible. Database migrations are additive only (new tables or columns); renaming or deleting our own columns only with a migration path and backup.
6. **Old tests stay green.** CI runs the tests of all phases. A failing test from an earlier phase blocks the merge.
7. **Upgrade test.** Before every release: install the previous tag, create data, update to the new tag, check the data.

### Phase 0 · Fork and code walkthrough

- [x] Bring Mealie's code into our own repo `gamingnet006/own-recipe-app`: set the remote `upstream` to Mealie and merge the latest stable version (no GitHub fork, so the repo can stay private).
- [x] Take over Mealie's `CLAUDE.md`, `README.md` and `.gitignore` unchanged (done: v3.29.0 merged, `# KH` block appended; confirmed 30 Oct 2026: Claude Code loads Mealie's `CLAUDE.md` and our `.claude/CLAUDE.md` together); append our `.gitignore` lines as a marked `# KH` block; check that Claude Code additionally loads `.claude/CLAUDE.md` (D17).
- [x] Build and start the fork locally on the Mac in Docker, run Mealie's tests (29 Oct 2026: image built, healthy with 2 CPUs/2 GB after ~33 s, ~222 MB RAM; backend pytest exit 0, frontend 602/602 tests green); enter the real commands in `.claude/CLAUDE.md` under "Commands".
- [x] Simple CI on GitHub: lint and tests on every push (`kh-ci.yml` calls Mealie's test workflows; first run 29 Oct 2026 green: frontend, backend SQLite and Postgres; other Mealie workflows disabled in the repo).
- [x] Code walkthrough: document the structure (backend, frontend, data model for recipe, ingredient and step, import, parser, scaling, cooking mode, backups) in `docs/code-rundgang.md`.
- [x] List "keep · rework · remove · new" and the paths for our `kh` folders in `docs/code-rundgang.md`.
- [ ] Early tests T6 and T8 (section 12); the others before their phase.
- **Done when:** the fork runs locally, tests are green, CI runs, and walkthrough and list exist.

### Phase 1 · Running for the family (v0.0)

- [x] CI builds the amd64 image per tag and publishes it to the GitHub Container Registry; the arm64 image is built natively on the Mac and pushed there with one command per release while the repo is private (D20). (30 Oct 2026: `.github/workflows/kh-release.yml` and `kh/ops/release.sh` created, tests green. Release candidate `v0.0-rc.1` published: `-amd64` from CI, `-arm64` from the Mac, run took 8:48 minutes. On the Mac pulled from GHCR with `update.sh`, started and switched back, data checked. 31 Oct 2026: release `v0.0` published. Before the upload, CI passed the upgrade test from `rc.2-amd64`, and on the MacBook the arm64 image passed `upgrade_test.sh` from `rc.2-arm64` (2 recipes, image unchanged). Open: test on the Pi.)
- [ ] `docker-compose.yml` and `.env.example` (placeholders only, no real credentials); start on the Pi. (29 Oct 2026: `kh/ops/docker-compose.yml` and `kh/ops/.env.example` created, healthy on the Mac with 2 CPUs/2 GB after ~36 s, ~299 MB RAM; open: start on the Pi.)
- [x] `update.sh`: backup first, then new version, health check; on failure restore the old image and the database (D21). (30 Oct 2026: `kh/ops/update.sh <image>` makes a Mealie backup, a file snapshot of the stopped database, switches, checks health, running image and recipe count; on failure the old image and the snapshot come back. Mealie's restore alone is not enough because it needs a running app with the same database version. Tests in CI; verified on the Mac: "already running", update there and back, a broken version that deletes all recipes and crashes, and rollback when the old image name now points elsewhere.)
- [x] Automatic upgrade test in CI: start the previous release with test recipes, update, check recipes and images; a failure blocks the release (D23). (30 Oct 2026: `kh/ops/upgrade_test.sh` with self-written test data in `kh/ops/testdata/`, built into `kh-release.yml`. Verified locally: upgrade `v0.0-rc.1` → current state passed, a broken version failed as it should. Passed in CI for release candidate `v0.0-rc.2`: `rc.1-amd64` → `rc.2-amd64`, 2 recipes and the image unchanged, published only afterwards.)
- [ ] Automatic updates for stable releases only, on by default, can be switched off (D29). (30 Oct 2026: `kh/ops/auto_update.sh on|off|status|check|run` with cron at 4 am, on macOS as a LaunchAgent because macOS blocks `crontab` over SSH; release images carry the ops files in `/app/kh-bundle`, `check_bundle.sh` checks every image before the upload; `update.sh` refreshes the backup service and the tunnel after the switch. Tests in CI; checked for real on the MacBook: tag list from GHCR, pull with a throwaway login, unpacking from a probe image, upgrade test including the backup service. 31 Oct 2026: switched on on the Mac mini (LaunchAgent, read-only key in `.env`), test run through launchd succeeded. After the `v0.0` release, `auto_update.sh check` there reports that it would update to `v0.0-amd64`. Open: the first real run in the night to 1 Nov.)
- [x] Short "Install" guide in the README for this release. Also covering: logging in to ghcr.io while the images are private, and `kh/ops/auto_update.sh on` with the read-only key (`KH_REGISTRY_USER`, `KH_REGISTRY_TOKEN`) for automatic updates (D29). Also: create the `data` and `backups` folders before the first start (Colima on macOS 12 cannot create them itself), and background jobs on macOS need `/usr/local/bin` in PATH. (2026-10-31: in `docs/kh/README.md` in German and English; `kh/ops/install.sh` asks for the backup location (D32) and the address, writes `.env`, starts and creates the backup key. Followed step by step on the MacBook into an empty folder: ops files from the image, `install.sh`, a backup works. The test found a bug, fixed: `up --build backup` also rebuilt the Mealie image. The Pi test follows (D30).)
- [x] Hide unneeded Mealie parts in UI and routes (stage 1 of the fork rules). (2026-10-31: share links off by default (`KH_SHARE_LINKS`), announcements off for new groups, explore pages closed as long as group and household are private; `tunnel.sh on` only goes online with private groups and households. Our own code in `mealie/kh/` and the Nuxt layer `frontend/kh/` (D26). Checked in the browser on the MacBook: recipe menu without "Share", back with `KH_SHARE_LINKS=true`, download works. Found while checking: the family's group and household were public, so new recipes would have been readable without login. Set to private through Mealie's settings, announcements off; checked from outside: 404.)
- [ ] Backup container using Mealie's backup API (create, copy to the second location; `restore.sh` uses Mealie's restore): daily, retention, push message to Uptime Kuma, restore test script. Admin access only as a placeholder in `.env.example` (D21). (29 Oct 2026: `kh/ops/backup/` with `backup.sh`, `restore.sh`, cron schedule, retention, Uptime Kuma push; tests in CI; backup and restore of a test recipe verified on the Mac. 2026-10-31: a Mac mini backup restored on the MacBook, recipes, accounts and group match; Uptime Kuma push URLs may be pasted with the example query. `kh/ops/restore_test.sh` restores a backup with `restore.sh` into a throwaway install and compares recipes and files; passed on the MacBook and the Mac mini. 2026-10-31: copy to a USB stick with `kh/ops/backup_copy.sh`, encrypted with a password if wanted (D32, D33); tests in CI, including encrypting and decrypting with real age in the backup image. Set up on the Mac mini, first copy checked. Open: push to a real Uptime Kuma, a schedule for the restore test.)
- [x] HTTPS and tunnel for access from outside (free, no open ports; D14). Self sign-up stays off (`ALLOW_SIGNUP=false`, Mealie default); the tunnel provider is listed in "What goes where" (D22). (30 Oct 2026: Cloudflare Tunnel as service `tunnel` in `kh/ops/docker-compose.yml`, `kh/ops/tunnel.sh on|off|status` with safety checks, tests in CI. Verified on the Mac: the guard blocks while the default account exists, an invalid token is rejected, "stop" in the desktop script stops the tunnel too. Tunnel created in Cloudflare, admin e-mail and password changed; since 30 Oct Küchenhelfer and the tunnel run on the Mac mini (D28), test backup there ok. Route created in Cloudflare: `https://kochbuch.example.org` answers through the tunnel (HTTP 200, valid certificate). Reachable from a phone over mobile data (30 Oct 2026). The move to the Pi comes with the Pi task, D27.)
- [ ] Create family accounts, sample recipes as seed data. (2026-10-31: no sample recipes, accounts through invite links (D31); guide in `docs/kh/familienkonten.en.md`. Checked on the MacBook copy: signing up with a link works although `ALLOW_SIGNUP=false`, each link works once, invited accounts get no admin or management rights. Open: create the family's accounts.)
- [x] `THIRD_PARTY_NOTICES.md` and `CHANGELOG.md`. (30 Oct 2026: `docs/kh/CHANGELOG.md` created, kept out of the root because of D17; `release.sh` requires a section per version. 31 Oct 2026: `docs/kh/THIRD_PARTY_NOTICES.md` with licenses checked at the source: GitHub and the package data in the images.)
- **Done when:** the family adds recipes from outside the home, a backup has been restored on a second device, and release `v0.0` installs on a fresh Pi using only the short guide.

### Phase 2 · Intake, review, duplicates (v0.1)

- [ ] Drafts in their own `kh` table including the original; only approval creates a normal recipe through Mealie's existing path and links the original. Mealie itself never has to filter drafts (D18, answers T6).
- [ ] AI connection via Mealie's AI provider management (Ollama on the Mac or own key, D6, D25).
- [ ] Extension points for later phases: list of checks and hints in the review view, list of intake paths (phase rule 4).
- [ ] Intake: link (existing scraper), text, photo or screenshot; result always a draft.
- [ ] Store the original: photo, description, source, author, date, AI model.
- [ ] Review view as in the mockup (screen 2): original and result, hints on top, save, discard, edit.
- [ ] Duplicate check: normalized link, title and ingredient similarity; only warn, never delete automatically.
- [ ] Provenance badge in the recipe view.
- [ ] Security when fetching: block private address ranges, limit size and time, accept AI answers only against a fixed schema, escape output.
- **Done when:** a photo of a handwritten recipe lands as a draft in the review view, the test cases (without video) produce reviewable drafts, nothing is saved without approval and the duplicate test cases trigger. Then release v0.1.

### Phase 3 · Quantities (v0.2)

- [ ] `parse_ingredient()` for German quantities (½, 1 1/2, ranges, EL, TL, pinch, bunch, packet, piece) with tests; replaces or extends Mealie's parser.
- [ ] Quantities in the step text: the text stays unchanged; a `kh` side table stores position, ingredient and optional fraction, building on Mealie's `ingredient_references`. `link_quantities()` on import; link and unlink in the review view; after a text edit the positions are re-checked (D19).
- [ ] Serving calculator with three ways (servings, "I only have …", baking tin) and one single display function `format_amount()` for all views.
- [ ] Times stay fixed; hint when the factor is above 2 or below 0.5.
- [ ] Plausibility warnings in the review view: quantities, times, temperatures, ingredient without a step, converted units (uses the parser).
- **Done when:** the quantity test cases (section 7) pass and the plausibility test cases trigger.

### Phase 4 · Cooking mode (v0.3)

- [ ] Detect times in the step text and make them clickable (also "20–30 min" and "half an hour").
- [ ] Timer with a locked phone based on T1: shortcut with a real clock timer, server timer with push, keep the screen on.
- [ ] Voice commands with Vosk in the browser (after T2); large buttons and swiping as fallback.
- [ ] Offline recipes (web app; needs HTTPS, available since phase 1).
- **Done when:** on the iPhone a timer rings with the phone locked, and "next" works in the kitchen or the buttons take over.

### Phase 5 · Family cookbook and sharing (v0.4)

- [ ] PDF: recipe card and family cookbook (selection, table of contents, free fonts, own photos only).
- [ ] Shortcut for the share sheet with a revocable token per device.
- [ ] Migration: guide for Mealie's migrations, followed by a duplicate scan.
- [ ] Convection converter and menu schedule.
- **Done when:** a link shared via the share sheet lands as a draft in the review view and a cookbook with 10 recipes is printable as PDF.

### Phase 6 · Nutrition and allergens (v0.5)

- [ ] Nutrition: BLS locally (after T5), Open Food Facts optional; confirm and remember the mapping; standard weights; display "approx.".
- [ ] Allergen tags: fixed rules for the 14 main EU allergens, AI only as a suggestion, family profile as a warning, note "no guarantee".
- [ ] Substitution rules: default list plus own rules; then re-run the allergen check; save as a variant, never overwrite the original.
- **Done when:** every allergen tag and nutrition value can be traced back to an ingredient and the allergen test cases (section 7) pass.

### Phase 7 · Video, bots and heavy AI (v0.6)

- [ ] Whisper service (OpenAI-compatible, local) after T3.
- [ ] Video intake: existing AI import with transcript, result as a draft; path after T4 (description and screenshot as default, download only as an optional plug-in, D5).
- [ ] Telegram bot (polls messages itself, only allowed IDs).
- [ ] Profiles `leicht` (light), `normal`, `stark` (strong), `lokal` (local) and hardware test (measure 1 minute of audio, suggest a profile).
- **Done when:** a reel link via the share sheet or Telegram lands as a draft in the review view and the `leicht` profile runs on the Pi.

### Phase 8 · Operations and publication (v1.0)

- [ ] New name and logo (after T7); Mealie notice, license and source code link in the UI.
- [ ] First-run wizard (hardware test, profile, AI connection, backup test) and system check.
- [ ] Checkbox "automatic updates" in the admin settings; switches `KH_AUTO_UPDATE` (D29).
- [ ] Remove unneeded Mealie tables via migration (stage 2 of the fork rules).
- [ ] README with "What goes where" (section 8), installation guide in German and English, maintenance checklist.
- [ ] Legal checklist (section 9), license scan, name checked.
- [ ] One image tag for both amd64 and arm64, once CI builds both architectures itself (public repo, D20).
- [ ] Release `v1.0`, issue templates.
- **Done when:** a stranger installs it on a fresh Raspberry Pi using only the README.

**Later:** meal plan and shopping list (exist in Mealie, only clean up) · note field "Next time" · desktop app.

---

## 6. Quantities: servings in the text and nutrition

All quantities scale live, in the ingredient list and in the step text; times, temperatures and tin sizes stay fixed.

**Basic idea.** Ingredients are structured (quantity, unit, ingredient, note). Quantities in the step text are linked to an ingredient, optionally with a fraction ("half of it"). The text itself stays unchanged; the link (position, ingredient, fraction) lives in a `kh` side table (D19). No freely programmable template system; that is simpler and safer.

**On import.** The AI delivers ingredients structured and steps with marked quantities. `link_quantities()` suggests a link where the text contains an ingredient quantity without a link ("250 g flour"). In the review view, linked quantities are colored; tapping links or unlinks. Numbers without a link stay fixed.

| Way | Input | Factor |
|---|---|---|
| Servings | new number of servings | new ÷ base |
| "I only have …" | quantity of one ingredient, e.g. 300 g flour | 300 ÷ 250 |
| Baking tin | old and new diameter, for rectangles length × width | new area ÷ old area (26 → 20 cm gives about 0.59) |

**Display in one function `format_amount()`** (web, cooking mode, PDF, shopping list):

- Fractions instead of decimals: ¼, ⅓, ½, ⅔, ¾.
- Countable items (eggs, onions) to half pieces; at 1½ eggs the hint "whisk one egg and use half".
- Switch units: 1000 g → 1 kg, 1000 ml → 1 l, 3 tsp → 1 tbsp.
- Round grams from 100 g to 5 or 10.
- Ranges ("2–3 tbsp") scale at both ends.
- Pinch, "some", "to taste" and all ingredients with scaling type "fixed" stay fixed.

**Stored** is only the base (servings or yield such as "baking tin Ø 26 cm"). The chosen factor is view-only and also applies to PDF and shopping list. Nutrition per serving stays the same, the total changes.

**Nutrition, simply explained**

1. Every ingredient line is mapped to an entry in the nutrition database ("flour" → "wheat flour type 405").
2. The quantity is converted to grams ("2 tbsp oil" about 28 g, "1 egg" about 55 g, "500 ml milk" about 515 g).
3. The database gives values per 100 g; these are calculated per ingredient.
4. Everything is summed, divided by servings and shown as "approx." per serving.

Steps 1 and 2 need confirmation: the mapping is confirmed once in the review view and remembered, plus a table of standard weights. Start simple: first only ingredients in grams or milliliters, the rest follows.

---

## 7. Quality and tests

- **Test set** (own test folder, path after the code walkthrough): 20 self-written cases with input and expected result. A mix of web page (local HTML file with JSON-LD), text, self-made photo or screenshot, transcript, duplicate pairs (same link with extra parameters, same recipe written differently), error cases (nonsense quantities) and allergen cases with hidden ingredients (e.g. Worcestershire sauce contains fish).
- **Quantity test cases:** ½, 1 1/2, ranges, countable items, spoons, unit switches, placeholders in text, factor 0.5 / 2 / 3, baking tin 26 → 20 cm, "I only have 300 g flour".
- **AI in tests:** tests use recorded AI answers (self-generated, freely licensed) and check schema, review view and error cases; no AI key in CI. Real model quality is measured separately (D23).
- **Real reels and web pages** only tested privately, never in the public repo.
- **CI on every push:** Mealie's lint and tests plus our tests; image build for amd64 and arm64.
- **Before every upstream sync and update:** test set, backup, short restore check.
- **AI quality (private):** share of correctly recognized ingredients and quantities before review, noted per model.
- **Pi check:** at the end of every phase, install on the real Raspberry Pi and click through.

---

## 8. README template: what goes where, profiles

In the profile "lokal" (local) nothing leaves the house; all other paths can be switched off individually.

| Feature | What is sent | To whom | Profile "local" |
|---|---|---|---|
| Import link | page address | the respective website | same |
| Read text or photo | text or image | local AI (default) or cloud AI, only with a configured key | local AI only |
| Convert video or audio | audio | local Whisper (default) | local only |
| Access from outside | all traffic to the web app; Cloudflare can read it because HTTPS ends there | Cloudflare (tunnel `kochbuch.example.org`, D27) | tunnel off: home network only or own VPN |
| Automatic updates | Requests for the version list and the new images, with the read-only key while the repo is private; when the backup service is rebuilt, the Alpine base image and packages | GitHub (ghcr.io), Docker Hub, Alpine package mirrors (D29) | off (`KH_AUTO_UPDATE=false`) |
| Share via Telegram | link or screenshot | Telegram servers | off |
| Share via shortcut | link | your Küchenhelfer | same |
| Voice commands | microphone audio | nowhere, Vosk runs in the browser | same |
| Nutrition | ingredient names | BLS locally; Open Food Facts online (optional) | BLS local only |
| Backups | data | your second storage location, external only encrypted | same |
| Notifications | short text | ntfy, SMTP or Resend, by choice | ntfy or SMTP in your own network |
| Timer push | timer text | Apple's push service via the web app | shortcut instead of push |

| Profile | Meant for | What runs | What doesn't |
|---|---|---|---|
| leicht (light) | Raspberry Pi, old mini PC | text and screenshot import, review view, cooking mode; videos queued at night or on a stronger machine | large local AI |
| normal | current mini PC, Mac | additionally small Whisper and small local AI | large models |
| stark (strong) | Apple Silicon, mini PC with lots of RAM | large Whisper and local AI | – |
| lokal (local) | any, combinable | everything on own hardware, no Telegram, no cloud keys | cloud features |

The hardware test on first start measures how long 1 minute of audio takes and suggests a profile.

---

## 9. Legal guardrails

Not legal advice; have it reviewed by a lawyer once before publishing.

1. **Private instances only.** Don't host, publicly share or put third-party recipes, texts or photos in the repo; always store source and author; share links only deliberately, off by default.
2. **No downloader in the repo.** yt-dlp only as an optional plug-in, installed by the user, off by default, with a warning. Background: Instagram [prohibits automated collection without permission](https://help.instagram.com/581066165581870) and [restricts accounts for scraping](https://help.instagram.com/740480200552298); Apple's [App Store guideline 5.2.3](https://developer.apple.com/app-store/review/guidelines/) forbids apps that download media from third-party sources.
3. **Default path without download:** paste the description text or upload a screenshot.
4. **Licenses.** The whole project is AGPL-3.0; Mealie's notices stay, the source code link is in the UI. `THIRD_PARTY_NOTICES.md` for every dependency; avoid server components with a "source-available" license. [Open Food Facts](https://support.openfoodfacts.org/help/en-gb/12-api-data-reuse/94-are-there-conditions-to-use-the-api) requires attribution and share-alike; read the [BLS terms](https://heise.de/-11123877) before integrating.
5. **Keys.** Only users' own keys, never keys from the internet; no keys in the repo; enable secret scanning.
6. **Privacy.** No telemetry; no central server, everyone hosts themselves; the table in section 8 lists everything that leaves the house.
7. **Names and logos.** No TikTok, Instagram or Mealie in name or logo; check the project name for conflicts; fonts only with a free license.
8. **Health.** Allergen tags and nutrition values are hints without guarantee, never "guaranteed free of".
9. **Tests and docs** only with self-written or freely licensed recipes.
10. **AI-written code.** Check dependencies with a license scan, take over no large third-party blocks, name the source in a comment.

---

## 10. Cost check

As of 28 Oct 2026; prices and limits change, re-check before publishing.

| Component | Cost | Catch |
|---|---|---|
| Küchenhelfer (fork), backup, Uptime Kuma | €0 | only electricity and own hardware |
| Local AI (Ollama) and Whisper | €0 | needs compute, hence profiles |
| Free cloud AI (optional) | €0 | limits, changes, partly data usage; [OpenAI's free tier is not enough for Mealie](https://mealie.io/documentation/getting-started/installation/ai-providers/) |
| Notifications | €0 | ntfy and SMTP free; [Resend](https://www.resend.com/pricing.md) only sends from your own verified domain |
| Telegram bot | €0 | Telegram account needed; the bot [only downloads files up to 20 MB](https://core.telegram.org/bots/faq) |
| Nutrition: BLS 4.0 | €0 | [free since December 2025](https://heise.de/-11123877); check terms |
| iPhone: web app and shortcut | €0 | [push only for web apps added to the home screen](https://firt.dev/notes/pwa-ios/) |
| GitHub (repo, CI, images) | €0 | [arm64 runners free only for public repos](https://github.blog/changelog/2025-08-07-arm64-hosted-runners-for-public-repositories-are-now-generally-available/); while the repo is private, build arm64 on the Mac (D20) |
| Cloudflare Tunnel | €0 | Cloudflare sees the traffic (section 8) |
| Domain `example.org` (from the Toggly project) | €0 until 3 Jul 2027 (already paid) | then renewal (about €10 a year) or a switch to a free address, e.g. Tailscale Funnel |
| Docker Desktop (Mac) | €0 privately | [paid in large companies](https://docs.docker.com/subscription-billing/desktop-license.md); Podman as free alternative |
| iOS app in the store, signed Mac app | USD 99 per year | [membership required](https://developer.apple.com/support/compare-memberships); not planned |

---

## 11. Risks and mitigations

| Risk | Mitigation | Phase |
|---|---|---|
| AI gets it wrong (quantities, invented ingredients) | Review view with the original, plausibility warnings, nothing saved unchecked | 2 |
| Reel import breaks (platforms change or block) | Description and screenshot as default, download only as plug-in, "experimental" | 7 |
| Recipe only in the image or a comment | Evaluate description and screenshot first | 2 |
| Duplicates hard to detect; [Mealie doesn't report duplicate links](https://github.com/mealie-recipes/mealie/discussions/3478) | Normalize links, compare title and ingredients, only warn | 2 |
| URL import: access to the home network, injected instructions, malicious code in the display | Block private address ranges, schema for AI answers, escape | 2 |
| [Mealie's parser sometimes stumbles, e.g. on 1/3](https://www.github.com/mealie-recipes/mealie/issues/3318) | Own German parser with tests | 3 |
| Nutrition only estimated | Confirm and remember mapping, standard weights, "approx." | 6 |
| Allergen tags wrong | Fixed rules, AI only a suggestion, confirmation, "no guarantee" | 6 |
| [Timers on a mobile web page cannot be guaranteed](https://github.com/mealie-recipes/mealie/discussions/5356) | Shortcut with clock timer, server timer with push, screen on; test early (T1) | 4 |
| [Browser speech recognition doesn't run in installed web apps](https://mobilexweb.com/ios-14.5/) | Vosk locally in the browser, buttons as fallback (T2) | 4 |
| Backup missing or cannot be restored | Daily to a second location, push message, restore test before every update | 1 |
| Large third-party codebase | Code walkthrough, Mealie's `AGENTS.md`, tests first, then changes | 0 |
| Conflicts during upstream sync | Own `kh` folders, `KH:` markers, `cherry-pick`, sync every three months | ongoing |
| Mac and Pi behave differently | Everything in Docker, Pi check at the end of every phase (section in `.claude/CLAUDE.md`) | ongoing |
| Pi too slow | Profiles, hardware test, queue, heavy builds only in CI | 7, 8 |
| Sharing on the go needs reachability and HTTPS | Tunnel or VPN with a free tier, revocable token per device, Telegram without an open port | 1, 5, 7 |
| Updates fail for others | `update.sh` with backup and rollback, upgrade test before every release, follow Mealie's security notices | 1 |
| Too much at once | Family uses it from phase 1, v0.1 after phase 2, feature freeze after v1.0 | ongoing |
| A later phase breaks something earlier | Phase rules (section 5): additive, extension points, old tests in CI, upgrade test | ongoing |
| AI-written code of unclear origin | License scan, no large third-party blocks | ongoing |
| Maintenance rests on one person | Few components, automated tests, monthly update date, good docs | ongoing |
| Legal trouble | Section 9, legal review before the release | 8 |

---

## 12. Early tests

- [ ] **T1 Timer:** Does a shortcut link start a ringing clock timer on a locked iPhone? Alternatively a server timer with push.
- [ ] **T2 Voice:** Vosk with a German model in the browser on the iPhone, with kitchen noise.
- [ ] **T3 Whisper speed:** How long does 1 minute of audio take on the MacBook, Raspberry Pi and possibly a mini PC?
- [ ] **T4 Instagram path:** description and screenshot versus download, with own examples.
- [ ] **T5 BLS:** read the terms of use and clarify integration into an open project.
- [x] **T6 Draft stage:** answered by D18 (own `kh` table, Mealie's data model stays unchanged).
- [ ] **T7 Name:** check the project name for trademark and name conflicts.
- [ ] **T8 Pi check:** start the official Mealie image on the Raspberry Pi and note speed and RAM. Waiting for the Pi (not reachable on 29 Oct 2026); stand-in value from the Mac with 2 CPUs/2 GB: healthy after ~33 s, ~222 MB RAM.

---

## 13. Start prompt for Claude Code

Paste in the cloned fork (with `PLAN.md` in the root folder and `.claude/CLAUDE.md`):

```text
Read .claude/CLAUDE.md and PLAN.md. We are building Küchenhelfer as a fork of Mealie.
Start with phase 0 and work in small steps:
1) Briefly explain how you build and start the fork locally on my Mac in Docker,
   and enter the real commands in .claude/CLAUDE.md under "Commands".
2) Run Mealie's tests and report the result.
3) Do the code walkthrough and write docs/code-rundgang.md with the list
   "keep · rework · remove · new" and the paths for our kh folders.
Do not change any Mealie code in phase 0. Ask when something is unclear,
and tick off finished items in PLAN.md.
```
