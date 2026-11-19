# Changelog – Kochheft (formerly Küchenhelfer)

Notable changes per release. Every release is a git tag with the app image in GHCR as
`ghcr.io/gamingnet006/own-recipe-app:<version>-arm64` (Raspberry Pi, Apple Silicon) and
`<version>-amd64` (Intel/AMD), published with `kh/ops/release.sh`. That script refuses a version without its own `## [version]` section here.

## [Unreleased]

## [v1.4] - 2026-11-19

- Simple view (D79): per person (More > Account, or the admin on the user page) larger text, a short bar and side menu
  (Recipes, Shopping list, Week, More), no filters on the start page, More with Show more; new column `simple`
  (migration kh0014), `PUT /api/kh/admin/navigation/{user_id}`.
- Season (D80): add-on `season` (off) with a start page row of what is in season in Germany and matching recipes
  (`GET /api/kh/recipes/season`).
- Shopping list by QR code and NFC (D81): on the setup page a printable QR code of `/einkauf`, writing NFC stickers in
  Chrome on Android, steps for iPhone.
- Our note on a recipe (D82): one note per recipe and household under the recipe head and in cook mode, in the text
  export ("Unsere Notiz:") and the import; new table `kh_recipe_notes` (migration kh0015); handed to the heir on
  account deletion. The 1.4 news has four cards.
- First-time setup knows Kochheft (D83): three new steps (add-ons as big preset cards, family with temporary
  passwords, a compact system check), German seed data only where the group has none, a summary of the Kochheft
  choices, buttons for the device setup and notifications on the last page; More > Settings > Setup assistant (admins)
  opens it again without touching what is set. News cards can be for admins only (`admin: true`).

## [v1.3] - 2026-11-19

- Flows simplified (D76): the bar at the bottom gets a "Week" tab (meal plan, only with the add-on), cook mode uses
  the whole screen, the inbox lists waiting drafts first and folds the add form, no-AI drafts offer "Type it yourself",
  failed drafts leave the inbox count, the draft review keeps "Accept" at the bottom and has one "Makes 12 muffins" row,
  More is sorted into Plan, Collection, Settings (own page), Help and Account, the meal plan starts on Monday and has a
  button "All to shopping list", the week suggestion fits a phone, and the 1.3 news has six cards instead of eleven.
- Delete account (D78): deleting an account (by an admin or by yourself under More > Account) keeps the person's recipes,
  lists, meal-plan entries, comments and cooked entries in the household, handed to another person who is shown in the
  dialog; favorites, ratings and settings go. Refused for the last admin and the last person of a household.
- Set up Kochheft (D68): a page under More (`/aufs-handy`) with short steps per device (iPhone, iPad, Android, Mac,
  other computers) for the home screen or Dock, the shopping list as its own icon, a key for shortcuts, the import and
  Siri shortcuts and the Clock timer; a question on each new device after sign-in; the introduction got steps for
  sharing and setup. New settings `KH_IMPORT_SHORTCUT_URL` and `KH_SIRI_SHORTCUT_URL`, in `/api/kh/features` as
  `importShortcutUrl` and `siriShortcutUrl`.
- "What's new" (D69): cards with the news after an update, under More → What's new for all versions; new column
  `news_seen` (migration kh0011); new people see the introduction instead.
- Notifications (D75): per person and household, push messages for the meal plan, an evening reminder with
  thaw and prepare hints, the shopping list, wishes, the inbox and news; More → Notifications. New tables
  `kh_push_subscriptions` and `kh_notification_settings` (migration kh0013), new dependency pywebpush (MPL-2.0).
- "What do I cook this week?" (D70): in the meal planner "Suggest a week" proposes a dinner for each free day from
  what you cook often, what you have not cooked for long, wishes and favorites; swap single ones, then apply.
- Phones stay upright (D71): a phone held sideways shows "Please turn your phone upright" over the app (iPads and
  computers are not affected); an installed Android app also asks the system to lock portrait.
- Wish list (D72): "I wish for this" on a recipe; the planner lists the household's wishes, a tap on a day plans one
  as dinner and ends the wish. New table `kh_recipe_wishes` (migration kh0012).
- Share the week (D73): "Share the week" in the planner sends the planned days as text.
- Cook mode on a landscape iPad or a computer (D74): ingredients on the left with the current step's ones
  highlighted, the step on the right; phones and portrait unchanged.
