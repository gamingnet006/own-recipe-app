# Code-Rundgang: Mealie v3.29.0 als Basis für das Kochheft

Ergebnis von Phase 0 (PLAN.md, Abschnitt 5). Stand 29.10.2026, Basis Mealie `v3.29.0` (Commit `89a1420`). Pfade relativ zum Repo-Hauptordner.

## 1. Aufbau

```text
mealie/                 Backend (FastAPI, Python 3.14)
  app.py                App-Start; hängt alle Router ein (api_routers(), Zeile ~154)
  routes/__init__.py    Sammel-Router /api: eine include_router-Zeile je Bereich
  routes/<bereich>/     Controller (HTTP), delegieren an services/
  services/             Fachlogik (Import, KI, Parser, Backups, Migrationen, Zeitplaner)
  repos/                Datenzugriff (AllRepositories, nach Gruppe/Haushalt gefiltert)
  schema/               Pydantic-Schemas; __init__.py werden von `mise run dev:generate` erzeugt
  db/models/            SQLAlchemy-Modelle; _all_models.py lädt alle Modelle
  alembic/              Migrationen (eine lineare Kette, 59 Dateien), alembic.ini
  pkgs/safehttp/        abgesicherte HTTP-Abrufe (private Adressen, Zeitlimit)
frontend/               Nuxt 4 + Vue 3 + Vuetify, statisch erzeugt und vom Backend ausgeliefert
  nuxt.config.ts        Module (u. a. @vite-pwa/nuxt, @nuxtjs/i18n), keine Layers
  app/pages/            Seiten (g/<gruppe>/… für Rezepte)
  app/components/Domain/Recipe/   Rezept-Ansicht, Editor, Druckansicht, Zutaten
  app/composables/recipes/        Skalierung, Brüche, Einheiten, Zutaten-Logik
  app/lib/api/          API-Clients; types/ wird erzeugt (nie von Hand ändern)
  app/lang/messages/    Übersetzungen; nur en-US.json pflegen, de-DE.json kommt über Crowdin
docker/                 Dockerfile (Frontend-Build + Python), docker-compose.yml (Port 9091)
tests/                  pytest: unit_tests/, integration_tests/, fixtures/
.github/workflows/      Mealies Workflows; aktiv nur test-backend/test-frontend über kh-ci.yml
```

Mandanten: Alles gehört zu einer **Gruppe**, Rezepte, Wochenpläne und Einkaufslisten zusätzlich zu einem **Haushalt**. Die Repositories filtern das automatisch. Das deckt „Familie trägt mit ein“ ohne neuen Code ab.

## 2. Datenmodell Rezept, Zutat, Schritt

| Tabelle | Modell | Wichtig für uns |
|---|---|---|
| `recipes` | `db/models/recipe/recipe.py` `RecipeModel` | Zutaten, Schritte, Notizen, Nährwerte, Tags, `is_ocr_recipe`, `extras` (freie Schlüssel/Werte) |
| `recipes_ingredients` | `db/models/recipe/ingredient.py` `RecipeIngredientModel` | Menge, Einheit (`ingredient_units`), Lebensmittel (`ingredient_foods`), Notiz, `reference_id`, `substitutions` |
| `recipe_instructions` | `db/models/recipe/instruction.py` `RecipeInstruction` | `text`, `title`, `summary`, `position`, Dauer (Schema `duration_seconds`) |
| `recipe_ingredient_ref_link` | `instruction.py` `RecipeIngredientRefLink` | Verknüpfung Schritt → Zutat über `reference_id`; Grundlage für D19 |
| `ingredient_foods_substitutions` | `ingredient.py` `IngredientFoodSubstitutionModel` | Zutaten-Ersatz pro Lebensmittel, bereits vorhanden (Phase 6) |
| `recipe_nutrition` | `db/models/recipe/nutrition.py` | Nährwerte pro Rezept, bereits vorhanden (Phase 6) |

## 3. Wo die Funktionen aus dem Plan heute in Mealie stecken

