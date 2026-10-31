# Phase 2: Eingang, Prüfen, Duplikate (v0.1) · Design

Stand 31.10.2026, im Chat Abschnitt für Abschnitt freigegeben (Weg 1: eigene Entwurfs-Funktion, die Mealies Erkennung mitbenutzt).

## Ziel

- Rezepte aus Link, Text, Foto oder Screenshot landen immer erst als **Entwurf**; ins Kochbuch kommt nur, was jemand freigibt (D18).
- Gebaut für Handy und iPad, weil die Familie dort Rezepte hinzufügt; am Computer geht es genauso.
- Erkannt wird mit Mealies vorhandenen Bausteinen; die KI kommt über einen kostenlosen Gemini-Schlüssel (D34).
- Mögliche Duplikate werden gemeldet, nie automatisch gelöscht.
- **Fertig wenn** (PLAN.md, Phase 2): Ein Foto eines handgeschriebenen Rezepts landet als Entwurf in der Prüfansicht, die Testfälle (ohne Video) ergeben prüfbare Entwürfe, nichts wird ohne Freigabe gespeichert, und die Duplikat-Testfälle schlagen an. Danach Release `v0.1`.

## Entscheidungen aus dem Gespräch (31.10.2026)

| Frage | Antwort |
|---|---|
| Wie kommen Rezepte an? | Bunt gemischt: Fotos, Links, Screenshots, Text, alle gleich wichtig |
| Wer fügt hinzu, womit? | Du und die Familie, meist am Handy und oft am iPad |
| Wer gibt frei? | Jeder im Haushalt jeden Entwurf, der Admin eingeschlossen |
| KI und Datenschutz | Kostenlos und gut zählt; Training durch den Anbieter ist in Ordnung, er steht in „Was geht wohin“ |
| Teilen aus anderen Apps | Erst in Küchenhelfer selbst; „Teilen“ per Kurzbefehl als eigener Schritt danach (`v0.1.1`) |
| Weg | Eigene Entwurfs-Funktion, Mealies Erkennung mitbenutzen (statt Mealies Anlegen-Seiten umzubauen oder Rezepte als „Entwurf“ zu markieren, was D18 widerspräche) |

## Nicht-Ziele

- Videos (Reels, TikToks) und jeder Video-Downloader (Leitplanke); Screenshots solcher Beiträge gehen.
- Ein eigener Rezept-Editor: „Übernehmen und bearbeiten“ öffnet Mealies Bearbeiten-Ansicht.
- Eigene lokale KI (D34) und automatisches Ausweichen auf einen zweiten KI-Anbieter.
- Der Kurzbefehl „Teilen“: eigener Schritt nach `v0.1`; er nutzt denselben Eingang.
- Unverändert bleiben Mealies leeres Rezept zum Selbst-Eintippen, der Import eigener Mealie-Zip-Exporte und die Scraper-Diagnose.

## Bausteine

| Baustein | Aufgabe |
|---|---|
| `mealie/kh/drafts/models.py` | Tabelle `kh_drafts` (Import in `mealie/db/models/_all_models.py`) |
| `mealie/kh/alembic/versions/` | additive Migration im Zweig `kh` (D24) |
| `mealie/kh/drafts/schemas.py` | Pydantic-Schemas mit Mealies Endungen (`DraftCreate`, `DraftOut`, …) |
| `mealie/kh/drafts/settings.py` | Grenzen und Schwellen aus der Umgebung, wie `mealie/kh/features/settings.py` |
| `mealie/kh/drafts/service.py` | Entwurf anlegen, im Hintergrund erkennen, übernehmen, verwerfen, aufräumen |
| `mealie/kh/drafts/duplicates.py` | Link bereinigen, Titel- und Zutaten-Ähnlichkeit |
| `mealie/kh/drafts/routes.py` | `/api/kh/drafts…`, eingehängt in `mealie/kh/__init__.py` |
| `tests/kh/drafts/` | Backend-Tests; KI nur mit aufgezeichneten Antworten (D23) |
| `frontend/kh/app/pages/g/[groupSlug]/drafts/` | Eingang (`new`), Liste (`index`), Prüfansicht (`[id]`) |
| `frontend/kh/app/components/`, `composables/` | Bausteine der Prüfansicht, Herkunfts-Abzeichen, API-Zugriff |
| `frontend/kh/app/middleware/` (global) | leitet Mealies Import-Seiten auf den Eingang um |
| Mealies Seitenleiste und Rezeptansicht (`KH:`-Kommentar) | Menüpunkt „Entwürfe (n)“; Herkunfts-Abzeichen und „Original ansehen“ |
| `frontend/kh/lang/en-US.json`, `de-DE.json` | Texte |
| `kh/ops/docker-compose.yml`, `kh/ops/.env.example` | reichen die `KH_DRAFT_…`- und `KH_DUPLICATE_…`-Einstellungen durch |
| `docs/kh/README.md` | Gemini-Schlüssel einrichten, Tabelle „Was geht wohin“, Liste „Stick verloren“ um den KI-Schlüssel ergänzt |

