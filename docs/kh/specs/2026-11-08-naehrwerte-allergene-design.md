# Nährwerte und Allergene · v0.5 (D44)

Stand 8.11.2026. Abgestimmt über die Vorschlagsseite: N1 bis X1 wie empfohlen („Mach alles einfach so, wie du es denkst“). Phase 6 aus `PLAN.md`. Baut auf der Mengen-Zerlegung aus `v0.2` auf (Zutatenzeilen mit Menge, Einheit und Mealie-Lebensmittel).

## Ziel

- Jedes Rezept zeigt Nährwerte pro Portion, „ca.“, und sagt, aus welchen Zutaten sie stammen.
- Jedes Rezept zeigt, welche der 14 EU-Hauptallergene es wahrscheinlich enthält, und warnt, wenn jemand im Haushalt etwas davon nicht verträgt.
- Wer etwas nicht verträgt, bekommt Austausch-Hinweise und kann eine Variante speichern; das Original bleibt.

## Nicht-Ziele

- Open Food Facts und Markenprodukte (N1 C): später, sobald jemand es vermisst.
- KI für Allergene oder Zuordnung: erst, wenn ein KI-Anbieter eingerichtet ist, und dann nur als Vorschlag. Nicht in `v0.5`.
- Allergene als Mealie-Schlagwörter oder Filter in Mealies Suche (A1 B).
- „Frei von“-Aussagen. Es heißt immer „enthält wahrscheinlich“ und „ohne Gewähr“.

## T5 · Datenquelle

- Bundeslebensmittelschlüssel BLS 4.0, Max Rubner-Institut, Open Data unter CC BY 4.0. Download ohne Anmeldung: `https://www.blsdb.de/assets/uploads/BLS_4_0_2025_DE.zip` (rund 14 MB, darin `BLS_4_0_Daten_2025_DE.xlsx`, 7.140 Lebensmittel, Werte je 100 g essbarer Anteil).
- Zitat laut MRI: „Max Rubner-Institut (2025): Bundeslebensmittelschlüssel (BLS), Version 4.0 – Deutsche Nährstoffdatenbank. Karlsruhe. DOI 10.25826/Data20251217-134202-0“. Lizenz: CC BY 4.0. Änderung: „auf 9 Werte gekürzt, Salz aus Natrium × 2,5 berechnet“.

## N1 · BLS wird mitgeliefert

- Ein Skript `mealie/kh/nutrition/build_bls.py` lädt die ZIP-Datei, prüft ihre SHA-256 gegen den im Skript festgehaltenen Wert und schreibt `mealie/kh/nutrition/data/bls.csv`. Nur Standardbibliothek (`zipfile`, `xml.etree`), keine neue Abhängigkeit.
- `bls.csv` liegt im Repo und damit im Image (etwa 1 MB). Spalten: `code`, `name` (deutsch), `kcal`, `fat`, `saturated`, `carbs`, `sugar`, `protein`, `fiber`, `salt` (g je 100 g; `kcal` je 100 g). Fehlende Werte bleiben leer.
- Die Namensnennung steht in `docs/kh/THIRD_PARTY_NOTICES.md`, in der README und als kleine Zeile unter jedem Nährwert-Block („Quelle: BLS 4.0, Max Rubner-Institut, CC BY 4.0“).
- Der Server liest die Datei einmal beim ersten Bedarf (zwischengespeichert). Ohne Internet im Betrieb.

## N2 · Zuordnung einmal pro Zutat

- Zugeordnet wird ein Mealie-Lebensmittel („Mehl“), nicht eine Rezeptzeile. Die Zuordnung gilt für alle Rezepte der Gruppe.
- Neue Tabelle `kh_food_nutrition`: `food_id` (eindeutig, Mealies `ingredient_foods`), `bls_code` (leer heißt „kein passender Eintrag“), `confirmed` (bool), `piece_grams` (eigenes Stückgewicht, optional).
- **Vorschlag:** Ohne Zeile rechnet Küchenhelfer mit einem Vorschlag:
  1. erst eine feste Liste häufiger Zutaten (`data/aliases.json`, Zutat → BLS-Code, etwa 60 Einträge, z. B. „Mehl“ → Weizenmehl Type 405);
  2. sonst der BLS-Eintrag, dessen Name den Wortstamm der Zutat am Anfang trägt, der kürzeste zuerst.
  Ein Vorschlag gilt als „geschätzt“, bis jemand ihn bestätigt.
