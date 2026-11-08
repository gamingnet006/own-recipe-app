# Familienkochbuch `v0.4` (D43) · Design

Stand 8.11.2026. Abgestimmt über die Vorschlagsseite: F1 bis F6 wie empfohlen, dazu der Wunsch nach einem Buch-Editor mit Vorschau. Phase 5 aus `PLAN.md`. Baut auf `v0.3` auf (Schritttext mit Klammern, `frontend/kh/app/lib/step-text.ts`).

## Ziel

- Aus einer Auswahl eigener Rezepte entsteht ein druckbares Familienkochbuch als PDF. Einzelne Rezepte gibt es als Rezeptkarte.
- Vor dem Drucken entscheidet man auf der Webseite, was hinein soll, und sieht sofort, wie es aussieht.
- Wer aus einer anderen App kommt, bringt seine Rezepte mit und findet danach die doppelten.
- Wer mit Umluft backt, sieht die passende Temperatur gleich im Schritt.

## Nicht-Ziele

- PDF-Datei vom Server (WeasyPrint) und Seitenzahlen im Inhaltsverzeichnis: nur wenn der Druckdialog nicht reicht. Dafür gibt es dann eine eigene Spezifikation.
- Menü-Zeitplan: später, sobald ihn jemand vermisst (PLAN, „Kann“).
- Eigene Schriften: Es bleibt bei der Systemschrift des Geräts, also kein Schrift-Download und keine Lizenz.
- Freies Layout wie in einem Grafikprogramm: Der Editor wählt aus, er gestaltet nicht frei.

## F1 · PDF über den Druckdialog

- Küchenhelfer baut eine Druckseite mit `@media print`:
  - DIN A4, Ränder 15 mm;
  - jedes Rezept beginnt auf einer neuen Seite (`break-before: page`);
  - Zutatenblöcke und Schritte werden nicht mitten im Absatz getrennt (`break-inside: avoid`).
- Die Taste „Drucken / Als PDF sichern“ öffnet den Druckdialog (`window.print()`). Am iPhone kommt man von dort über Teilen zu „Als PDF sichern“, am Mac direkt über „Als PDF sichern“. Die README erklärt beide Wege.
- Das Inhaltsverzeichnis nummeriert die Rezepte („Nr. 12 Apfelkuchen“), und jedes Rezept trägt seine Nummer im Titel. Seitenzahlen kann der Browser dort nicht eintragen.

## F2 · Buch-Editor mit Vorschau (Wunsch nach dem Vorschlag)

- Eine Seite `/g/<gruppe>/kochbuch/<kochbuch-slug>` aus unserer Schicht (`frontend/kh/app/pages/`).
- Mealies Kochbuch-Seite bekommt eine Taste „Als Buch drucken“, die dorthin führt, mit `KH:` markiert.
- Die Rezepte des Kochbuchs sind die, die Mealies gespeicherter Filter dieses Kochbuchs findet. Daraus wählt man im Editor ab.
- **Oben: Einstellungen.** Auf dem Handy untereinander, ab 840 px links neben der Vorschau.
  - **Buch:**
    - Titel, Standard ist der Name des Kochbuchs.
    - Untertitel, Standard „<Haushalt> · <Jahr>“.
    - Titelseite an oder aus.
    - Inhaltsverzeichnis an oder aus.
    - Reihenfolge: „nach Kategorie, dann A–Z“ (Standard) oder „A–Z“.
  - **Für alle Rezepte:** Beschreibung an oder aus, Notizen an oder aus, Umluft-Klammern an oder aus (F6). Die Mengen-Klammern aus dem Kochmodus sind immer an.
  - **Pro Rezept,** als Liste mit Bild-Vorschau:
    - Häkchen „ins Buch“, Standard an.
    - „mit Foto“: nur wählbar, wenn das Rezept als „Foto ist von uns“ markiert ist (F4). Die Markierung lässt sich dort setzen, mit dem Hinweis „Nur für Fotos, die ihr selbst gemacht habt“.
    - Portionen, Standard ist die Grundmenge des Rezepts.
- **Darunter oder rechts: Vorschau.**
  - Die Druckseite selbst, verkleinert als weiße Blätter im A4-Format. Was dort steht, kommt so aufs Papier.
  - Seitenumbrüche zeigt die Vorschau als Blattgrenzen vor jedem Rezept.
  - Sie folgt jeder Änderung sofort, und es gibt keine zweite Darstellung, die von der Druckseite abweichen könnte.