| Bereich | Mealie-Code | Befund |
|---|---|---|
| Link-Import | `services/scraper/` (`recipe_scraper.py`, `scraper_strategies.py`) | Strukturierte Daten zuerst, KI nur als Rückfall (`RecipeScraperOpenAI`) |
| KI-Import (Text, Foto, Audio) | `services/recipe/ai_recipe_service.py`, Route `routes/recipe/recipe_crud_routes.py:468` (`/recipes/create/ai`) | Nutzt `RecipeImportWorkflow` |
| Import-Ablauf | `services/recipe/import_workflow/workflow.py` | Schritte `CompileSource → BuildRecipe → TranslateRecipe → ResolveOrganizers`; laut Kommentar „never persists the recipe; it returns a draft for the caller to save“ |
| Quellen-Aufbereitung | `import_workflow/compilers/` (`image.py`, `web_page.py`, `structured_data.py`, `transcription.py`) | Bild und Transkription sind schon da (Phase 2 und 7) |
| KI-Anbieter | `services/openai/openai.py` + Admin-Route `routes/admin/admin_management_ai_providers.py` | Anbieter liegen pro Gruppe in der Datenbank (Standard- und Audio-Anbieter), nicht in `.env`; seit D39 fragt Kochhefts Prio-Liste sie der Reihe nach |
| Zutaten-Parser | `services/parser_services/ingredient_parser.py` (`BruteForceParser`, `NLPParser`), `parser_services/openai/` | Grundlage für `parse_ingredient()` (Phase 3) |
| Skalierung, Brüche, Einheiten | `frontend/app/composables/recipes/use-scaled-amount.ts`, `use-fraction.ts`, `use-unit-conversion.ts`, `use-unit-system.ts` | Grundlage für `format_amount()` (Phase 3) |
| Schritt-Zutat-Verknüpfung | `frontend/app/composables/recipe-page/use-extract-ingredient-references.ts` | Grundlage für `link_quantities()` (Phase 3) |
| Kochmodus | `frontend/app/composables/recipe-page/use-cook-mode-query.ts`, `RecipePage/RecipePageParts/RecipePageInstructions.vue` | Phase 4 baut darauf auf |
| Bildschirm an | `frontend/app/components/global/WakelockSwitch.vue` | vorhanden |
| Offline / als App installierbar | `@vite-pwa/nuxt` in `nuxt.config.ts` | Grundlage für Offline-Rezepte (Phase 4) |
| Druckansicht | `components/Domain/Recipe/RecipePrintView.vue`, `RecipePrintContainer.vue` | Grundlage für PDF-Rezeptkarte (Phase 5) |
| Umzug aus anderen Apps | `services/migrations/` (Paprika, Tandoor, Nextcloud, …) | vorhanden (Phase 5) |
| Backups | `services/backups_v2/`, Routen `routes/admin/admin_backups.py` (erstellen `:44`, wiederherstellen `:105`) | D21 nutzt diese Schnittstelle |
| Abrufe fremder Seiten | `mealie/pkgs/safehttp/transport.py` (`is_blocked_ip`, Zeitlimit) | Erfüllt „private Adressbereiche sperren“ (Phase 2) |
| Zeitgesteuerte Aufgaben | `services/scheduler/` | Für nächtliche Warteschlange (Phase 7) |
| Statistik | `services/analytics/service_analytics.py` | Nur lokale Auswertung, sendet nichts nach außen. Außer Doku-Links fanden sich keine Aufrufe an mealie.io oder GitHub |

## 4. Liste „behalten · umbauen · entfernen · neu“

**Behalten (unverändert nutzen):** Gruppen und Haushalte, Benutzer und Login, Rezept-Editor, Suche, Tags und Kategorien, Kochbücher, Wochenplan und Einkaufsliste (Plan: „Später aufräumen“), Backups, Migrationen, Druckansicht, Bildschirm-an, PWA, KI-Anbieter-Verwaltung, `safehttp`, Zutaten-Ersatz, Nährwert-Modell, Zeitplaner, Selbstregistrierung aus.

**Umbauen (über Erweiterungspunkte, nicht durch Umschreiben):**

| Was | Phase | Wie |
|---|---|---|
| Ergebnis von `/recipes/create/ai` und KI-Rückfall beim Link-Import | 2 | Statt direkt zu speichern, landet der Entwurf aus `RecipeImportWorkflow` in der `kh`-Entwurfstabelle (D18). Eine `KH:`-markierte Stelle im Aufrufer |
| Zutaten-Parser | 3 | Deutscher Parser als eigener Parser neben `BruteForceParser`/`NLPParser`, ausgewählt über `get_parser()` |
| Skalierungs-Anzeige | 3 | `format_amount()` im `kh`-Frontend, nutzt `use-fraction` und `use-unit-conversion` |
| Kochmodus | 4 | Klickbare Zeiten und Timer als `kh`-Komponenten in der Schritt-Ansicht |
| Druckansicht | 5 | Familienkochbuch als eigene `kh`-Seite, nutzt `RecipePrintView` |
| Zutaten-Ersatz | 6 | Eigene Regeln auf Mealies Ersatz-Tabellen aufsetzen |