- Shopping and cooking made simpler (D77): recipe ingredients without a linked food show their unit under the name and
  join the matching tile; "2 milk" keeps the unit already on the list and only shows a short note instead of opening
  the sheet; 2 to 5 stores are chips under the title; "Add to shopping list" lists the store used last first. In cook
  mode "You need" writes the amount first, the last step has one "Done - cooked" button (and "Just close"), and
  timers are named "Step 3 · 20 Min".
- Shopping list without network (D63): `/einkauf` opens from the last loaded state when there is no signal; ticking
  off, adding, amounts, properties, urgency and notes work and are sent in order when the network is back (a banner
  says so). Needs the add-on "Offline recipes"; switching it off or signing out removes the stored lists.
- "Always in the house" (D65): a switch in the shopping detail sheet, or long-press on a tile, marks a food as
  always in stock for the household (new `POST /api/kh/shopping/on-hand`, also for members who may not organize);
  such tiles show a small house and sit at the end of their department, and "Add to shopping list" on a recipe
  leaves those ingredients unticked.
- "Hey Siri, add milk to the shopping list" (D64): a Shortcut sends what you say to `POST /api/kh/shopping/add`
  (with your API token); "milk and 2 butter" become two items on the list you name or the one used last, and Siri
  reads back what stands on which list.
- Whole week onto the shopping list (D66): described in the README; Mealie's meal planner already adds the shown
  days with their servings to a store list of your choice and leaves out what is always in the house.
- Start page rows "Often cooked" and "Not cooked for a while" (D67), from the recipes you marked as cooked.
- Recipes as text (D61): "Share as text" in the recipe menu (share, copy or save as `.txt`, for the servings you choose)
  and "Export as text files" in the cookbook view (ZIP with one text per recipe, photos optional).
- File import (D62): the intake takes `.txt`, `.md` and ZIP files (texts and photos, up to 100 drafts and 50 MB
  unpacked); texts exported by Kochheft are read without AI.
- Shopping list with tiles (D60): own page `/einkauf` with one list per store, red tiles for what is missing, details
  (amount, properties, urgency) when writing down, own home-screen icon and an Android shortcut; Mealie's page stays
  as the classic view (`?klassisch=1`).
- Accounts without e-mail (D53): the admin can leave the e-mail empty; the person signs in with the user name.
  Everyone the admin creates chooses their own password at the first sign-in. "Reset password" on the sign-in page
  shows only with mail sending set up, otherwise "ask the admin". With mail sending (new `KH_SMTP_*` settings):
  a welcome mail with a link to choose the password, and the admin switch "e-mail address required" with a confirm link.
- Comments are back under every recipe (D54); Mealie's household and recipe switches still turn them off.
- Servings: a section title like "Zutaten für 6 Portionen" follows the chosen servings; "2 Eigelbe" and
  "2 Eiweiß" in a step grow with the eggs.
- Pages read without AI, like Chefkoch: a first step "Für 12 Muffins." becomes the yield, steps are linked to the
  ingredients they name (the amount shows behind "Milch" again), and "Birne(n)", "Ei(er)", "Prise(n) Salz" are read
  right. Recipes imported before stay as they are; import them again to get this.
- Reviewing a new recipe (D55): tap the title, an ingredient or a step in the preview and change it right there; below
  it, "Wohin kommt das Rezept?" sets categories and a cookbook, or makes a new one.
- Share the shopping list (D56): "Teilen" sends the open items, one per line, to WhatsApp, Notes, Reminders or
  Bring! through the phone's share sheet; without one the list is copied.
- Import from any app's share sheet (D57): `/r/create/url?recipe_import_text=…` puts the text into the intake, also
  through the sign-in; a link, or a short app message with one link (as Chefkoch or Rezeptwelt share), is read as a
  link. The README shows the iOS shortcut.
- Own sidebar (D58): under More each person ticks what their side menu shows; saved per account.
- First-sign-in tour (D59): the admin ticks "Mit Einführung" when creating an account; six short cards after the first
  steps, "Überspringen" bottom left, and "Einführung ansehen" under More.
- Drafts and the first-steps pages no longer show Mealie's extra English "request failed with status 409" message next
  to their own (e.g. next to the duplicates warning).
- Cook mode starts at the first step again after it was finished, and the last step offers "Fertig und als gekocht
  markieren".

## [v1.2.1] - 2026-11-18

