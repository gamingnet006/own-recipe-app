# Code-Rundgang: Mealie v3.29.0 als Basis für den Küchenhelfer

Ergebnis von Phase 0 (PLAN.md, Abschnitt 5). Stand 29.10.2026, Basis Mealie `v3.29.0` (Commit `89a1420`). Pfade relativ zum Repo-Hauptordner.

## 1. Aufbau

```text
mealie/                 Backend (FastAPI, Python 3.14)
  app.py                App-Start; hängt alle Router ein (api_routers(), Zeile ~154)
  routes/__init__.py    Sammel-Router /api: eine include_router-Zeile je Bereich
  routes/<bereich>/     Controller (HTTP), delegieren an services/
  services/             Fachlogik (Import, KI, Parser, Backups, Migrationen, Zeitplaner)
  repos/                Datenzugriff (AllRepositories, nach Gruppe/Haushalt gefiltert)
  schema/               Pydantic-Schemas; __init__.py werden von `task dev:generate` erzeugt
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
| KI-Anbieter | `services/openai/openai.py` + Admin-Route `routes/admin/admin_management_ai_providers.py` | Anbieter liegen pro Gruppe in der Datenbank (Standard- und Audio-Anbieter), nicht in `.env` |
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

**Entfernen (Stufe 1: nur ausblenden, Tabellen bleiben bis Phase 8):** Vorschlag, noch nicht beschlossen. Öffentliche „Explore“-Seiten und öffentliche Rezept-Links (Nicht-Ziel „öffentliche Rezeptdatenbank“, Leitplanke „Teilen-Links standardmäßig aus“) sowie Mealies „Ankündigungen“ mit Links zur Mealie-Doku. Alles Weitere entscheidet die Nutzung in Phase 1.

**Neu:** Entwurfstabelle und Prüfansicht, Duplikat-Warnung, Herkunfts-Badge (Phase 2) · Mengen-Nebentabelle, Plausibilität, Backform-Rechner (Phase 3) · Timer-Wege, Vosk-Sprachbefehle (Phase 4) · PDF-Kochbuch, Kurzbefehl-Token, Umluft und Menü-Zeitplan (Phase 5) · BLS-Nährwerte, Allergene, Familienprofil (Phase 6) · Telegram-Bot, Profile, Hardware-Test (Phase 7) · Erststart-Assistent, Systemprüfung (Phase 8) · Backup-Container, `update.sh`, Upgrade-Test (Phase 1).

## 5. Pfade für unsere `kh`-Ordner

| Teil | Pfad | Einhängung in Mealie (je eine `KH:`-markierte Stelle) |
|---|---|---|
| Backend-Code | `mealie/kh/<funktion>/` (Routen, Services, Modelle, Schemas je Funktion) | Router in `mealie/routes/__init__.py` (`router.include_router(kh.router)`) |
| Datenbank-Modelle | `mealie/kh/<funktion>/models.py` | Import in `mealie/db/models/_all_models.py` |
| Migrationen | `mealie/kh/alembic/versions/` als eigener Alembic-Zweig `kh` | `version_locations` in `mealie/alembic/alembic.ini` und `"head"` → `"heads"` in `mealie/db/init_db.py:119` (D24) |
| Backend-Tests | `tests/kh/<funktion>/` | keine (pytest findet `tests/` automatisch) |
| Frontend | `frontend/kh/` als Nuxt-Layer mit `components/`, `composables/`, `pages/` je Funktion | `extends: ["./kh"]` in `frontend/nuxt.config.ts` (D26) |
| Frontend-Texte | `frontend/kh/lang/en-US.json` und `de-DE.json` | über den Layer, Mealies Übersetzungsdateien bleiben unberührt |
| Betrieb (Phase 1) | `kh/ops/` (Backup-Container, `update.sh`, `restore.sh`, Compose-Ergänzungen) | eigene `docker-compose`-Datei neben `docker/docker-compose.yml` |
| Doku | `docs/kh/` | keine |

Das Python-Paket wird aus `mealie/` gebaut, darum liegt der Backend-Code unter `mealie/kh/` und nicht in einem eigenen Hauptordner.

## 6. Befunde und Entscheidungen

1. **Migrationen (D24).** Mealie führt beim Start `command.upgrade(alembic_cfg, "head")` aus (`mealie/db/init_db.py:119`) und kennt nur eine lineare Kette. Hängen wir unsere Migrationen in diese Kette, gibt es nach jedem Mealie-Update zwei Enden und jedes Mal eine Zusammenführung. Vorschlag: eigener Alembic-Zweig `kh` mit eigenem Ordner, beim Start `"heads"`. `db_is_at_head()` (`init_db.py:66`) vergleicht bereits Mengen von Enden und funktioniert damit.
2. **KI-Anbindung (D25, beschlossen, betrifft D6).** Mealie verwaltet KI-Anbieter in der Admin-Oberfläche und in der Datenbank, nicht über `.env`. Vorschlag: Phase 2 nutzt diese Verwaltung (Ollama auf dem Mac oder eigener Key dort eintragen) statt einer eigenen `.env`-Einstellung. D6 selbst (lokal zuerst, eigener Key) bleibt.
3. **Frontend als Nuxt-Layer (D26).** Mealies `nuxt.config.ts` nutzt noch keine Layers. Ein eigener Layer `frontend/kh/` hält unsere Seiten, Komponenten und Texte getrennt; Mealie braucht dafür nur eine `extends`-Zeile.
4. **Entfernen-Liste.** Die Vorschläge in Abschnitt 4 sind noch nicht beschlossen.

## 7. Bei jedem Upstream-Abgleich prüfen

- Neue Workflows in `.github/workflows/` deaktivieren (`.claude/CLAUDE.md`, Fork-Regeln).
- Alle `KH:`-Stellen auffindbar halten: `grep -rn "KH:" mealie frontend docker`.
- Neue Migrationen von Mealie: Dank D24 entstehen keine Konflikte mit unserem `kh`-Zweig.
- Geänderte Import-, Parser- oder Kochmodus-Dateien aus Abschnitt 3 gegen unsere Einhängepunkte prüfen.