**Entfernen (Stufe 1: nur ausblenden, Tabellen bleiben bis Phase 8):** Beschlossen und umgesetzt am 31.10.2026 (Arbeitsplan `docs/kh/plans/2026-10-31-phase-1-abschluss.md`, Paket 5).

- **Teilen-Links:** standardmäßig aus (`KH_SHARE_LINKS`, `mealie/kh/features/`). Das Rezeptmenü zeigt dann kein „Teilen“. Die öffentliche Rezeptansicht per Token antwortet mit 404, und ihre Vorschau-Seite zeigt keine Rezeptdaten.
  - Mealies Rezept-Download nutzt intern ebenfalls einen Token (30 Tage gültig) und eine eigene Zip-Route. Beide bleiben, damit der Download funktioniert.
- **Ankündigungen:** Neue Gruppen starten mit `show_announcements = false`; Mealies Schalter in den Gruppeneinstellungen bleibt.
- **Explore-Seiten:** schon aus, weil neue Gruppen privat sind (`private_group`). Ein Test in `tests/kh/features/` sichert das ab.

Alles Weitere entscheidet die Nutzung in Phase 1.

**Neu:** Entwurfstabelle und Prüfansicht, Duplikat-Warnung, Herkunfts-Badge (Phase 2) · Mengen-Nebentabelle, Plausibilität, Backform-Rechner (Phase 3) · Timer-Wege, Vosk-Sprachbefehle (Phase 4) · PDF-Kochbuch, Kurzbefehl-Token, Umluft und Menü-Zeitplan (Phase 5) · BLS-Nährwerte, Allergene, Familienprofil (Phase 6) · Telegram-Bot, Profile, Hardware-Test (Phase 7) · Erststart-Assistent, Systemprüfung (Phase 8) · Backup-Container, `update.sh`, Upgrade-Test (Phase 1).

## 5. Pfade für unsere `kh`-Ordner