## Daten

Tabelle `kh_drafts`, eine Zeile je Entwurf; nach der Freigabe bleibt sie als Herkunftsnachweis am Rezept:

| Spalte | Inhalt |
|---|---|
| `id` | UUID |
| `group_id`, `household_id` | Zuordnung wie bei Rezepten; nur dieser Haushalt sieht den Entwurf |
| `user_id`, `created_at`, `updated_at` | wer, wann |
| `status` | `working` (in Arbeit), `ready` (bereit), `failed` (Fehler), `approved` (übernommen) |
| `source_type` | `link`, `text` oder `image` (Foto und Screenshot) |
| `source_url`, `source_url_normalized` | der eingegebene und der bereinigte Link |
| `source_text` | eingefügter Text |
| `original_files` | Dateinamen der Originalbilder |
| `recipe` | das erkannte Rezept als JSON in Mealies `Recipe`-Schema, noch nicht gespeichert |
| `warnings` | Hinweise für die Prüfung, darunter Duplikate mit Verweis auf Rezept oder Entwurf |
| `error` | verständlicher Grund bei `failed` |
| `ai_model` | Anbieter und Modell, leer, wenn keine KI beteiligt war |
| `recipe_id` | gesetzt bei `approved`; Fremdschlüssel auf das Rezept mit `ON DELETE CASCADE` |
| `approved_by`, `approved_at` | wer übernommen hat, wann |

- **Originalbilder:** `DATA_DIR/kh/drafts/<id>/original-<n>.webp`, verkleinert wie Mealies Rezeptbilder (längste Seite höchstens 2048 px, WebP). iPhone-Fotos (HEIC) liest Mealie schon über `pillow-heif`. Die Dateinamen vergibt Küchenhelfer, nie der Absender.
- **Bilder der Erkennung:** Mealies `finalize_scraped_recipe` gibt dem erkannten Rezept schon eine ID und legt dessen Bild unter `DATA_DIR/recipes/<recipe.id>/` ab. Das Übernehmen speichert das Rezept mit genau dieser ID. Verwerfen und „Neu versuchen“ löschen den Ordner zur `recipe.id` des Entwurfs, aber nur, wenn es kein Rezept mit dieser ID gibt.
- **Aufräumen beim Start:** Ordner unter `DATA_DIR/kh/drafts/` ohne Eintrag gehen weg, etwa nach dem Löschen eines Rezepts, dessen Eintrag per `CASCADE` verschwand. Mealies Rezeptordner fasst das Aufräumen nie an.
- Alles liegt im Datenordner und ist damit in jedem Backup und auf dem Stick.

## Ablauf

