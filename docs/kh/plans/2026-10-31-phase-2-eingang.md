# Phase 2: Eingang, Prüfen, Duplikate (v0.1) · Umsetzungsplan

> **Für ausführende Agenten:** Pflicht-Skill: superpowers:subagent-driven-development (empfohlen) oder superpowers:executing-plans, Aufgabe für Aufgabe. Schritte nutzen Checkboxen (`- [ ]`).

**Ziel:** Rezepte aus Link, Text, Foto oder Screenshot werden zu Entwürfen, die jeder im Haushalt prüft und übernimmt; nichts kommt ohne Freigabe ins Kochbuch, mögliche Duplikate werden gemeldet.

**Architektur:** Eine eigene Funktion `mealie/kh/drafts/` (Tabelle `kh_drafts`, Dienst, Routen unter `/api/kh`), die für das Erkennen Mealies Bausteine aufruft: `create_from_html` für Links, `AIRecipeService.build_recipe` für Text, Bilder und Links ohne Rezeptdaten. Beide liefern ein Rezept, ohne es zu speichern; das Übernehmen speichert es mit `RecipeService.create_one`. Das Frontend kommt als Seiten und Bausteine im Nuxt-Layer `frontend/kh/`, mit kleinen markierten Eingriffen in Mealies Seitenleiste und Rezeptansicht.

**Technik:** FastAPI, SQLAlchemy, Alembic (eigener Zweig `kh`), Pydantic, Pillow mit `pillow-heif` (beides schon in Mealie), Nuxt 4 mit Vue 3 und Vuetify, Vitest, pytest.

**Spezifikation:** `docs/kh/specs/2026-10-31-phase-2-eingang-design.md`

## Feste Vorgaben

- Code, Bezeichner und Kommentare englisch; Texte für Menschen nur im Frontend, über `frontend/kh/lang/en-US.json` und `de-DE.json`. Das Backend liefert Codes, keine Sätze.
- Jede neue Datei beginnt mit 1 bis 3 Zeilen Zweck, jede Funktion hat eine Kurzbeschreibung (was und warum). Kein toter Code, keine Platzhalter.
- Jede Änderung an einer Mealie-Datei trägt einen Kommentar `KH: <Grund>`; erzeugte Dateien (`frontend/app/lib/api/types/`) bleiben unberührt.
- Datenbank nur über die additive Migration im Zweig `kh` (D24).
- KI in Tests nur mit aufgezeichneten Antworten: `AIRecipeService.build_recipe` wird in Tests durch eine Funktion ersetzt, die ein selbst geschriebenes Rezept aus `tests/kh/drafts/data/` liefert oder eine vorgegebene Ausnahme wirft (D23). Testdaten nur selbst geschrieben (Regel 9).
- Stand eines Entwurfs: `working`, `ready`, `failed`, `approved`. Quelle: `link`, `text`, `image`.
- Das erkannte Rezept liegt in `recipe` in camelCase wie Mealies Schnittstelle (`recipe.model_dump(mode="json", by_alias=True)`). `Recipe.model_validate(draft.recipe)` liest es zurück, denn Mealies Modelle nehmen beide Schreibweisen an.
- Fehler-Codes (`DraftError`): `no_recipe_data`, `ai_not_configured`, `quota_exceeded`, `address_blocked`, `invalid_result`, `interrupted`, `unknown`. Zuordnung:
  - `mealie.core.exceptions.RateLimitError` → `quota_exceeded`
  - `mealie.services.openai.openai.OpenAINotEnabledException`, `mealie.services.recipe.ai_recipe_service.AIProviderNotEnabledError` → `ai_not_configured`
  - `mealie.services.recipe.import_workflow.exceptions.NoRecipeDataError`, `HTTPException` mit Status 400 aus `create_from_html` → `no_recipe_data`
  - `mealie.pkgs.safehttp.transport.InvalidDomainError` → `address_blocked`
  - `pydantic.ValidationError` → `invalid_result`; alles andere → `unknown` (mit `logger.exception`)
  - Link ohne Rezeptdaten und ohne eingerichtete KI → `no_recipe_data`
- Einstellungen: neue Felder in `KhSettings` (`mealie/kh/features/settings.py`, Umgebung `KH_…`), mit `env_ignore_empty=True`, damit leer durchgereichte Werte die Vorgaben im Code behalten:
  `draft_max_images=5`, `draft_max_image_mb=20`, `draft_max_text=20000`, `draft_stale_minutes=15`, `duplicate_title=0.85`, `duplicate_ingredients=0.7`, `duplicate_title_with_ingredients=0.5`.