- **Seite „Mehr → Nährwerte“:** alle Lebensmittel, die in Rezepten vorkommen, offene oben. Pro Zeile der Eintrag, eine Suche im BLS (Name enthält den Suchtext, höchstens 20 Treffer), „Bestätigen“, „Kein passender Eintrag“ und das Stückgewicht.

## N3 · Gramm

- Gramm und Kilogramm direkt. Milliliter und Liter mit der Dichte der Zutat (Standard 1,0).
- `data/weights.json`:
  - `units`: Esslöffel 15 ml, Teelöffel 5 ml, Tasse 240 ml, Becher 200 g, Prise, Msp., „etwas“, „nach Geschmack“ ohne Wert (werden nicht gezählt);
  - `foods`: pro Wortstamm Dichte (g/ml) und Stückgewicht (g), z. B. Öl 0,92 g/ml, Mehl 0,55 g/ml, Zucker 0,85 g/ml, Milch 1,03 g/ml, Ei 55 g, Zwiebel 80 g, Knoblauchzehe 4 g, Apfel 150 g, Kartoffel 120 g, Zitrone 100 g. Etwa 60 Einträge.
- Zeilen ohne Einheit mit Menge zählen als Stück. Das eigene Stückgewicht aus N2 geht vor der Tabelle.
- Was sich nicht in Gramm umrechnen lässt (keine Menge, kein Stückgewicht, unbekannte Einheit, Zeile ohne Lebensmittel, kein BLS-Eintrag), wird nicht gezählt und steht unter „ohne: …“ mit dem Zeilentext.

## N4 · Anzeige

- Block „Nährwerte pro Portion (ca.)“ auf der Rezeptseite unter den Zutaten, zugeklappt mit Energie in der Kopfzeile („ca. 320 kcal pro Portion“), aufgeklappt mit Energie, Fett, davon gesättigte Fettsäuren, Kohlenhydrate, davon Zucker, Eiweiß, Ballaststoffe, Salz.
- Gerundet: kcal auf 10, Gramm ab 10 g ganz, darunter auf eine Nachkommastelle, Salz auf eine Nachkommastelle.
- Darunter: „aus 7 von 8 Zutaten“, die Liste „ohne: …“, „geschätzt“, wenn ein Vorschlag mitrechnet (Link zur Seite aus N2), die Quelle.
- Ohne Portionenzahl im Rezept: „für das ganze Rezept“. Pro Portion ändert sich beim Umrechnen nicht.
- Hat jemand in Mealies Nährwert-Feldern etwas eingetragen, zeigt der Block diese Werte mit „von Hand eingetragen“ und rechnet nicht. Mealies eigene Nährwert-Anzeige bleibt unverändert.
- Schalter unter „Mehr“: „Nährwerte zeigen“, auf dem Gerät gespeichert, Standard an.
- Endpunkt `GET /api/kh/recipes/{slug}/nutrition`.

## A1 · Allergene aus festen Regeln

- Die 14 Gruppen nach Anhang II der Verordnung (EU) 1169/2011, mit festen Schlüsseln: `gluten`, `crustaceans`, `eggs`, `fish`, `peanuts`, `soy`, `milk`, `nuts`, `celery`, `mustard`, `sesame`, `sulphites`, `lupin`, `molluscs`. Deutsche Namen: Gluten, Krebstiere, Ei, Fisch, Erdnüsse, Soja, Milch, Schalenfrüchte, Sellerie, Senf, Sesam, Sulfite, Lupinen, Weichtiere.
- `mealie/kh/allergens/data/rules.json`: pro Schlüssel Wortteile, die treffen („weizen“, „dinkel“, „mehl“, „paniermehl“, „sahne“, „käse“, „worcester“ …), und Ausnahmen („kokosmilch“, „hafermilch“, „reismehl“, „buchweizen“ …). Geprüft wird der Name des Lebensmittels, sonst der Zeilentext, klein geschrieben.
- Ergebnis pro Rezept: Liste der Allergene, jedes mit den Zeilen, aus denen es stammt.
- Korrektur pro Rezept: „stimmt nicht“ (nimmt ein erkanntes heraus) oder „fehlt“ (fügt eines hinzu). Neue Tabelle `kh_recipe_allergen`: `recipe_id`, `allergen`, `present` (bool). Ändern darf, wer das Rezept ändern darf.
- Anzeige: Chips „Enthält wahrscheinlich: …“ und „Erkannt aus den Zutaten, ohne Gewähr“. Ein Tipp auf einen Chip zeigt die Zeilen und die Korrektur.
- 20 selbst geschriebene Testfälle, darunter versteckte Quellen (Worcestersauce, Pesto, Brühe, Sojasauce, Mayonnaise, Marzipan) und Ausnahmen (Kokosmilch, Erdnussöl bleibt Erdnuss).
- Endpunkte `GET /api/kh/recipes/{slug}/allergens` und `PUT /api/kh/recipes/{slug}/allergens/{allergen}` mit `{present: bool | null}` (`null` hebt die Korrektur auf).