1. **Anlegen:** `POST /api/kh/drafts` (multipart) mit genau einer Quelle: `url`, `text` oder `images` (1 bis `KH_DRAFT_MAX_IMAGES`). Grenzen verletzt, ergibt sofort 400 ohne Entwurf. Sonst entsteht ein Eintrag `working`, die Originale werden gespeichert, die Erkennung startet als Hintergrundaufgabe, und die Antwort kommt sofort mit der Entwurfs-ID.
2. **Erkennen** (Hintergrund):
   - `link`: zuerst Mealies Webseiten-Leser `create_from_html(url, …)`, ohne KI und über Mealies sicheren Abruf. Findet er keine Rezeptdaten, folgt `AIRecipeService.build_recipe(url=…)`.
   - `text`: `build_recipe(content=…)`; `image`: `build_recipe(images=[…])`. Beide speichern kein Rezept, nur das Erkennungsbild (siehe Daten).
   - Das Ergebnis wird gegen Mealies `Recipe`-Schema geprüft und in `recipe` abgelegt. Danach folgt die Duplikat-Prüfung, dann `ready`. Jeder Fehler ergibt `failed` mit Grund (siehe Fehlerfälle).
   - Hängt ein Entwurf länger als `KH_DRAFT_STALE_MINUTES` in `working`, etwa nach einem Neustart mittendrin, gilt er als `failed` mit dem Grund „unterbrochen“.
3. **Neu versuchen:** `POST /api/kh/drafts/{id}/retry` bei `failed`; zurück auf `working`, die Erkennung startet neu.
4. **Übernehmen:** `POST /api/kh/drafts/{id}/approve` bei `ready`.
   - Die Duplikate werden erneut geprüft. Gibt es neue Treffer, kommt die Antwort mit Hinweis; erst `force=true` übernimmt trotzdem.
   - Gespeichert wird über `RecipeService.create_one(recipe)` wie bei Mealies Import. Bei `image` wird das erste Original zum Rezeptbild, wie bei Mealies `create_from_ai`.
   - Der Statuswechsel auf `approved` ist atomar (`… WHERE status = 'ready'`). Übernehmen zwei Personen gleichzeitig, gewinnt eine; die andere bekommt „schon übernommen“ mit Link.
   - Die Antwort enthält den Rezept-Slug. Die Ansicht öffnet das Rezept oder bei „Übernehmen und bearbeiten“ Mealies Bearbeiten-Ansicht.
5. **Verwerfen:** `DELETE /api/kh/drafts/{id}` bei `ready` oder `failed`; löscht Eintrag, Originale und Erkennungsbilder.
6. **Lesen:**
   - `GET /api/kh/drafts`: alle nicht übernommenen Entwürfe des Haushalts, neueste zuerst, mit Zähler.
   - `GET /api/kh/drafts/{id}`: ein Entwurf.
   - `GET /api/kh/drafts/{id}/originals/{n}`: Originalbild, nur für den Haushalt.
   - `GET /api/kh/recipes/{recipe_id}/origin`: Herkunft für das Abzeichen.

## Ansichten

- **Eingang** (`/g/<gruppe>/drafts/new`): drei große Knöpfe für Link, Text und Foto/Screenshot. Fotos kommen über Kamera oder Mediathek (`<input type="file" accept="image/*" multiple>`).
- **Liste** (`/g/<gruppe>/drafts`): Titel, Vorschaubild, von wem, wann, Stand. Solange etwas in Arbeit ist, aktualisiert sie sich von selbst; bei `failed` gibt es „Neu versuchen“.
- **Prüfansicht** (`/g/<gruppe>/drafts/<id>`):
  - Oben stehen die Hinweise, Duplikate mit Link zum vorhandenen Rezept.
  - Darunter Original und Ergebnis, am Handy untereinander, ab Tablet-Breite (iPad) nebeneinander.
  - Drei Knöpfe: Übernehmen, Übernehmen und bearbeiten, Verwerfen mit Rückfrage.
- **Menü:** „Entwürfe (n)“; n zählt alle nicht übernommenen Entwürfe (in Arbeit, bereit, Fehler).
- **Rezeptansicht:** Herkunfts-Abzeichen (zum Beispiel „Aus Foto · 31.10.2026 · <Name>“) und „Original ansehen“. Rezepte ohne Herkunftseintrag, also ältere oder selbst eingetippte, zeigen kein Abzeichen.
- **Umleitung:** `/g/<gruppe>/r/create/url`, `…/ai`, `…/image`, `…/html` und `…/bulk` führen auf den Eingang.
- Alle Texte sind auf Deutsch und Englisch. Inhalte aus Entwürfen werden nie als HTML ausgeführt.

## Duplikat-Prüfung

Läuft bei `ready` und beim Übernehmen, gegen alle Rezepte und offenen Entwürfe des Haushalts. Sie liefert nur Hinweise.