- Originale: `<DATA_DIR>/kh/drafts/<draft_id>/original-<n>.webp`, `n` ab 1, Pillow `thumbnail((2048, 2048))`, WebP-Qualität 80. HEIC öffnet Pillow, sobald `mealie.pkgs.img.minify` importiert ist (dort `register_heif_opener()`).
- Schnittstelle (Präfix `/api/kh`): `POST /drafts`, `GET /drafts`, `GET /drafts/{id}`, `GET /drafts/{id}/originals/{n}`, `POST /drafts/{id}/retry`, `POST /drafts/{id}/approve`, `DELETE /drafts/{id}`, `GET /recipes/{recipe_id}/origin`.
- Antworten bei Konflikten: 409 mit `{"code": "<code>", …}`; Codes `not_ready`, `already_approved` (mit `slug`), `still_working`, `not_failed`, `duplicates` (mit `warnings`).
- Befehle (aus dem Repo-Hauptordner). Der Name `kh-uv-venv` hält die Python-Umgebung zwischen den Läufen:
  - Backend-Tests einer Aufgabe:
    ```bash
    docker run --rm -v "$PWD":/app -w /app -v kh-uv-venv:/venv -e UV_PROJECT_ENVIRONMENT=/venv -e UV_LINK_MODE=copy ghcr.io/astral-sh/uv:python3.14-bookworm-slim sh -c "apt-get update -qq && apt-get install -qq -y --no-install-recommends build-essential libsasl2-dev libldap2-dev libssl-dev >/dev/null && uv sync --frozen --quiet && uv run --frozen pytest tests/kh -q -p no:cacheprovider"
    ```
  - Lint im selben Container: `uv run --frozen ruff check mealie/kh tests/kh && uv run --frozen ruff format --check mealie/kh tests/kh` statt `pytest …`.
  - Ganzes Backend und Frontend: die Befehle aus `.claude/CLAUDE.md` (Abschnitt „Befehle“); Frontend-Lint dort mit `pnpm lint` statt `pnpm test:ci`.

## Review-Schwerpunkte

1. **Haushalts-Grenze an jedem Endpunkt**, auch an Originalbild und Herkunft: Ein Nutzer aus einem anderen Haushalt (`h2_user`) und einer anderen Gruppe (`g2_user`) bekommt 404. Tests in Task 2 und 3.
2. **Aufräumen löscht nie ein echtes Rezept:** Der Erkennungsordner zur `recipe.id` des Entwurfs wird nur gelöscht, wenn es kein Rezept mit dieser ID gibt. Test in Task 3.
3. **Hintergrund mit eigener Sitzung:** Die Erkennung öffnet ihre Datenbank-Sitzung mit `session_context()`; ein hängender Entwurf wird nach `draft_stale_minutes` zu `failed`/`interrupted`. Tests in Task 2.
4. **Gleichzeitiges Übernehmen:** Der Wechsel auf `approved` ist eine bedingte Änderung (`WHERE status = 'ready'`); der zweite Versuch bekommt 409 `already_approved`. Test in Task 3.
5. **Hochladen prüft den Inhalt, nicht den Namen:** Text mit Endung `.jpg` wird abgelehnt, HEIC angenommen, zu große Bilder und zu viele Bilder abgelehnt, ohne dass ein Entwurf entsteht. Tests in Task 2.

---

### Task 1: Einstellungen, Tabelle, Migration, Schemas

**Dateien:**
- Ändern: `mealie/kh/features/settings.py` (neue Felder, `env_ignore_empty=True`)
- Neu: `mealie/kh/drafts/__init__.py`, `mealie/kh/drafts/models.py`, `mealie/kh/drafts/schemas.py`, `mealie/kh/drafts/repository.py`
- Ändern: `mealie/db/models/_all_models.py` (Import, `KH:`), `mealie/alembic/alembic.ini` (`version_locations`, `KH:`), `mealie/db/init_db.py:119` (`"head"` → `"heads"`, `KH:`)
- Neu: `mealie/kh/alembic/versions/2026-11-01-00.00.00_kh0001_add_kh_drafts.py`
- Neu: `tests/kh/drafts/__init__.py`, `tests/kh/drafts/test_kh_drafts_model.py`
- Ändern: `docs/kh/specs/2026-10-31-phase-2-eingang-design.md` (Bausteine: Einstellungen in `KhSettings` statt `drafts/settings.py`)

**Schnittstellen:**
- Liefert:
  - `KhDraft` (Tabelle `kh_drafts`): `id` GUID; `group_id`, `household_id`, `user_id` (Fremdschlüssel); `status`, `source_type`, `source_url`, `source_url_normalized` (Index), `source_text`; `original_files` JSON (Liste); `recipe` JSON; `warnings` JSON (Liste); `error`, `ai_model`; `recipe_id` (Fremdschlüssel `recipes.id`, `ondelete="CASCADE"`, eindeutig); `approved_by`, `approved_at`. Dazu `created_at` und `update_at` aus `SqlAlchemyBase`, die Beziehung `user` und die Eigenschaft `user_name` (`user.full_name`), aus der `DraftOut.user_name` liest.
  - In `schemas.py`: `DraftStatus`, `DraftSource`, `DraftError` (StrEnum); `DraftWarning(kind: Literal["duplicate_link", "similar_title", "similar_ingredients"], name: str, recipe_slug: str | None, draft_id: UUID4 | None)`; `DraftOut` (alle Spalten plus `user_name`, `from_attributes`); `OriginOut(draft_id, source_type, source_url, user_name, created_at, ai_model, original_count)`; `ApproveIn(force: bool = False)`; `ApproveOut(slug: str)`.
  - In `repository.py`: `drafts_repo(session, group_id, household_id) -> HouseholdRepositoryGeneric[DraftOut, KhDraft]`. Mit `group_id=None, household_id=None` ist der Zugriff ungefiltert, nur für das Aufräumen.