| Teil | Pfad | Einhängung in Mealie (je eine `KH:`-markierte Stelle) |
|---|---|---|
| Backend-Code | `mealie/kh/<funktion>/` (Routen, Services, Modelle, Schemas je Funktion) | `mealie/kh/routes.py` sammelt unsere Router, eingebunden in `mealie/routes/__init__.py` (`router.include_router(kh_routes.router)`) |
| Tägliche Aufgaben | z. B. `mealie/kh/drafts/files.py` (`sweep_orphans`) | `register_daily` in `mealie/app.py` |
| Backup und Wiederherstellen | – | `mealie/services/backups_v2/alchemy_exporter.py`: Datumsspalten `approved_at`, `paused_until`, `until`, `last_read_at`, JSON-Spalten in `look_for_json`, jeder Alembic-Kopf eines Backups wird aufgebaut; `backup_v2.py`: nur vorhandene Datenordner ersetzen |
| Datenbank-Modelle | `mealie/kh/<funktion>/models.py` | Import in `mealie/db/models/_all_models.py` |
| Migrationen | `mealie/kh/alembic/versions/` als eigener Alembic-Zweig `kh` | `version_locations` in `mealie/alembic/alembic.ini` und `"head"` → `"heads"` in `mealie/db/init_db.py` (D24) |
| Backend-Tests | `tests/kh/<funktion>/` | `tests/utils/alembic_reader.py` fragt Alembic nach allen Köpfen; sonst findet pytest `tests/` von selbst |
| Frontend | `frontend/kh/` als Nuxt-Layer; unter Nuxt 4 liegen die Dateien in `frontend/kh/app/` (`plugins/`, `components/`, `composables/`, `pages/`, `middleware/` je Funktion) | `extends: ["./kh"]` in `frontend/nuxt.config.ts` (D26); Menü in `frontend/app/components/Layout/DefaultLayout.vue`, Herkunfts-Abzeichen in `frontend/app/components/Domain/Recipe/RecipePage/RecipePage.vue` |
| Oberfläche (D38) | `frontend/kh/app/components/` (`KhBottomNav`, `KhDraftHint`, `KhRecipeHeader`, `KhAddToShoppingList`), `composables/use-kh-navigation.ts`, `use-kh-recipe.ts`, `pages/g/[groupSlug]/more.vue`, `lib/theme.ts`, `assets/kh-theme.css` | `DefaultLayout.vue` (Leiste, Seitenmenü), `AppHeader.vue`, `AppScrollToTop.vue`, `plugins/theme.ts`, `RecipeExplorerPage.vue` (Entwürfe-Hinweis), `RecipeCard.vue` und `RecipeCardMobile.vue` (ohne Sterne), `RecipePage.vue` (Kopf, Einkaufsliste, ohne Kommentare und Chips), `RecipeLastMade.vue` (Dialog von außen), `mealie/core/settings/themes.py` und `branding.py` (Farben, Name) |
| KI-Prio-Liste und Glocke (D39) | `mealie/kh/ai/` (Kette `ask_ai`, Fehlerarten, Zustand, Routen), `mealie/kh/notices/` (Meldungen, Routen), `frontend/kh/app/components/` (`KhAiProviderOrder`, `KhFreeAiKeys`, `KhBell`), `composables/use-kh-ai.ts`, `use-kh-notices.ts`, `lib/free-ai-keys.ts` | `services/openai/openai.py` (`get_response` ruft die Kette, `_get_raw_response` wiederholt auf ihren Wunsch nicht selbst, der Test merkt sich sein Ergebnis), `services/recipe/import_workflow/steps/compile_source.py` (findet die Liste keine KI, endet der Import mit diesem Grund), `repos/repository_ai_provider.py` (Speichern macht bereit, Rollen folgen der Liste), `routes/groups/controller_group_ai_providers.py` und `routes/admin/admin_management_groups.py` (Rollen nach dem Speichern), `GroupAIProviderSettingsEditor.vue` (Liste und Infofeld statt Auswahl von Standard- und Bildanbieter, auch für andere Gruppen), `AppHeader.vue` (Glocke), `lib/icons/icons.ts` (Pfeil, Glocke), `alchemy_exporter.py` (Datumsspalten) |
| Mengen (D39, D40, Phase 3) | `mealie/kh/amounts/` (Zeilen lesen `parse.py`, Schritte verknüpfen `steps.py`, Hinweise `plausibility.py`, Tabellen `models.py`, Ablauf `service.py`, Route), `frontend/kh/app/lib/amounts.ts` (Anzeige, Umrechnen, Schritttext), `lib/amounts-store.ts`, `composables/use-kh-amounts.ts`, `components/KhScaleSheet.vue` | `composables/recipes/use-recipe-ingredients.ts` (eine Anzeige für alle Mengen), `RecipePage.vue` (lädt die Mengen), `RecipePageInstructions.vue` und `RecipePrintView.vue` (Schritttext umgerechnet), `services/recipe/recipe_service.py` (`update_one` und `patch_one` führen Verknüpfungen nach, `delete_many` löscht die Mengen); Entwürfe: `mealie/kh/drafts/recognize.py` und `service.py` |
| Kochmodus (D41, D42, Phase 4) | `frontend/kh/app/lib/times.ts` (Zeiten im Text erkennen), `lib/step-text.ts` (Schritttext mit Mengen und anklickbaren Zeiten), `lib/offline.ts` (Offline-Regeln und Aufräumen), `composables/use-kh-timers.ts` (Timer, Alarm, Uhr-Kurzbefehl), `use-kh-cook.ts` (Schritt), `use-kh-time-tap.ts` (Tipp auf eine Zeit), `components/KhTimers.vue`, `KhCookStep.vue`; Offline-Regeln in `frontend/kh/nuxt.config.ts` (`pwa.workbox.runtimeCaching`) | `RecipePage.vue` (Schrittansicht statt Mealies Kochmodus, Schalter „Alle Schritte“), `RecipePageInstructions.vue` (Schritttext, Tipp auf Zeiten), `DefaultLayout.vue` (Timer-Leiste und Alarm auf jeder Seite), `use-auth-backend.ts` (`signOut` löscht die Offline-Rezepte), `lib/icons/icons.ts` |
| Familienkochbuch, Umluft, Duplikate (D43, Phase 5) | `mealie/kh/books/` (Buch-Einstellungen pro Kochbuch: Modelle, Schemas, Service, Routen), `mealie/kh/duplicates/` (mögliche Doppelte und Entscheidungen), Migration `kh0004` in `mealie/kh/alembic/versions/`; Tests `tests/kh/books/`, `tests/kh/duplicates/`; Frontend `frontend/kh/app/lib/book.ts`, `lib/oven.ts`, `lib/duplicates.ts`, `lib/api/books.ts`, `composables/use-kh-book.ts`, `components/KhPrintBook.vue`, `KhBookEditor.vue`, `assets/kh-print.css`, Seiten `pages/g/[groupSlug]/kochbuch/[slug].vue`, `kochbuch/rezept/[slug].vue`, `doppelte.vue` | `CookbookPage.vue` (Knopf „Als Buch drucken“), `RecipePageInstructions.vue` (Umluft-Klammer), `controller_cookbooks.py`, `recipe_service.py`, `_all_models.py`, `alchemy_exporter.py` |
| Nährwerte, Allergene, Austausch (D44, Phase 6) | `mealie/kh/nutrition/` (BLS-Tabelle `data/`, Zuordnung, Gramm, Rechnung, Routen, `build_bls.py`), `mealie/kh/allergens/` (Regeln, Profil, Austausch, Service, Routen), Migration `kh0005`; Tests `tests/kh/nutrition/`, `tests/kh/allergens/`; Frontend `frontend/kh/app/lib/nutrition.ts`, `lib/api/nutrition.ts`, `lib/api/allergens.ts`, `composables/use-kh-allergens.ts`, `use-kh-can-edit.ts`, `components/KhNutrition.vue`, `KhFoodMapping.vue`, `KhAllergens.vue`, `KhAllergenMark.vue`, Seiten `pages/g/[groupSlug]/naehrwerte.vue`, `vertraeglichkeit.vue` | `RecipePage.vue`, `RecipeCard.vue`, `RecipeCardMobile.vue`, `foods.py`, `admin_management_users.py`, `admin_management_households.py`, `recipe_service.py`, `_all_models.py`, `alchemy_exporter.py` |
| Frontend-Texte | `frontend/kh/lang/en-US.json` und `de-DE.json` | über den Layer, Mealies Übersetzungsdateien bleiben unberührt |
| Betrieb (Phase 1) | `kh/ops/` (Backup-Container, `update.sh`, `restore.sh`, Compose-Ergänzungen) | eigene `docker-compose`-Datei neben `docker/docker-compose.yml` |
| Doku | `docs/kh/` | keine |