- **Gleicher Link:** Bereinigt werden Schema und Host (klein, ohne `www.`), Sprungmarke, Tracking-Parameter (`utm_*`, `fbclid`, `gclid`, `igshid`, `igsh`, `si`, `ref`) und der Schrägstrich am Ende. Dann folgt ein exakter Vergleich mit `source_url_normalized` und mit dem bereinigten `org_url` der Rezepte.
- **Ähnlicher Titel:** klein, ohne Satzzeichen, Wörter sortiert; Ähnlichkeit ab `KH_DUPLICATE_TITLE` (Vorgabe 0,85).
- **Ähnliche Zutaten:** bereinigte Lebensmittelnamen; Überschneidung ab `KH_DUPLICATE_INGREDIENTS` (0,7) zusammen mit einer Titel-Ähnlichkeit ab `KH_DUPLICATE_TITLE_WITH_INGREDIENTS` (0,5).
- Verglichen wird linear mit allen Einträgen; das reicht für ein Familienkochbuch (`ponytail:`-Kommentar mit Ausbaupfad).

## Einstellungen (Umgebung, mit Vorgaben)

| Einstellung | Vorgabe | Zweck |
|---|---|---|
| `KH_DRAFT_MAX_IMAGES` | 5 | Bilder je Entwurf |
| `KH_DRAFT_MAX_IMAGE_MB` | 20 | Größe je Bild vor dem Verkleinern |
| `KH_DRAFT_MAX_TEXT` | 20000 | Zeichen eingefügter Text |
| `KH_DRAFT_STALE_MINUTES` | 15 | ab wann `working` als unterbrochen gilt |
| `KH_DUPLICATE_TITLE` | 0.85 | Titel-Ähnlichkeit allein |
| `KH_DUPLICATE_INGREDIENTS` | 0.7 | Zutaten-Überschneidung |
| `KH_DUPLICATE_TITLE_WITH_INGREDIENTS` | 0.5 | Titel-Ähnlichkeit zusammen mit den Zutaten |

Der KI-Anbieter ist keine Einstellung in `.env`: Er steht in Mealies Verwaltung → KI-Anbieter (D25).

## KI-Anbieter

- **Google Gemini** über den OpenAI-kompatiblen Zugang `https://generativelanguage.googleapis.com/v1beta/openai/`, mit einem kostenlosen Schlüssel aus Google AI Studio. Ein Google-Konto genügt, eine Kreditkarte nicht. Die Quellen stehen im Chat vom 31.10.2026.
- Gemini kann, was Mealie verlangt: Bilder als Base64, Antworten nach festem Schema (`chat.completions.parse`), Streaming. Groq kam nur als Reserve in Frage: ein Bildmodell mit höchstens drei Bildern, und Schema plus Bild sind nicht belegt.
- Die kostenlose Tagesgrenze zeigt nur das Konto. Nach dem Einrichten messe ich, wie viele Anfragen ein Rezept braucht, und trage das in die Anleitung ein.
- Kosten entstehen nicht, solange bei Google kein Bezahlkonto hinterlegt ist; die Anleitung sagt das deutlich.
- Fotos, Screenshots und Texte gehen an Google, und Google darf sie im Gratis-Angebot nutzen. Das steht in „Was geht wohin“.

## Fehlerfälle

| Fall | Ergebnis |
|---|---|
| Keine KI eingerichtet | `failed`: „Keine KI eingerichtet: Verwaltung → KI-Anbieter“; Links mit Rezeptdaten gehen trotzdem |
| Tageskontingent aufgebraucht (Anbieter antwortet 429) | `failed`: „Kontingent für heute aufgebraucht, morgen neu versuchen“ |
| Keine Rezeptdaten auf Seite oder Bild | `failed` mit Mealies Grund |
| Link auf private Adresse (Mealies sicherer Abruf) | `failed`: „Adresse nicht erlaubt“ |
| Zu viele oder zu große Bilder, falscher Dateityp, zu langer Text, keine oder mehrere Quellen | sofort 400, kein Entwurf |
| KI-Antwort passt nicht zum Schema | `failed`: „Erkennung lieferte kein gültiges Rezept“ |
| Neustart während der Erkennung | nach `KH_DRAFT_STALE_MINUTES` `failed`: „unterbrochen“ |
| Übernehmen bei nicht `ready`, Verwerfen bei `working` oder `approved`, „Neu versuchen“ bei nicht `failed` | 409 |
| Entwurf eines anderen Haushalts | 404 |