- [ ] **Schritt 1: Tests schreiben**

```python
def test_settings_defaults_and_override(monkeypatch):
    assert KhSettings().draft_max_images == 5 and KhSettings().duplicate_title == 0.85
    monkeypatch.setenv("KH_DRAFT_MAX_IMAGES", "2")
    assert KhSettings().draft_max_images == 2
    monkeypatch.setenv("KH_DRAFT_MAX_IMAGES", "")  # compose passes unset values as empty
    assert KhSettings().draft_max_images == 5


def test_table_exists_with_columns(session):
    columns = {c["name"] for c in sa.inspect(session.get_bind()).get_columns("kh_drafts")}
    assert {"status", "source_type", "recipe", "warnings", "recipe_id", "approved_by"} <= columns


def test_two_heads_and_database_at_heads():
    script = ScriptDirectory.from_config(alembic_config())  # Mealie's config, see init_db.py
    assert len(script.get_heads()) == 2 and "kh0001" in script.get_heads()
    assert db_is_at_head(alembic_config())


def test_repo_is_scoped_to_household(session, unique_user, h2_user):
    mine = drafts_repo(session, unique_user.group_id, unique_user.household_id)
    theirs = drafts_repo(session, h2_user.group_id, h2_user.household_id)
    draft = mine.create(
        {
            "user_id": unique_user.user_id,
            "status": "ready",
            "source_type": "text",
            "source_text": "x",
            "group_id": unique_user.group_id,
            "household_id": unique_user.household_id,
        }
    )
    assert mine.get_one(draft.id) and theirs.get_one(draft.id) is None
    assert draft.user_name == unique_user.full_name
```

- [ ] **Schritt 2: Tests laufen lassen**, Befehl „Backend-Tests einer Aufgabe“. Erwartet: FAIL (Import `mealie.kh.drafts` fehlt, Tabelle fehlt).
- [ ] **Schritt 3: Umsetzen.**
  - Einstellungen erweitern. Modell nach dem Muster von `mealie/db/models/group/ai_providers.py` (`SqlAlchemyBase, BaseMixins`, `GUID`, `@auto_init()`), `id` als GUID mit `default=GUID.generate`.
  - Migration: `revision = "kh0001"`, `down_revision = "1e69ea7cd45e"` (Mealies neueste am 31.10.2026), `branch_labels = ("kh",)`; `create_table` mit allen Spalten und Indizes, `downgrade` löscht die Tabelle.
  - `alembic.ini`: `version_locations = %(here)s/versions:%(here)s/../kh/alembic/versions` (Trenner `os`). `init_db.py:119`: `command.upgrade(alembic_cfg, "heads")`.
- [ ] **Schritt 4: Tests laufen lassen.** Erwartet: PASS. Außerdem `tests/unit_tests/test_alembic.py` grün; er prüft nur `mealie/alembic/versions`.
- [ ] **Schritt 5: Commit** `Drafts: kh_drafts table on the kh migration branch, settings and schemas`

### Task 2: Eingang und Erkennung im Hintergrund

**Dateien:**
- Neu: `mealie/kh/drafts/files.py`, `mealie/kh/drafts/recognize.py`, `mealie/kh/drafts/service.py`, `mealie/kh/drafts/routes.py`
- Ändern: `mealie/kh/__init__.py` (Router einhängen)
- Neu: `tests/kh/drafts/conftest.py`, `tests/kh/drafts/test_kh_drafts_intake.py`
- Neu, selbst geschrieben: `tests/kh/drafts/data/recipe.json` (Rezept „Testkuchen“ im `Recipe`-Schema, 4 Zutaten, 3 Schritte), `tests/kh/drafts/data/page.html` (Seite mit JSON-LD für „Testkuchen“, ohne Bildadresse, damit kein Download nötig ist)

**Schnittstellen:**
- Verbraucht: alles aus Task 1.
- Liefert:
  - `files.py`:
    - `drafts_root() -> Path`, `draft_dir(draft_id) -> Path`
    - `save_original(draft_id, n: int, data: bytes, max_mb: int) -> str`: wirft `ValueError("not_an_image")` oder `ValueError("too_large")`
    - `original_path(draft_id, name) -> Path`
  - `recognize.py`: `async def recognize(draft_id: UUID4, *, user: PrivateUser, household: HouseholdInDB, translator: Translator) -> None` (eigene Sitzung) und `error_code(ex: Exception) -> DraftError`.
  - `service.py`: `DraftService(session: Session, user: PrivateUser, household: HouseholdInDB, translator: Translator)` mit `create(url: str | None, text: str | None, images: list[UploadFile]) -> DraftOut`, `list_open() -> list[DraftOut]`, `get(draft_id) -> DraftOut` (wirft 404), `retry(draft_id) -> DraftOut`, `mark_stale() -> None`.
  - `routes.py`: `router = APIRouter(prefix="/drafts")`, Klasse `KhDraftsController(BaseUserController)` mit `@controller(router)`.
  - In `tests/kh/drafts/conftest.py` die Fixtures `fake_ai` und `fake_page`:
    - `fake_ai(result="recipe.json" | Exception)` ersetzt `AIRecipeService.build_recipe` und hält die übergebenen Argumente fest.
    - `fake_page(html="page.html" | None)` ersetzt `mealie.kh.drafts.recognize.create_from_html` durch einen Aufruf des echten `create_from_html` mit gespeichertem HTML. Bei `None` wirft es `HTTPException(400)`.

