# Oberfläche: Alltag zuerst, Look „Salbei“ (D38) · Design

Stand 1.11.2026, im Chat abgestimmt: erst den Alltag einfacher machen, den eigenen Look dazu (Ziel C); Leiste unten mit Rezepte, Eingang, Einkaufsliste, Mehr; Weg 2 (aufräumen plus eigene Rezeptseite); Look A „Salbei“. Mockups: https://claude.ai/artifact/TXV9AKbMmiZNM47u3cUjYV

## Ziel

- Mit einem Tipp dort sein, wo man im Alltag hinwill: Rezepte, Eingang, Einkaufsliste. Alles Seltenere liegt unter „Mehr“.
- Die Rezeptseite zeigt zuerst, was man zum Kochen braucht: Bild, Zutaten, Schritte. Phase 3 (Mengen, Portionsrechner) und Phase 4 (Kochmodus) docken dort an, statt Mealies Seite umzubauen.
- Ein ruhiger, eigener Look für die ganze App, hell und dunkel.
- Mealies Code bleibt weitgehend, wie er ist: Einkaufsliste, Essensplaner, Einstellungen, Bearbeiten, Kochmodus und Prüfansicht behalten ihre Seiten, nur in den neuen Farben.

## Nicht-Ziele (später oder nie)

- Eigene Startseite mit Kachel-Raster wie im Mockup: Die Startseite bleibt Mealies Seite, auf dem Handy mit Listenkarten. Ein Raster kommt, wenn es nach dem Alltagstest fehlt.
- Neuer Name und Logo: Phase 8, nach der Namensprüfung (T7). Bis dahin zeigt die Kopfzeile den Arbeitsnamen „Küchenhelfer“ neben Mealies Logo.
- Portionsrechner mit „Ich habe nur …“ und Backform, Mengen im Text, Timer: Phase 3 und 4. Die Rezeptseite lässt dafür Platz.
- Sterne, Kommentare und der Block „Zuletzt gemacht“: ausgeblendet. Ein Schalter kommt erst, wenn sie jemand vermisst.
- Farben in der App einstellbar: nein; wer anders will, ändert `themes.py`.

## Look „Salbei“

| Rolle | Hell | Dunkel |
|---|---|---|
| Akzent (Knöpfe, aktiver Tab) | `#2F7A55`, darauf weiße Schrift (5,2:1) | `#4FB07E`, darauf dunkle Schrift |
| Grund | `#F4F5F1` | Mealies `#1E1E1E` |
| Flächen (Karten, Leiste) | `#FFFFFF` | Mealies Flächen |
| Hinweis-Fläche und -Text | `#E6F2EC` / `#256447` | Akzent mit 16 % Deckkraft / `#4FB07E` (4,9:1) |
| Warnung | `#FBEBDD` / `#8F4512` | Mealies `warning` |
| Fehler | `#B42318` | Mealies `error` |

- Schrift: die **Systemschrift** des Geräts (auf iPhone und iPad San Francisco), es wird keine Schrift geladen. (1.11.2026: statt Figtree aus dem Mockup, weil Mealies `@nuxt/fonts` beim Bauen Google nicht erreicht und die Systemschrift Datei und Lizenz spart.)
- Text und gedämpfter Text (`#1D1F1C`, `#5E625C`) erreichen auf Grund und Flächen mindestens 4,5:1.
- Mealies Standardfarben (`mealie/core/settings/themes.py`) werden die Salbei-Farben; die Rückfallwerte im Frontend (`plugins/theme.ts`) ebenso. Dort steht auch der helle Grund, so wie Mealie dort den dunklen setzt. Die Schrift setzt eine CSS-Datei im kh-Layer.

## Navigation

**Handy und iPad hochkant (unter 960 px):** Leiste unten mit vier Zielen, Eingang mit der Zahl wartender Entwürfe. Kein Seitenmenü und kein Menü-Knopf. Die Kopfzeile zeigt den Namen und die Suche; „Abmelden“ zieht nach „Mehr“ um.

**iPad quer und Computer (ab 960 px):** Mealies Seitenmenü bleibt, mit denselben Zielen in derselben Reihenfolge. Der Knopf „Erstellen“ bietet „Rezept hinzufügen“ (Eingang) und „Selbst eintippen“ (Mealie).

| Ziel | Leiste | Seitenmenü | Adresse |
|---|---|---|---|
| Rezepte | ja | ja | `/g/<gruppe>` (Mealie) |
| Eingang (n) | ja | ja | `/g/<gruppe>/drafts` |
| Einkaufsliste | ja | ja | `/shopping-lists` (Mealie; gibt es genau eine Liste, öffnet Mealie sie direkt) |
| Mehr | ja | nein | `/g/<gruppe>/more` (neu) |
| Essensplaner, Kochbücher | unter Mehr | ja | Mealie |
| Was kann ich kochen? | unter Mehr | ja | `/g/<gruppe>/recipes/finder` (Mealies Rezept-Finder) |
| Favoriten, Organisieren, Zeitstrahl | unter Mehr | ja (Favoriten unter dem eigenen Namen) | Mealie |

