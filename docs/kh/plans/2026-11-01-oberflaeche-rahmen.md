# Oberfläche, Rahmen (v0.1.2) · Umsetzungsplan

> **Für ausführende Agenten:** Pflicht-Skill: superpowers:subagent-driven-development (empfohlen) oder superpowers:executing-plans, Aufgabe für Aufgabe. Schritte nutzen Checkboxen (`- [ ]`).

**Ziel:** Der Rahmen der neuen Oberfläche aus D38: Look „Salbei“ mit Figtree und dem Namen „Küchenhelfer“, auf dem Handy die Leiste unten (Rezepte, Eingang, Einkaufsliste, Mehr) mit der Seite „Mehr“, der Eingang auf einer Seite, der Entwürfe-Hinweis über der Startseite und Rezeptkarten ohne Sterne.

**Architektur:** Alle Ziele stehen in einer Liste in `frontend/kh/app/composables/use-kh-navigation.ts`; Leiste, Seitenmenü und „Mehr“ lesen daraus. Neue Teile liegen im Nuxt-Layer `frontend/kh/`, Mealie-Dateien bekommen nur kleine, mit `KH:` markierte Eingriffe. Die Rezeptseite bleibt in diesem Release Mealies; sie folgt mit `v0.1.3` in einem eigenen Plan.

**Technik:** Nuxt 4, Vue 3, Vuetify 3 (`v-bottom-navigation`, `useDisplay`), `@nuxt/fonts` (schon in Mealie), Vitest; Pydantic Settings, pytest.

**Spezifikation:** `docs/kh/specs/2026-11-01-oberflaeche-design.md` (D38). Mockups: https://claude.ai/artifact/TXV9AKbMmiZNM47u3cUjYV

## Feste Vorgaben

- Code, Bezeichner und Kommentare englisch. Texte nur über `frontend/kh/lang/en-US.json` und `de-DE.json` (neue Schlüssel unter `kh.nav.*`); wo Mealie einen passenden Schlüssel hat (wie heute in `DefaultLayout.vue`), wird er genutzt. Beide kh-Dateien haben dieselben Schlüssel (bestehender Test).
- Jede neue Datei beginnt mit 1 bis 3 Zeilen Zweck, jede Funktion hat eine Kurzbeschreibung. Kein toter Code: Ersetztes und unbenutzte Texte werden gelöscht.
- Jeder Eingriff in eine Mealie-Datei trägt `KH: <Grund> (D38)`. Mealies Sprachdateien und erzeugte Dateien bleiben unberührt.
- „Klein“ heißt unter 960 px Breite, Vuetifys `smAndDown`; ab 960 px (`mdAndUp`) bleibt Mealies Seitenmenü.
- Farben: Akzent hell `#2F7A55`, dunkel `#4FB07E`; Grund hell `#F4F5F1` (in `frontend/app/plugins/theme.ts`). Schrift: Systemschrift (kh-CSS; 1.11.2026 statt Figtree, siehe Spezifikation). Name: `Küchenhelfer` (Arbeitsname bis Phase 8).
- Adressen:
  - in der Leiste: Rezepte `/g/<slug>`, Eingang `/g/<slug>/drafts`, Einkaufsliste `/shopping-lists` oder `/shopping-lists/<id>`, Mehr `/g/<slug>/more`
  - unter „Mehr“: Essensplaner `/household/mealplan/planner/view`, Kochbücher `/g/<slug>/cookbooks`, Was kann ich kochen? `/g/<slug>/recipes/finder`, Favoriten `/user/<userId>/favorites`, Kategorien `/g/<slug>/recipes/categories`, Schlagworte `/g/<slug>/recipes/tags`, Utensilien `/g/<slug>/recipes/tools`, Zeitstrahl `/g/<slug>/recipes/timeline`
  - Einstellungen: Benutzereinstellungen `/user/profile`, Datenverwaltung `/group/data` (nur `canOrganize`), Verwaltung `/admin/site-settings` (nur `admin`)
- Links im Fuß von „Mehr“: Quellcode `https://github.com/gamingnet006/own-recipe-app`, Mealie `https://github.com/mealie-recipes/mealie`.
- Keine neuen API-Endpunkte, keine Migration, keine neuen Einstellungen; im Betrieb keine Anfrage an Google.
- Arbeitszweig `kh/v0.1.2-rahmen`.
- Befehle (Repo-Hauptordner):
  - Backend, einzelne Dateien: das Backend-Kommando aus `.claude/CLAUDE.md` mit `-v kh-uv-venv:/venv` und `uv run --frozen pytest <dateien> -q -p no:cacheprovider`; Lint dort mit `uv run --frozen ruff check <dateien> && uv run --frozen ruff format --check <dateien>`.
  - Frontend: das Frontend-Kommando aus `.claude/CLAUDE.md`; eine Datei mit `pnpm vitest --watch=false kh/app/__tests__/<datei>`, Lint mit `pnpm lint`.

