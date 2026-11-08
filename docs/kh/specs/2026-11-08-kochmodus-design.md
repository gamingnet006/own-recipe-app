# Kochmodus `v0.3` (D42) · Design

Stand 8.11.2026. Abgestimmt über die Vorschlagsseite: sechs Entscheidungen E1 bis E6, alle wie empfohlen. Phase 4 aus `PLAN.md`; Sprachbefehle kommen als `v0.3.1` nach Test T2.

## Ziel

- In der Küche ohne Suchen kochen: Ein Schritt steht groß auf dem Bildschirm, Weiter und Zurück sind mit nassen Händen zu treffen.
- Zeiten aus dem Rezept werden mit einem Tipp zum Timer, und der Timer klingelt auch dann, wenn man nicht hinschaut.
- Jeder Schritt nennt die Menge der Zutat, die er braucht, passend zum Portionsrechner.
- Ein Rezept, das man gerade geöffnet hatte, bleibt lesbar, wenn das Netz kurz weg ist.

## Nicht-Ziele

- Sprachbefehle: kommen als `v0.3.1`, wenn T2 zeigt, dass Vosk auf dem iPhone mit Küchenlärm taugt.
- Push-Mitteilungen vom Server: nur falls T1 zeigt, dass der Uhr-Timer per Kurzbefehl nicht klingelt. Dann gibt es eine eigene Spezifikation.
- Zeiten mit dem Portionsfaktor umrechnen: Zeiten bleiben fest (Phase 3); den Hinweis bei Faktor über 2 oder unter 0,5 gibt es schon.
- Rezepte gezielt zum Offline-Lesen speichern, offline bearbeiten, die Rezeptliste offline: nein.
- Der Server ändert sich nicht: keine Migration, kein neuer Endpunkt, keine neue Python-Abhängigkeit.

## E1 · Schritt-Ansicht

- Mealies Kochmodus (`?cook=true`) bleibt der Einstieg; „Kochen starten“ aus `KhCookBar` führt wie bisher hinein.
- Im Kochmodus zeigt ein neues `KhCookStep` statt Mealies Liste genau einen Schritt.
  - Oben links „✕“: Damit verlässt man den Kochmodus und kommt zurück zur Rezeptseite. Rechts steht „Alle Schritte“.
  - Darunter ein schmaler Balken (4 px) mit einem Abschnitt je Schritt (8.11.2026, Anregung aus Kitchen Stories): erledigte Schritte gefüllt, der aktuelle betont. Ein Tipp auf einen Abschnitt springt zu diesem Schritt, auch zurück. Daneben „Schritt 3 von 7“. Ab 12 Schritten werden die Abschnitte zu einem durchgehenden Balken, und das Springen geht über „Alle Schritte“.
  - Darunter eine ruhige Zeile „Du brauchst: Butter 200 g · Zucker 150 g“ mit den Zutaten, die mit diesem Schritt verknüpft sind (statt Chips). Die Mengen folgen dem Portionsfaktor. Ist eine Zutat auf mehrere Schritte verteilt, steht dort nur ihr Name ohne Menge, denn die Gesamtmenge würde zu „die Hälfte der Semmelbrösel“ nicht passen. Ohne verknüpfte Zutaten fehlt die Zeile.
  - Kochutensilien pro Schritt gibt es nicht: Mealie kennt Utensilien nur für das ganze Rezept, und die stehen schon auf der Rezeptseite.
  - Dann der Schritttext in großer Schrift, darunter die laufenden Timer.
  - Unten zwei große Tasten, immer an derselben Stelle direkt über der Leiste unten, auch bei kurzen Schritten (8.11.2026, Wunsch: beim Kochen nur eine Stelle anfassen): „Zurück“ (schmal) und „Weiter“ (breit, Akzentfarbe). Im letzten Schritt heißt „Weiter“ „Fertig“ und beendet den Kochmodus.