Beide Darstellungen lesen ihre Ziele aus **einer** Liste (Code-Regel 2). „Mehr“ gibt es nur in der Leiste; ab 960 px stehen dieselben Ziele direkt im Seitenmenü, Profil, Einstellungen und Abmelden bleiben dort, wo Mealie sie hat. Mealies einzelne Kochbücher im Seitenmenü bleiben.

**Seite „Mehr“:** Planen: Essensplaner, Kochbücher, Was kann ich kochen? · Sammlung: Favoriten, Kategorien, Schlagworte, Utensilien, Zeitstrahl · Einstellungen: Benutzereinstellungen (Mealies Übersicht mit Profil, Haushalt, Gruppe und KI-Anbietern, dort auch die Geräte-Schlüssel für den Kurzbefehl), Familie einladen, Sprache, Hell/Dunkel, Datenverwaltung und Verwaltung für die, die dürfen · Abmelden · darunter „Küchenhelfer <Version> · basiert auf Mealie · Quellcode (AGPL)“. Damit ist auf dem Handy alles erreichbar, was heute im Seitenmenü steht.

## Eingang

- Eine Seite `/g/<gruppe>/drafts`: oben „Neues Rezept“ mit Link, Text oder Foto, so wie die heutige Seite „Rezept hinzufügen“ (mit Fotovorschau und Entfernen). Darunter die Entwürfe, wie die heutige Liste. Dazu ein kleiner Link „Selbst eintippen“ zu Mealies Seite und ein Satz zum Kurzbefehl.
- `/drafts/new` und Mealies Import-Seiten führen weiter dorthin und behalten ihre Parameter, damit ein geteilter Link vorausgefüllt ankommt.

## Startseite „Rezepte“

- Mealies Seite im neuen Look. Über der Suche steht der Hinweis „n Entwürfe warten auf Prüfung“, wenn es welche gibt; er führt in den Eingang.
- Die Sterne auf den Rezeptkarten fallen weg, wie auf der Rezeptseite.

## Rezeptseite

Eine eigene Ansicht im kh-Layer ersetzt Mealies Ansicht. Bearbeiten und Kochmodus bleiben Mealies; die Seite wechselt wie bisher dorthin. Von oben nach unten:

1. Bild (ohne Bild eine ruhige Fläche mit Symbol), darauf Zurück, Favorit (Herz) und Menü ⋯.
2. Titel, darunter „Geprüft“ mit Herkunft und Link zum Original (der bestehende Herkunfts-Hinweis).
3. Zeiten als Kacheln (Vorbereiten, Kochen oder Backen, Gesamt), nur die vorhandenen.
4. Menge mit − und +: Mealies Skalierung, Anzeige mit Mealies Mengenangabe („12 Stücke“, „1 Portion“, richtige Einzahl und Mehrzahl). Ohne Mengenangabe kein Regler.
5. Zutaten zum Abhaken (Mealies Zutatenliste mit Abschnitten und Notizen), darunter „Auf die Einkaufsliste“.
6. Zubereitung als nummerierte Schritte mit Abschnittstiteln; Text wie bei Mealie über `SafeMarkdown`.
7. Notizen, Nährwerte (nur wenn der Haushalt sie zeigt, Mealies Einstellung) und der Schalter „Bildschirm nicht abschalten“.
8. Unten fest: „Kochen starten“ (Mealies Kochmodus).

**Menü ⋯** nutzt Mealies vorhandene Aktionen: Bearbeiten, In den Essensplan, Als gekocht markieren, Teilen und Drucken, Original ansehen (nur mit Quelle), Löschen.

**Ausgeblendet:** Sterne, Kommentare, der Block „Zuletzt gemacht“, Kategorie- und Schlagwort-Chips (beim Bearbeiten und in Suche und Filter bleiben sie), der Einheiten-Umschalter („As written“).

## Bausteine