- [ ] **Schritt 1: Tests schreiben** (Auswahl der Zusicherungen; Starlettes `TestClient` führt Hintergrundaufgaben vor der Antwort aus)

```python
def test_link_with_recipe_data_needs_no_ai(api_client, unique_user, fake_page, fake_ai):
    fake_page("page.html"); calls = fake_ai("recipe.json")
    draft = api_client.post("/api/kh/drafts", data={"url": "https://example.org/testkuchen"}, headers=unique_user.token)
    assert draft.status_code == 201 and draft.json()["status"] == "working"
    ready = api_client.get(f"/api/kh/drafts/{draft.json()['id']}", headers=unique_user.token).json()
    assert ready["status"] == "ready" and ready["recipe"]["name"] == "Testkuchen" and ready["aiModel"] is None
    assert calls == []

def test_link_without_recipe_data_falls_back_to_ai(...): fake_page(None) -> status "ready", one AI call with url
def test_text_uses_ai(...): data={"text": "Testkuchen: 200 g Mehl ..."} -> "ready", AI call with content
def test_image_is_stored_as_webp(...): one 3000x2000 PNG -> original-1.webp exists, WEBP, max(size) == 2048,
    AI call got exactly one image path
def test_heic_is_accepted(...): HEIC written with pillow_heif -> 201
@pytest.mark.parametrize("files,form", [
    ([("images", ("x.jpg", b"not an image", "image/jpeg"))], {}),        # content, not name
    ([("images", png(10, 10))] * 6, {}),                                   # more than draft_max_images
    ([], {}),                                                              # no source
    ([], {"url": "https://example.org", "text": "x"}),                    # two sources
    ([], {"text": "x" * 20001}),                                           # longer than draft_max_text
])
def test_rejected_input_creates_no_draft(files, form, ...): status 400 and list stays empty
def test_too_large_image(monkeypatch, ...): draft_max_image_mb patched to 1, 2 MB image -> 400
@pytest.mark.parametrize("exc,code", [(RateLimitError(), "quota_exceeded"), (OpenAINotEnabledException(), "ai_not_configured"),
    (AIProviderNotEnabledError(), "ai_not_configured"), (NoRecipeDataError(), "no_recipe_data"),
    (InvalidDomainError("x"), "address_blocked"), (RuntimeError("x"), "unknown")])
def test_failure_codes(exc, code, ...): text draft -> "failed" with error == code
def test_link_without_data_and_without_ai(...): fake_page(None), fake_ai(OpenAINotEnabledException()) -> "no_recipe_data"
def test_retry_turns_failed_into_ready(...); test_retry_needs_failed(...): 409 {"code": "not_failed"}
def test_stale_working_draft_is_interrupted(session, ...): row "working", update_at 20 minutes ago -> GET -> "failed"/"interrupted"
def test_other_household_and_group_see_nothing(h2_user, g2_user, ...): list without the draft, GET -> 404
```

- [ ] **Schritt 2: Tests laufen lassen.** Erwartet: FAIL (404 auf `/api/kh/drafts`).
- [ ] **Schritt 3: Umsetzen.**
  - **`create`:** prüft genau eine Quelle und alle Grenzen, ehe etwas gespeichert wird. Dann legt es den Eintrag `working` an, speichert die Originale (bei einem Fehler darin werden Eintrag und Ordner gelöscht, Antwort 400) und gibt `DraftOut` zurück. Die Route hängt `recognize` an `BackgroundTasks`.
  - **`recognize`:**
    - öffnet `session_context()`, baut `get_repositories(session, group_id=…, household_id=…)` und lädt den Entwurf.
    - `link`: erst `create_from_html(url, repos, translator)`, bei `HTTPException` mit Status 400 dann `AIRecipeService(repos, user, household, translator=translator).build_recipe(url=url)`.
    - `text` und `image`: gleich `build_recipe(content=…)` bzw. `build_recipe(images=[original_path(…)])`.
    - Erfolg: `recipe.model_dump(mode="json")`, `status=ready`, `ai_model` gefüllt nur bei KI. Woher Name und Modell kommen, zeigt `AIRecipeService._validate_providers`; gespeichert wird `"<name> (<model>)"`.
    - Fehler: `status=failed`, `error=error_code(ex)`.
  - **`mark_stale`** läuft am Anfang von `list_open` und `get`.
- [ ] **Schritt 4: Tests und Lint laufen lassen.** Erwartet: PASS, Ruff ohne Meldungen.
- [ ] **Schritt 5: Commit** `Drafts: intake for links, text and images, recognized in the background`

### Task 3: Übernehmen, Verwerfen, Herkunft, Aufräumen