- **Speichern:** Die Einstellungen gehören zum Kochbuch und sind damit an jedem Gerät gleich.
  - Sie liegen in der neuen Tabelle `kh_cookbook_print` mit `cookbook_id` als Schlüssel und den Einstellungen als JSON, das ein Pydantic-Schema prüft.
  - Die Migration `kh0004` fügt nur hinzu.
  - Endpunkte: `GET` und `PUT /api/kh/cookbooks/{id}/print`.
  - Lesen dürfen alle, die das Kochbuch sehen. Ändern dürfen alle, die das Kochbuch ändern dürfen, wie bei Mealie.
  - Gespeichert wird automatisch eine Sekunde nach der letzten Änderung.
- **Ohne Rezepte** steht in der Vorschau ein Hinweis: „Dieses Kochbuch findet keine Rezepte. Passe den Filter in Mealies Kochbuch an.“

## F3 · Rezeptkarte

- Die Karte nutzt dieselbe Druckseite mit genau einem Rezept und ohne Titelseite und Inhaltsverzeichnis:
  - DIN A4;
  - Titel, darunter Portionen und Zeiten;
  - links Zutaten (etwa ein Drittel der Breite), rechts die Schritte mit den Klammern aus `v0.3`;
  - Notizen am Ende.
- „Drucken“ im Menü der Rezeptseite (`KhRecipeHeader`) öffnet den Editor im Rezept-Modus `/g/<gruppe>/kochbuch/rezept/<rezept-slug>`. Er hat dieselben Schalter pro Rezept (Foto, Beschreibung, Notizen, Portionen), wird aber nicht gespeichert. Die Portionen übernimmt er vom gewählten Faktor der Rezeptseite.
- Mealies alter Druckdialog bleibt im Code, unsere Rezeptseite ruft ihn nur nicht mehr auf.

## F4 · Nur eigene Fotos

- Eine Rezept-Markierung „Foto ist von uns“ in der neuen Tabelle `kh_recipe_flags` (`recipe_id`, `own_photo`, Standard aus), angelegt mit derselben Migration `kh0004`.
- Endpunkt: `PUT /api/kh/recipes/{id}/flags`. Ändern darf, wer das Rezept ändern darf.
- Ohne Markierung kommt nie ein Foto ins PDF, auch nicht, wenn jemand es im Editor anfordert: Der Server liefert die Einstellungen dann mit „Foto aus“.
- In der App bleiben alle Fotos sichtbar wie bisher.

## F5 · Umzug

- Die README bekommt einen Abschnitt „Umzug aus einer anderen App“:
  - Mealie übernimmt Rezepte aus Paprika, Tandoor, Nextcloud Kochbuch, Copy Me That, Recipe Keeper, Plan to Eat, MyRecipeBox, Cook'n, Chowdown und alten Mealie-Versionen.
  - Der Weg dahin: **Gruppe → Daten-Migration** (`/group/migrations`), Export aus der alten App, Datei wählen, „Tag hinzufügen“ einschalten.
  - Kitchen Stories und Chefkoch haben keinen Export; dort geht es einzeln per Link über den Eingang. Papierrezepte und Kochbuchseiten kommen als Foto über den Eingang.
- **Duplikat-Bericht:**
  - Neue Seite `/g/<gruppe>/doppelte` unter „Mehr“. Sie listet Paare von Rezepten, die nach der Erkennung aus Phase 2 (`mealie/kh/drafts/duplicates.py`, Titel und Zutaten) doppelt sein könnten.
  - Je Paar: beide Titel mit Herkunft, Ähnlichkeit, die Taste „ansehen“ (öffnet beide), „Beide behalten“ (das Paar kommt nicht wieder) und „<Titel> löschen“ mit Bestätigung. Gelöscht wird über Mealies normale Funktion.
  - „Beide behalten“ landet in der Tabelle `kh_duplicate_ignored` (`recipe_a`, `recipe_b`), ebenfalls aus `kh0004`.
  - Die Liste kann nach Tag filtern, zum Beispiel nach dem Tag des Umzugs.
  - Endpunkt `GET /api/kh/duplicates?tag=<id>`. Er vergleicht jedes Rezept mit jedem (bei 2000 Rezepten etwa 2 Mio. Titelvergleiche) und liefert höchstens 200 Paare, die ähnlichsten zuerst.
- Die Vergleichsfunktionen aus `duplicates.py` werden dafür wiederverwendet, nicht kopiert. Wo sie heute an Entwürfe gebunden sind, bekommen sie eine kleine Hülle für zwei Rezepte.

## F6 · Umluft

