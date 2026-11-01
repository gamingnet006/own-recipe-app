# Oberfläche, Rezeptseite · Umsetzungsplan

> **Für ausführende Agenten:** Pflicht-Skill: superpowers:executing-plans (vom Nutzer gewählt: selbst ausführen, Prüfung am Ende). Schritte nutzen Checkboxen (`- [ ]`).

**Ziel:** Die ruhige Rezeptseite aus D38: Bild mit Zurück, Favorit und Menü ⋯, Titel mit Herkunft, Zeiten als Kacheln, Mengen-Regler, Mealies Zutaten und Schritte, Notizen, unten „Kochen starten“; Sterne, Kommentare, „Zuletzt gemacht“, Chips und Einheiten-Umschalter fallen weg.

**Architektur:** Nur die Ansicht ändert sich. In `RecipePage.vue` ersetzt in der Ansicht ein eigener Kopf (`KhRecipeHeader.vue`) Mealies Kopf, Mengen-Chip und Herkunfts-Zeile; Mealies Zutatenliste (`RecipePageIngredientToolsView`) und Schritte (`RecipePageInstructions`) bleiben, denn dort docken Phase 3 und 4 an. Bearbeiten, Kochmodus und Drucken bleiben unverändert Mealies.

**Technik:** Nuxt 4, Vue 3, Vuetify 3, Vitest.

**Spezifikation:** `docs/kh/specs/2026-11-01-oberflaeche-design.md`, Abschnitt „Rezeptseite“ (D38). Mockup: https://claude.ai/artifact/TXV9AKbMmiZNM47u3cUjYV (Artboard „A · Rezeptseite“).

## Feste Vorgaben

- Wie im Plan `2026-11-01-oberflaeche-rahmen.md`: englischer Code, Texte nur in `frontend/kh/lang/*.json` (Schlüssel `kh.recipe.*`), `KH: <Grund> (D38)` an jedem Eingriff in Mealie, kein toter Code, Befehle über `.claude/CLAUDE.md`.
- Mealies Bausteine statt Nachbau: `RecipeFavoriteBadge`, `RecipeContextMenu` (Menü ⋯), `RecipeYield` (Mengenangabe mit Skalierung), `KhOriginBadge` (Herkunft), `useStaticRoutes().recipeImage`, `SafeMarkdown` (Beschreibung), `RecipeDialogAddToShoppingList`.
- Die Skalierung bleibt Mealies `scale` aus `RecipePage.vue`; der Regler ändert nur diesen Wert.
- Arbeitszweig `kh/oberflaeche-rezeptseite`, abgezweigt vom fertigen Rahmen-Zweig. Kein Release ohne Rückfrage beim Nutzer.

## Review-Schwerpunkte

1. **Bearbeiten bleibt Mealies:** „Bearbeiten“ im Menü öffnet Mealies Editor mit seinem Kopf, Speichern und Verwerfen; danach steht wieder unsere Ansicht da. Von Hand in Task 3.
2. **Kochmodus und Drucken bleiben:** „Kochen starten“ öffnet Mealies Kochmodus, „Drucken“ druckt das Rezept wie bisher. Von Hand in Task 3.
3. **Lücken bei fehlenden Angaben:** ohne Bild, Zeiten, Mengenangabe, Beschreibung, Notizen oder Quelle entfällt der Teil ohne leeren Platz. Test in Task 1, von Hand in Task 3.
4. **Regler:** ändert die Mengen in Zutaten und Schritten, geht nie unter 1, zeigt Einzahl und Mehrzahl richtig. Test in Task 1.
5. **Leiste unten:** „Kochen starten“ sitzt über der Leiste und verdeckt keinen Inhalt. Von Hand in Task 3.

---

### Task 1: Rechenteile der Rezeptansicht

**Dateien:** Neu `frontend/kh/app/composables/use-kh-recipe.ts`, `frontend/kh/app/__tests__/kh-recipe.test.ts`

**Schnittstellen (Liefert):**
- `recipeTimes(recipe: Pick<Recipe, "prepTime" | "performTime" | "totalTime">): { key: "prep" | "perform" | "total"; value: string }[]`: nur vorhandene, in dieser Reihenfolge
- `scaleBase(recipe: Pick<Recipe, "recipeYieldQuantity" | "recipeServings">): number`: Mengenangabe, sonst Portionen, sonst 0 (dann kein Regler)
- `stepScale(base: number, scale: number, delta: 1 | -1): number`: neuer Faktor für eine ganze Zahl mehr oder weniger, nie unter 1 Stück