## A2 · „Ich vertrage nicht“

- Jedes Konto hakt unter „Mehr → Ich vertrage nicht“ an, welche der 14 Gruppen es nicht verträgt. Neue Tabelle `kh_user_allergies`: `user_id` (eindeutig), `allergens` (JSON-Liste der Schlüssel).
- Die Rezeptseite zeigt allen im Haushalt eine Warnung: „Enthält wahrscheinlich Schalenfrüchte. Lena verträgt das nicht.“ Der Name ist Mealies vollständiger Name des Kontos.
- Rezeptkarten in Listen bekommen ein kleines Warnzeichen, wenn ein Rezept etwas enthält, das jemand im Haushalt nicht verträgt. Endpunkt `GET /api/kh/allergens/warnings` liefert `{slug: [allergen]}` für alle Rezepte der Gruppe, die eine Warnung haben.
- Endpunkte `GET` und `PUT /api/kh/users/self/allergies`.

## X1 · Austausch und Varianten

- `mealie/kh/allergens/data/substitutions.json`: etwa 20 Regeln, jede mit Wortteil der Zutat, Ersatz und dem Allergen, das dadurch wegfällt, z. B. Milch → Haferdrink, Butter → Margarine, Sahne → Hafer-Kochcreme, Weizenmehl → glutenfreie Mehlmischung, gemahlene Mandeln → Semmelbrösel, Ei (zum Binden) → 1 EL Leinsamen mit 3 EL Wasser.
- Eigene Regeln pro Haushalt unter „Mehr → Ich vertrage nicht“: Zutat, Ersatz, Allergen. Neue Tabelle `kh_substitution`: `household_id`, `match`, `replacement`, `allergen`. Eigene Regeln gehen vor der Standardliste.
- Die Warnung aus A2 nennt pro betroffener Zeile den Ersatz („Statt Butter: Margarine“).
- **„Als Variante speichern“**: legt mit Mealies Duplizieren eine Kopie an, Name mit Zusatz „(ohne Schalenfrüchte)“, und ersetzt in den betroffenen Zeilen das Lebensmittel durch den Ersatz (Mealie-Lebensmittel mit diesem Namen, sonst neu angelegt); Menge und Einheit bleiben. Danach neuer Allergen-Check. Das Original bleibt unverändert. Endpunkt `POST /api/kh/recipes/{slug}/variant` mit `{allergens: [key]}` gibt den neuen Slug zurück.

## Daten und Sicherheit

- Eine additive Migration `kh0005` legt `kh_food_nutrition`, `kh_recipe_allergen`, `kh_user_allergies` und `kh_substitution` an. Beim Löschen eines Rezepts, Lebensmittels oder Kontos werden ihre Zeilen im Code mit entfernt (SQLite prüft keine Fremdschlüssel; so wie bei `kh0003` und `kh0004`).
- Alle Endpunkte brauchen eine Anmeldung und bleiben in der eigenen Gruppe; Haushalts-Daten (eigene Regeln, Warnungen) im eigenen Haushalt.
- JSON-Spalten kommen in die Backup-Liste wie bei `kh0004`.

## Dateien

| Datei | Zweck |
|---|---|
| `mealie/kh/nutrition/` | BLS laden und suchen, Gramm, Zuordnung, Rechnung, Endpunkte |
| `mealie/kh/allergens/` | Regeln, Korrekturen, Profil, Warnungen, Austausch, Varianten |
| `frontend/kh/app/components/KhNutrition.vue`, `KhAllergens.vue` | Blöcke auf der Rezeptseite |
| `frontend/kh/app/pages/g/[groupSlug]/naehrwerte.vue`, `vertraeglichkeit.vue` | Seiten aus N2 und A2 |
| `frontend/kh/app/lib/api/nutrition.ts`, `allergens.ts` | API-Aufrufe |

## Fertig wenn

Jeder Nährwert und jedes Allergen ist auf eine Zutatenzeile zurückführbar, die 20 Allergen-Testfälle bestehen, und ein Rezept mit Mehl, Butter, Eiern und Zucker zeigt plausible Werte pro Portion.
