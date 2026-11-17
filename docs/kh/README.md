# Kochheft

*Formerly called Küchenhelfer (German: vormals Küchenhelfer). Repository, image and folder names such as `kh/` and `own-recipe-app` stay as they are.*

A free, self-hosted family recipe app and website, based on a fork of [Mealie](https://github.com/mealie-recipes/mealie) (AGPL-3.0). Runs in Docker on a Raspberry Pi, a Mac or any Linux machine.

**Deutsch:** Eine kostenlose, selbst gehostete Rezept-App und Webseite für die Familie, auf Basis eines Mealie-Forks. Läuft in Docker auf einem Raspberry Pi, einem Mac oder einem Linux-Rechner. Die Kurzanleitung steht direkt unten, die englische Fassung danach.

**Status:** `v1.0` (9 Nov 2026): recipes come in by link, text, photo or Telegram and are reviewed before they are saved; amounts scale in the steps; cook mode with timers and voice commands (test); family cookbook PDF; nutrition and allergens; add-ons that can be switched off. Runs for the family with backups, automatic updates and access from outside. Every release can be installed on its own (D15).

- Plan: [PLAN.md](../../PLAN.md) (Deutsch, authoritative) · [PLAN.en.md](../../PLAN.en.md)
- Rules for development: [CLAUDE.md](../../.claude/CLAUDE.md) · [CLAUDE.en.md](CLAUDE.en.md)
- Changes: [CHANGELOG.md](CHANGELOG.md) · Licenses: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)
- Family accounts: [Deutsch](familienkonten.md) · [English](familienkonten.en.md)

No credentials, passwords or keys are ever stored in this repo; configuration uses placeholders in `kh/ops/.env.example`.

---

## Was du brauchst · What you need

Gemessen am 9.11.2026 mit `v1.0` · measured on 9 Nov 2026 with `v1.0`:

| | Mindestens · minimum | Empfohlen · recommended |
|---|---|---|
| Rechner · machine | 64-Bit (arm64 oder amd64), 2 Kerne · cores | Raspberry Pi 4/5 oder Mini-PC, 4 Kerne · cores |
| Arbeitsspeicher · RAM | 2 GB (Kochheft selbst: rund 300 MB, beim Import kurz mehr) | 4 GB |
| Speicherplatz · disk | 5 GB frei · free | 20 GB auf einer SSD · on an SSD |
| Mit Whisper (optional) · with Whisper | + 1 GB RAM, + 2 GB Speicher · disk | 8 GB RAM, 4 Kerne · cores |

- **Warum so viel Speicherplatz?** Das Programm-Image ist rund 1,5 GB groß (Download rund 400 MB). Bei einem Update liegt das alte Image als Rückfall bereit, also kurz zweimal. Dazu kommen deine Rezepte mit Fotos (etwa 1 GB je 2.000 Rezepte mit Foto) und die Backups, die ungefähr so groß sind wie die Rezeptdaten.
- **Der Code selbst** ist klein: das Repository rund 37 MB, davon unsere Erweiterungen rund 3 MB (einschließlich der Nährwert-Tabelle mit 0,6 MB).
- **Why this much disk?** The app image is about 1.5 GB (about 400 MB to download). During an update the old image stays as a fallback, so briefly twice. Add your recipes with photos (roughly 1 GB per 2,000 recipes with a photo) and backups of about the same size. The code itself is small: about 37 MB for the repository, about 3 MB of it our additions.

## Installieren

### Voraussetzungen

- **Ein Rechner, der dauernd läuft:**
  - Raspberry Pi 4 oder 5 mit Raspberry Pi OS 64-Bit, die Daten auf einer SSD statt auf der SD-Karte.
  - Ein Mac oder ein Linux-Rechner.
  - Windows mit Docker Desktop (WSL2) ist noch nicht getestet.