- Wischen nach links geht weiter, nach rechts zurück (`useSwipe` aus `@vueuse/core`, schon vorhanden). Am iPad mit Tastatur gehen auch die Pfeiltasten und die Leertaste.
- „Alle Schritte“ schaltet auf Mealies Liste um. Ein Tipp auf einen Schritt dort hakt ihn ab wie bisher (8.11.2026, geändert: beim Kochen ist das Abhaken wichtiger als das Springen). Neben Mealies Schließen-Taste steht „Schritt für Schritt“; sie führt zurück in die Schritt-Ansicht, zum aktuellen Schritt.
- Der aktuelle Schritt steht in der Adresse (`&step=3`), so bleibt er beim Neuladen erhalten.
- Abschnitts-Überschriften aus Mealie (Schritte mit Titel) erscheinen über dem Schritt.
- Die Bildschirmsperre ist im Kochmodus aus (`useWakeLock`) und wird beim Verlassen wieder freigegeben, unabhängig von Mealies Schalter. Kann das Gerät das nicht, kommt ein einmaliger Hinweis, die automatische Sperre selbst länger zu stellen.
- Andocken: Mealies `RecipePage.vue` bekommt im Kochmodus-Zweig eine Weiche zwischen `KhCookStep` und der vorhandenen Liste, markiert mit `KH:`. Sonst bleibt Mealies Code, wie er ist.

## E2 · Mengen neben Zutaten im Schritt (D41)

- Darstellung: in Klammern direkt hinter dem Zutatennamen, etwas blasser: „die Butter (200 g) schmelzen“.
- Gilt überall, wo Schritttext steht: auf der Rezeptseite und im Kochmodus, in beiden Ansichten. Die Klammer folgt dem Portionsrechner.
- Eine Menge kommt nur dazu, wenn alles davon zutrifft:
  1. Die Zutat ist über Mealies `ingredientReferences` mit genau diesem einen Schritt verknüpft.
  2. Ihr Name steht im Satz, als Name oder Mehrzahl des Lebensmittels (`food.name`, `food.pluralName`), ohne Rücksicht auf Groß- und Kleinschreibung und als ganzes Wort.
  3. Im Schritt steht für diese Zutat noch keine Menge, also gibt es dafür keine Mengen-Stelle aus Phase 3.
  4. Die Zutat hat eine Menge.
- Nur beim ersten Vorkommen im Schritt.
- Ist eine Zutat über mehrere Schritte verknüpft oder fehlt eine Bedingung, bleibt der Satz unverändert. So steht nie eine falsche Menge da.
- Der gespeicherte Text bleibt unverändert; die Klammer entsteht nur beim Anzeigen.
- Mealies Markdown im Schritt bleibt erhalten. Die Klammer kommt als `<span class="kh-amount">` in den Text, den `SafeMarkdown` darstellt; `span` mit `class` lässt Mealies Bereinigung durch.
- Eine Funktion für alle Ansichten, neben `khStepText()`: Die Anzeige erweitert nur die bestehende Stelle, an der Phase 3 Mengen umrechnet.

## E3 · Zeiten werden Timer

- `parseTimes(text)` findet Zeiten im Schritttext und liefert je Fund: Stelle im Text, Dauer in Sekunden und bei Spannen die längere Dauer.
- Erkannt werden:
  - Zahlen mit Einheit: „10 Min.“, „10 Minuten“, „1 Std.“, „1,5 Stunden“, „1½ Stunden“, „45 Sek.“.
  - Kombinationen als ein Timer: „1 Std. 20 Min.“, „1 Stunde und 20 Minuten“.
  - Spannen: „20–30 Min.“, „20-30 Minuten“, „20 bis 30 Minuten“, „1–2 Std.“.
  - Wörter: „eine Minute“, „eine halbe Stunde“, „eine Viertelstunde“, „eine Dreiviertelstunde“, „anderthalb Stunden“, „zwei Stunden“ (Zahlwörter bis zwölf).
  - Englische Rezepte, die nicht übersetzt wurden: „10 minutes“, „10 mins“, „1 hour“, „1 hr“, „1-2 hours“.