## Review-Schwerpunkte

1. **Aktiver Tab auf Unterseiten:** Rezeptseite `/g/<slug>/r/<rezept>` gehört zu „Rezepte“, `/g/<slug>/drafts/<id>` zu „Eingang“, `/shopping-lists/<id>` zu „Einkaufsliste“, Essensplaner, Kochbücher, Profil und Unbekanntes zu „Mehr“. Test in Task 2.
2. **Einkaufsliste bei 0, 1 und mehreren Listen und offline:** genau eine Liste öffnet direkt; keine, mehrere oder ein Ladefehler öffnen die Übersicht. Test in Task 2.
3. **Alte Adressen ohne Schleife:** `/g/<slug>/drafts/new` und Mealies Import-Seiten führen in den Eingang und behalten `recipe_import_url`; `/g/<slug>/drafts` und `/g/<slug>/drafts/<id>` leiten nicht weiter. Test in Task 4, von Hand in Task 6.
4. **Nichts aus dem Seitenmenü geht auf dem Handy verloren:** Sprache, Hell/Dunkel, Benutzereinstellungen, Datenverwaltung (wer darf), Verwaltung (Admins), Favoriten, Kochbücher, Familie einladen, Abmelden sind über „Mehr“ erreichbar. Test der Listen in Task 2, von Hand in Task 6.
5. **Breite wechselt (iPad drehen, Fenster ziehen):** über 960 px verschwindet die Leiste und das Seitenmenü erscheint, darunter umgekehrt; nie beides, nie verdeckter Inhalt. Von Hand in Task 6.

---

### Task 1: Look „Salbei“ und Name

**Dateien:**
- Ändern: `mealie/core/settings/themes.py` (`light_primary = "#2F7A55"`, `dark_primary = "#4FB07E"`)
- Ändern: `mealie/core/settings/branding.py` (`name = "Küchenhelfer"`)
- Ändern: `frontend/app/plugins/theme.ts` (Rückfallwerte `primary` wie oben; im hellen Theme `background: "#F4F5F1"`)
- Ändern: `frontend/app/components/Layout/LayoutParts/AppHeader.vue`: helle Kopfzeile wie im Mockup (`color="surface"`, flach, Linie unten), Logo-Symbol in `primary`, Suchfeld mit neutralem Hintergrund statt `primary-darken-1`
- Neu: `frontend/kh/app/assets/kh-theme.css`: `font-family: "Figtree", system-ui, sans-serif !important` auf `.v-application` und `.v-application [class*="text-"]`. Die Angabe steht wörtlich da, damit `@nuxt/fonts` Figtree beim Bauen findet und ins Image legt.
- Ändern: `frontend/kh/nuxt.config.ts` (`css` mit dem Pfad der Datei relativ zum Layer, über `import.meta.url`)
- Neu: `tests/kh/test_kh_look.py`
- Ändern: `tests/integration_tests/admin_tests/test_admin_about.py:104` (erwartet `"Küchenhelfer"`)
- Ändern: `docs/kh/THIRD_PARTY_NOTICES.md` (Figtree, Erik Kennedy, SIL OFL 1.1, beim Bauen über `@nuxt/fonts` ins Image)

**Schnittstellen:**
- Liefert: Vuetify-Farben `primary` und, hell, `background` mit den Salbei-Werten; `$appInfo.brandingName === "Küchenhelfer"`.

- [ ] **Schritt 1: Test schreiben**

```python
def test_the_look_is_sage(api_client: TestClient):
    theme = api_client.get(api_routes.app_about_theme).json()
    assert theme["lightPrimary"] == "#2F7A55"
    assert theme["darkPrimary"] == "#4FB07E"
```

Dazu in `test_admin_about.py:104`: `assert as_dict["brandingName"] == "Küchenhelfer"  # KH: …`.

- [ ] **Schritt 2: Tests laufen lassen** (`tests/kh/test_kh_look.py tests/integration_tests/admin_tests/test_admin_about.py`). Erwartet: FAIL mit `#E58325` und `Mealie`.
- [ ] **Schritt 3: Umsetzen** (Dateien oben).
- [ ] **Schritt 4: Tests, Ruff und Frontend-Lint.** Erwartet: PASS, keine Meldungen.
- [ ] **Schritt 5: Commit** `Look: sage colors, Figtree and the name Küchenhelfer (D38)`