**Dateien:**
- Ändern: `mealie/kh/drafts/files.py`, `service.py`, `routes.py`, `mealie/kh/__init__.py` (Router `/recipes` für die Herkunft)
- Ändern: `mealie/app.py` (`SchedulerRegistry.register_daily(…, sweep_orphans)`, `KH:`)
- Neu: `tests/kh/drafts/test_kh_drafts_approve.py`

**Schnittstellen:**
- Verbraucht: Tasks 1 und 2.
- Liefert:
  - `files.py`: `remove_draft_dir(draft_id) -> None`, `remove_recognition_dir(recipe_id, repos) -> None` (nur ohne Rezept mit dieser ID), `sweep_orphans() -> None` (eigene Sitzung, ungefiltertes Repository)
  - `DraftService`: `approve(draft_id, force: bool) -> ApproveOut`, `discard(draft_id) -> None`, `origin(recipe_id) -> OriginOut`
  - Routen: `POST /drafts/{id}/approve`, `DELETE /drafts/{id}` (204), `GET /drafts/{id}/originals/{n}` (`FileResponse`, `image/webp`), `GET /recipes/{recipe_id}/origin`

- [ ] **Schritt 1: Tests schreiben**

```python
def test_approve_saves_recipe_with_recognized_id(...):
    slug = approve(draft)["slug"]
    recipe = api_client.get(f"/api/recipes/{slug}", headers=unique_user.token).json()
    assert recipe["id"] == draft["recipe"]["id"]
    after = get(draft)
    assert after["status"] == "approved" and after["recipeId"] == recipe["id"] and after["approvedBy"] == str(unique_user.user_id)
def test_approve_image_draft_uses_first_original_as_cover(...): RecipeDataService(id).dir_image / "original.webp" exists
def test_anyone_in_household_may_approve(unique_user, ...): second user in the same household approves -> 200
def test_second_approve_conflicts(...): 409 {"code": "already_approved", "slug": slug}
def test_approve_needs_ready(...): working -> 409 {"code": "not_ready"}
def test_list_hides_approved(...)
def test_discard_removes_row_originals_and_recognition_dir(...): DELETE -> 204, draft dir and DATA_DIR/recipes/<id> gone
def test_discard_keeps_folder_of_existing_recipe(...): recognition id equals a saved recipe's id -> folder stays
def test_discard_needs_ready_or_failed(...): working -> 409 "still_working"; approved -> 409 "already_approved"
def test_original_is_served_only_to_household(h2_user, ...): 200 image/webp for owner, 404 for h2_user, 404 for n out of range
def test_origin(...): approved draft -> sourceType, userName, createdAt; recipe without draft -> 404
def test_retry_removes_old_recognition_dir(...): failed draft with recipe id X and folder DATA_DIR/recipes/X -> retry -> folder X gone
def test_deleting_recipe_drops_origin_and_sweep_removes_folder(...): DELETE recipe -> row gone; sweep_orphans() -> dir gone
def test_sweep_keeps_folders_with_rows(...)
```

- [ ] **Schritt 2: Tests laufen lassen.** Erwartet: FAIL (404 bzw. 405 auf den neuen Routen).
- [ ] **Schritt 3: Umsetzen.**
  - **Übernehmen:** Die Statusänderung läuft als `update(KhDraft).where(id == …, status == "ready")` mit `approved_by` und `approved_at`. Bei Zeilenzahl 0 kommt 409 mit dem passenden Code.
  - **Speichern:** über `RecipeService(repos, user, household, translator).create_one(Recipe.model_validate(draft.recipe))`. Bei `image` schreibt `RecipeDataService(recipe.id).write_image(<erstes Original>, "webp")` das Titelbild, wie Mealies `create_from_ai`. Danach wird `recipe_id` gesetzt. Scheitert das Speichern, geht der Stand zurück auf `ready`, und der Fehler wird gemeldet.
  - **Verwerfen** prüft den Stand, ruft dann `remove_recognition_dir`, `remove_draft_dir` und löscht den Eintrag.
  - **„Neu versuchen“** aus Task 2 ruft vor dem Neustart `remove_recognition_dir` für die `recipe.id` des alten Ergebnisses.
- [ ] **Schritt 4: Tests, Lint und Mealies Rezept-Tests laufen lassen** (`pytest tests/kh tests/integration_tests/user_recipe_tests -q`). Erwartet: PASS.
- [ ] **Schritt 5: Commit** `Drafts: approve into Mealie, discard, origin and cleanup`

### Task 4: Duplikat-Prüfung

**Dateien:**
- Neu: `mealie/kh/drafts/duplicates.py`, `tests/kh/drafts/test_kh_drafts_duplicates.py`
- Ändern: `mealie/kh/drafts/recognize.py` (Hinweise bei `ready`), `service.py` (erneute Prüfung beim Übernehmen)