- Nicht erkannt werden Angaben ohne feste Dauer wie „über Nacht“, „einige Stunden“, „mehrere Minuten“ oder „ein paar Minuten“, außerdem Temperaturen und Mengen.
- Im Text wird eine erkannte Zeit hervorgehoben (`<span class="kh-time">`, Weg wie in E2). Ein Tipp darauf startet einen Timer, und ein Tipp auf einen laufenden Timer hält ihn an.
- Bei einer Spanne läuft der Timer bis zur kürzeren Zeit. Wenn er klingelt, gibt es neben „Aus“ die Taste „noch 10 Min.“, also die Differenz zur längeren Zeit.
- Timer:
  - Mehrere laufen gleichzeitig, jeder mit Namen, nämlich der Schrittnummer und den ersten Wörtern des Satzes.
  - Sie liegen in einem gemeinsamen Speicher (`use-kh-timers`) und bleiben beim Wechsel der Schritte und der Ansicht sichtbar.
  - Im Kochmodus stehen sie unter dem Schritt, auf der Rezeptseite als schmale Leiste über der Leiste unten.
- Ein Timer merkt sich seine Endzeit, nicht die verbleibenden Sekunden. So zeigt er nach Sperren, Wechsel der App oder Ruhezustand des Browsers die richtige Restzeit, und ein abgelaufener Timer zeigt beim Zurückkommen sofort „fertig“.
- Die Timer gelten für das Gerät und überleben das Neuladen der Seite (`localStorage`). Läuft ein Timer eines anderen Rezepts, verlinkt sein Name dorthin.

## E4 · Timer, die man hört

- **In der App (Grundlage):**
  - Ist ein Timer abgelaufen, spielt die App einen Weckton, bis man „Aus“ tippt, höchstens zwei Minuten lang. Wo das Gerät es kann, vibriert es dazu.
  - Der Ton wird im Browser erzeugt (Web Audio), es kommt keine Tondatei ins Repo.
  - Damit iOS den Ton erlaubt, wird die Wiedergabe beim ersten Tipp auf einen Timer freigeschaltet.
  - Weil die Bildschirmsperre im Kochmodus aus ist (E1), klingelt es, solange der Kochmodus offen ist.
- **„Auf Uhr-Timer legen“:**
  - Diese Taste hängt an T1 und kommt nur, wenn T1 klappt.
  - Neben jedem Timer startet sie den echten Timer der Uhr-App, und der klingelt auch bei gesperrtem Handy. Technisch öffnet sie `shortcuts://run-shortcut?name=<Name>&input=text&text=<Minuten>`.
  - Der Kurzbefehl wird einmal pro Gerät eingerichtet, mit zwei Aktionen wie im Test T1. Die Anleitung kommt in die README neben „Ins Kochbuch“.
  - Die Taste erscheint erst, wenn man sie am Gerät einschaltet. Der Schalter liegt unter „Mehr“, zusammen mit dem Namen des Kurzbefehls, Standard „KH Timer“, und wird auf dem Gerät gespeichert. Ohne eingerichteten Kurzbefehl würde iOS sonst nur eine Fehlermeldung zeigen.
  - Geht T1 schief, fällt diese Taste weg, und Push wird in einer eigenen Spezifikation geprüft.

## E5 · Sprachbefehle

Nicht in `v0.3`. Weil Weiter und Zurück eigene Funktionen der Schritt-Ansicht sind, kann `v0.3.1` die Sprachbefehle daran anschließen, ohne die Ansicht umzubauen.

## E6 · Rezepte offline

- Mealies Service Worker (`@vite-pwa/nuxt`, Workbox) hält schon die App-Dateien vor. Dazu kommt `runtimeCaching` in `frontend/nuxt.config.ts` (mit `KH:` markiert):
  - **Rezeptdaten:** `GET /api/recipes/<slug>` und `GET /api/kh/amounts/…`, mit Strategie `NetworkFirst`. Sie laden immer frisch, und nur ohne Netz kommt die gespeicherte Fassung. Höchstens 30 Einträge, die ältesten fallen heraus.
  - **Rezeptbilder:** `/api/media/recipes/…`, mit Strategie `CacheFirst`, höchstens 150 Einträge und 30 Tage.