- [ ] **Schritt 1: Tests schreiben**

```ts
expect(recipeTimes({ prepTime: "25 Minuten", performTime: "", totalTime: "1 Stunde" }))
  .toEqual([{ key: "prep", value: "25 Minuten" }, { key: "total", value: "1 Stunde" }]);
expect(recipeTimes({})).toEqual([]);
expect(scaleBase({ recipeYieldQuantity: 12, recipeServings: 4 })).toBe(12);
expect(scaleBase({ recipeYieldQuantity: 0, recipeServings: 4 })).toBe(4);
expect(scaleBase({})).toBe(0);
expect(stepScale(12, 1, 1)).toBeCloseTo(13 / 12);
expect(stepScale(4, 0.25, -1)).toBeCloseTo(0.25);   // 1 Portion ist das Minimum
expect(stepScale(4, 1.5, -1)).toBeCloseTo(5 / 4);
```

- [ ] **Schritt 2: laufen lassen.** Erwartet: FAIL (Modul fehlt).
- [ ] **Schritt 3: umsetzen.**
- [ ] **Schritt 4: Tests und Lint.** Erwartet: PASS.
- [ ] **Schritt 5: Commit** `Recipe page: times, scale base and steps (D38)`

### Task 2: Kopf und Einbau in Mealies Rezeptseite

**Dateien:**
- Neu: `frontend/kh/app/components/KhRecipeHeader.vue`. Props `recipe`, `scale` (v-model), Ereignisse `edit`, `cook`. Inhalt von oben:
  - Bild über die ganze Breite (ohne Bild eine Fläche mit Symbol), darauf Zurück, `RecipeFavoriteBadge` und das Menü ⋯ (`RecipeContextMenu` mit Bearbeiten, Essensplan, Einkaufsliste, Drucken, Teilen, Löschen)
  - Titel, Beschreibung, `KhOriginBadge`
  - Zeit-Kacheln aus `recipeTimes`
  - Regler aus `scaleBase` und `stepScale`, Anzeige über `RecipeYield` mit dem aktuellen `scale`
- Ändern: `frontend/app/components/Domain/Recipe/RecipePage/RecipePage.vue`:
  - in der Ansicht `KhRecipeHeader` statt `RecipePageHeader`, `RecipePageScale` und der Zeile mit `KhOriginBadge`; im Bearbeiten bleibt alles wie es ist
  - `RecipePageOrganizers` nur beim Bearbeiten
  - `RecipePageComments` entfällt
  - unter den Zutaten „Auf die Einkaufsliste“ (öffnet `RecipeDialogAddToShoppingList`)
  - in der Ansicht unten fest „Kochen starten“ (`toggleCookMode`)
- Ändern: `frontend/kh/lang/en-US.json`, `de-DE.json` (`kh.recipe.*`: Zeiten, Kochen starten, Auf die Einkaufsliste, Zurück, Weniger/Mehr)

**Schnittstellen:** Verbraucht Task 1.

- [ ] **Schritt 1: umsetzen.** Die Logik liegt in Task 1; hier Darstellung und Verdrahtung.
- [ ] **Schritt 2: ganze Frontend-Suite und Lint.** Erwartet: PASS.
- [ ] **Schritt 3: Commit** `Recipe page: own header, cook button, no comments or chips (D38)`

### Task 3: Prüfen von Hand und Doku

- [ ] **Schritt 1:** Image bauen, Wegwerf-Installation mit den Testrezepten; Handy, iPad, Computer, hell und dunkel:
  - Rezept mit Bild und ohne, mit Zeiten und ohne
  - Regler bis 1 und hoch, Mengen in Zutaten und Schritten
  - Bearbeiten mit Speichern und Verwerfen
  - Kochen starten, Drucken, Auf die Einkaufsliste, Löschen-Dialog
- [ ] **Schritt 2:** `docs/kh/README.md` (DE/EN, kurz die Rezeptseite) und `docs/kh/CHANGELOG.md` (`[Unreleased]`); Commit `Docs: the new recipe page (D38)`.
- [ ] **Schritt 3:** Abschluss-Review des Zweigs, dann den Nutzer fragen, ob und wann veröffentlicht wird.