Das Python-Paket wird aus `mealie/` gebaut, darum liegt der Backend-Code unter `mealie/kh/` und nicht in einem eigenen Hauptordner.

## 6. Befunde und Entscheidungen

1. **Migrationen (D24).** Mealie führt beim Start `command.upgrade(alembic_cfg, "head")` aus (`mealie/db/init_db.py:119`) und kennt nur eine lineare Kette. Hängen wir unsere Migrationen in diese Kette, gibt es nach jedem Mealie-Update zwei Enden und jedes Mal eine Zusammenführung. Vorschlag: eigener Alembic-Zweig `kh` mit eigenem Ordner, beim Start `"heads"`. `db_is_at_head()` (`init_db.py:66`) vergleicht bereits Mengen von Enden und funktioniert damit.
2. **KI-Anbindung (D25, beschlossen, betrifft D6).** Mealie verwaltet KI-Anbieter in der Admin-Oberfläche und in der Datenbank, nicht über `.env`. Vorschlag: Phase 2 nutzt diese Verwaltung (Ollama auf dem Mac oder eigener Key dort eintragen) statt einer eigenen `.env`-Einstellung. D6 selbst (lokal zuerst, eigener Key) bleibt.
3. **Frontend als Nuxt-Layer (D26).** Mealies `nuxt.config.ts` nutzt noch keine Layers. Ein eigener Layer `frontend/kh/` hält unsere Seiten, Komponenten und Texte getrennt; Mealie braucht dafür nur eine `extends`-Zeile.
4. **Entfernen-Liste.** Stufe 1 ist beschlossen und umgesetzt (31.10.2026), siehe Abschnitt 4.

## 7. Bei jedem Upstream-Abgleich prüfen

- Neue Workflows in `.github/workflows/` deaktivieren (`.claude/CLAUDE.md`, Fork-Regeln).
- Alle `KH:`-Stellen auffindbar halten: `grep -rn "KH:" mealie frontend docker tests`.
- Neue Migrationen von Mealie hängen neben unserem `kh`-Zweig am selben Vorgänger; dann gibt es zwei Köpfe. Das ist erlaubt (D24): `init_db` baut alle Köpfe, und das Wiederherstellen baut jeden Kopf, den ein Backup verzeichnet. Der Test `test_kh_branch_on_mealies_newest_and_database_at_heads` schlägt dann absichtlich an. Ihn auf die neue Lage anpassen und danach Backup-Tests, Upgrade-Test und `restore_test.sh` laufen lassen.
- Geänderte Import-, Parser- oder Kochmodus-Dateien aus Abschnitt 3 gegen unsere Einhängepunkte prüfen.