- Die Zahlen stehen als benannte Werte an einer Stelle in der Konfiguration.
- Ohne Netz zeigt die Rezeptseite oben „Offline: gespeicherte Fassung“. Ein Rezept, das nicht gespeichert ist, zeigt Mealies normale Fehlermeldung.
- Beim Abmelden werden diese Speicher gelöscht (`caches.delete`): `signOut()` in `use-auth-backend.ts` bekommt einen Aufruf mit `KH:`. So bleiben auf einem geteilten Gerät keine Rezepte zurück.
- Safari kann den Speicher einer Website nach Wochen ohne Besuch selbst leeren. Das ist in Ordnung, weil es nur um die zuletzt geöffneten Rezepte geht.

## Dateien

| Datei | Zweck |
|---|---|
| `frontend/kh/app/lib/times.ts` | `parseTimes()`: Zeiten im Text erkennen |
| `frontend/kh/app/lib/step-text.ts` | Schritttext für die Anzeige: Mengen-Klammern (E2) und Zeit-Hervorhebung (E3) als `span`, auf Basis von `khStepText()` |
| `frontend/kh/app/composables/use-kh-timers.ts` | Timer-Speicher, Endzeiten, Weckton, Vibration, Uhr-Timer-Link |
| `frontend/kh/app/composables/use-kh-cook.ts` | aktueller Schritt, Weiter und Zurück, Bildschirmsperre |
| `frontend/kh/app/components/KhCookStep.vue` | die Schritt-Ansicht |
| `frontend/kh/app/components/KhTimers.vue` | Liste der laufenden Timer (Kochmodus und Rezeptseite) |
| `frontend/kh/lang/{de-DE,en-US}.json` | neue Texte |
| Mealie, mit `KH:` | `RecipePage.vue` (Weiche im Kochmodus), `RecipePageInstructions.vue` (Klick auf Zeiten), `nuxt.config.ts` (`runtimeCaching`), `use-auth-backend.ts` (Speicher beim Abmelden leeren), `more.vue` (Schalter Uhr-Timer) |

Ob `step-text.ts` eine eigene Datei wird oder in `amounts-store.ts` aufgeht, entscheidet der Bauplan nach Regel „eine Datei, ein Thema“.

## Tests

- Vitest für `parseTimes()`: jede Form aus E3, die Ausschlüsse, Spannen, Kombinationen und Englisch.
- Vitest für den Schritttext:
  - Klammer nur unter den vier Bedingungen aus E2;
  - Mehrzahl, Groß- und Kleinschreibung, ganzes Wort;
  - keine Klammer bei mehreren Schritten oder vorhandener Menge;
  - Markdown bleibt erhalten;
  - die Klammer folgt dem Faktor.
- Vitest für `use-kh-timers` mit falscher Uhr: Endzeit nach Ruhezustand, Spanne und „noch … Min.“, mehrere Timer, Speichern und Laden.
- Vitest für `use-kh-cook`: Weiter, Zurück, Grenzen, `step` in der Adresse, „Fertig“.
- Alle Tests laufen ohne Netz und ohne KI. Das Backend ist nicht betroffen, seine Tests müssen trotzdem grün bleiben.
- Von Hand am iPhone, bevor die Phase fertig ist:
  - Kochmodus mit Tasten und Wischen;
  - Timer klingelt bei offenem Kochmodus;
  - Uhr-Timer klingelt bei gesperrtem Handy, wenn T1 klappt;
  - ein geöffnetes Rezept im Flugmodus.

## Fertig wenn

Auf dem iPhone klingelt ein Timer bei gesperrtem Handy (über den Uhr-Timer) und die Tasten führen durch die Schritte (PLAN Phase 4). Ist T1 gescheitert, gilt der erste Teil erst mit der Push-Spezifikation.

## Offene Punkte

- T1 macht der Nutzer am iPhone. Die Anleitung steht auf der Vorschlagsseite, und das Ergebnis entscheidet über „Auf Uhr-Timer legen“.
- T2 kommt vor `v0.3.1`.