- An update now deletes the older Kochheft images and keeps only the new one and the fallback. Every release is
  about 1.5 GB and they used to pile up until Docker's disk was full; on the Mac mini that stopped the restore test.
- Before an update Kochheft checks that Docker has at least 4 GB free (`KH_UPDATE_MIN_FREE_GB`). With less it
  stops before changing anything and says so; automatic updates report it and try again the next night.

## [v1.2] - 2026-11-17

- The clock timer shortcut is now called "Kochheft Timer" (was "KH Timer"), so it is clear in the Shortcuts app what
  it belongs to. A device that already uses "KH Timer" keeps its stored name.
- Kochheft comes with the ready-made "Kochheft Timer" shortcut: More → Timer shows "Add shortcut" without any setting;
  `KH_CLOCK_SHORTCUT_URL` can still name another one.
- Switch household (D52): the admin can give a person further households, also in other groups, under More →
  Household access; the person switches under More → Switch household without a password. Each household gets its
  own linked account, so what someone adds belongs to the household they are in. Linked accounts always have the main
  account's rights; unlinking takes them.
- The AI provider page has a step-by-step Gemini guide, open while no provider exists: its button opens the provider
  window already filled in and also makes the "Gemini Reserve" (same key, second free model), so only the key is left
  to paste; both are tested on their own. Free places and providers carry "(free)" or "(trial
  credits)" in bold.
- The sign-in page says "Kochheft" and links only to Kochheft's own source (`KH_SOURCE_URL`); Mealie's sponsor link
  and all "Docs" buttons to Mealie's documentation are gone.
- More → Timer offers the clock timer on iPhone and iPad only; Android and computers see a short note instead, since
  they have no Shortcuts app.

## [v1.1] - 2026-11-15

- Based on Mealie v3.31.0 (was v3.29.0): 23 published security fixes, newer libraries (Pillow 13, SQLAlchemy 2.1 and
  others with known vulnerabilities fixed), instruction durations and weekly meal plans. Mealie's migrations run beside
  Kochheft's own as a second head (D24); the unused `cook_time` column moves into the cook time Mealie shows.
- Mealie's new sanitizer keeps Kochheft's step marks (tap a time, amounts in brackets); printed ingredient lines and
  the recipe header go through Mealie's safe inline HTML.
- Fixed after a full audit: timers read "1/2 Stunde" and "1 1/2 Stunden"; ingredient lines read "1.000 g" and
  "ca. 200 g"; allergen words fill gaps (Cheddar, Rührei, Eiweiss, Pizzateig, Langusten) and drop false alarms
  (Tamarinde, Insekten, Milcheiweiß as egg); compounds weigh like their last part (Weizenmehl like Mehl); a 48 MP
  photo no longer stops a small server; video links inside text and links without https are recognized; a stored
  add-on switch from a newer version is ignored instead of breaking pages.
- From 840 px the side menu ends with "More", so add-ons, system check and the oven, nutrition and clock settings are
  reachable on iPad landscape and computers (D51). "I don't tolerate" never shows empty boxes after a failed load.
  Saved recipes answer after 4 s on weak Wi-Fi; the alarm sound unlocks on the end of a tap; Enter cannot send a
  draft twice.
- Second audit round: approving a draft whose follow-up step fails no longer leaves a duplicate recipe, and a double
  tap on "retry" starts one recognition; an update interrupted after the switch (closed terminal, signal) rolls back,
  and a nightly update stopped by a signal is tried again instead of being skipped; a full USB stick makes room
  first and says "Laufwerk voll"; voice commands stop when the app goes to the background; allergen marks retry
  after a failed load; a failed add-on load no longer slows every page change; larger buttons and labels for
  touch and screen readers; manual nutrition values read "1.200" as 1200.
- Operations: a failed or damaged backup copy never keeps a backup's name; a keep count of 0 or a typo deletes
  nothing; .env values may contain & and |; relative recordings in the hardware test; the release gate fails when no
  older image can be loaded instead of skipping the upgrade test.

## [v1.0.1] - 2026-11-10

- AI settings: Mealie's audio provider select is gone (it only served Mealie's video import, which Kochheft refuses);
  instead a short note explains how to add a provider with a key, that the top provider of the list does text and the
  top one that reads images does photos and screenshots, and that recordings go to the local Whisper add-on.
- The list of free key places ticks itself off: a place shows "set up" when one of your providers uses its address,
  and says that one provider is enough, more are a reserve. The provider list now also carries the address (never
  the key).

