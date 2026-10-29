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
| D6 | AI: local first (Ollama, Whisper), free cloud only as a fallback and only with the user's own key. From phase 2 a simple AI setting in `.env` (Ollama on the Mac or own key); profiles follow in phase 7 | decided |
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
| D20 | Build arm64 images on the Mac and push to GHCR while the repo is private; amd64 in CI (eng review) | decided |
| D21 | Backups via Mealie's backup API; on failure `update.sh` restores image and database from the pre-update backup (eng review) | decided |
| D22 | Access from outside: self sign-up off, tunnel provider listed in "What goes where" (eng review) | decided |
| D23 | Automatic upgrade test in CI; AI calls in tests only with recorded answers (eng review) | decided |

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

- [ ] Bring Mealie's code into our own repo `gamingnet006/own-recipe-app`: set the remote `upstream` to Mealie and merge the latest stable version (no GitHub fork, so the repo can stay private).
- [ ] Take over Mealie's `CLAUDE.md`, `README.md` and `.gitignore` unchanged; append our `.gitignore` lines as a marked `# KH` block; check that Claude Code additionally loads `.claude/CLAUDE.md` (D17).
- [ ] Build and start the fork locally on the Mac in Docker, run Mealie's tests; enter the real commands in `.claude/CLAUDE.md` under "Commands".
- [ ] Simple CI on GitHub: lint and tests on every push.
- [ ] Code walkthrough: document the structure (backend, frontend, data model for recipe, ingredient and step, import, parser, scaling, cooking mode, backups) in `docs/code-rundgang.md`.
- [ ] List "keep · rework · remove · new" and the paths for our `kh` folders in `docs/code-rundgang.md`.
- [ ] Early tests T6 and T8 (section 12); the others before their phase.
- **Done when:** the fork runs locally, tests are green, CI runs, and walkthrough and list exist.

### Phase 1 · Running for the family (v0.0)

- [ ] CI builds the amd64 image per tag and publishes it to the GitHub Container Registry; the arm64 image is built natively on the Mac and pushed there with one command per release while the repo is private (D20).
- [ ] `docker-compose.yml` and `.env.example` (placeholders only, no real credentials); start on the Pi.
- [ ] `update.sh`: backup first, then new version, health check; on failure restore the old image and the database from exactly this backup (D21).
- [ ] Automatic upgrade test in CI: start the previous release with test recipes, update, check recipes and images; a failure blocks the release (D23).
- [ ] Short "Install" guide in the README for this release.
- [ ] Hide unneeded Mealie parts in UI and routes (stage 1 of the fork rules).
- [ ] Backup container using Mealie's backup API (create, copy to the second location; `restore.sh` uses Mealie's restore): daily, retention, push message to Uptime Kuma, restore test script. Admin access only as a placeholder in `.env.example` (D21).
- [ ] HTTPS and tunnel for access from outside (free, no open ports; D14). Self sign-up stays off (`ALLOW_SIGNUP=false`, Mealie default); the tunnel provider is listed in "What goes where" (D22).
- [ ] Create family accounts, sample recipes as seed data.
- [ ] `THIRD_PARTY_NOTICES.md` and `CHANGELOG.md`.
- **Done when:** the family adds recipes from outside the home, a backup has been restored on a second device, and release `v0.0` installs on a fresh Pi using only the short guide.

### Phase 2 · Intake, review, duplicates (v0.1)

- [ ] Drafts in their own `kh` table including the original; only approval creates a normal recipe through Mealie's existing path and links the original. Mealie itself never has to filter drafts (D18, answers T6).
- [ ] AI connection via `.env` (Ollama on the Mac or own key, D6).
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
- [ ] Remove unneeded Mealie tables via migration (stage 2 of the fork rules).
- [ ] README with "What goes where" (section 8), installation guide in German and English, maintenance checklist.
- [ ] Legal checklist (section 9), license scan, name checked.
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
| Access from outside | all traffic to the web app | the chosen tunnel provider (D22) | own VPN instead of a third-party tunnel |
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
- [ ] **T8 Pi check:** start the official Mealie image on the Raspberry Pi and note speed and RAM.

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