**Schnittstellen:**
- Verbraucht: `DraftWarning`, `KhSettings`, `DraftService.approve`.
- Liefert:
  - `normalize_url(url: str) -> str`, `title_key(title: str) -> str`, `title_similarity(a: str, b: str) -> float`
  - `ingredient_names(recipe: dict) -> set[str]`, `ingredient_overlap(a: set[str], b: set[str]) -> float`
  - `Candidate(kind: Literal["recipe", "draft"], name: str, url: str | None, ingredients: set[str], recipe_slug: str | None, draft_id: UUID4 | None)`
  - `candidates(repos, exclude_draft: UUID4) -> list[Candidate]`
  - `find_duplicates(recipe: dict, url: str | None, candidates: list[Candidate], settings: KhSettings) -> list[DraftWarning]`

- [ ] **Schritt 1: Tests schreiben**

```python
def test_normalize_url():
    assert normalize_url("HTTP://www.Example.org/rezept/testkuchen/?utm_source=x&b=2&a=1#oben") == "https://example.org/rezept/testkuchen?a=1&b=2"
    assert normalize_url("https://www.instagram.com/p/ABC123/?igsh=xyz") == "https://instagram.com/p/ABC123"
def test_title_similarity():
    assert title_similarity("Omas Apfelkuchen", "Apfelkuchen nach Oma") >= 0.85
    assert title_similarity("Apfel-Kuchen!", "apfel kuchen") >= 0.85
    assert title_similarity("Apfelkuchen", "Linsensuppe") < 0.5
def test_ingredient_names():
    assert ingredient_names({"recipeIngredient": [{"note": "200 g Mehl"}, {"note": "3 Eier"}, {"note": "1 Prise Salz"}]}) == {"mehl", "eier", "salz"}
def test_find_duplicates_kinds():  # one candidate each: same link, similar title, same ingredients plus similar title
    assert [w.kind for w in find_duplicates(...)] == ["duplicate_link", "similar_title", "similar_ingredients"]
def test_same_ingredients_other_dish_is_no_duplicate():  # "Pfannkuchen" vs "Waffeln", same 5 ingredients
    assert find_duplicates(...) == []
def test_second_draft_with_same_link_warns(...): warnings[0].kind == "duplicate_link", draftId == first draft
def test_approve_with_new_duplicate_needs_force(...): 409 {"code": "duplicates", "warnings": [...]}, force=true -> 200
```

- [ ] **Schritt 2: Tests laufen lassen.** Erwartet: FAIL (`mealie.kh.drafts.duplicates` fehlt).
- [ ] **Schritt 3: Umsetzen.**
  - **Link:** `normalize_url` macht aus `http` `https`, schreibt den Host klein und ohne `www.`, entfernt Sprungmarke und Parameter aus `{utm_*, fbclid, gclid, igshid, igsh, si, ref}`, sortiert die übrigen Parameter und nimmt den Schrägstrich am Ende weg.
  - **Titel:** `title_key` faltet die Groß- und Kleinschreibung, entfernt Satzzeichen und Füllwörter aus einer festen Liste (`nach, von, vom, mit, und, a, la, der, die, das, ein, eine, mein, meine`), streicht ein `s` am Wortende bei Wörtern über drei Buchstaben und sortiert die Wörter. Die Ähnlichkeit kommt aus `difflib.SequenceMatcher`.
  - **Zutaten:** `ingredient_names` nimmt `food.name` oder `note`, ohne Ziffern und ohne Einheiten aus einer festen Liste (`g, kg, mg, ml, l, el, tl, prise, stück, packung, becher, tasse, cup, tbsp, tsp`). Die Überschneidung ist das Jaccard-Maß.
  - **Ein Hinweis je Kandidat**, der stärkste zählt. Bei der Prüfung beim Übernehmen zählen nur Treffer, die beim Erkennen noch nicht da waren.
  - Ein `ponytail:`-Kommentar vermerkt den linearen Vergleich mit Ausbaupfad.
- [ ] **Schritt 4: Tests und Lint laufen lassen.** Erwartet: PASS.
- [ ] **Schritt 5: Commit** `Drafts: duplicate check by link, title and ingredients`

### Task 5: Frontend-Grundlage (Schnittstelle, Texte, Umleitung, Menü, Abzeichen)

**Dateien:**
- Ändern: `frontend/kh/nuxt.config.ts` (`i18n: { langDir: "./../lang", locales: [{ code: "en-US", file: "en-US.json" }, { code: "de-DE", file: "de-DE.json" }] }`; Codes wie in `frontend/nuxt.config.ts`)
- Neu: `frontend/kh/lang/en-US.json`, `frontend/kh/lang/de-DE.json` (Schlüssel unter `kh.drafts.*`, auch die Fehler-Codes und Hinweise)
- Neu: `frontend/kh/app/lib/api/drafts.ts` (Typen `KhDraft`, `KhDraftWarning`, `KhOrigin`; Klasse `KhDraftsApi extends BaseAPI`)
- Neu: `frontend/kh/app/composables/use-kh-drafts.ts`, `frontend/kh/app/middleware/kh-import-redirect.global.ts`, `frontend/kh/app/components/KhOriginBadge.vue`
- Ändern: `frontend/app/components/Layout/DefaultLayout.vue` (`KH:`): In `createLinks` werden „Import“ und „Mit KI importieren“ zu einem Eintrag „Rezept hinzufügen“ auf `/g/<slug>/drafts/new`; in `topLinks` kommt „Entwürfe (n)“ hinter „Rezepte“ dazu.
- Ändern: `frontend/app/components/Domain/Recipe/RecipePage/RecipePage.vue` (`KH:`): `<KhOriginBadge v-if="!isEditMode" :recipe-id="recipe.id" />` unter `RecipePageHeader`
- Neu: `frontend/kh/app/__tests__/kh-drafts.test.ts`