## [v1.0] - 2026-11-09

The big update (D45 to D49): phase 6 plus everything of phases 7 and 8 that needs no decision, under the new name.

Renamed to Kochheft (formerly Küchenhelfer, D49), with a new logo and app icons. Only what users see changed; the `kh` folders, `KH_*` variables,
container names and image name stay, so running installs and updates keep working.

Nutrition and allergens (Phase 6, D44):

- Recipe page: block "Nährwerte pro Portion (ca.)" from the BLS 4.0 table (Max Rubner-Institut, CC BY 4.0, shipped in the
  image). It counts lines with an amount and a matched food, shows "from n of m ingredients" and "without: ...", and says
  "estimated" until the matching is confirmed. Values entered by hand in Mealie win. More -> "Show nutrition" hides it.
- More -> Nutrition: confirm the matching once per ingredient and set a piece weight; it applies to all recipes.
- Allergens: the 14 EU groups are detected from the ingredients by fixed rules, always "probably, without guarantee".
  They can be corrected per recipe ("not correct", "Add an allergen").
- More -> "I do not tolerate" per account: the recipe page warns with the names, recipe cards show a mark.
- Substitution hints from a standard list plus the household's own rules; "Save as variant" makes a copy "(ohne ...)"
  and leaves the original unchanged.
- New additive migration `kh0005`. The table can be rebuilt with `uv run python -m mealie.kh.nutrition.build_bls`.

Add-ons (D46, D48):

- More -> Add-ons (admins change, per household): the big areas shopping list and meal planner can be switched off,
  with the presets "Only recipes", "Recipes and shopping list" and "Everything with meal planner"; without the shopping
  list the bottom bar has three places. Family cookbook, duplicates, fan-oven brackets, nutrition, allergens,
  substitutions, offline recipes, clock timer, share links, Telegram, Whisper and voice commands can be switched too.
  Switched-off features leave the interface; their data stays. Migration `kh0007`.

Sharing, video and voice (Phase 7, D45):

- Telegram bot (optional, off): links, texts and photos from allowed chats become drafts; polls by itself, no open port.
- Video links (Instagram, TikTok, YouTube, Facebook) are never fetched (D5): the description or a screenshot makes the
  draft, the link stays its source. Mealie's video downloader yt-dlp is removed.
- Own audio and video files become drafts through an optional local Whisper service (speaches); migration `kh0006`.
- Profiles leicht, normal, stark, lokal and `kh/ops/hardware_test.sh`, which proposes one.
- Voice commands in cook mode as a test switch ("weiter", "zurück", "Timer", "stopp"); recognition runs in the browser
  with Vosk, the German model is served by the app itself.
- Local AI (for example Ollama) only as an untested guide, `docs/kh/LOKALE-KI.md`.

Operation and publishing (Phase 8, D45):

- More -> About: version, Mealie notice, AGPL-3.0, source link and the third-party list.
- Checkbox "Automatic updates" in the admin settings, read by `auto_update.sh` (which now keeps its nightly job when
  switched off) and a status line in the app.
- More -> System check for admins: a traffic light per point and a first-start list.
- README: what you need (measured), what goes where, maintenance checklist; legal checklist `docs/kh/RECHT.md`;
  issue templates.
- CI: licence scan of all Python and npm packages, secret scan of the whole history with gitleaks, CI on every push.

## [v0.4] - 2026-11-08

Family cookbook and moving house (Phase 5, D43):

- "Print as book" on a Mealie cookbook opens an editor with a live preview: title, subtitle, title page, contents with
  recipe numbers, order, description, notes, fan-oven brackets and, per recipe, in the book / with photo / servings.
  Print or "Save as PDF" on the Mac and the iPhone (Share -> Print). Settings are saved per cookbook for every
  device; only the own household can change them, others can print.
- Single recipes print as a recipe card (recipe menu -> Print).
- Photos enter the book only with "The photo is ours" (photos you took yourselves).
- Fan-oven brackets: "180 °C (Umluft 160 °C)" after each oven temperature in the steps, following the oven chosen
  under More -> Our oven. The difference is 20 °C; nothing below 100 °C is converted; the stored text never changes.
- More -> "Duplicate recipes" lists possible duplicates (optionally only recipes with an import tag) so you can keep
  both or delete one after a migration from another app.