## Sicherheit

- Links werden nur über Mealies sicheren Abruf (`mealie/pkgs/safehttp/`) geholt. Der sperrt private Adressbereiche (auch CGNAT) und begrenzt Zeit und Größe. Einen eigenen Abruf gibt es nicht.
- Hochgeladen werden nur Bilder (JPEG, PNG, WebP, HEIC), mit Anzahl- und Größengrenze. Text ist begrenzt. Die Dateinamen vergibt Küchenhelfer.
- KI-Antworten werden nur nach festem Schema angenommen und vor dem Speichern noch einmal gegen Mealies Rezeptformat geprüft (Regel 8).
- Ausgaben sind maskiert; Anleitungen laufen über Mealies abgesicherte Markdown-Anzeige.
- Alle Endpunkte verlangen eine Anmeldung und sind auf den Haushalt beschränkt.
- Der KI-Schlüssel liegt in Mealies Datenbank, also in jedem Backup und auch auf dem Stick ohne Passwort. Die Liste „Stick verloren“ bekommt den Punkt „KI-Schlüssel in AI Studio neu erzeugen“.

## Tests

- **Backend** (`tests/kh/drafts/`, pytest, Mealies Fixtures):
  - Anlegen mit allen Grenzen.
  - Haushalts-Trennung: Ein fremder Haushalt sieht, übernimmt und verwirft nichts.
  - Statuswechsel einschließlich „unterbrochen“.
  - Link mit Rezeptdaten ohne KI, an selbst geschriebenem HTML.
  - Link, Text und Bild mit aufgezeichneten KI-Antworten (D23).
  - Übernehmen erzeugt ein Mealie-Rezept mit Bild und Herkunft.
  - Gleichzeitiges Übernehmen.
  - Verwerfen und Aufräumen löschen genau die richtigen Dateien.
  - Duplikat-Fälle: Link mit Tracking-Anhang, Titel anders geschrieben, gleiche Zutaten unter anderem Namen, Gegenproben ohne Treffer.
- **Frontend** (Vitest): Umschalten der Anordnung zwischen Handy und iPad, Zähler, Umleitung.
- **Probelauf von Hand:** Deinen Gemini-Schlüssel trägst du selbst in der Entwicklungs-Installation auf dem MacBook ein. Dann geht es mit iPhone und iPad über Tailscale durch alle vier Eingänge. Der handschriftliche Zettel ist selbst geschrieben.
- Testdaten sind nur selbst geschrieben, nie fremde Rezepte (Regel 9).

## Einführung

1. Entwurfs-Tabelle mit Migration und Zugriffsregeln.
2. Eingang mit Erkennung im Hintergrund (Link, Text, Bilder).
3. Übernehmen und Verwerfen samt Herkunft und Aufräumen.
4. Duplikat-Prüfung.
5. Ansichten: Eingang, Liste mit Zähler, Prüfansicht für Handy und iPad, Herkunfts-Abzeichen, Umleitung, Texte.
6. Anleitung (Gemini-Schlüssel, „Was geht wohin“, „Stick verloren“), dann Probelauf mit echtem Schlüssel.
7. Release `v0.1` mit Upgrade-Test von `v0.0.2` in der CI; der Mac mini holt es nachts.
8. Danach als eigener Schritt: Kurzbefehl „Teilen“ für iPhone und iPad, mit eigenem, widerrufbarem Schlüssel je Gerät (`v0.1.1`).

Fertige Schritte kommen unterwegs nach `main`; der Mac mini installiert nur veröffentlichte Releases.

## Später

- Kurzbefehl „Teilen“ (`v0.1.1`, siehe oben).
- Ein zweiter KI-Anbieter als Ausweichweg, falls das Gratis-Kontingent nicht reicht.
- Videos (eigene Phase), Profile (Phase 7), die README-Tabelle für alle Profile (Abschnitt 8 im Plan).