**Schnittstellen:**
- Verbraucht: die Schnittstelle aus Tasks 2 bis 4 (camelCase-Antworten).
- Liefert:
  - `useKhDraftsApi(): KhDraftsApi` mit `create(form: FormData)`, `list()`, `get(id)`, `retry(id)`, `approve(id, force)`, `discard(id)`, `origin(recipeId)`, `originalUrl(id, n): string`
  - `useKhDraftCount(): { count: Ref<number>, refresh(): Promise<void> }` (gemeinsamer Zustand)
  - `importRedirectTarget(path: string): string | null`
  - `reviewLayout(width: number): "stacked" | "side"`, ab 768 Pixel `"side"`
  - `errorText(code: string, t): string`

- [ ] **Schritt 1: Tests schreiben**

```ts
for (const page of ["url", "ai", "image", "html", "bulk"]) {
  expect(importRedirectTarget(`/g/familie/r/create/${page}`)).toBe("/g/familie/drafts/new");
}
expect(importRedirectTarget("/g/familie/r/create/ai/")).toBe("/g/familie/drafts/new");
expect(importRedirectTarget("/g/familie/r/create/new")).toBeNull();      // typing it yourself stays
expect(importRedirectTarget("/g/familie/r/create/zip")).toBeNull();
expect(reviewLayout(390)).toBe("stacked"); expect(reviewLayout(820)).toBe("side");
expect(errorText("quota_exceeded", t)).toBe(t("kh.drafts.error.quota_exceeded"));
expect(errorText("something_new", t)).toBe(t("kh.drafts.error.unknown"));
```

- [ ] **Schritt 2: Tests laufen lassen** (Frontend-Befehl). Erwartet: FAIL (Module fehlen).
- [ ] **Schritt 3: Umsetzen.**
  - Die Schnittstellenklasse nach dem Muster der Mealie-Klassen auf `BaseAPI`, mit `useRequests()`.
  - Die Logik steckt in reinen Funktionen, damit sie testbar ist.
  - Das Abzeichen zeigt nichts, wenn `origin` 404 liefert. Sonst: „Aus Foto/Link/Text · Datum · Name“ und den Knopf „Original ansehen“ (öffnet den Entwurf).
- [ ] **Schritt 4: Tests und Lint laufen lassen.** Erwartet: PASS, ESLint ohne Meldungen.
- [ ] **Schritt 5: Commit** `Drafts UI: API client, texts, import redirect, menu entry and origin badge`

### Task 6: Eingang, Entwurfsliste, Prüfansicht

**Dateien:**
- Neu: `frontend/kh/app/pages/g/[groupSlug]/drafts/new.vue`, `index.vue`, `[id].vue`
- Neu: `frontend/kh/app/components/KhDraftReview.vue`, `KhDraftWarnings.vue`, `KhDraftOriginal.vue`
- Ändern: `frontend/kh/app/__tests__/kh-drafts.test.ts`

**Schnittstellen:**
- Verbraucht: alles aus Task 5.
- Liefert: die drei Seiten.
- Logik in reinen Funktionen:
  - `draftTitle(d: KhDraft): string`, Rezeptname oder Link oder Textanfang
  - `pollingNeeded(list: KhDraft[]): boolean`
  - `approveTarget(slug, groupSlug, edit: boolean): string`, ergibt `/g/<gruppe>/r/<slug>` bzw. `…?edit=true`

- [ ] **Schritt 1: Tests schreiben**

```ts
expect(draftTitle({ recipe: { name: "Testkuchen" } } as KhDraft)).toBe("Testkuchen");
expect(draftTitle({ recipe: null, sourceUrl: "https://example.org/x" } as KhDraft)).toBe("example.org/x");
expect(pollingNeeded([{ status: "ready" }, { status: "working" }] as KhDraft[])).toBe(true);
expect(approveTarget("testkuchen", "familie", true)).toBe("/g/familie/r/testkuchen?edit=true");
```

- [ ] **Schritt 2: Tests laufen lassen.** Erwartet: FAIL.
- [ ] **Schritt 3: Umsetzen.**
  - **Eingang:** drei große Knöpfe für Link, Text und Foto/Screenshot. Bilder kommen über `<input type="file" accept="image/*" multiple>`, ohne `capture`, damit iOS Kamera und Mediathek anbietet. Nach dem Absenden geht es zur Liste.
  - **Liste:** Titel, Vorschaubild (erstes Original oder Quelle), Name, Zeit, Stand. Solange `pollingNeeded` gilt, wird alle 3 Sekunden neu geladen, beim Verlassen der Seite nicht mehr. Bei `failed` steht der Fehlertext dabei, mit „Neu versuchen“.
  - **Prüfansicht:**
    - oben die Hinweise mit Link zum Rezept oder Entwurf
    - darunter `KhDraftOriginal`: Bilder, Text oder Link
    - dann das Ergebnis: Name, Portionen, Zeiten, Zutaten, Schritte über Mealies `SafeMarkdown`; Inhalte aus dem Entwurf nie über `v-html`
    - Anordnung nach `reviewLayout`
    - Übernehmen: bei 409 `duplicates` ein Dialog mit „Trotzdem übernehmen“ (`force`); bei 409 `already_approved` geht es zum Rezept.
    - Verwerfen mit Rückfrage.
    - Nach jeder Änderung wird der Zähler neu geladen.