- New additive migration `kh0004` for the book settings and duplicate decisions.
- Docs: how to move from another app with Mealie's migrations.

## [v0.3] - 2026-11-08

Cook mode (Phase 4, D41, D42):

- Cook mode shows one step at a time in large type with big Back and Next buttons, swipe and arrow keys, a bar of
  segments (up to 12 steps) and the ingredients of the step ("You need:"). "All steps" shows Mealie's list; the screen
  stays on while you cook.
- Amounts stand next to ingredient names in the steps ("melt the butter (200 g)"), following the chosen factor; the
  stored text never changes.
- Times in the steps ("10 Min.", "1,5 Stunden", "20-30 Min.", "eine halbe Stunde") can be tapped and start a timer.
  Several timers run at once and survive sleep, reloads and page changes; a thin bar shows them on every page, and a
  timer that runs out rings and vibrates until "Off" (2 minutes at most). A range rings at the lower end and offers
  "more min." up to the upper end.
- Where a step uses only part of an ingredient, the share stands in brackets ("half of the flour (125 g)", "the
  rest of the flour (125 g)").
- Optional "Put on the clock" button hands a timer to the iPhone's Clock app through a Shortcut named "KH Timer"
  (More -> Timer), so it rings on a locked phone, too. The switch explains the setup; with `KH_CLOCK_SHORTCUT_URL`
  set, it links straight to the shared Shortcut.
- The last 30 recipes you opened and their photos open offline, with a hint; signing out deletes them.

## [v0.2] - 2026-11-08

The new interface (D38): everyday use first, in the look "Salbei", with a calm recipe page.

- A calm green instead of Mealie's orange, the device's own font (San Francisco on iPhone and iPad), a light
  header and the name Küchenhelfer; hints, warnings and errors in tones that stay readable. Browsers fetch the new
  colors right after the update.
- On phones and upright iPads a bar at the bottom: Recipes, Intake with the number of waiting drafts, Shopping list
  and More, which holds everything the side menu had. From 840 px (iPad landscape, computer) the side menu stays,
  with the same destinations, also after an iPad is turned; "What can I cook?" is Mealie's recipe finder.
- The shopping list tab opens the household's list directly when there is only one, for everyone in it.
- Adding a recipe and the drafts are one page now, the intake; the old addresses lead there.
- The start page says when drafts wait for a review; recipe cards show no stars.
- The recipe page: the photo with back, favorite and a menu ⋯ (edit, mark as cooked, view original, meal plan, print, delete),
  title and origin, the times as tiles and the amount with − and +, which scales ingredients and steps of recipes
  with parsed ingredients. "Add to shopping list" sits under the ingredients, "Start cooking" at the bottom. No stars,
  comments, "last made", category and tag chips or unit switch; editing, cook mode and printing stay Mealie's.

Amounts (Phase 3, D39):

- Importing reads German amounts without AI: fractions, decimals with a comma, ranges, EL, TL, Prise, Pck., Msp.,
  Stück and more; missing German units are added once, unknown foods stay text.
- Amounts in the step text are linked to their ingredient; the review shows them tinted and taps unlink them, and
  they follow later edits of the text.
- The recipe page scales the step text too, in cook mode and print; "Scale" offers servings, "I only have …" and
  baking pans, with a hint when times may change.
- One display for all amounts: fractions, rounded grams, kg and l from 1000, halves of pieces with a tip for half an
  egg, 3 TL as 1 EL, ranges at both ends, pinches that stay.
- The review warns about unrecognized or unusual amounts, times over a day, odd temperatures, unused ingredients and
  amounts converted from American units.

AI priority list and bell (D39):

- Any number of AI providers in an order set with ▲▼; a request moves on to the next when a quota is used up, a key is
  invalid, a model is gone or a provider is down, and a failing one is skipped for a while. Each provider shows its
  state, e.g. "quota used up until 9:00", and whether it reads images; Küchenhelfer sets Mealie's default and image
  provider from the list in every group, and photos go only to providers whose test read an image, or untested ones.
- After the update the list starts where requests went so far: the default provider first, the image provider next;
  a new provider joins at the end.
- A bell next to the search for everyone who manages AI providers, with messages such as "Gemini: quota used up until
  9:00. Now using Groq." and one message when no AI is reachable, until one answers again; the intake tells the family
  when no provider is free or none is set up. A draft no provider could read says "No AI reachable", and a draft names
  every provider that read it.
- Under the AI providers, ten places to get free keys, with the date they were checked.

Backups explain themselves, and their copy can move:

- Next to the backups, on the USB stick and in the backup folder, lie `LIESMICH.txt`, a step-by-step guide to
  get the recipes back (reinstall, decrypt, restore, check), and `CLAUDE.md`, the same for Claude Code started
  in that folder. Both are renewed when they change; the short guide on sticks set up earlier is replaced.
- Changing where the copies go, later too: on a Mac a double-click on `kh/ops/backup-ort-aendern.command`, elsewhere
  `kh/ops/backup_copy.sh on` without a folder. It shows the place now, how to prepare a stick or disk and the
  plugged-in drives; the first copy, guides included, goes there right away, and on a Mac the result shows. The old
  place keeps its copies. On purpose only on the machine itself, not on the website.

## [v0.1.1] - 2026-11-01

Recipes from the share menu, and clearer messages when the connection drops.

- Share shortcut for iPhone and iPad (D37): links, texts and photos from the share menu go straight to the
  drafts, with a revocable API token per device; the guide shows how to build it and share it with the family.
- Without a connection, the drafts list and the review say so and try again by themselves, instead of
  "no drafts" or "not found".
- Chosen photos show as small previews on the intake page and can be removed again.

## [v0.1] - 2026-11-01

Phase 2: every new recipe gets a review before it is saved (D35).

- **Add recipe** takes a link, a text or photos; Mealie's import pages lead there too. The recipe is
  recognized in the background and waits as a draft under "Drafts (n)" for anyone in the household.
- The review shows the original next to the result (one below the other on a phone, side by side on an
  iPad), with Save, Save and edit, Discard and Try again.
- Possible duplicates (same link, similar title, the same ingredients) are pointed out, never deleted.
- A saved recipe shows where it came from, with a way back to its original.
- AI: Google Gemini with a free key, entered in Mealie's group settings; the guide explains how and
  lists what goes where.
- The review shows the picture a link brought and the yield with its amount ("4 personen"), and takes
  servings and yield before saving, e.g. 1 and "Springform Ø 26 cm".
- Recipe language (D36): with `KH_RECIPE_LANGUAGE=German` whatever the AI reads is translated into German;
  recipes already in it cost no extra request.
- Backups restore drafts intact, also into a new install: Mealie's restore now keeps JSON columns and the
  approval date, builds every migration branch and, on Postgres, resets every id counter (marked `KH:`).
- New optional settings `KH_DRAFT_*`, `KH_DUPLICATE_*` and `KH_RECIPE_LANGUAGE`, see `kh/ops/.env.example`.

## [v0.0.2] - 2026-10-31

The copy to a USB stick also works without a password (D33).

- `backup_copy.sh on` asks once whether the copies get a password (j/n). Without one they are
  normal Mealie backups (`KH_BACKUP_COPY_KEY=none`), copied as they are and compared with the original.
- The guide says what to do when a stick without a password gets lost.

## [v0.0.1] - 2026-10-31

Second backup location on a removable drive (D32, D33).

- Encrypted copy of the backups on a USB stick or another drive (`kh/ops/backup_copy.sh on|off|status|run|decrypt`):
  every night at 3:45 am, encrypted with age, the newest `KH_BACKUP_KEEP` copies stay. The private key lies on
  the drive, locked with a password that is stored nowhere. Without the drive, or when the folder lies on this
  machine's own disk, the job writes nothing and reports it. Encrypted, because a Mealie backup holds the backup
  service's API key in plain text.
- `backup_copy.sh decrypt` checks a copy: while the same backup is still on this machine, it compares
  the decrypted copy with it instead of replacing it.
- On macOS the copy runs as a LaunchAgent with `/bin/dash`, which needs Full Disk Access once: macOS locks
  removable drives for background jobs and SSH.
- The backup image now contains age (BSD-3-Clause).
- Release images carry `kh/ops/nightly_job.sh` (scheduling shared by the nightly update and the copy) and
  `kh/ops/backup_copy.sh`; `check_bundle.sh` refuses an image without them.

## [v0.0] - 2026-10-31

First release for the family (phase 1, PLAN.md section 5). It runs on the Mac mini with access from
outside, daily backups and automatic updates; new installs follow the guide in `docs/kh/README.md`.
The install test on a fresh Raspberry Pi follows later (D30).

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