### Task 2: Gemeinsame Zielliste

**Dateien:**
- Neu: `frontend/kh/app/composables/use-kh-navigation.ts`
- Neu: `frontend/kh/app/__tests__/kh-navigation.test.ts`
- Ändern: `frontend/kh/lang/en-US.json`, `de-DE.json` (Titel der Ziele, die Mealie nicht hat: Eingang, Einkaufsliste, Mehr, Was kann ich kochen?)

**Schnittstellen:**
- Liefert:
  - `type KhNavKey = "recipes" | "intake" | "shopping" | "more" | "mealplan" | "cookbooks" | "finder" | "favorites" | "organizers" | "categories" | "tags" | "tools" | "timeline" | "profile" | "data" | "admin"`
  - `interface KhNavTarget { key: KhNavKey; to: string; icon: string /* Name in Mealies $globals.icons */; title: string /* i18n-Schlüssel */; children?: KhNavTarget[] }`
  - `barTargets(groupSlug: string, shoppingTo: string): KhNavTarget[]`: recipes, intake, shopping, more
  - `sidebarTargets(groupSlug: string, shoppingTo: string): KhNavTarget[]`: recipes, intake, shopping, mealplan, cookbooks, finder, organizers (Kinder: categories, tags, tools), timeline
  - `moreSections(groupSlug: string, userId: string): { plan: KhNavTarget[]; collection: KhNavTarget[] }`
  - `settingsTargets(user: { canOrganize?: boolean; admin?: boolean }): KhNavTarget[]`
  - `activeTab(path: string, groupSlug: string): "recipes" | "intake" | "shopping" | "more"`
  - `shoppingTarget(listIds: string[]): string`
  - `useKhShoppingTarget(): Ref<string>`: lädt die Listen einmal je App-Start über `useUserApi().shopping.lists.getAll(1, -1)`, bis dahin und bei Fehlern `/shopping-lists`

- [ ] **Schritt 1: Tests schreiben**

```ts
expect(barTargets("familie", "/shopping-lists").map(t => [t.key, t.to])).toEqual([
  ["recipes", "/g/familie"], ["intake", "/g/familie/drafts"], ["shopping", "/shopping-lists"], ["more", "/g/familie/more"],
]);
expect(sidebarTargets("familie", "/shopping-lists").map(t => t.key)).toEqual(
  ["recipes", "intake", "shopping", "mealplan", "cookbooks", "finder", "organizers", "timeline"]);
const { plan, collection } = moreSections("familie", "u1");
expect(plan.map(t => t.key)).toEqual(["mealplan", "cookbooks", "finder"]);
expect(collection.map(t => t.key)).toEqual(["favorites", "categories", "tags", "tools", "timeline"]);
expect(collection[0].to).toBe("/user/u1/favorites");
expect(settingsTargets({}).map(t => t.key)).toEqual(["profile"]);
expect(settingsTargets({ canOrganize: true, admin: true }).map(t => t.key)).toEqual(["profile", "data", "admin"]);

expect(activeTab("/g/familie", "familie")).toBe("recipes");
expect(activeTab("/g/familie/r/apfelkuchen", "familie")).toBe("recipes");
expect(activeTab("/g/familie/drafts/123", "familie")).toBe("intake");
expect(activeTab("/shopping-lists/abc", "familie")).toBe("shopping");
expect(activeTab("/g/familie/cookbooks/kuchen", "familie")).toBe("more");
expect(activeTab("/household/mealplan/planner/view", "familie")).toBe("more");
expect(activeTab("/user/profile", "familie")).toBe("more");

expect(shoppingTarget([])).toBe("/shopping-lists");
expect(shoppingTarget(["abc"])).toBe("/shopping-lists/abc");
expect(shoppingTarget(["abc", "def"])).toBe("/shopping-lists");
// useKhShoppingTarget: Mealies API gemockt; eine Liste → "/shopping-lists/abc", Fehler → "/shopping-lists"
```

- [ ] **Schritt 2: Tests laufen lassen.** Erwartet: FAIL (Modul fehlt).
- [ ] **Schritt 3: Umsetzen.** Eine Tabelle aller Ziele; die Funktionen wählen daraus aus, keine Liste wird zweimal geschrieben. Der Zustand von `useKhShoppingTarget` ist ein Modul-Ref wie `useKhDraftCount`.
- [ ] **Schritt 4: Tests und Lint.** Erwartet: PASS.
- [ ] **Schritt 5: Commit** `Navigation: one list of destinations for bar, side menu and More (D38)`