- [ ] **Schritt 4: Tests und Lint laufen lassen.** Dann auf dem MacBook von Hand prüfen: `docker compose -f kh/ops/docker-compose.yml up -d --build`, im Browser in Handy- und iPad-Breite. Erwartet: PASS; alle drei Seiten in beiden Breiten bedienbar.
- [ ] **Schritt 5: Commit** `Drafts UI: intake, list and review for phone and iPad`

### Task 7: Betrieb, Anleitung, Probelauf

**Dateien:**
- Ändern: `kh/ops/docker-compose.yml` (die sieben `KH_DRAFT_*`/`KH_DUPLICATE_*` als `${…:-}` an `mealie`), `kh/ops/.env.example` (auskommentierte Zeilen mit den Vorgaben)
- Ändern: `docs/kh/README.md` (Deutsch und Englisch):
  - „Rezept hinzufügen“
  - „KI einrichten (Gemini)“: Schlüssel in Google AI Studio anlegen, in Küchenhelfer unter Verwaltung → KI-Anbieter eintragen (Adresse `https://generativelanguage.googleapis.com/v1beta/openai/`, das Modell gerade aus AI Studio), dort testen; kein Bezahlkonto anlegen
  - Tabelle „Was geht wohin“ mit allen heute aktiven Wegen
  - „Stick verloren“ um den KI-Schlüssel ergänzt
- Ändern: `docs/kh/THIRD_PARTY_NOTICES.md` (Google Gemini als genutzter Dienst neben Cloudflare), `docs/kh/CHANGELOG.md` (Abschnitt `[Unreleased]`), `PLAN.md` und `PLAN.en.md` (Phase-2-Punkte abhaken), `.claude/CLAUDE.md` und `docs/kh/CLAUDE.en.md` (Befehle, falls neu)

- [ ] **Schritt 1:** Compose-Weitergabe prüfen. `docker compose -f kh/ops/docker-compose.yml config | grep KH_DRAFT_MAX_IMAGES` zeigt `""`; ein laufendes Mealie liefert dann die Vorgabe 5. Die Prüfung macht ein kurzer Test über `docker compose exec mealie python -c "from mealie.kh.features.settings import KhSettings; print(KhSettings().draft_max_images)"`. Erwartet: `5`.
- [ ] **Schritt 2:** Anleitung und Tabellen schreiben, beide Sprachen.
- [ ] **Schritt 3: Probelauf mit dem Nutzer** auf dem MacBook.
  - Er trägt seinen Gemini-Schlüssel selbst ein. Dann geht es vom iPhone und vom iPad über Tailscale durch Link, Text, Foto eines selbst geschriebenen Zettels und Screenshot.
  - Festzuhalten: Anfragen je Rezept (AI Studio → Nutzung), Dauer je Erkennung, Auffälligkeiten.
  - Die Zahlen kommen in die Anleitung, die Auffälligkeiten werden zu Tests und Korrekturen.
- [ ] **Schritt 4:** Ganzes Backend und Frontend laufen lassen. Erwartet: alles grün.
- [ ] **Schritt 5: Commit** `Drafts: settings passthrough, guide for Gemini, where data goes`

### Task 8: Release v0.1

- [ ] **Schritt 1:** `docs/kh/CHANGELOG.md`: `[Unreleased]` wird zu `## [v0.1] - <Datum>`.
- [ ] **Schritt 2:** Arbeitszweig per Fast-Forward nach `main`, pushen. Danach die CI abwarten. Erwartet: alle vier Jobs grün.
- [ ] **Schritt 3:** `kh/ops/release.sh v0.1`. Erwartet: „Release fertig“ mit beiden Images; Upgrade-Test von `v0.0.2` in der CI bestanden.
- [ ] **Schritt 4:** Mac mini: `kh/ops/auto_update.sh check` meldet `v0.1-amd64`. Nach dem nächtlichen Update:
  - `status` zeigt `v0.1-amd64`.
  - Der Nutzer trägt den Gemini-Schlüssel auch dort ein, denn jede Installation hat ihre eigene Datenbank.
  - Ein Entwurf vom Handy über `kochbuch.example.org` klappt.
- [ ] **Schritt 5:** `PLAN.md`, `PLAN.en.md` und dieser Plan: Stand eintragen. Commit `Plan: phase 2 released as v0.1`.

Danach folgt als eigener Plan der Kurzbefehl „Teilen“ (`v0.1.1`, Spezifikation „Einführung“ Punkt 8).