- **Docker mit Compose:**
  - Auf dem Pi und unter Linux: [Docker Engine](https://docs.docker.com/engine/install/).
  - Auf dem Mac: [Colima](https://github.com/abiosoft/colima), zum Beispiel `brew install colima docker docker-compose`, dann `colima start --cpu 2 --memory 4`. Docker Desktop geht auch.
- **Auf dem Mac außerdem:**
  - Ruhezustand aus.
  - Automatische Anmeldung an.
  - Colima startet beim Anmelden (`brew services start colima`).
- **Speicher:** siehe [Was du brauchst](#was-du-brauchst--what-you-need).

### 1. Bei ghcr.io anmelden

Das ist nur nötig, solange die Images privat sind.

1. Lege bei GitHub einen Schlüssel an: Settings → Developer settings → Personal access tokens → Tokens (classic). Setz nur das Häkchen bei `read:packages`.
2. Melde dich an:

   ```bash
   docker login ghcr.io -u DEIN-GITHUB-NAME
   ```

   Als Passwort fügst du den Schlüssel ein.

### 2. Betriebsdateien holen

Die Dateien kommen aus dem Release-Image. Die zweite Zeile wählt das passende Image für den Prozessor: `arm64` für Pi und Apple Silicon, `amd64` für Intel und AMD.

```bash
mkdir -p ~/kuechenhelfer && cd ~/kuechenhelfer
image=ghcr.io/gamingnet006/own-recipe-app:v0.1-$(docker version -f '{{.Server.Arch}}')
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD":/out --entrypoint sh "$image" -c 'cp -R /app/kh-bundle/. /out/'
```

### 3. Einrichten und starten

```bash
kh/ops/install.sh "$image"
```

Das Skript fragt zwei Dinge:

- **Wohin die Backups sollen:** Am sichersten ist ein anderes Laufwerk, ein Netzlaufwerk oder ein Ordner, den ein zweites Gerät abholt.
- **Unter welcher Adresse ihr Kochheft öffnet.**

Danach startet es alles, legt den Schlüssel für die Backups an und zeigt die erste Anmeldung an. Das tägliche Backup läuft um 3:30 Uhr.

### 4. Erste Anmeldung

1. Öffne die angezeigte Adresse und melde dich mit dem Standard-Konto an, das `install.sh` nennt.
2. Ändere sofort unter **Profil** E-Mail und Passwort.
3. Erscheint Mealies Einrichtungs-Assistent, lass **Öffentlichen Zugriff aktivieren** aus.

### 5. Familie einladen

Jede Person bekommt einen Einladungslink und legt ihr Konto selbst an, siehe [familienkonten.md](familienkonten.md).

**Mehrere Haushalte:** Wohnt jemand in zwei Haushalten, gibst du ihm unter **Mehr → Haushalte freigeben** einen weiteren frei, auch in einer anderen Gruppe. Kochheft legt dafür ein verbundenes Konto an; die Person schaltet unter **Mehr → Haushalt wechseln** um, ohne Passwort. Was sie dort anlegt, gehört zu diesem Haushalt. Die Rechte sind überall dieselben wie beim Hauptkonto (D52).

### 6. Automatische Updates

Jede Nacht um 4 Uhr holt Kochheft die neueste stabile Version und spielt sie mit Backup und Rückfall ein (D29).

1. Trag den Lese-Schlüssel aus Schritt 1 in `kh/ops/.env` ein, zum Beispiel mit `nano kh/ops/.env`: `KH_REGISTRY_USER` (dein GitHub-Name) und `KH_REGISTRY_TOKEN` (der Schlüssel).
2. Schalte die Updates ein und prüf den Stand:

   ```bash
   kh/ops/auto_update.sh on
   kh/ops/auto_update.sh status
   ```

### 7. KI einrichten (Gemini)

Eine KI liest Fotos, Screenshots, Texte und Links ohne Rezeptdaten. Links mit Rezeptdaten gehen auch ohne sie. Kochheft nutzt dafür Google Gemini mit einem kostenlosen Schlüssel (D35). Ein Google-Konto genügt, eine Kreditkarte nicht.

1. Melde dich in [Google AI Studio](https://aistudio.google.com) an und leg unter **Get API key** einen Schlüssel an. Hinterleg dort **kein Bezahlkonto**. Ohne Bezahlkonto entstehen keine Kosten; ist das Tageskontingent aufgebraucht, meldet Kochheft „Das KI-Kontingent ist aufgebraucht“.
2. Öffne in Kochheft **Profil → Gruppen-Einstellungen → KI-Anbieter-Einstellungen → Anbieter erstellen** und leg zwei Anbieter mit demselben Schlüssel an. Jedes Modell hat sein eigenes Tageslimit: Ist das des ersten aufgebraucht, nimmt Kochheft das zweite (Schritt 5).
   - **Gemini:** Basis-URL `https://generativelanguage.googleapis.com/v1beta/openai/`, API-Key aus AI Studio, Modell `gemini-3.5-flash-lite`
   - **Gemini Reserve:** dieselbe Basis-URL und derselbe Schlüssel, Modell `gemini-3.1-flash-lite`

   Ins Feld **Modell** gehört die Kennung wie `gemini-3.5-flash-lite`, nicht der Anzeigename aus AI Studio („Gemini 3.5 Flash Lite“).
3. Speichere beide und prüf dann jeden mit **Test Connection**: Erst der Test eines gespeicherten Anbieters zeigt der Liste, ob er Bilder liest. Standard- und Bildanbieter wählt Kochheft selbst aus der Liste (Schritt 5); den **Audio-Anbieter** lässt du leer, Videos kommen in einer späteren Phase.
4. Sollen alle Rezepte in einer Sprache ankommen, trag sie in `kh/ops/.env` als englischen Namen ein, zum Beispiel `KH_RECIPE_LANGUAGE=German`, und starte mit `docker compose -f kh/ops/docker-compose.yml up -d` neu (D36). Was die KI liest, wird dann übersetzt; Rezepte, die schon in dieser Sprache sind, kosten nichts extra. Links mit Rezeptdaten bleiben in der Sprache der Seite.

**Was es braucht (Probelauf 1.11.2026):** Ein Link mit Rezeptdaten braucht keine KI-Anfrage und ist nach etwa einer Sekunde da, ein Text braucht eine Anfrage (etwa 5 Sekunden), ein Foto zwei: eine liest das Foto, eine baut das Rezept (4 bis 12 Sekunden). Eine Übersetzung kostet eine Anfrage mehr. Im Gratis-Angebot hatten die beiden Flash-Lite-Modelle je 500 Anfragen am Tag und 15 pro Minute, Flash-Modelle ohne „Lite“ nur 20 am Tag. Den eigenen Stand zeigt AI Studio unter [Ratenbegrenzungen](https://aistudio.google.com/rate-limit).

Im Gratis-Angebot darf Google eingereichte Texte, Fotos und Screenshots nutzen (siehe „Was geht wohin“). Der Schlüssel liegt in Kochhefts Datenbank und damit in jedem Backup.

5. **Mehrere Anbieter, Prio-Liste (D39):** In den KI-Anbieter-Einstellungen stehen die Anbieter als Liste, die du mit ▲▼ ordnest. Die KI fragt sie von oben nach unten: Ist bei einem das Kontingent leer, der Schlüssel ungültig, das Modell weg oder er nicht erreichbar, nimmt sie den nächsten. Neben jedem Anbieter steht sein Zustand, etwa „Kontingent leer bis 9:00“.
   - Übersprungen wird ein leeres Kontingent bis zu der Zeit, die der Anbieter nennt, sonst eine Stunde; ein ungültiger Schlüssel oder ein fehlendes Modell, bis du den Anbieter speicherst oder sein Test grün ist; ein nicht erreichbarer Anbieter zehn Minuten. Die Zeiten lassen sich in `kh/ops/.env` ändern (`KH_AI_…`).
   - Fotos gehen zuerst an Anbieter, deren Test „liest Bilder“ ergab, dann an ungetestete. Standard- und Bildanbieter stellt Kochheft dafür selbst auf den ersten passenden der Liste.
   - **Glocke:** Wer KI-Anbieter verwalten darf, sieht oben neben der Suche eine Glocke mit der Zahl neuer Meldungen, etwa „Gemini: Kontingent aufgebraucht bis 9:00. Ich nehme jetzt Groq.“ Meldungen bleiben 30 Tage. Die übrige Familie sieht nur im Eingang einen Hinweis, wenn gar kein Anbieter frei oder noch keiner eingerichtet ist.
   - **Kostenlose Schlüssel:** Unter der Liste steht ein Infofeld mit diesen Stellen (Stand 4.11.2026). Kostenlose Stufen ändern sich oft; ob ein Modell passt, zeigt **Test Connection**. Jeder weitere Anbieter sieht die Rezepte, die er liest (siehe „Was geht wohin“).

| Anbieter, Schlüssel holen | Basis-URL | Gut zu wissen |
|---|---|---|
| [Google AI Studio (Gemini)](https://aistudio.google.com/apikey) | `https://generativelanguage.googleapis.com/v1beta/openai/` | liest Fotos; im Gratis-Angebot darf Google die Daten zur Verbesserung nutzen |
| [Groq](https://console.groq.com/keys) | `https://api.groq.com/openai/v1` | sehr schnell; die feste Antwortform können nur neuere Modelle |
| [Mistral](https://console.mistral.ai/api-keys) | `https://api.mistral.ai/v1` | kostenloser „Free mode“; die Datenschutz-Einstellungen in der Konsole ansehen |
| [OpenRouter](https://openrouter.ai/settings/keys) | `https://openrouter.ai/api/v1` | nur Modelle, deren Name auf „:free“ endet; 50 Anfragen am Tag |
| [SambaNova](https://cloud.sambanova.ai) | `https://api.sambanova.ai/v1` | ohne Zahlungsmittel 20 Anfragen am Tag je Modell |
| [Cloudflare Workers AI](https://dash.cloudflare.com/profile/api-tokens) | `https://api.cloudflare.com/client/v4/accounts/<ACCOUNT_ID>/ai/v1` | API-Token mit „Workers AI“; statt `<ACCOUNT_ID>` kommt die Konto-ID in die Adresse; 10.000 „Neurons“ am Tag |
| [Z.ai (GLM)](https://z.ai/manage-apikey/apikey-list) | `https://api.z.ai/api/paas/v4/` | die Flash-Modelle sind kostenlos, GLM-4.6V-Flash liest auch Fotos; Firma in Singapur, die Daten werden dort verarbeitet |
| [Vercel AI Gateway](https://vercel.com/d?to=%2F%5Bteam%5D%2F%7E%2Fai-gateway&title=Go+to+AI+Gateway) | `https://ai-gateway.vercel.sh/v1` | monatliches Gratis-Guthaben für ausgewählte Modelle; wer Guthaben kauft, bekommt es nicht mehr |
| [Cohere](https://dashboard.cohere.com/api-keys) | `https://api.cohere.ai/compatibility/v1` | Test-Schlüssel mit 1.000 Anfragen im Monat und 20 pro Minute, zum Ausprobieren gedacht |
| [NVIDIA](https://build.nvidia.com) | `https://integrate.api.nvidia.com/v1` | einmalig 1.000 Credits zum Ausprobieren, bis 40 Anfragen pro Minute |

### So findest du dich zurecht

Am Handy und am iPad hochkant steht unten eine Leiste:

- **Rezepte:** suchen und stöbern. Warten Entwürfe auf Prüfung, steht darüber ein Hinweis.
- **Eingang:** neue Rezepte hinzufügen und die Entwürfe prüfen; die Zahl zeigt, wie viele warten.
- **Einkaufsliste:** Gibt es nur eine, öffnet sie direkt.
- **Mehr:** Essensplaner, Kochbücher, „Was kann ich kochen?“, Favoriten, Kategorien, Schlagworte, Utensilien, Zeitstrahl, Einstellungen, Sprache, Hell/Dunkel, Familie einladen und Abmelden.

Am iPad quer und am Computer stehen dieselben Ziele im Seitenmenü links.

### Ein Rezept ansehen und kochen

Oben steht das Foto mit **Zurück**, dem Herz für die Favoriten und dem Menü **⋯**: Bearbeiten, Als gekocht markieren, Original ansehen (bei Rezepten aus dem Netz), In den Essensplan, Drucken und Löschen. Darunter folgen Titel, Herkunft, die Zeiten und die **Menge**. Mit − und + rechnest du die Mengen in Zutaten und Schritten um (siehe „Mengen und Umrechnen“). Unter den Zutaten legt **Auf die Einkaufsliste** sie auf eine Liste; unten öffnet **Kochen starten** den Kochmodus. Kategorien und Schlagworte stehen nur beim Bearbeiten.

### Rezept hinzufügen

Neue Rezepte kommen über den **Eingang**; auch Mealies Import-Seiten führen dorthin. Selbst eintippen geht über **Rezept selbst eintippen** im Eingang oder über **Erstellen** im Seitenmenü.

- **Link:** Adresse einfügen. Hat die Seite Rezeptdaten, liest Kochheft sie ohne KI, sonst liest die KI die Seite.
- **Text:** Rezepttext einfügen, zum Beispiel aus einer Nachricht.
- **Foto oder Screenshot:** Kamera oder Mediathek. Ein Rezept auf mehreren Seiten bekommt alle Fotos zusammen, bis zu fünf.

Danach wartet das Rezept als Entwurf unten im **Eingang** und ist nach ein paar Sekunden erkannt. Jeder im Haushalt sieht alle Entwürfe und darf sie übernehmen. In der Prüfansicht steht das Original neben dem Ergebnis, am Handy untereinander:

- Unter dem Ergebnis trägst du bei Bedarf **Portionen**, **Portionsangabe** und **Ergibt Text** ein, zum Beispiel 1 und „Springform Ø 26 cm“. Sie werden beim Übernehmen mitgespeichert.
- **Übernehmen** speichert das Rezept, **Übernehmen und bearbeiten** öffnet es gleich zum Ändern.
- **Verwerfen** löscht den Entwurf samt Original.
- Gibt es das Rezept vielleicht schon (gleicher Link, ähnlicher Titel oder dieselben Zutaten), steht oben ein Hinweis mit Link. Gelöscht wird nie etwas von selbst.
- Ging die Erkennung schief, steht der Grund dabei, mit **Neu versuchen**.

Am gespeicherten Rezept zeigt ein Abzeichen, woher es kam, mit **Original ansehen**.

### Mengen und Umrechnen

- **Beim Einlesen** liest Kochheft deutsche Mengen selbst, ohne KI und ohne Netz: „250 g“, „½ TL“, „1 1/2 EL“, „1,5 kg“, Bereiche wie „2–3 EL“ oder „2 bis 3 EL“, dazu Prise, Msp., Pck., Bund, Stück und mehr. Fehlen der Gruppe Einheiten wie Messerspitze, Stück, Scheibe oder Becher, legt Kochheft sie beim ersten Mal an. Gibt es eine Zutat schon bei den Lebensmitteln, wird sie verknüpft; sonst bleibt ihr Name als Text neben Menge und Einheit.
- **In der Prüfansicht** sind Mengen im Schritttext farbig hinterlegt, wenn sie zu einer Zutat passen („125 g Mehl“ bei 250 g Mehl). Antippen löst eine Verknüpfung, erneutes Antippen verknüpft wieder. Hinweise zeigen, was auffällt:
  - eine Menge, die nicht erkannt wurde;
  - ungewöhnliche Mengen, also mehr als 5000 g, 5 kg, 20 EL, 3 Prisen oder 30 Stück;
  - Zeiten über 24 Stunden;
  - Temperaturen unter 30 oder über 300 °C, und Angaben in °F;
  - Zutaten, die in keinem Schritt vorkommen;
  - Mengen, die aus cups oder oz umgerechnet wurden.
- **Auf der Rezeptseite** rechnen − und + die Zutaten und die verknüpften Mengen im Schritttext um, auch im Kochmodus, im Druck und für die Einkaufsliste. Gespeichert wird nur die Basis. **Umrechnen** bietet drei Wege:
  - Portionen;
  - „Ich habe nur …“: eine Zutat und wie viel davon da ist;
  - Backform, rund oder eckig. Die alte Form steht oft schon in der Portionsangabe, etwa „Springform Ø 26 cm“.
- **Die Anzeige:**
  - Brüche wie ½ und ¾ statt Kommazahlen.
  - Gramm und Milliliter gerundet, ab 1000 in kg oder l.
  - Stückware in halben Stücken, bei halben Eiern mit Tipp.
  - 3 TL werden 1 EL.
  - Prise, Messerspitze, „etwas“ und „nach Geschmack“ bleiben, wie sie sind.
  - Zeiten bleiben fest. Bei mehr als dem Doppelten oder weniger als der Hälfte erinnert ein Hinweis daran, dass sich Back- und Garzeiten ändern können.
- Ältere Rezepte bleiben, wie sie sind; ihre Zutaten zerlegst du beim Bearbeiten mit **Zutaten parsen**. Wird ein Schritt später umgeschrieben oder verschoben, wandert seine Verknüpfung mit; fehlt die Menge danach, fällt sie weg.

### Kochen

**Kochen starten** unten auf dem Rezept zeigt jeweils einen Schritt in großer Schrift (D42):

- **Weiter** und **Zurück** unten, oder nach links und rechts wischen (am Computer die Pfeiltasten und die Leertaste). Der Balken oben zeigt, wo du stehst; bis 12 Schritte ist er in Abschnitte geteilt, auf die du tippen kannst. Die Adresse merkt sich den Schritt, ein Neuladen bleibt also beim Schritt.
- **Du brauchst:** nennt die Zutaten dieses Schritts. Steht eine Zutat nur in diesem Schritt, steht ihre Menge dabei, sonst nur der Name. In Zutaten und Schritten stehen die Mengen mit, auch umgerechnet.
- **Alle Schritte** zeigt Mealies Liste mit allen Schritten und Zutaten; ein Tipp hakt einen Schritt ab wie gewohnt. **Schritt für Schritt** führt zurück zum aktuellen Schritt, **✕** verlässt den Kochmodus. Der Bildschirm bleibt an; kann das Gerät das nicht, steht ein Hinweis zur automatischen Sperre da.
- **Zeiten und Timer:** Zeiten im Text („10 Min.“, „1,5 Stunden“, „20–30 Min.“) sind antippbar und starten einen Timer. Bei einem Bereich klingelt er am unteren Ende; „noch 10 Min.“ läuft bis zum oberen weiter. Mehrere Timer laufen gleichzeitig, mit Pause und Stopp. Sie überleben Sperren, Neuladen und Seitenwechsel und stehen als schmale Leiste auf jeder Seite; ist einer abgelaufen, klingelt und vibriert das Gerät (höchstens 2 Minuten), bis du **Aus** tippst. Das klappt, solange die App offen ist; nach einem Neuladen reicht ein Tipp irgendwo auf die Seite, damit der Ton wieder erlaubt ist. Auf dem iPhone übertönt der Ton den Stummschalter (ab iOS 17); ältere Versionen bleiben bei Stumm still. Bei gesperrtem Handy hilft der Uhr-Timer (nächster Abschnitt, „Uhr-Timer per Kurzbefehl“). Zeiten wachsen beim Umrechnen nicht mit.
- **Offline:** Die zuletzt geöffneten 30 Rezepte und ihre Fotos bleiben auf dem Gerät und öffnen sich auch ohne Netz, mit dem Hinweis „Offline: gespeicherte Fassung“. Beim Abmelden werden sie gelöscht, damit auf einem geteilten Gerät nichts liegen bleibt.

#### Sprachbefehle (Test)

Unter **Mehr** → **Zusatzfunktionen** gibt es den Schalter **Sprachbefehle (Test)**, standardmäßig aus (nur Admins). Ist er an, zeigt der Kochmodus **Sprachbefehle an**. Nach dem Tipp (und der Erlaubnis fürs Mikrofon) lädt das Gerät einmal das Sprachmodell (etwa 45 MB, von deinem eigenen Kochheft) und hört dann auf vier Wörter: **weiter**, **zurück**, **Timer** (startet den ersten Timer des Schritts) und **stopp** (schaltet klingelnde Timer aus). **Sprachbefehle aus** beendet das Mikrofon. Die Erkennung läuft ganz im Browser; Audio verlässt das Gerät nie.

Das ist ein Test (T2): Auf manchen iPhones und Browsern klappt es nicht, etwa bei wenig Arbeitsspeicher oder in Küchenlärm. Dann steht ein Hinweis da, und der Schalter bleibt besser aus. Die Tasten und das Wischen gehen immer.

#### Umluft

Die Rezepte nennen meist Ober-/Unterhitze. Unter **Mehr** → **Unser Ofen** stellst du ein, welchen Ofen du hast (gilt nur für dieses Gerät). Temperaturen in den Schritten bekommen dann eine Klammer mit dem Wert für deinen Ofen, zum Beispiel „180 °C (Umluft 160 °C)“.

- Umluft ist 20 °C kühler als Ober-/Unterhitze; umgekehrt 20 °C wärmer.
- Unter 100 °C wird nichts umgerechnet.
- Die Rezepte selbst bleiben unverändert; die Klammer ist nur Anzeige.

### Nährwerte

Unter den Zutaten steht der Block **Nährwerte pro Portion (ca.)**.

- Gerechnet wird mit den Zeilen, die eine Menge haben und zu einem bekannten Lebensmittel passen. Darunter steht, wie viele: „aus 7 von 9 Zutaten“, und „ohne: …“ nennt die Zeilen, die fehlen.
- Solange du die Zuordnung nicht bestätigt hast, steht dort **geschätzt**. Die Werte sind immer ungefähr, nie genau.
- **Mehr** → **Nährwerte**: Dort bestätigst du einmal pro Zutat, welcher Eintrag der Tabelle passt, und trägst bei Bedarf ein Stückgewicht in Gramm ein (zum Beispiel für „1 Ei“). Das gilt dann für alle Rezepte.
- **Mehr** → **Nährwerte zeigen**: Schalter, der den Block ein- oder ausblendet. Er wird auf diesem Gerät gespeichert.
- Hast du in Mealie Nährwerte von Hand eingetragen, gehen diese vor.
- Quelle: Bundeslebensmittelschlüssel (BLS) 4.0, Max Rubner-Institut, CC BY 4.0.

### Allergene und Unverträglichkeiten

Aus den Zutaten erkennt Kochheft die 14 Allergen-Gruppen der EU. Das ist immer „wahrscheinlich, ohne Gewähr“ und nie eine Garantie. Prüfe im Zweifel die Packung.

- Am Rezept kannst du Fehler korrigieren: **stimmt nicht** nimmt ein Allergen heraus, **Allergen ergänzen** fügt eines hinzu. Beides gilt nur für dieses Rezept.
- **Mehr** → **Ich vertrage nicht**: Hier hakt jede Person für ihr Konto an, was sie nicht verträgt. Enthält ein Rezept das wahrscheinlich, steht auf der Rezeptseite eine Warnung mit den Namen, und die Rezeptkarte trägt ein Zeichen.
- Zur Warnung zeigt Kochheft Ersatz-Hinweise („Statt Butter: Margarine“). Dort legt der Haushalt auch eigene Regeln an; sie gehen vor der Standardliste.
- **Als Variante speichern** macht eine Kopie „(ohne …)“ mit den Ersatz-Zutaten. Das Original bleibt unverändert.

### Familienkochbuch drucken

1. Öffne in Mealie ein Kochbuch und tippe **Als Buch drucken**. Es öffnet sich der Editor mit Live-Vorschau.
2. Stelle ein: Titel, Untertitel, Titelseite, Inhaltsverzeichnis (mit Rezeptnummern), Reihenfolge, Beschreibung, Notizen und die Umluft-Klammern. Pro Rezept wählst du: **ins Buch**, **mit Foto** und **Portionen**.
3. **Drucken / Als PDF sichern** drücken. Am Mac wählst du im Druckdialog **Als PDF sichern**. Am iPhone: **Teilen** → **Drucken**, dann das Teilen-Symbol und **In Dateien sichern** (das ergibt ein PDF).

- Die Einstellungen werden pro Kochbuch gespeichert und gelten auf allen Geräten. Nur der eigene Haushalt kann sie ändern; andere können das Buch drucken.
- Ein einzelnes Rezept druckst du als Rezeptkarte: Rezeptmenü **⋯** → **Drucken**.
- Fotos kommen nur ins Buch, wenn du **Foto ist von uns** anhakst. Hake das nur bei Fotos an, die ihr selbst gemacht habt.

### Umzug aus einer anderen App

1. Unter `/group/migrations` (in Mealie: Gruppe → Migrationen) bietet Mealie Importe aus diesen Apps an: Nextcloud Cookbook, Paprika, Chowdown, Copy Me That, My Recipe Box, Plan to Eat, Recipe Keeper, Tandoor, Cook'n und Mealie (alt). Lade die Exportdatei der alten App dort hoch.
2. Gib den importierten Rezepten einen Tag, zum Beispiel „Import“.
3. Öffne **Mehr** → **Doppelte Rezepte**, filtere nach dem Tag und entscheide bei jedem Paar: **Beide behalten** oder eines löschen (Löschen lässt sich nicht rückgängig machen).

Rezepte aus Kitchen Stories und Chefkoch holst du über den Link im **Eingang**, Rezepte auf Papier über ein Foto.

### Teilen per Kurzbefehl (iPhone und iPad)

Mit einem Kurzbefehl im Teilen-Menü kommen Links, Texte und Fotos aus Safari, Instagram, Fotos oder Nachrichten direkt als Entwurf an (D37).

1. **Ein Schlüssel je Gerät:** In Kochheft unter **Profil → API-Tokens** einen Token anlegen, zum Beispiel „iPhone Anna“, und kopieren. Geht ein Gerät verloren, löschst du dort nur seinen Token.
2. **Kurzbefehl bauen**, einmal in der App **Kurzbefehle** über **+**, Name zum Beispiel „Ins Kochbuch“:
   - Unter **ⓘ** „Im Share-Sheet anzeigen“ einschalten, mit den Typen URLs, Safari-Webseiten, Bilder und Text.
   - Aktion **Text** mit dem Schlüssel.
   - **Bilder aus Eingabe abrufen** (aus der Kurzbefehleingabe), dann **Wenn** die Bilder einen Wert haben: **Inhalte von URL abrufen** mit `https://<eure-adresse>/api/kh/drafts`, Methode **POST**, Header `Authorization` mit `Bearer ` und dahinter dem Text, Anfragetext **Formular** mit dem Feld `images` (Datei) = Bilder.
   - **Sonst** **URLs aus Eingabe abrufen**, dann **Wenn** es URLs gibt: dieselbe Abfrage mit dem Feld `url` (Text) = URLs; **sonst** mit dem Feld `text` (Text) = Kurzbefehleingabe.
   - Zum Schluss **Mitteilung anzeigen**, zum Beispiel „Liegt bei den Entwürfen“.
3. **Für die Familie:** Unter **ⓘ → Importfragen** für die Aktion **Text** eine Frage einrichten („Dein Kochheft-Schlüssel“) und den Kurzbefehl dann per iCloud-Link teilen. So trägt jeder beim Hinzufügen seinen eigenen Schlüssel ein, und deiner geht nicht mit.

Danach im Teilen-Menü „Ins Kochbuch“ wählen; der Entwurf erscheint im **Eingang**. Ob Instagram die Beschreibung eines Beitrags herausgibt, entscheidet Instagram; sonst einen Screenshot teilen. Ein Rezept über mehrere Seiten gibst du am besten in der App im **Eingang** ein.

### Uhr-Timer per Kurzbefehl (iPhone und iPad)

Ein Timer in der App klingelt nur, solange die App offen ist. Damit er auch bei gesperrtem Handy klingelt, legt die Taste „Auf Uhr-Timer legen“ ihn in die Uhr-App (D42). Dafür braucht jedes Gerät einmal einen Kurzbefehl:

> **Nur iPhone und iPad.** Der Uhr-Timer braucht die App Kurzbefehle. Android hat keine, und eine Webseite kann dort den Timer der Uhr-App nicht starten. Auf Android und am Computer zeigt **Mehr → Timer** deshalb nur einen Hinweis; der Timer in Kochheft klingelt dort, solange die App offen ist.

1. **Kurzbefehl einrichten.** Unter **Mehr → Timer** steht die Anleitung gleich beim Schalter („So richtest du den Kurzbefehl ein“); gibt es dort die Taste „Kurzbefehl hinzufügen“, genügt sie. Von Hand:
   - App **Kurzbefehle** öffnen, unten rechts auf **+** tippen.
   - Oben den Namen auf „Kochheft Timer“ ändern (oder den Namen in Kochheft anpassen).
   - Aktion **Zahlen aus Eingabe abrufen** hinzufügen, Quelle **Kurzbefehleingabe**.
   - Aktion **Timer starten** hinzufügen, Dauer = diese Zahl, Einheit **Minuten**.
2. **Einschalten:** In Kochheft unter **Mehr → Timer** „Timer auch in der Uhr-App anbieten“ einschalten. Hat der Kurzbefehl einen anderen Namen, trag ihn dort ein. „Ausprobieren (1 Minute)“ startet einen Test; sperre das Handy und prüfe, dass es klingelt.

Danach steht neben jedem laufenden Timer „Auf Uhr-Timer legen“. Ein Tipp öffnet kurz die Kurzbefehle-App und startet den Timer der Uhr mit der Restzeit, aufgerundet auf volle Minuten. Der Timer in Kochheft läuft weiter.

**Kurzbefehl hinzufügen:** Kochheft bringt den fertigen Kurzbefehl „Kochheft Timer“ als iCloud-Link mit. **Mehr → Timer** zeigt dafür die Taste „Kurzbefehl hinzufügen“; ein Tipp legt ihn auf dem Gerät an. Wer lieber einen eigenen nimmt, teilt ihn (Kurzbefehle → Teilen → „iCloud-Link kopieren“) und trägt den Link in `.env` als `KH_CLOCK_SHORTCUT_URL` ein (nur `https://www.icloud.com/shortcuts/…`; alles andere blendet die Taste aus).

### Telegram-Bot einrichten

Optional und standardmäßig aus: Wer Links, Texte oder Fotos lieber an einen Telegram-Chat schickt, bekommt sie als Entwurf im **Eingang** (P7.1). Der Bot fragt Telegram selbst nach Nachrichten, es wird kein Port geöffnet.

1. In Telegram den Chat mit **@BotFather** öffnen, `/newbot` senden und die Fragen beantworten. Den Token, den er nennt, trägst du in `kh/ops/.env` als `KH_TELEGRAM_TOKEN` ein.
2. In Kochheft unter **Profil → API-Tokens** einen eigenen Token anlegen, zum Beispiel „Telegram-Bot“, und als `KH_TELEGRAM_API_TOKEN` eintragen.
3. Starte den Bot mit `docker compose -f kh/ops/docker-compose.yml --profile telegram up -d telegram`, schreib ihm eine Nachricht und trag die Chat-ID, die er zurückschickt („Diese Chat-ID ist nicht freigeschaltet: …“), in `KH_TELEGRAM_ALLOWED_IDS` ein (mehrere mit Komma). Dann startest du den Bot mit demselben Befehl neu.

Danach legt jeder Link, Text oder jedes Foto aus einem freigeschalteten Chat einen Entwurf an; der Bot antwortet mit „Entwurf angelegt“ und dem Link zur Prüfansicht. Bei Fotos zählt das größte, höchstens `KH_DRAFT_MAX_IMAGE_MB` groß. Videolinks (Instagram, TikTok, YouTube, Facebook) werden nicht abgerufen: Schick die Beschreibung als Text dazu oder einen Screenshot. Im Profil `lokal` startet der Bot nicht. Ausschalten: `docker compose -f kh/ops/docker-compose.yml stop telegram`.

### Audio und Video (Whisper)

Optional und standardmäßig aus (P7.3): Eigene Aufnahmen, zum Beispiel ein Sprachmemo von Oma oder ein selbst gedrehtes Kochvideo, wandelt ein Whisper-Dienst in Text um. Der Text wird zum Entwurf und geht den üblichen Weg mit dem KI-Anbieter. Die Datei bleibt in deinem Netz.

1. In `kh/ops/.env` `KH_WHISPER_URL=http://whisper:8000` eintragen.
2. Dienst starten: `docker compose -f kh/ops/docker-compose.yml --profile whisper up -d whisper`. Den Speicher begrenzt `KH_WHISPER_MEM_LIMIT` (Standard 2g). Beim ersten Mal lädt der Dienst das Modell aus dem Netz (Hugging Face), danach nicht mehr; nach 5 Minuten ohne Aufnahme gibt er den Speicher wieder frei.
3. Kochheft neu starten (`docker compose -f kh/ops/docker-compose.yml up -d`). Im Eingang erscheint dann **Audio- oder Videodatei (eigene Aufnahme)**.

Das Modell hängt vom Profil ab (siehe „Profile und Hardware-Test“): `tiny`, `base` oder `small`; mit `KH_WHISPER_MODEL` kannst du es festlegen. Größte Datei: `KH_DRAFT_MAX_MEDIA_MB` (Standard 95, weil Cloudflare Tunnel im Gratis-Tarif bei 100 MB abschneidet). Die Umwandlung läuft im Hintergrund und kann auf einem Pi Minuten dauern; die Aufnahme wird danach gelöscht, der Dateiname bleibt als Hinweis am Entwurf. Ohne `KH_WHISPER_URL` gibt es kein Dateifeld. Videos aus dem Netz (Instagram, TikTok, YouTube) lädt Kochheft nie; es geht nur um deine eigenen Dateien.

### Profile und Hardware-Test

Das Profil sagt Kochheft, wie viel dein Rechner trägt (P7.4). Es steht in `kh/ops/.env` als `KH_PROFILE` (Standard `leicht`) und setzt das Whisper-Modell: `leicht` = `tiny`, `normal` = `base`, `stark` = `small`, `lokal` = `base`. Im Profil `lokal` startet der Telegram-Bot nicht; Whisper bleibt erlaubt, weil es bei dir läuft. KI-Anbieter solltest du dann nur lokale eintragen (z. B. Ollama); die App weist bei den KI-Anbietern und in der Systemprüfung darauf hin. Die Systemprüfung zeigt das Profil an.

Welches Profil passt, misst `sh kh/ops/hardware_test.sh`: Architektur, Prozessorkerne und Arbeitsspeicher, dazu ein Vorschlag (unter 4 GB oder bis 4 Kerne: `leicht`; ab 8 GB und mehr als 4 Kernen: `normal`; Apple Silicon mit 16 GB oder 8 und mehr Kerne: `stark`). Ein Raspberry Pi landet damit bei `leicht`.

Mit einer eigenen Aufnahme von etwa 1 Minute misst es auch die Spracherkennung: `sh kh/ops/hardware_test.sh --audio memo.m4a`. Der Whisper-Dienst muss laufen; er ist auf diesem Rechner unter `localhost:8000` erreichbar (`KH_WHISPER_PORT`). Ohne `ffprobe` gibst du die Länge mit `--seconds 60` an. Das Ergebnis ist ein Faktor (Dauer der Umwandlung durch Länge der Aufnahme): bis 1 passt das Profil, bis 3 ist es als Hintergrundarbeit brauchbar, darüber nimm das nächstkleinere. Beim ersten Mal lädt der Dienst das Modell; miss danach noch einmal.

### Optional

- **Zugang von unterwegs** (Cloudflare Tunnel, D27):
  1. Leg in Cloudflare Zero Trust unter Networks → Tunnels einen Tunnel an, mit Route auf `http://mealie:9000`.
  2. Trag seinen Schlüssel als `KH_TUNNEL_TOKEN` und die öffentliche Adresse als `KH_BASE_URL` ein.
  3. Starte ihn mit `kh/ops/tunnel.sh on`. Das Skript geht nur online, wenn Selbstregistrierung aus ist, das Standard-Konto geändert ist und alle Gruppen und Haushalte privat sind.
- **Meldungen an Uptime Kuma:** Lege zwei Monitore vom Typ „Push“ an und trag ihre Adressen ein, mit Hinweisen in `kh/ops/.env.example`.
  - `KH_BACKUP_PUSH_URL`: mit `host.docker.internal` statt `localhost`, weil das Backup im Container läuft.
  - `KH_UPDATE_PUSH_URL`
  - Danach `docker compose -f kh/ops/docker-compose.yml up -d backup`.
- **Backup prüfen:** `kh/ops/restore_test.sh` spielt das neueste Backup in eine Wegwerf-Installation ein und vergleicht Rezepte und Dateien.
- **Kopie auf einen USB-Stick** (D32): Jede Nacht um 3:45 Uhr kommen die neuen Backups auf ein zweites Laufwerk, zum Beispiel einen USB-Stick mit exFAT. Beim Einrichten wählst du, ob sie ein Passwort bekommen (D33). Mit Passwort sind sie verschlüsselt, und das Passwort wird nirgends gespeichert: Vergisst du es, sind die Kopien verloren. Ohne Passwort sind es normale Mealie-Backups.
  1. Am Mac braucht der nächtliche Job einmal Festplattenvollzugriff, sonst sperrt macOS den Stick: Systemeinstellungen → Sicherheit & Datenschutz → Datenschutz → Festplattenvollzugriff → „+“ → ⇧⌘G → `/bin/dash`. Auf einem Mac startet sonst kaum etwas `dash`, die Freigabe bleibt also bei diesem Job.
  2. Stick einstecken und die Kopie einschalten: am Mac per Doppelklick auf `kh/ops/backup-ort-aendern.command`, sonst mit `kh/ops/backup_copy.sh on` (über SSH mit `ssh -t`). Beides zeigt, wie man ein Laufwerk vorbereitet, und die eingesteckten Laufwerke; du wählst eines per Nummer oder gibst einen Ordner mit vollem Pfad an. Direkt geht auch `kh/ops/backup_copy.sh on /Volumes/<Stick>/Kuechenhelfer-Backups`. Beim ersten Mal fragt das Skript „Kopien mit Passwort verschlüsseln? (j/n)“; bei „j“ fragt age zweimal nach dem Passwort. Am Pi muss der Stick eingehängt sein, zum Beispiel über `/etc/fstab`.
  3. Stand prüfen: `kh/ops/backup_copy.sh status`. Fehlt der Stick, schreibt der Job nichts und meldet es, mit `KH_BACKUP_PUSH_URL` auch an Uptime Kuma.
  4. Mit Passwort zur Probe eine Kopie öffnen: `kh/ops/backup_copy.sh decrypt <Stick>/Kuechenhelfer-Backups/<backup>.zip.age`. Solange dasselbe Backup noch auf diesem Rechner liegt, vergleicht der Befehl nur und meldet, ob die Kopie stimmt.
  - Zurückholen: Mit Passwort fragt `kh/ops/backup_copy.sh decrypt <Stick>/Kuechenhelfer-Backups/<backup>.zip.age` danach und legt das Backup in den Backup-Ordner; am Mac im Terminal am Gerät selbst aufrufen, nicht über SSH. Ohne Passwort die `.zip` vom Stick nach `kh/ops/backups` kopieren. Danach `restore.sh <backup>.zip` wie unter „Alltag“.
  - Anleitung neben den Backups: Auf dem Stick und im Backup-Ordner liegen `LIESMICH.txt` mit allen Schritten, auch zum Neuinstallieren, und `CLAUDE.md` für Claude: Wer Claude Code in diesem Ordner startet, bekommt beim Wiederherstellen Hilfe. Beide erneuern sich, wenn sich die Anleitung ändert.
  - Backup-Ort ändern: genauso wie in Schritt 2, am Mac also per Doppelklick auf `kh/ops/backup-ort-aendern.command`, bequem als Verweis auf dem Schreibtisch (im Finder mit gedrückter ⌥⌘-Taste dorthin ziehen). Passwort-Wahl und Schlüssel bleiben, die erste Kopie kommt samt `LIESMICH.txt` und `CLAUDE.md` sofort an den neuen Ort, und am Mac steht danach das Ergebnis da. Am alten Ort bleiben die Kopien liegen. Das geht absichtlich nur am Gerät selbst oder über SSH, nicht über die Webseite.
  - Stick ohne Passwort verloren: Wer ihn hat, kommt mit dem Backup-Schlüssel darin in die App. Lösch dann in Kochheft unter Profil → API-Tokens den Token des Backup-Dienstes (bei neuen Installationen `kh-backup`), leg einen neuen an, trag ihn als `KH_BACKUP_API_TOKEN` in `kh/ops/.env` ein und führ `docker compose -f kh/ops/docker-compose.yml up -d backup` aus. Lösch zuletzt `kh/ops/data/.secret` und starte Mealie neu (`docker compose -f kh/ops/docker-compose.yml restart mealie`); danach melden sich alle einmal neu an. Auch der KI-Schlüssel steckt im Backup: Leg in Google AI Studio einen neuen an, trag ihn unter Gruppen-Einstellungen → KI-Anbieter ein und lösch den alten in AI Studio.

### Alltag

```bash
# Update von Hand: Backup, Wechsel, Prüfung, bei Fehler zurück
kh/ops/update.sh ghcr.io/gamingnet006/own-recipe-app:<version>-<arm64|amd64>
# Backup sofort, vorhandene Backups anzeigen, eines wiederherstellen
docker compose -f kh/ops/docker-compose.yml run --rm --no-deps backup backup.sh
docker compose -f kh/ops/docker-compose.yml run --rm --no-deps backup restore.sh [datei.zip]
# Stoppen und wieder starten
docker compose -f kh/ops/docker-compose.yml down
docker compose -f kh/ops/docker-compose.yml up -d
```

Auf dem Mac brauchen eigene Hintergrund-Jobs (cron, launchd) `/usr/local/bin` im PATH, sonst finden sie `docker` nicht. `auto_update.sh` ergänzt das selbst.

### Wartung

**Jeden Monat (10 Minuten):**

1. Backup prüfen: `kh/ops/restore_test.sh`. Es spielt das neueste Backup in eine Wegwerf-Installation ein und vergleicht Rezepte und Dateien. Melde einen Fehler sofort.
2. Freien Platz prüfen: `df -h` auf dem Laufwerk mit den Daten und mit den Backups. Unter 20 % frei: alte Backups löschen oder ein größeres Laufwerk nehmen.
3. Updates prüfen: `kh/ops/auto_update.sh status` und das Protokoll darin lesen. Steht dort ein Fehler, ist das alte Image noch aktiv; die Daten sind sicher.
4. USB-Kopie prüfen: `kh/ops/backup_copy.sh status`.
5. Auf neue Hinweise zu Sicherheitslücken in Mealie achten und Kochheft dann von Hand aktualisieren.

**Nach jedem Update:**

1. Öffne Kochheft und schau unter **Mehr → Über Kochheft**, ob die neue Version steht.
2. Öffne ein Rezept und starte den Kochmodus.
3. Mach ein Backup sofort: `docker compose -f kh/ops/docker-compose.yml run --rm --no-deps backup backup.sh`.
4. Läuft etwas nicht, spiel das Backup vor dem Update wieder ein (siehe „Alltag“).

### Was geht wohin

Was Kochheft nach draußen schickt. Telemetrie gibt es keine.

| Funktion | Was wird gesendet | An wen | Abschalten |
|---|---|---|---|
| Link einlesen | Abruf der Seite und ihres Rezeptbilds | die jeweilige Webseite | – |
| KI: Text, Foto, Screenshot oder Link ohne Rezeptdaten auslesen; Mealies KI-Zutatenerkennung, wenn man sie wählt | der Text, die Bilder oder der Inhalt der Seite; im Gratis-Angebot darf Google sie nutzen | die eingetragenen KI-Anbieter in der Reihenfolge der Prio-Liste, z. B. Google Gemini; jeder mit eigenen Regeln (D35, D39) | KI-Anbieter in den Gruppen-Einstellungen löschen |
| Teilen per Kurzbefehl | Link, Text oder Foto, mit dem Schlüssel des Geräts | dein Kochheft, direkt vom Gerät (D37) | Kurzbefehl löschen; Token unter Profil → API-Tokens löschen |
| Zugang von unterwegs | gesamter Verkehr zur Web-App; Cloudflare kann ihn lesen, weil HTTPS dort endet | Cloudflare (Tunnel, D27) | `kh/ops/tunnel.sh off` |
| Automatische Updates | Abruf der Versionsliste und der neuen Images, mit dem Lese-Schlüssel, solange das Repo privat ist; beim Erneuern des Backup-Dienstes das Alpine-Basisimage und Pakete | GitHub (ghcr.io), Docker Hub, Alpine-Paketspiegel (D29) | `kh/ops/auto_update.sh off` |
| Mealies Versionsprüfung | nur die Frage nach der neuesten Mealie-Version, wenn ein Admin die Verwaltung öffnet | GitHub (api.github.com) | – |
| Backups und Kopie | alle Daten, auch der KI-Schlüssel | dein Backup-Ordner und, falls eingerichtet, der USB-Stick; verschlüsselt, wenn beim Einrichten ein Passwort gewählt wurde (D32, D33) | `kh/ops/backup_copy.sh off` für die Kopie |
| Meldungen | ob Backup, Kopie und Update geklappt haben | dein Uptime Kuma | Push-Adressen in `kh/ops/.env` leer lassen |
| Nährwerte | die Zutatennamen, nur zum Abgleich mit der Tabelle in deinem eigenen Kochheft | nirgends: Die BLS-Tabelle (CC BY 4.0) liegt im Image | – |
| Videolinks (Instagram, TikTok, YouTube, Facebook) | nichts: Kochheft ruft sie nicht ab und lädt keine Videos (D5); du fügst die Beschreibung ein oder lädst einen Screenshot hoch | niemand | – |
| Teilen per Telegram (Zusatzmodul, standardmäßig aus) | Link, Text oder Foto aus deinem Chat | Telegram-Server; im Profil „lokal“ gesperrt | Dienst `telegram` nicht starten |
| Sprachbefehle (Test, Zusatzfunktion, standardmäßig aus) | das Mikrofon-Audio, nur an die Erkennung im Browser selbst; das Sprachmodell kommt vom eigenen Kochheft | nirgends | Schalter **Sprachbefehle (Test)** aus oder **Sprachbefehle aus** im Kochmodus |
| Audio und Video mit Whisper (Zusatzmodul, standardmäßig aus) | die eigene Datei, nur an das Whisper im eigenen Netz | dein Whisper-Dienst, nicht nach draußen | Dienst `whisper` nicht starten |

**Profile (`KH_PROFILE` in `kh/ops/.env`, Standard `leicht`):**

- **leicht:** Raspberry Pi und alte Rechner. Text- und Screenshot-Import, Prüfansicht, Kochmodus; Whisper `tiny`, keine große lokale KI.
- **normal:** aktueller Mini-PC oder Mac. Zusätzlich Whisper `base` und kleine lokale KI.
- **stark:** Apple Silicon oder Mini-PC mit viel Arbeitsspeicher. Whisper `small` und lokale KI.
- **lokal:** alles auf eigener Hardware, kein Telegram, keine Cloud-KI, Whisper `base`. Dann verlässt nichts das Haus (Tunnel aus, Updates aus).

---

## Install (English)

### Requirements

- **A machine that is always on:**
  - Raspberry Pi 4 or 5 with Raspberry Pi OS 64-bit, with the data on an SSD instead of the SD card.
  - A Mac or a Linux machine.
  - Windows with Docker Desktop (WSL2) is not tested yet.
- **Docker with Compose:**
  - On the Pi and on Linux: [Docker Engine](https://docs.docker.com/engine/install/).
  - On a Mac: [Colima](https://github.com/abiosoft/colima), for example `brew install colima docker docker-compose`, then `colima start --cpu 2 --memory 4`. Docker Desktop works too.
- **On a Mac also:**
  - Sleep off.
  - Automatic login on.
  - Colima starts at login (`brew services start colima`).
- **Memory:** see [What you need](#was-du-brauchst--what-you-need).

### 1. Log in to ghcr.io

This is only needed while the images are private.

1. Create a key on GitHub: Settings → Developer settings → Personal access tokens → Tokens (classic). Tick only `read:packages`.
2. Log in:

   ```bash
   docker login ghcr.io -u YOUR-GITHUB-NAME
   ```

   Paste the key as the password.

### 2. Get the ops files

The files come from the release image. The second line picks the image for your CPU: `arm64` for the Pi and Apple Silicon, `amd64` for Intel and AMD.

```bash
mkdir -p ~/kuechenhelfer && cd ~/kuechenhelfer
image=ghcr.io/gamingnet006/own-recipe-app:v0.1-$(docker version -f '{{.Server.Arch}}')
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD":/out --entrypoint sh "$image" -c 'cp -R /app/kh-bundle/. /out/'
```

### 3. Set up and start

```bash
kh/ops/install.sh "$image"
```

The script asks two things:

- **Where the backups go:** safest on another drive, a network drive or a folder a second device collects.
- **Under which address you open Kochheft.**

It then starts everything, creates the key for the backups and shows the first login. The daily backup runs at 3:30 am.

### 4. First login

1. Open the address shown and log in with the default account that `install.sh` names.
2. Change e-mail and password right away under **Profile**.
3. If Mealie's setup wizard appears, leave **Enable public access** off.

### 5. Invite the family

Each person gets an invite link and creates their own account, see [familienkonten.en.md](familienkonten.en.md).

**Several households:** if someone lives in two households, give them another one under **More → Household access**, also in another group. Kochheft creates a linked account for it; the person switches under **More → Switch household**, without a password. What they add there belongs to that household. Rights are the same everywhere as on the main account (D52).

### 6. Automatic updates

Every night at 4 am Kochheft fetches the newest stable version and installs it with a backup and a rollback (D29).

1. Put the read key from step 1 into `kh/ops/.env`, for example with `nano kh/ops/.env`: `KH_REGISTRY_USER` (your GitHub name) and `KH_REGISTRY_TOKEN` (the key).
2. Switch the updates on and check the state:

   ```bash
   kh/ops/auto_update.sh on
   kh/ops/auto_update.sh status
   ```

### 7. Set up AI (Gemini)

An AI reads photos, screenshots, texts and links without recipe data. Links with recipe data work without it. Kochheft uses Google Gemini with a free key for this (D35). A Google account is enough, no credit card.

1. Sign in to [Google AI Studio](https://aistudio.google.com) and create a key under **Get API key**. Do **not** add a billing account there. Without one nothing costs money; when the daily quota is used up, Kochheft says "The AI quota is used up".
2. In Kochheft open **Profile → Group Settings → AI Provider Settings → Create Provider** and create two providers with the same key. Every model has its own daily limit: when the first one's is used up, Kochheft takes the second (step 5).
   - **Gemini:** Base URL `https://generativelanguage.googleapis.com/v1beta/openai/`, the API key from AI Studio, model `gemini-3.5-flash-lite`
   - **Gemini Reserve:** the same base URL and key, model `gemini-3.1-flash-lite`

   The **Model** field takes the ID such as `gemini-3.5-flash-lite`, not the display name from AI Studio ("Gemini 3.5 Flash Lite").
3. Save both, then check each with **Test Connection**: only the test of a saved provider tells the list whether it reads images. Kochheft picks the default and the image provider from the list itself (step 5); leave the **Audio Provider** empty, videos come in a later phase.
4. If all recipes should arrive in one language, put it into `kh/ops/.env` as an English name, for example `KH_RECIPE_LANGUAGE=German`, and restart with `docker compose -f kh/ops/docker-compose.yml up -d` (D36). Whatever the AI reads is then translated; recipes already in that language cost nothing extra. Links with recipe data stay in the page's language.

**What it takes (trial run 2026-11-01):** a link with recipe data needs no AI request and is there after about a second, a text needs one request (about 5 seconds), a photo two: one reads the photo, one builds the recipe (4 to 12 seconds). A translation costs one request more. On the free tier the two Flash-Lite models had 500 requests a day and 15 a minute each, Flash models without "Lite" only 20 a day. AI Studio shows your own numbers under [rate limits](https://aistudio.google.com/rate-limit).

On the free tier Google may use the texts, photos and screenshots handed in (see "What goes where"). The key is stored in Kochheft's database and so in every backup.

5. **Several providers, priority list (D39):** the AI provider settings show the providers as a list you order with ▲▼. The AI asks them from top to bottom: when a quota is used up, a key is invalid, a model is gone or a provider cannot be reached, it takes the next. Next to each provider is its state, such as "quota used up until 9:00".
   - A used-up quota is skipped until the time the provider names, else an hour; an invalid key or a missing model until you save the provider or its test is green; an unreachable provider ten minutes. The times can be changed in `kh/ops/.env` (`KH_AI_…`).
   - Photos go first to providers whose test read an image, then to untested ones. For this Kochheft sets the default and image provider to the first fitting one of the list.
   - **Bell:** whoever may manage AI providers sees a bell next to the search with the number of new messages, such as "Gemini: quota used up until 9:00. Now using Groq." Messages are kept 30 days. The rest of the family only sees a hint in the intake when no provider is free at all or none is set up yet.
   - **Free keys:** under the list an info box names these places (as of 2026-11-04). Free tiers change often; **Test Connection** shows whether a model fits. Every further provider sees the recipes it reads (see "What goes where").

| Provider, get a key | Base URL | Good to know |
|---|---|---|
| [Google AI Studio (Gemini)](https://aistudio.google.com/apikey) | `https://generativelanguage.googleapis.com/v1beta/openai/` | reads photos; on the free tier Google may use the data to improve its products |
| [Groq](https://console.groq.com/keys) | `https://api.groq.com/openai/v1` | very fast; only newer models give the fixed answer form |
| [Mistral](https://console.mistral.ai/api-keys) | `https://api.mistral.ai/v1` | free "Free mode"; look at the privacy settings in the console |
| [OpenRouter](https://openrouter.ai/settings/keys) | `https://openrouter.ai/api/v1` | only models whose name ends in ":free"; 50 requests a day |
| [SambaNova](https://cloud.sambanova.ai) | `https://api.sambanova.ai/v1` | without a payment method 20 requests a day per model |
| [Cloudflare Workers AI](https://dash.cloudflare.com/profile/api-tokens) | `https://api.cloudflare.com/client/v4/accounts/<ACCOUNT_ID>/ai/v1` | API token with "Workers AI"; the account ID replaces `<ACCOUNT_ID>` in the address; 10,000 "neurons" a day |
| [Z.ai (GLM)](https://z.ai/manage-apikey/apikey-list) | `https://api.z.ai/api/paas/v4/` | the Flash models are free, GLM-4.6V-Flash also reads photos; a company in Singapore, the data is processed there |
| [Vercel AI Gateway](https://vercel.com/d?to=%2F%5Bteam%5D%2F%7E%2Fai-gateway&title=Go+to+AI+Gateway) | `https://ai-gateway.vercel.sh/v1` | monthly free credit for selected models; buying credits ends it |
| [Cohere](https://dashboard.cohere.com/api-keys) | `https://api.cohere.ai/compatibility/v1` | trial key with 1,000 requests a month and 20 a minute, meant for trying it out |
| [NVIDIA](https://build.nvidia.com) | `https://integrate.api.nvidia.com/v1` | 1,000 one-time credits to try it out, up to 40 requests a minute |

### Finding your way

On a phone and an upright iPad there is a bar at the bottom:

- **Recipes:** search and browse. When drafts wait for a review, a hint shows above.
- **Intake:** add new recipes and review the drafts; the number shows how many wait.
- **Shopping list:** if there is only one, it opens right away.
- **More:** meal planner, cookbooks, "What can I cook?", favorites, categories, tags, tools, timeline, settings, language, light/dark, invite family and log out.

On an iPad in landscape and on a computer, the same destinations are in the side menu on the left.

### View and cook a recipe

At the top is the photo with **Back**, the heart for favorites and the **⋯** menu: Edit, Mark as cooked, View original (for recipes from the web), Add to plan, Print and Delete. Below come the title, where the recipe came from, the times and the **Amount**. − and + scale the amounts in ingredients and steps (see "Amounts and scaling"). Under the ingredients, **Add to shopping list** puts them on a list; **Start cooking** at the bottom opens cook mode. Categories and tags show only while editing.

### Add a recipe

New recipes come in through the **Intake**; Mealie's import pages lead there too. To type a recipe in yourself, use **Type a recipe in yourself** in the intake or **Create** in the side menu.

- **Link:** paste the address. If the page has recipe data, Kochheft reads it without AI, otherwise the AI reads the page.
- **Text:** paste the recipe text, for example from a message.
- **Photo or screenshot:** camera or photo library. A recipe on several pages gets all its photos together, up to five.

The recipe then waits as a draft at the bottom of the **Intake** and is recognized after a few seconds. Everyone in the household sees all drafts and may save them. The review shows the original next to the result, one below the other on a phone:

- Below the result you can set **Servings**, **Yield** and **Yield Text** if needed, for example 1 and "springform pan Ø 26 cm". They are saved with the recipe.
- **Save** stores the recipe, **Save and edit** opens it right away for changes.
- **Discard** deletes the draft with its original.
- If the recipe may exist already (same link, similar title or the same ingredients), a hint with a link is shown on top. Nothing is ever deleted by itself.
- If the recognition went wrong, the reason is shown, with **Try again**.

A badge on the saved recipe shows where it came from, with **View original**.

### Amounts and scaling

- **On import** Kochheft reads German amounts itself, without AI and without the network: "250 g", "½ TL", "1 1/2 EL", "1,5 kg", ranges such as "2–3 EL" or "2 bis 3 EL", and Prise, Msp., Pck., Bund, Stück and more. If the group lacks units such as Messerspitze, Stück, Scheibe or Becher, Kochheft adds them the first time. An ingredient that already exists among the foods is linked; otherwise its name stays as text next to amount and unit.
- **In the review** amounts in the step text are tinted when they fit an ingredient ("125 g Mehl" for 250 g Mehl). Tapping unlinks one, tapping again links it again. Hints point out what stands out:
  - an amount that was not recognized;
  - unusual amounts, that is more than 5000 g, 5 kg, 20 EL, 3 pinches or 30 pieces;
  - times over 24 hours;
  - temperatures below 30 or above 300 °C, and any given in °F;
  - ingredients no step uses;
  - amounts converted from cups or oz.
- **On the recipe page** − and + scale the ingredients and the linked amounts in the step text, also in cook mode, in print and for the shopping list. Only the base is saved. **Scale** offers three ways:
  - servings;
  - "I only have …": an ingredient and how much of it there is;
  - baking pan, round or rectangular. The old pan is often in the yield already, such as "Springform Ø 26 cm".
- **The display:**
  - Fractions such as ½ and ¾ instead of decimals.
  - Grams and millilitres rounded, from 1000 in kg or l.
  - Pieces in halves, with a tip for half an egg.
  - 3 TL become 1 EL.
  - Pinches, Messerspitze, "etwas" and "nach Geschmack" stay as they are.
  - Times stay fixed. Above double or below half, a hint reminds you that baking and cooking times may change.
- Older recipes stay as they are; split their ingredients with **Parse ingredients** while editing. If a step is rewritten or moved later, its link moves with it; if the amount is gone afterwards, the link goes.

### Cooking

**Start cooking** at the bottom of a recipe shows one step at a time in large type (D42):

- **Next** and **Back** at the bottom, or swipe left and right (on a computer the arrow keys and the space bar). The bar at the top shows where you are; up to 12 steps it is split into segments you can tap. The address remembers the step, so a reload stays on it.
- **You need:** lists the ingredients of this step. An ingredient that appears only in this step shows its amount, otherwise just the name. Ingredients and steps show the amounts, scaled too.
- **All steps** shows Mealie's list of all steps and ingredients; a tap ticks a step off as usual. **Step by step** returns to the current step, **✕** leaves cook mode. The screen stays on; if the device cannot do that, a hint about the automatic lock shows.
- **Times and timers:** times in the text ("10 Min.", "1,5 Stunden", "20–30 Min.") can be tapped and start a timer. For a range it rings at the lower end; "10 more min." runs on to the upper end. Several timers run at once, with pause and stop. They survive locking, reloading and changing pages and show as a thin bar on every page; when one runs out, the device rings and vibrates (for 2 minutes at most) until you tap **Off**. That works while the app is open; after a reload, one tap anywhere on the page allows sound again. On the iPhone the sound overrides the mute switch (iOS 17 and later); older versions stay silent when muted. On a locked phone use the Clock timer (next section, "Clock timer via shortcut"). Times do not grow when you scale.
- **Offline:** the last 30 recipes you opened and their photos stay on the device and open without a network, with the hint "Offline: saved version". Signing out deletes them, so nothing stays on a shared device.

#### Voice commands (test)

Under **More** → **Add-ons** there is the switch **Voice commands (test)**, off by default (admins only). When it is on, cook mode shows **Voice commands on**. After the tap (and the microphone permission) the device loads the speech model once (about 45 MB, from your own Kochheft) and then listens for four words: **weiter** (next), **zurück** (back), **Timer** (starts the first timer of the step) and **stopp** (silences ringing timers). **Voice commands off** ends the microphone. Recognition runs entirely in the browser; audio never leaves the device.

This is a test (T2): on some iPhones and browsers it does not work, for example with little memory or in kitchen noise. A hint then shows, and the switch is better left off. The buttons and swiping always work.

#### Fan oven

Recipes usually give conventional (top and bottom) heat. Under **More** → **Our oven** you choose which oven you have (this device only). Temperatures in the steps then get a bracket with the value for your oven, for example "180 °C (fan 160 °C)".

- A fan oven runs 20 °C cooler than conventional; the other way round, 20 °C warmer.
- Nothing below 100 °C is converted.
- The recipes themselves stay unchanged; the bracket is display only.

### Nutrition

Under the ingredients there is the block **Nutrition per serving (approx.)**.

- It counts the lines that have an amount and match a known food. Below it says how many: "from 7 of 9 ingredients", and "without: ..." names the lines that are missing.
- Until you have confirmed the matching, it says **estimated**. The values are always approximate, never exact.
- **More** → **Nutrition**: There you confirm once per ingredient which entry of the table fits, and set a weight of one piece in grams if needed (for example for "1 egg"). It then applies to all recipes.
- **More** → **Show nutrition**: a switch that shows or hides the block. It is stored on this device.
- If you entered nutrition values by hand in Mealie, they win.
- Source: Bundeslebensmittelschlüssel (BLS) 4.0, Max Rubner-Institut, CC BY 4.0.
- Developer note: rebuild the table with `uv run python -m mealie.kh.nutrition.build_bls`.

### Allergens and intolerances

Kochheft detects the 14 EU allergen groups from the ingredients. This is always "probably, without guarantee" and never a promise. When in doubt, check the packaging.

- On the recipe you can correct mistakes: **not correct** takes an allergen out, **Add an allergen** adds one. Both apply to this recipe only.
- **More** → **I do not tolerate**: Each person ticks, for their own account, what they do not tolerate. If a recipe probably contains it, the recipe page shows a warning with the names and the recipe card carries a mark.
- With the warning, Kochheft shows substitution hints ("Instead of butter: margarine"). The household can also add its own rules there; they come before the standard list.
- **Save as variant** makes a copy "(ohne ...)" with the replacement ingredients. The original stays unchanged.

### Print the family cookbook

1. In Mealie, open a cookbook and tap **Print as book**. The editor opens with a live preview.
2. Set: title, subtitle, title page, contents (with recipe numbers), order, description, notes and the fan-oven brackets. Per recipe you choose: **in the book**, **with photo** and **servings**.
3. Press **Print / Save as PDF**. On the Mac, choose **Save as PDF** in the print dialog. On the iPhone: **Share** → **Print**, then the share icon and **Save to Files** (this makes a PDF).

- Settings are saved per cookbook and apply on every device. Only your own household can change them; others can print the book.
- To print a single recipe as a recipe card, use the recipe menu **⋯** → **Print**.
- Photos go into the book only if you tick **The photo is ours**. Tick it only for photos you took yourselves.

### Moving from another app

1. Under `/group/migrations` (in Mealie: group → migrations), Mealie offers imports from these apps: Nextcloud Cookbook, Paprika, Chowdown, Copy Me That, My Recipe Box, Plan to Eat, Recipe Keeper, Tandoor, Cook'n and Mealie (old). Upload the old app's export file there.
2. Put a tag on the imported recipes, for example "Import".
3. Open **More** → **Duplicate recipes**, filter by the tag and decide for each pair: **Keep both** or delete one (deleting cannot be undone).

Recipes from Kitchen Stories and Chefkoch come in by link through the **Inbox**, paper recipes by photo.

### Share shortcut (iPhone and iPad)

With a shortcut in the share menu, links, texts and photos from Safari, Instagram, Photos or Messages arrive straight as drafts (D37).

1. **One key per device:** in Kochheft under **Profile → API Tokens** create a token, for example "iPhone Anna", and copy it. If a device gets lost, delete just its token there.
2. **Build the shortcut** once in the **Shortcuts** app with **+**, named for example "Into the cookbook":
   - Under **ⓘ** turn on "Show in Share Sheet", with the types URLs, Safari web pages, images and text.
   - A **Text** action holding the key.
   - **Get Images from Input** (from the shortcut input), then **If** the images have any value: **Get Contents of URL** with `https://<your-address>/api/kh/drafts`, method **POST**, header `Authorization` with `Bearer ` followed by the text, request body **Form** with the field `images` (File) = images.
   - **Otherwise** **Get URLs from Input**, then **If** there are URLs: the same request with the field `url` (Text) = URLs; **otherwise** with the field `text` (Text) = shortcut input.
   - Finally **Show Notification**, for example "Waiting in the drafts".
3. **For the family:** under **ⓘ → Import Questions** add a question for the **Text** action ("Your Kochheft key"), then share the shortcut by iCloud link. Everyone enters their own key when adding it, and yours stays with you.

Then pick "Into the cookbook" in the share menu; the draft shows in the **Intake**. Whether Instagram hands out a post's caption is up to Instagram; otherwise share a screenshot. A recipe on several pages is best entered in the app in the **Intake**.

### Clock timer via shortcut (iPhone and iPad)

A timer in the app rings only while the app is open. So that it rings on a locked phone, too, the button "Put on the clock" hands it to the Clock app (D42). Each device needs one shortcut for that:

> **iPhone and iPad only.** The clock timer needs the Shortcuts app. Android has none, and a web page cannot start the Clock app's timer there. On Android and on a computer, **More → Timer** therefore shows only a note; the timer in Kochheft rings there while the app is open.

1. **Set up the shortcut.** Under **More → Timer** the steps sit right at the switch ("How to set up the shortcut"); if the button "Add shortcut" is there, it is enough. By hand:
   - Open the **Shortcuts** app and tap **+** at the bottom right.
   - Change the name at the top to "Kochheft Timer" (or adjust the name in Kochheft).
   - Add the action **Get Numbers from Input**, source **Shortcut Input**.
   - Add the action **Start Timer**, duration = that number, unit **minutes**.
2. **Turn it on:** in Kochheft under **More → Timer** turn on "Also offer timers in the Clock app". If the shortcut has another name, enter it there. "Try it (1 minute)" starts a test; lock the phone and check that it rings.

Then every running timer gets a "Put on the clock" button. A tap briefly opens the Shortcuts app and starts the Clock timer with the time left, rounded up to whole minutes. The timer in Kochheft keeps running.

**Add shortcut:** Kochheft comes with the ready-made "Kochheft Timer" shortcut as an iCloud link. **More → Timer** shows the button "Add shortcut" for it; one tap adds it on the device. To use your own instead, share it (Shortcuts → Share → "Copy iCloud Link") and put the link into `.env` as `KH_CLOCK_SHORTCUT_URL` (only `https://www.icloud.com/shortcuts/…`; anything else hides the button).

### Set up the Telegram bot

Optional and off by default: if you prefer to send links, texts or photos to a Telegram chat, they arrive as a draft in the **inbox** (P7.1). The bot asks Telegram for messages itself, no port is opened.

1. In Telegram open the chat with **@BotFather**, send `/newbot` and answer the questions. Put the token it gives you into `kh/ops/.env` as `KH_TELEGRAM_TOKEN`.
2. In Kochheft create a token of its own under **Profile → API Tokens**, for example "Telegram bot", and enter it as `KH_TELEGRAM_API_TOKEN`.
3. Start the bot with `docker compose -f kh/ops/docker-compose.yml --profile telegram up -d telegram`, write it a message and put the chat ID it sends back ("Diese Chat-ID ist nicht freigeschaltet: …") into `KH_TELEGRAM_ALLOWED_IDS` (several with commas). Then restart the bot with the same command.

From then on every link, text or photo from an allowed chat becomes a draft; the bot answers "Entwurf angelegt" with the link to the review. For photos the largest size counts, at most `KH_DRAFT_MAX_IMAGE_MB`. Video links (Instagram, TikTok, YouTube, Facebook) are not fetched: send the description as text with it, or a screenshot. In the `lokal` profile the bot does not start. Switch it off: `docker compose -f kh/ops/docker-compose.yml stop telegram`.

### Audio and video (Whisper)

Optional and off by default (P7.3): a Whisper service turns your own recordings, for example a voice memo from grandma or a cooking video you filmed, into text. The text becomes a draft and takes the usual way through the AI provider. The file stays in your network.

1. Put `KH_WHISPER_URL=http://whisper:8000` into `kh/ops/.env`.
2. Start the service: `docker compose -f kh/ops/docker-compose.yml --profile whisper up -d whisper`. `KH_WHISPER_MEM_LIMIT` caps its memory (default 2g). The first time, the service downloads the model from the internet (Hugging Face), never again; after 5 minutes without a recording it frees the memory.
3. Restart Kochheft (`docker compose -f kh/ops/docker-compose.yml up -d`). The intake then offers **Audio or video file (own recording)**.

The model depends on the profile (see "Profiles and hardware test"): `tiny`, `base` or `small`; `KH_WHISPER_MODEL` overrides it. Largest file: `KH_DRAFT_MAX_MEDIA_MB` (default 95, because the free Cloudflare tunnel cuts uploads at 100 MB). The conversion runs in the background and can take minutes on a Pi; the recording is deleted afterwards, its file name stays as a note on the draft. Without `KH_WHISPER_URL` there is no file field. Kochheft never downloads videos from the internet (Instagram, TikTok, YouTube); this is about your own files only.

### Profiles and hardware test

The profile tells Kochheft how much your machine can carry (P7.4). It lives in `kh/ops/.env` as `KH_PROFILE` (default `leicht`) and sets the Whisper model: `leicht` = `tiny`, `normal` = `base`, `stark` = `small`, `lokal` = `base`. In the `lokal` profile the Telegram bot does not start; Whisper stays allowed because it runs at your place. You should then enter only local AI providers (e.g. Ollama); the app reminds you at the AI providers and in the system check. The system check shows the profile.

`sh kh/ops/hardware_test.sh` measures which profile fits: architecture, CPU cores and RAM, plus a proposal (under 4 GB or up to 4 cores: `leicht`; from 8 GB and more than 4 cores: `normal`; Apple Silicon with 16 GB or 8 and more cores: `stark`). A Raspberry Pi ends up at `leicht`.

With your own recording of about 1 minute it also measures speech recognition: `sh kh/ops/hardware_test.sh --audio memo.m4a`. The Whisper service must be running; it is reachable on this machine at `localhost:8000` (`KH_WHISPER_PORT`). Without `ffprobe` give the length with `--seconds 60`. The result is a factor (time of the conversion divided by the length of the recording): up to 1 the profile fits, up to 3 it is usable as background work, above that take the next smaller one. The first time the service downloads the model; measure again afterwards.

### Optional

- **Access from outside** (Cloudflare Tunnel, D27):
  1. Create a tunnel in Cloudflare Zero Trust under Networks → Tunnels, with a route to `http://mealie:9000`.
  2. Put its key into `KH_TUNNEL_TOKEN` and the public address into `KH_BASE_URL`.
  3. Start it with `kh/ops/tunnel.sh on`. The script only goes online when self sign-up is off, the default account is changed and every group and household is private.
- **Reports to Uptime Kuma:** create two monitors of type "Push" and put their addresses in, with hints in `kh/ops/.env.example`.
  - `KH_BACKUP_PUSH_URL`: with `host.docker.internal` instead of `localhost`, because the backup runs in a container.
  - `KH_UPDATE_PUSH_URL`
  - Then run `docker compose -f kh/ops/docker-compose.yml up -d backup`.
- **Check a backup:** `kh/ops/restore_test.sh` restores the newest backup into a throwaway install and compares recipes and files.
- **Copy to a USB stick** (D32): every night at 3:45 am the new backups go to a second drive such as a USB stick with exFAT. When you set it up, you choose whether they get a password (D33). With a password they are encrypted and the password is stored nowhere: if you forget it, the copies are lost. Without one they are normal Mealie backups.
  1. On a Mac the nightly job needs Full Disk Access once, or macOS locks the stick: System Preferences → Security & Privacy → Privacy → Full Disk Access → "+" → ⇧⌘G → `/bin/dash`. Hardly anything else on a Mac starts `dash`, so the permission stays with this job.
  2. Plug in the stick and switch the copy on: on a Mac with a double-click on `kh/ops/backup-ort-aendern.command`, elsewhere with `kh/ops/backup_copy.sh on` (over SSH with `ssh -t`). Both show how to prepare a drive and the plugged-in drives; pick one by number or type a folder with its full path. `kh/ops/backup_copy.sh on /Volumes/<stick>/Kuechenhelfer-Backups` works directly too. The first time, the script asks "Kopien mit Passwort verschlüsseln? (j/n)" (encrypt the copies with a password?); with "j", age asks for the password twice. On a Pi the stick must be mounted, for example through `/etc/fstab`.
  3. Check: `kh/ops/backup_copy.sh status`. Without the stick the job writes nothing and reports it, with `KH_BACKUP_PUSH_URL` also to Uptime Kuma.
  4. With a password, open a copy as a test: `kh/ops/backup_copy.sh decrypt <stick>/Kuechenhelfer-Backups/<backup>.zip.age`. While the same backup is still on this machine, the command only compares and reports whether the copy is right.
  - Bring one back: with a password, `kh/ops/backup_copy.sh decrypt <stick>/Kuechenhelfer-Backups/<backup>.zip.age` asks for it and puts the backup into the backup folder; on a Mac run it in the Terminal on the machine itself, not over SSH. Without a password, copy the `.zip` from the stick into `kh/ops/backups`. Then `restore.sh <backup>.zip` as under "Day to day".
  - A guide next to the backups: the stick and the backup folder hold `LIESMICH.txt` with every step, reinstalling included, and `CLAUDE.md` for Claude: whoever starts Claude Code in that folder gets help with the restore. Both are renewed when the guide changes.
  - Change where the copies go: the same as in step 2, so on a Mac a double-click on `kh/ops/backup-ort-aendern.command`, handy as an alias on the desktop (drag it there in the Finder holding ⌥⌘). The password choice and the key stay, the first copy lands at the new place right away with `LIESMICH.txt` and `CLAUDE.md`, and on a Mac the result shows. The old place keeps its copies. On purpose this works only on the machine itself or over SSH, not on the website.
  - Lost a stick without a password: whoever has it gets into the app with the backup key inside. Then delete the backup service's token in Kochheft under Profile → API Tokens (`kh-backup` on new installs), create a new one, put it into `kh/ops/.env` as `KH_BACKUP_API_TOKEN` and run `docker compose -f kh/ops/docker-compose.yml up -d backup`. Finally delete `kh/ops/data/.secret` and restart Mealie (`docker compose -f kh/ops/docker-compose.yml restart mealie`); everyone then logs in once more. The AI key is in the backup too: create a new one in Google AI Studio, enter it under Group Settings → AI Providers and delete the old one in AI Studio.

### Day to day

```bash
# Update by hand: backup, switch, check, roll back on failure
kh/ops/update.sh ghcr.io/gamingnet006/own-recipe-app:<version>-<arm64|amd64>
# Backup right now, list backups, restore one
docker compose -f kh/ops/docker-compose.yml run --rm --no-deps backup backup.sh
docker compose -f kh/ops/docker-compose.yml run --rm --no-deps backup restore.sh [file.zip]
# Stop and start again
docker compose -f kh/ops/docker-compose.yml down
docker compose -f kh/ops/docker-compose.yml up -d
```

On a Mac, your own background jobs (cron, launchd) need `/usr/local/bin` in PATH, or they do not find `docker`. `auto_update.sh` adds it itself.

### Maintenance

**Every month (10 minutes):**

1. Check the backup: `kh/ops/restore_test.sh`. It restores the newest backup into a throwaway installation and compares recipes and files. Report a failure right away.
2. Check free space: `df -h` on the drive with the data and on the one with the backups. Below 20 % free: delete old backups or use a bigger drive.
3. Check updates: `kh/ops/auto_update.sh status` and read the log it shows. On an error the old image stays active; the data is safe.
4. Check the USB copy: `kh/ops/backup_copy.sh status`.
5. Watch for security notices about Mealie and then update Kochheft by hand.

**After every update:**

1. Open Kochheft and check under **More → About Kochheft** that the new version shows.
2. Open a recipe and start cooking mode.
3. Take a backup right now: `docker compose -f kh/ops/docker-compose.yml run --rm --no-deps backup backup.sh`.
4. If something fails, restore the backup from before the update (see "Day to day").

### What goes where

What Kochheft sends out. There is no telemetry.

| Feature | What is sent | To whom | Switch off |
|---|---|---|---|
| Read a link | fetching the page and its recipe picture | the website in question | – |
| AI: read a text, photo, screenshot or a link without recipe data; Mealie's AI ingredient parser when chosen | the text, the pictures or the page's content; on the free tier Google may use them | the AI providers entered, in the order of the priority list, e.g. Google Gemini; each with its own rules (D35, D39) | delete the AI provider in the group settings |
| Share shortcut | link, text or photo, with the device's key | your Kochheft, straight from the device (D37) | delete the shortcut; delete the token under Profile → API Tokens |
| Access from outside | all traffic to the web app; Cloudflare can read it because HTTPS ends there | Cloudflare (tunnel, D27) | `kh/ops/tunnel.sh off` |
| Automatic updates | requests for the version list and the new images, with the read key while the repo is private; when the backup service is rebuilt, the Alpine base image and packages | GitHub (ghcr.io), Docker Hub, Alpine package mirrors (D29) | `kh/ops/auto_update.sh off` |
| Mealie's version check | only the question for the newest Mealie version, when an admin opens the admin pages | GitHub (api.github.com) | – |
| Backups and copy | all data, the AI key included | your backup folder and, if set up, the USB stick; encrypted when a password was chosen during setup (D32, D33) | `kh/ops/backup_copy.sh off` for the copy |
| Reports | whether backup, copy and update worked | your Uptime Kuma | leave the push addresses in `kh/ops/.env` empty |
| Nutrition | the ingredient names, only to match them with the table inside your own Kochheft | nowhere: the BLS table (CC BY 4.0) ships in the image | – |
| Video links (Instagram, TikTok, YouTube, Facebook) | nothing: Kochheft does not fetch them and does not download videos (D5); you paste the description or upload a screenshot | nobody | – |
| Share via Telegram (optional module, off by default) | link, text or photo from your chat | Telegram servers; blocked in the "lokal" profile | do not start the `telegram` service |
| Voice commands (test, add-on, off by default) | the microphone audio, only to the recognizer in the browser itself; the speech model comes from your own Kochheft | nowhere | switch **Voice commands (test)** off, or **Voice commands off** in cook mode |
| Audio and video with Whisper (optional module, off by default) | your own file, only to the Whisper in your own network | your Whisper service, not outside | do not start the `whisper` service |

**Profiles (`KH_PROFILE` in `kh/ops/.env`, default `leicht`):**

- **leicht** (light): Raspberry Pi and old machines. Text and screenshot import, review view, cooking mode; Whisper `tiny`, no large local AI.
- **normal:** current mini PC or Mac. Adds Whisper `base` and a small local AI.
- **stark** (strong): Apple Silicon or a mini PC with a lot of RAM. Whisper `small` and local AI.
- **lokal** (local): everything on your own hardware, no Telegram, no cloud AI, Whisper `base`. Then nothing leaves the house (tunnel off, updates off).