### Task 3: Leiste unten, Seitenmenü und „Mehr“

**Dateien:**
- Neu: `frontend/kh/app/components/KhBottomNav.vue`: `v-bottom-navigation` mit `barTargets`, aktiver Tab aus `activeTab(route.path, …)`; Eingang mit Zahl (`useKhDraftCount`) als Abzeichen und Beschriftung „Eingang, n Entwürfe“ für Screenreader; Einkaufsliste mit `useKhShoppingTarget()`
- Neu: `frontend/kh/app/pages/g/[groupSlug]/more.vue` (Middleware `auth`, `group-only` wie die Entwurfsseiten):
  - Abschnitte „Planen“ und „Sammlung“ aus `moreSections`
  - „Einstellungen“ aus `settingsTargets`, dazu Familie einladen (`UserInviteDialog`), Sprache (`LanguageDialog`), Hell/Dunkel (`useToggleDarkMode`)
  - „Abmelden“ (`useMealieAuth().signOut("/login?direct=1")`, wie in `AppHeader.vue`)
  - Fuß: `Küchenhelfer <$appInfo.version> · basiert auf Mealie · Quellcode (AGPL)` mit den Links aus den Vorgaben
- Ändern: `frontend/app/components/Layout/DefaultLayout.vue`:
  - `AppSidebar` und der Menü-Knopf nur ab `mdAndUp`, `KhBottomNav` nur bei `smAndDown`
  - `topLinks` aus `sidebarTargets` (Symbole über `$globals.icons[target.icon]`, Eingang mit `kh.nav.intake-count`)
  - in `createLinks` führt „Rezept hinzufügen“ auf `/g/<slug>/drafts`
- Ändern: `frontend/app/components/Layout/LayoutParts/AppHeader.vue`: „Abmelden“ nur ab `mdAndUp`
- Ändern: `frontend/kh/lang/*.json` (Abschnittsnamen, Familie einladen, Fuß, Hauptmenü-Beschriftung)

**Schnittstellen:**
- Verbraucht: alles aus Task 2; `useKhDraftCount` aus `use-kh-drafts.ts`.

- [ ] **Schritt 1: Umsetzen.** Die Logik liegt in Task 2; hier nur Darstellung.
- [ ] **Schritt 2: Lint und Frontend-Tests.** Erwartet: PASS, keine Meldungen.
- [ ] **Schritt 3: Commit** `Navigation: bar at the bottom, More page, side menu from the shared list (D38)`

### Task 4: Eingang auf einer Seite

**Dateien:**
- Neu: `frontend/kh/app/components/KhDraftIntake.vue`: das Formular aus `drafts/new.vue` (Link, Text, Fotos mit Vorschau und Entfernen, Absenden); Prop `sharedLink: string`, Ereignis `submitted`; nach Erfolg leert es sich und gibt die Vorschau-Adressen frei
- Ändern: `frontend/kh/app/pages/g/[groupSlug]/drafts/index.vue`:
  - Titel „Eingang“, oben `KhDraftIntake` mit `route.query.recipe_import_url`
  - darunter die Liste wie bisher, ohne den Knopf „Rezept hinzufügen“
  - nach `submitted`: Liste neu laden und die Zahl auffrischen
  - Link „Selbst eintippen“ auf `/g/<slug>/r/create/new` und der Satz zum Kurzbefehl
- Löschen: `frontend/kh/app/pages/g/[groupSlug]/drafts/new.vue`. `/drafts/new` trifft `drafts/[id].vue`; die globale Middleware leitet vorher um.
- Ändern: `frontend/kh/app/composables/use-kh-drafts.ts`: `importRedirectTarget` gibt für Mealies Import-Seiten und für `/g/<slug>/drafts/new` den Pfad `/g/<slug>/drafts` zurück
- Ändern: `frontend/kh/app/__tests__/kh-drafts.test.ts`, `frontend/kh/lang/*.json`

**Schnittstellen:**
- Verbraucht: `useKhDraftsApi`, `useKhDraftCount`, `requestError`, `errorText` aus `use-kh-drafts.ts`.
- Liefert: `importRedirectTarget(path: string): string | null` mit neuem Ziel.

- [ ] **Schritt 1: Tests anpassen und ergänzen**