- Unter „Mehr“ gibt es die Einstellung „Unser Ofen“: „Ober-/Unterhitze“ (Standard) oder „Umluft“. Sie wird auf dem Gerät gespeichert.
- Temperaturen im Schritttext, also „180 °C“, „180°C“ oder „180 Grad“, bekommen eine Klammer wie die Mengen aus `v0.3`:
  - Bei „Umluft“ und einem Text ohne „Umluft“: „180 °C **(Umluft 160 °C)**“.
  - Bei „Ober-/Unterhitze“ und einem Text mit „Umluft“ (bis zu drei Wörter davor oder danach): „160 °C Umluft **(Ober-/Unterhitze 180 °C)**“.
  - Steht „Ober-/Unterhitze“, „O/U“ oder „Umluft“ passend zum eigenen Ofen schon da, gibt es keine Klammer.
- Umrechnung: 20 °C Unterschied, als benannter Wert. Temperaturen unter 100 °C bekommen keine Klammer, weil sie selten Ofen-Temperaturen sind („auf 60 °C abkühlen“).
- Im Buch-Editor gilt der Schalter „Umluft-Klammern“ (F2) mit der Ofen-Einstellung des druckenden Geräts.

## Dateien

| Datei | Zweck |
|---|---|
| `frontend/kh/app/lib/oven.ts` | Temperaturen finden, Umluft-Klammer (rein, getestet) |
| `frontend/kh/app/lib/step-text.ts` | bindet die Umluft-Klammer neben den Mengen ein |
| `frontend/kh/app/lib/book.ts` | Einstellungen des Buchs, Reihenfolge, Nummern, welche Rezepte und Fotos (rein, getestet) |
| `frontend/kh/app/components/KhPrintBook.vue` | Druckseite (Titelseite, Inhalt, Rezepte) |
| `frontend/kh/app/components/KhBookEditor.vue` | Einstellungen und Vorschau |
| `frontend/kh/app/pages/g/[groupSlug]/kochbuch/…` | Buch und Rezeptkarte |
| `frontend/kh/app/pages/g/[groupSlug]/doppelte.vue` | Duplikat-Bericht |
| `mealie/kh/books/` | Modell, Schema, Repository, Routen für `kh_cookbook_print` und `kh_recipe_flags` |
| `mealie/kh/duplicates/` | Bericht über alle Rezepte, nutzt `mealie/kh/drafts/duplicates.py` |
| `mealie/kh/alembic/versions/…kh0004…` | drei neue Tabellen, nur hinzufügend |
| Mealie, mit `KH:` | Kochbuch-Seite (Taste), `KhRecipeHeader` ist unsere, sonst nichts |

## Tests

- **Backend (pytest):**
  - Einstellungen speichern und lesen; ein fremder Haushalt bekommt 404.
  - Ungültiges JSON wird abgelehnt.
  - Ohne „Foto ist von uns“ steht das Foto immer auf aus.
  - Flags ändern darf nur, wer das Rezept ändern darf.
  - Duplikat-Bericht: findet ein Paar mit gleichem Titel und gleichen Zutaten, findet kein Paar aus verschiedenen Gruppen, „Beide behalten“ blendet aus, der Tag-Filter wirkt, höchstens 200 Paare.
  - Die Migration läuft vor und zurück, auf SQLite und Postgres (CI).
- **Frontend (Vitest):**
  - `oven.ts` mit allen Formen aus F6 und den Grenzfällen unter 100 °C, „Umluft“ vor und nach der Zahl, „Grad“.
  - `book.ts`: Reihenfolge, Nummern, Filter für „ins Buch“, Foto nur mit Markierung, Standardwerte.
- **Von Hand:**
  - Buch mit 10 Rezepten am Mac als PDF und am iPhone über Teilen als PDF.
  - Seitenumbrüche, Fotos, Inhaltsverzeichnis.
  - Rezeptkarte mit einem langen Rezept.
  - Umzug mit einer kleinen selbst gebauten Export-Datei, zum Beispiel aus Paprika, danach der Duplikat-Bericht.
- Testdaten nur selbst geschrieben, keine fremden Rezepte, keine fremden Fotos.

## Fertig wenn

Ein Kochbuch mit 10 Rezepten ist als PDF druckbar (PLAN Phase 5), und der Editor zeigt vorher genau, was gedruckt wird. Der Link über das Teilen-Menü ist seit `v0.1.1` erledigt.

## Offene Punkte

- Aus welcher App die Familie umzieht, ist offen. Die Anleitung deckt alle Wege ab, die Mealie kennt.
- Gebaut wird nach dem Release von `v0.3`, weil F6 auf dem Schritttext von `v0.3` aufbaut.