| Baustein | Aufgabe |
|---|---|
| `frontend/kh/app/composables/use-kh-navigation.ts` (neu) | die Ziele für Leiste, Seitenmenü und „Mehr“ in einer Liste |
| `frontend/kh/app/components/KhBottomNav.vue` (neu) | Leiste unten, nur unter 960 px |
| `frontend/kh/app/pages/g/[groupSlug]/more.vue` (neu) | Seite „Mehr“ |
| `frontend/kh/app/components/KhDraftHint.vue` (neu) | Hinweis auf wartende Entwürfe über der Startseite |
| `frontend/kh/app/components/KhRecipeView.vue` (neu, bei Bedarf in Teile zerlegt) | eigene Rezeptansicht aus Mealies Bausteinen |
| `frontend/kh/app/pages/g/[groupSlug]/drafts/index.vue` (geändert) | Eingang mit Formular und Entwürfen; das Formular zieht aus `new.vue` in eine Komponente |
| `frontend/kh/app/pages/g/[groupSlug]/drafts/new.vue` (wird Weiterleitung) | alte Adresse bleibt gültig |
| `frontend/kh/app/assets/kh-theme.css` (neu), `frontend/kh/nuxt.config.ts` | Schrift |
| `frontend/kh/lang/en-US.json`, `de-DE.json` | neue Texte |
| `mealie/core/settings/themes.py`, `frontend/app/plugins/theme.ts` (Mealie, `KH:`) | Salbei als Standard- und Rückfallfarben, heller Grund |
| `mealie/core/settings/branding.py` (Mealie, `KH:`) | Name „Küchenhelfer“ in Kopfzeile, Browser-Tab und App-Manifest |
| `DefaultLayout.vue`, `AppHeader.vue` (Mealie, `KH:`) | Leiste einhängen, Seitenmenü aus der gemeinsamen Liste, Menü-Knopf und Abmelden nur ab 960 px, helle Kopfzeile wie im Mockup |
| `RecipePage.vue` (Mealie, `KH:`) | in der Ansicht unsere Rezeptansicht; Bearbeiten und Kochmodus unverändert |
| `RecipeCardMobile.vue`, `RecipeCard.vue` (Mealie, `KH:`) | Sterne ausblenden |
| `RecipeExplorerPage` (Mealie, `KH:`) | Entwürfe-Hinweis einhängen |
| `docs/kh/README.md` | kurz die neue Navigation |

Keine neuen API-Endpunkte, keine Migration, keine neuen Einstellungen.

## Kompatibilität

- Alle bisherigen Adressen bleiben gültig, auch `/drafts/new`, Mealies Import-Seiten, `/recipes/finder` und `/recipes/timeline`.
- Kurzbefehl und API bleiben unverändert.
- Mealies Tests bleiben grün; wo eine `KH:`-Änderung Mealies Verhalten ändert (Sterne, Ansicht), wird der Mealie-Test angepasst und markiert.

## Fehlerfälle

- Entwürfe-Zahl nicht ladbar (offline): Eingang ohne Zahl, nichts blockiert.
- Theme nicht ladbar: die Rückfallfarben sind ebenfalls Salbei.
- Rezept ohne Bild, Zeiten, Mengenangabe, Notizen oder Quelle: der jeweilige Teil entfällt, ohne Lücke.
- Lange Titel und Zutaten brechen um; nichts wird abgeschnitten.

## Barrierefreiheit

- Tippflächen mindestens 44 px; Kontrast mindestens 4,5:1 (hell und dunkel).
- Leiste mit `aria-current`; Eingang nennt die Zahl auch für Screenreader; Symbol-Knöpfe haben Beschriftungen.
- Zutaten sind echte Checkboxen mit Beschriftung.

## Sicherheit und Datenschutz

- Es wird keine Schrift geladen, auch nicht von Google; die Tabelle „Was geht wohin“ bleibt unverändert.
- Rezepttexte laufen weiter über Mealies `SafeMarkdown`; Links zum Original nur bei `http(s)` (wie bisher).

## Tests

- Vitest: die gemeinsame Zielliste (Ziele, Zahl, aktiver Eintrag, Leiste ohne „Mehr“-Ziele), Weiterleitung von `/drafts/new` mit Parametern, welche Teile die Rezeptansicht ohne Bild, Zeiten, Mengenangabe, Notizen oder Quelle zeigt.
- Pytest: `/api/app/about/theme` liefert die Salbei-Farben.
- Von Hand in einer Wegwerf-Installation: Handy-, iPad- und Computer-Breite, hell und dunkel; im Netzwerk-Mitschnitt keine Anfrage an `fonts.googleapis.com` oder `fonts.gstatic.com`.

## Einführung

- Zwei Releases, damit jede Änderung einzeln im Alltag geprüft wird:
  - `v0.1.2` Rahmen: Look und Schrift, Leiste, „Mehr“, Seitenmenü, Eingang auf einer Seite, Entwürfe-Hinweis, Sterne aus.
  - `v0.1.3` Rezeptseite.
- Beide kommen über die automatischen Updates; Upgrade-Test wie immer (keine Datenänderung).

## Später

- Startseite als Raster, wenn gewünscht.
- Schalter für Sterne und Kommentare, wenn sie vermisst werden.
- iPad quer: Rezeptseite zweispaltig (Zutaten neben den Schritten).
- Name und Logo (Phase 8).