```ts
for (const page of ["url", "ai", "image", "html", "bulk"]) {
  expect(importRedirectTarget(`/g/familie/r/create/${page}`)).toBe("/g/familie/drafts");
}
expect(importRedirectTarget("/g/familie/drafts/new")).toBe("/g/familie/drafts");
expect(importRedirectTarget("/g/familie/drafts")).toBeNull();      // no loop
expect(importRedirectTarget("/g/familie/drafts/abc")).toBeNull();  // a draft's review stays
```

- [ ] **Schritt 2: Tests laufen lassen.** Erwartet: FAIL (altes Ziel `/drafts/new`).
- [ ] **Schritt 3: Umsetzen.**
- [ ] **Schritt 4: Tests und Lint.** Erwartet: PASS.
- [ ] **Schritt 5: Commit** `Drafts: intake and drafts on one page (D38)`

### Task 5: Startseite: Entwürfe-Hinweis, Karten ohne Sterne

**Dateien:**
- Neu: `frontend/kh/app/components/KhDraftHint.vue`: nur in der eigenen Gruppe und bei `count > 0` ein Hinweis mit Link auf `/g/<slug>/drafts`, Text `kh.nav.drafts-waiting` in Einzahl und Mehrzahl („1 Entwurf wartet auf Prüfung | {count} Entwürfe warten auf Prüfung“)
- Ändern: `frontend/app/components/Domain/Recipe/RecipeExplorerPage/RecipeExplorerPage.vue`: `<KhDraftHint />` über `RecipeExplorerPageSearch`
- Ändern: `frontend/app/components/Domain/Recipe/RecipeCardMobile.vue`, `RecipeCard.vue`: `RecipeCardRating` und sein Import entfallen; die Props `rating` und `ratingColor` bleiben, weil Mealies Seiten sie übergeben
- Ändern: `frontend/kh/lang/*.json`, `frontend/kh/app/__tests__/kh-navigation.test.ts`

- [ ] **Schritt 1: Test schreiben:** `kh.nav.drafts-waiting` hat in beiden Sprachen zwei Formen, getrennt durch ` | `.
- [ ] **Schritt 2: Test laufen lassen.** Erwartet: FAIL (Schlüssel fehlt).
- [ ] **Schritt 3: Umsetzen.**
- [ ] **Schritt 4: Tests und Lint.** Erwartet: PASS.
- [ ] **Schritt 5: Commit** `Start page: hint on waiting drafts, recipe cards without stars (D38)`

### Task 6: Prüfen, Doku, Release v0.1.2

**Dateien:**
- Ändern: `docs/kh/README.md` (DE und EN: kurzer Abschnitt „So findest du dich zurecht“: Leiste, Eingang, Mehr; ab iPad quer das Seitenmenü)
- Ändern: `docs/kh/CHANGELOG.md` (`## [v0.1.2] - <Datum>`)
- Ändern: `PLAN.md`, `PLAN.en.md` (beim Punkt „Oberfläche nach D38 umsetzen“: `v0.1.2` erledigt, `v0.1.3` offen)

- [ ] **Schritt 1: Ganze Suiten:** Backend und Frontend (Lint und Tests) nach `.claude/CLAUDE.md`. Erwartet: alles grün.
- [ ] **Schritt 2: Von Hand** in einer Wegwerf-Installation auf Port 9194 mit den Testrezepten aus `kh/ops/testdata`:
  - Handy (375 px): Leiste, aktiver Tab auf Rezept- und Entwurfsseiten, Eingang-Zahl, alles unter „Mehr“ (auch Sprache, Hell/Dunkel, Abmelden)
  - Einkaufsliste mit 0, 1 und 2 Listen
  - iPad hochkant (820 px) mit Leiste, quer (1180 px) mit Seitenmenü und ohne Leiste; Wechsel durch Ändern der Breite
  - Computer: Seitenmenü mit „Eingang (n)“, „Erstellen“ führt in den Eingang
  - hell und dunkel: Knopfschrift lesbar (hell weiß auf `#2F7A55`, dunkel dunkel auf `#4FB07E`)
  - `/g/home/drafts/new?recipe_import_url=https://example.org/x` landet im Eingang mit vorausgefülltem Link
  - Netzwerk-Mitschnitt: keine Anfrage an `fonts.googleapis.com` oder `fonts.gstatic.com`, Figtree kommt aus `/_fonts/`
- [ ] **Schritt 3: Doku** (Dateien oben); Commit `Release: v0.1.2 changelog and guide`.
- [ ] **Schritt 4: Release:** `main` vorspulen (`--ff-only`), pushen, CI grün abwarten, `kh/ops/release.sh v0.1.2`, Zweig löschen. Die Installationen holen sich das Release nachts um 4 Uhr.
