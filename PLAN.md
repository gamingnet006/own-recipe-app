# Küchenhelfer – Plan (Fusion-Fassung)

Stand: 29.10.2026 · Arbeitsname „Küchenhelfer“ (Name vor der Veröffentlichung prüfen, T7)
Mockups: Planung https://claude.ai/artifact/3STTwHpXE6DXtPGUoKQoPr · Oberfläche (D38) https://claude.ai/artifact/TXV9AKbMmiZNM47u3cUjYV

Ein kostenloses, selbst gehostetes Rezept-System auf Basis eines Mealie-Forks: geprüfter Import (Link, Text, Foto, Video), Duplikat-Warnung, mitrechnende Mengen im Text, Nährwerte, Allergene, Kochmodus mit Timern und Sprachbefehlen, PDF-Familienkochbuch und automatische Backups. Alles liegt in einem Repo und ist so veröffentlichbar, dass andere es genauso nutzen können.

> **Für Claude Code:** Diese Datei ist die Arbeitsgrundlage. Arbeite die Phasen der Reihe nach ab, hake Erledigtes ab (`- [x]`), trage neue Entscheidungen in Abschnitt 2 ein und ändere Ziele oder Leitplanken nie stillschweigend.

---

## 1. Leitplanken

1. **Kostenlos:** keine Abos, keine bezahlten Bestandteile (Abschnitt 10).
2. **Rechtlich sauber:** Abschnitt 9.
3. **Ein Repo mit allem:** Code, Docker-Setup, Doku und Tests, reproduzierbar installierbar.
4. **Fusion:** Mealies Code ist die Basis. Wir behalten, was passt, entfernen, was wir nicht brauchen, und bauen neu, was wir anders wollen, ohne Abstriche.
5. **Nichts doppelt bauen:** zuerst prüfen, ob Mealie oder eine Bibliothek es schon kann.
6. **Prüfen vor Speichern:** Kein KI-Ergebnis landet ungeprüft in der Sammlung.
7. **Schwache Hardware und komplett lokal** müssen funktionieren (Profile, Abschnitt 8).
8. **Code-Regeln** in `.claude/CLAUDE.md` gelten für alles.
9. **Jede Phase eigenständig installierbar:** Das Ende jeder Phase ist ein Release, das man ohne spätere Phasen installieren und betreiben kann (D15).
10. **Späteres ändert Früheres nicht:** Neue Phasen fügen hinzu, statt fertigen Code umzubauen; die Tests aller früheren Phasen bleiben grün (D15).

**Nicht-Ziele:** öffentliche Rezeptdatenbank · Bezahl-Tarife · App-Store-Apps (die Web-App genügt) · mitgelieferter Video-Downloader · Desktop-App (zurückgestellt).

---

## 2. Entscheidungen

| Nr. | Entscheidung | Stand |
|---|---|---|
| D1 | Basis ist Mealie, als Fork mit fester Version | beschlossen |
| D2 | Das ganze Projekt steht unter AGPL-3.0; Mealies Lizenz- und Copyright-Hinweise bleiben | beschlossen |
| D3 | ersetzt durch D11 | – |
| D4 | Eigene Prüfansicht, direkt im Programm | beschlossen |
| D5 | Instagram/TikTok: Beschreibung und Screenshot sind der Standard; Video-Download nur als optionales Plug-in, standardmäßig aus, nicht im Repo mitgeliefert | Vorschlag, bitte bestätigen |
| D6 | KI: lokal zuerst (Ollama, Whisper), Gratis-Cloud nur als Reserve und nur mit eigenem Key. Ab Phase 2 über Mealies KI-Anbieter-Verwaltung (Ollama auf dem Mac oder eigener Key, D25), Profile folgen in Phase 7 | beschlossen |
| D7 | Code, Bezeichner und Kommentare auf Englisch (passt zu Mealie); Anleitungen auf Deutsch und Englisch | beschlossen |
| D8 | Technik = Mealies Stack: FastAPI, SQLAlchemy, Alembic, Nuxt 4, Vue 3, TypeScript | beschlossen |
| D9 | Projektname | offen (T7) |
| D10 | Desktop-App und iOS-App im Store | zurückgestellt |
| D11 | Fusion statt Zusatz-Container, mit Code-Rundgang in Phase 0 als Prüfpunkt | beschlossen |
| D12 | Entwicklung auf dem MacBook, Betrieb auf Raspberry Pi oder Server: alles in Docker, Images für arm64 und amd64 | beschlossen |
| D13 | Reihenfolge: Familie nutzt den Fork ab Phase 1; Abhängiges nacheinander; was nur für Fremde nötig ist (Name, Erststart, Profile) kommt zuletzt. Keine Funktion fällt weg | beschlossen |
| D14 | Erreichbarkeit von unterwegs (HTTPS, Tunnel) ist eine Aufgabe in Phase 1 | beschlossen |
| D15 | Jede Phase endet mit einem eigenständig installierbaren Release (Tag, Images, Kurzanleitung); neue Phasen sind additiv und ändern fertigen Code früherer Phasen nicht (Regeln in Abschnitt 5). Dafür kommen Images für amd64/arm64 und `update.sh` schon in Phase 1 | beschlossen |
| D16 | Code, Doku und Plan liegen im privaten Repo `gamingnet006/own-recipe-app` (eigenes Repo, Mealie per `upstream`, kein GitHub-Fork); nie Zugangsdaten, Passwörter oder Keys im Repo, nur Platzhalter in `.env.example` | beschlossen |
| D17 | Unsere Regeln liegen in `.claude/CLAUDE.md`, unsere README bis Phase 8 in `docs/kh/`; Mealies `CLAUDE.md`, `README.md` und `.gitignore` bleiben unverändert (Eng-Review) | beschlossen |
| D18 | Entwürfe in eigener `kh`-Tabelle; erst die Freigabe erzeugt ein Mealie-Rezept (Eng-Review) | beschlossen |
| D19 | Mengen im Schritttext: Text unverändert, Verknüpfungen in `kh`-Nebentabelle auf Basis von `ingredient_references` (Eng-Review) | beschlossen |
| D20 | arm64-Images auf dem Mac bauen und nach GHCR schieben, solange das Repo privat ist; amd64 in der CI (Eng-Review). Umsetzung: Veröffentlicht wird das App-Image als `<version>-arm64` (Pi, Apple Silicon) und `<version>-amd64` (PC); ein gemeinsamer Tag folgt, wenn die CI beide Architekturen selbst baut (Phase 8). Das kleine Backup-Image baut jedes Gerät selbst aus dem Release-Stand (Sekunden, kein schwerer Build) | beschlossen |
| D21 | Backups über Mealies Backup-Schnittstelle; `update.sh` holt bei Fehler Image und Datenbank aus dem Backup vor dem Update zurück (Eng-Review). Umsetzung: Die Datenbank kommt aus einem Datei-Schnappschuss, der direkt vor dem Wechsel bei gestopptem Mealie entsteht; das klappt auch, wenn die neue Version die Datenbank schon umgebaut hat. Das Mealie-Backup am zweiten Ort bleibt zusätzliches Sicherheitsnetz | beschlossen |
| D22 | Zugang von unterwegs: Selbstregistrierung aus, Tunnel-Anbieter in „Was geht wohin“ (Eng-Review) | beschlossen |
| D23 | Upgrade-Test automatisch in der CI; KI-Aufrufe in Tests nur mit aufgezeichneten Antworten (Eng-Review). Umsetzung: `kh-release.yml` testet das Upgrade vom vorigen Release, bevor das amd64-Image hochgeladen wird; scheitert der Test, wird nichts veröffentlicht | beschlossen |
| D24 | Eigene Migrationen als Alembic-Zweig `kh` (`mealie/kh/alembic/versions/`), Mealie startet mit `"heads"` statt `"head"` (`init_db.py:119`), damit Mealie-Updates keine Zusammenführungs-Migrationen brauchen (Code-Rundgang); das Wiederherstellen baut jeden Kopf, den ein Backup verzeichnet (1.11.2026) | beschlossen |
| D25 | KI-Anbindung ab Phase 2 über Mealies vorhandene KI-Anbieter-Verwaltung (Admin, pro Gruppe) statt über `.env`; D6 bleibt inhaltlich gleich (Code-Rundgang) | beschlossen |
| D26 | Frontend-Erweiterungen als Nuxt-Layer `frontend/kh/` mit einer `extends`-Zeile in `nuxt.config.ts` (Code-Rundgang) | beschlossen |
| D27 | Zugang von unterwegs über Cloudflare Tunnel auf `kochbuch.example.org` (Domain bei Cloudflare, bezahlt bis 3.7.2027). Bewusst ohne Cloudflare Access, damit es für die Familie einfach bleibt; eine Anmeldung bleibt 30 Tage gültig (`TOKEN_TIME=720`). `tunnel.sh` startet den Tunnel nur, wenn die Selbstregistrierung aus ist, kein Konto mehr die Standard-E-Mail nutzt und alle Gruppen und Haushalte privat sind (Letzteres seit 31.10.2026). Access lässt sich jederzeit nachrüsten | beschlossen |
| D28 | Betrieb überall, wo Docker läuft: Raspberry Pi, alte und neue Macs, Linux, Windows (Docker Desktop mit WSL2, noch ungetestet). Wer installiert, entscheidet selbst, wo; die Images gibt es für arm64 und amd64, die Betriebs-Skripte sind POSIX-sh. Bis der Pi vom Radiowecker fertig ist, läuft Küchenhelfer auf dem Mac mini (Intel, macOS 12, Colima, `KH_MEMORY_LIMIT=768m`); entwickelt wird weiter auf dem MacBook. Umzug auf den Pi nach der Entwicklung per Backup und Wiederherstellen; der Tunnel läuft immer nur auf einem Rechner | beschlossen |
| D29 | Automatische Updates: Jede Installation holt nachts um 4 Uhr die neueste stabile Version (Tags `vX.Y` oder `vX.Y.Z` ohne `-rc`) für ihren Prozessortyp und spielt sie über `update.sh` ein (Backup, Schnappschuss, Prüfung, Rückfall). Standardmäßig an, Schalter `KH_AUTO_UPDATE` in `.env` (`kh/ops/auto_update.sh on|off|status|check|run`); das Häkchen in der App kommt in Phase 8. Die Betriebsdateien kommen im Image mit (`/app/kh-bundle`), kein Git auf dem Server. Bricht `update.sh` vor jeder Änderung ab, versucht die nächste Nacht dieselbe Version erneut; übersprungen wird nur eine Version, die nach dem Wechsel gescheitert ist. Design: `docs/kh/specs/2026-10-30-auto-update-design.md` | beschlossen |
| D30 | `v0.0` darf erscheinen, bevor der Pi bereitsteht. Die Installation auf einem frischen Pi aus „Fertig wenn“ von Phase 1 wird nachgeholt; Fehler daraus kommen als `v0.0.1` (31.10.2026) | beschlossen |
| D31 | Keine Beispielrezepte als Startdaten, die Familie startet mit leerer Rezeptliste. Familienkonten entstehen per Einladungslink; jede Person legt ihr Konto ohne Admin-Rechte selbst an und setzt ihr Passwort selbst (31.10.2026) | beschlossen |
| D32 | Die Installation fragt, wo die Backups liegen sollen. Den zweiten Ort für den Mac mini legen wir danach fest; bis dahin liegen seine Backups auf derselben Platte wie die Datenbank (31.10.2026). Gewählt: ein USB-Stick; eingerichtet wird, sobald er steckt (31.10.2026). Umgesetzt mit `kh/ops/backup_copy.sh`: jede Nacht um 3:45 Uhr eine Kopie auf den Stick (D33). Am Mac mini eingerichtet: Festplattenvollzugriff für `/bin/dash`, Stick als exFAT `KH-Backup`, `backup_copy.sh on` ohne Passwort; die erste Kopie (3 Backups) stimmt mit den Originalen überein (31.10.2026). Den Ort später wechseln (2.11.2026): am Gerät selbst per Doppelklick auf `kh/ops/backup-ort-aendern.command` (Mac) oder mit `backup_copy.sh on` ohne Ordner; es erklärt, wie man ein Laufwerk vorbereitet, und listet die eingesteckten. Bewusst nicht über die Webseite, damit von außen niemand den Ort ändern kann | beschlossen |
| D33 | Kopien, die das Gerät verlassen, bekommen auf Wunsch ein Passwort (age); `backup_copy.sh on` fragt einmal j/n. Wichtig für die Wahl: Ein Mealie-Backup enthält den API-Schlüssel des Backup-Dienstes im Klartext, ein offener Stick öffnet also die App. Mit Passwort liegt der private Schlüssel gesperrt auf dem Stick, das Passwort nirgends, und auch Mealies `.secret` darf mit; nach einer Wiederherstellung bleiben alle angemeldet. Am Mac mini ohne Passwort: Es ist zu umständlich, und die Daten sind nicht heikel. Was bei Verlust des Sticks zu tun ist, steht in der Anleitung. Erschienen als `v0.0.1` (immer mit Passwort) und `v0.0.2` (Frage j/n); Fehler aus dem Pi-Test (D30) kommen als nächste Patch-Version (31.10.2026) | beschlossen |
| D34 | Vorerst keine eigene lokale KI: kein Ollama oder Whisper im Dauerbetrieb, weder auf dem MacBook (es soll nicht durchlaufen müssen) noch auf dem Mac mini (zu schwach). Die KI kommt über Mealies KI-Anbieter-Verwaltung (D25) mit eigenem Key bei einem Anbieter mit kostenloser Stufe; welcher, klären wir zu Beginn von Phase 2. Das dreht die Reihenfolge aus D6 (lokal zuerst) vorerst um (31.10.2026) | beschlossen |
| D35 | Phase 2 (Eingang, Prüfen, Duplikate): eigene Entwurfs-Funktion, die Mealies Erkennung mitbenutzt (`create_from_html`, `AIRecipeService.build_recipe`); Mealies Import-Seiten führen auf den Eingang. Jeder im Haushalt sieht alle Entwürfe und darf jeden freigeben; gebaut für Handy und iPad. KI: Google Gemini mit kostenlosem Schlüssel, Training durch den Anbieter ist in Ordnung. „Teilen“ per Kurzbefehl folgt als eigener Schritt (`v0.1.1`). Design: `docs/kh/specs/2026-10-31-phase-2-eingang-design.md` (31.10.2026) | beschlossen |
| D36 | Rezeptsprache und KI-Modelle (Probelauf 1.11.2026): Der Admin trägt in `kh/ops/.env` `KH_RECIPE_LANGUAGE` als englischen Namen ein, z. B. `German`. Was die KI liest (Text, Fotos, Links ohne Rezeptdaten), übersetzt dann Mealies Übersetzungsschritt; Rezepte, die schon in dieser Sprache sind, kosten keine Anfrage. Links mit Rezeptdaten bleiben in der Sprache der Seite, vorhandene Rezepte werden nicht übersetzt (zu viele Anfragen). Modelle im Gratis-Angebot: `gemini-3.5-flash-lite` als Standard- und `gemini-3.1-flash-lite` als Bildanbieter, je 500 Anfragen am Tag; ein Foto braucht zwei, ein Text eine, ein Link mit Rezeptdaten keine. Portionen und Portionsangabe lassen sich in der Prüfansicht vor dem Übernehmen eintragen. | beschlossen |
| D37 | Teilen per Kurzbefehl (`v0.1.1`): Jeder baut den Kurzbefehl nach der Anleitung oder übernimmt ihn per iCloud-Link mit Importfrage für den Schlüssel. Schlüssel ist ein eigener Mealie-API-Token je Gerät (Profil → API-Tokens), widerrufbar. Keine neue Schnittstelle, der Kurzbefehl nutzt `POST /api/kh/drafts`; kein fertiger Kurzbefehl im Repo, weil er einen Schlüssel tragen würde. | beschlossen |
| D38 | Oberfläche (1.11.2026, Spezifikation `docs/kh/specs/2026-11-01-oberflaeche-design.md`): erst der Alltag, dann der Look. Handy und iPad hochkant: Leiste unten mit Rezepte, Eingang, Einkaufsliste, Mehr; ab 840 px Mealies Seitenmenü mit denselben Zielen aus einer Liste. Eingang heißt: Rezept hinzufügen und Entwürfe auf einer Seite. Eigene Rezeptansicht im kh-Layer, Bearbeiten und Kochmodus bleiben Mealies; Sterne, Kommentare und „Zuletzt gemacht“ sind ausgeblendet. Look „Salbei“: Akzent `#2F7A55`, Grund `#F4F5F1`, Systemschrift des Geräts. Einkaufsliste, Essensplaner und Einstellungen bleiben Mealies Seiten. Einführung in `v0.1.2` (Rahmen) und `v0.1.3` (Rezeptseite). | beschlossen |
| D39 | `v0.2` (3.11.2026, Spezifikation `docs/kh/specs/2026-11-03-v0.2-mengen-ki-liste-design.md`): Phase 3 „Mengen“ baut auf Mealies NLP-Parser auf und erkennt deutsche Angaben beim Import ohne KI-Anfrage; Mengen im Schritttext rechnen über eine `kh`-Nebentabelle mit (D19); Umrechnen über Portionen, „Ich habe nur …“ und Backform. Dazu eine KI-Prio-Liste mit beliebig vielen kostenlosen Anbietern, die bei leerem Kontingent, ungültigem Schlüssel, fehlendem Modell oder Ausfall zum nächsten wechselt, mit Infofeld zu kostenlosen Schlüsseln (Stand mit Datum) und einer Glocke mit Meldungen für alle mit `can_manage`. Der Ton-Anbieter bleibt Mealies Auswahl; keine Push-Nachrichten aufs Handy. Beim Update beginnt die Liste mit Mealies bisherigem Standard- und Bildanbieter, neue Anbieter kommen ans Ende (4.11.2026, Review). Zwei Pläne, ein Release; erst KI-Liste und Glocke, dann Mengen. | beschlossen |
| D40 | Deutsche Mengen liest Küchenhelfer selbst (`parse_ingredient()`), weil Mealies NLP-Bibliothek deutsche Einheiten nicht erkennt (Probe 4.11.2026); von Mealie kommt nur der Abgleich mit Einheiten und Lebensmitteln der Gruppe. Verknüpfungen im Schritttext nennen ihren Schritt nach Position, weil Mealie bei jedem Speichern neue Schritt-IDs vergibt. | beschlossen |
| D41 | Mengen neben Zutatennamen im Schritttext („die Butter (200 g) schmelzen“) kommen in Phase 4 (Kochmodus), nicht mehr in `v0.2`; Phase 3 rechnet nur Mengen um, die schon im Schritt stehen (8.11.2026) | beschlossen |
| D42 | Kochmodus `v0.3` (8.11.2026, Spezifikation `docs/kh/specs/2026-11-08-kochmodus-design.md`), alles wie empfohlen: ein Schritt groß mit großen Tasten und Wischen, „Alle Schritte“ öffnet Mealies Liste, Bildschirmsperre im Kochmodus aus, „✕“ zurück zum Rezept, Balken mit einem Abschnitt je Schritt zum Springen, Zeile „Du brauchst: …“ mit den Zutaten des Schritts, keine Utensilien pro Schritt (E1); Mengen in Klammern hinter der Zutat, nur bei Verknüpfung mit genau diesem Schritt und ohne Menge im Satz, überall wo Schritte stehen (E2); Zeiten werden Timer, bei Spannen bis zur kürzeren Zeit mit „noch … Min.“ (E3); Timer klingelt in der App, dazu „Auf Uhr-Timer legen“ per Kurzbefehl, falls T1 klappt, Push nur wenn nicht (E4); Sprachbefehle erst in `v0.3.1` nach T2 (E5); die letzten 30 geöffneten Rezepte offline, beim Abmelden geleert (E6) | beschlossen |
| D43 | Familienkochbuch `v0.4` (8.11.2026, Spezifikation `docs/kh/specs/2026-11-08-familienkochbuch-design.md`), alles wie empfohlen: PDF über den Druckdialog, Inhaltsverzeichnis mit Rezeptnummern statt Seitenzahlen (F1); Buch-Editor mit Vorschau pro Mealie-Kochbuch, Einstellungen pro Kochbuch gespeichert (F2, Wunsch nach dem Vorschlag); Rezeptkarte A4 mit demselben Editor (F3); Fotos nur mit der Markierung „Foto ist von uns“ (F4); Umzug über Mealies Migrationen plus Duplikat-Bericht (F5); Umluft-Klammer im Schritt, Menü-Zeitplan später (F6) | beschlossen |
| D44 | Nährwerte und Allergene `v0.5` (8.11.2026, Spezifikation `docs/kh/specs/2026-11-08-naehrwerte-allergene-design.md`), alles wie empfohlen: BLS 4.0 (CC BY 4.0) als schlanke Tabelle im Image (N1); Zuordnung einmal pro Mealie-Lebensmittel mit Vorschlag (N2); Gramm über Dichte und Stückgewichte (N3); eigener Block „Nährwerte pro Portion (ca.)“, Handwerte in Mealie gehen vor (N4); Allergene der 14 EU-Gruppen aus festen Regeln, pro Rezept korrigierbar (A1); „Ich vertrage nicht“ pro Konto mit Warnung und Namen (A2); Austausch-Hinweise und „Als Variante speichern“ (X1) | beschlossen |

---

## 3. Architektur

Eine Anwendung (unser Mealie-Fork) plus ein Backup-Container; KI und Whisper sind austauschbare Zusatzdienste.

```text
Handy · iPad · Browser  (Web-App, als App installierbar)
        │
Küchenhelfer = Mealie-Fork  (Backend FastAPI · Frontend Nuxt)
  ├─ Eingang · Prüfansicht · Duplikate · Plausibilität
  ├─ Mengen: Parser · Portionsrechner · Nährwerte · Allergene · Austausch
  ├─ Kochmodus: Timer · Sprachbefehle · Offline
  ├─ Teilen und Ausgabe: Kurzbefehl · Telegram · PDF
  ├─ Betrieb: Erststart · Systemprüfung · Profile
  └─ Datenbank (SQLite; Postgres optional) + Bilder
        │
        ├─ KI-Dienst       OpenAI-kompatibel: Ollama lokal oder Gratis-Cloud
        └─ Whisper-Dienst  OpenAI-kompatibel, lokal
Backup-Container → zweiter Speicherort → Push-Meldung an Uptime Kuma
```

**Fork-Regeln**

1. Unsere Funktionen liegen in eigenen Unterordnern mit dem Kürzel `kh`; die genauen Pfade legt der Code-Rundgang in Phase 0 fest.
2. Änderungen an Mealies vorhandenem Code bleiben klein; jede trägt den Kommentar `KH: <Grund>`, damit man sie beim Upstream-Abgleich findet.
3. Upstream: Remote `upstream` zeigt auf Mealie. Sicherheitsfixes immer einzeln übernehmen (`cherry-pick`), neue Funktionen nur bei Bedarf, Abgleich alle drei Monate.
4. Entfernen in zwei Stufen: erst Oberfläche und Routen ausblenden, Datenbank-Tabellen erst später per Migration.
5. Neuer Name und neues Logo; „basiert auf Mealie“, Lizenz und Copyright bleiben; Quellcode-Link in der Oberfläche (AGPL).

---

## 4. Funktionen und Reihenfolge

Grundsatz (D13): Die Familie nutzt es so früh wie möglich; was aufeinander aufbaut, kommt nacheinander; was nur für fremde Nutzer nötig ist, kommt zum Schluss. Keine Funktion fällt weg, sie kommt nur später.

| Funktion | Priorität | Woher | Phase |
|---|---|---|---|
| Tägliche Backups mit Restore-Test und Meldung | Muss | neu (Container) | 1 |
| Erreichbarkeit von unterwegs (HTTPS, Tunnel) | Muss | neu (Betrieb) | 1 |
| Beispielrezepte (selbst geschrieben, frei lizenziert) | Kann | neu | 1 |
| Eingang: Link, Text, Foto | Muss | umbauen: Mealies Import und KI-Import liefern einen Entwurf | 2 |
| Prüfansicht mit Original daneben | Muss | neu | 2 |
| Duplikat-Warnung | Muss | neu | 2 |
| Herkunfts-Badge (Quelle, Autor, geprüft) | Soll | neu | 2 |
| Deutscher Zutaten-Parser | Muss | umbauen (Mealies Parser) | 3 |
| Portionsrechner mit Mengen im Text, drei Wege | Muss | umbauen (Mealies Skalierung) | 3 |
| Plausibilitäts-Warnungen | Soll | neu | 3 |
| Kochmodus mit klickbaren Timern, auch bei gesperrtem Handy | Soll | umbauen (Mealies Kochmodus) | 4 |
| Sprachbefehle (weiter, zurück, Timer) | Soll | neu (Vosk im Browser) | 4 |
| Bildschirm bleibt an, Offline-Rezepte | Soll | Mealie hat „Bildschirm an“, Offline neu | 4 |
| PDF-Rezeptkarte und PDF-Familienkochbuch | Soll | neu | 5 |
| Teilen per Kurzbefehl | Soll | neu | 5 |
| Umzug aus anderen Apps | Soll | Mealie (Migrationen vorhanden) + Anleitung | 5 |
| Umluft-Umrechner, Menü-Zeitplan | Kann | neu | 5 |
| Nährwerte (BLS, „ca.“) | Muss | neu | 6 |
| Allergen-Tags und Familienprofil | Soll | neu | 6 |
| Eigene Austausch-Regeln | Soll | neu | 6 |
| Eingang: Video (Whisper) | Muss | umbauen (vorhandener KI-Import) | 7 |
| Telegram-Bot | Soll | neu | 7 |
| Profile: leicht, normal, stark, lokal; Hardware-Test | Muss | neu (Konfiguration) | 7 |
| Images für amd64/arm64 pro Release, `update.sh` | Muss | neu | 1 |
| Name, Logo | Muss | neu | 8 |
| Erststart-Assistent, Systemprüfung | Soll | neu | 8 |
| Wochenplan, Einkaufsliste | Später | Mealie (vorhanden) | – |
| Notizfeld „Nächstes Mal“ | Später | Mealie-Notizen | – |

---

## 5. Phasen

Jede Phase ist erst fertig, wenn ihr „Fertig wenn“ erfüllt ist. Die Familie nutzt den Fork ab Phase 1 (v0.0); die erste Version mit Prüfansicht (v0.1) ist das Ende von Phase 2. Nach v1.0 gilt ein Feature-Stopp, damit die Pflege machbar bleibt.

**Phasen-Regeln (D15)**

1. **Release pro Phase.** Jede Phase endet mit einem Git-Tag (`v0.0`, `v0.1`, …), fertigen Images in der GitHub Container Registry, einem `CHANGELOG.md`-Eintrag und einer Kurzanleitung. Wer Tag `v0.0` installiert, hat genau die Funktionen von Phase 1, vollständig lauffähig.
2. **Phasen bauen aufeinander auf.** Ein Release enthält seine Phase und alle davor (`v0.2` = Phasen 1 bis 3). Einzelne spätere Funktionen, die schwer sind oder Daten nach außen senden (Video, Telegram, Open Food Facts), lassen sich zusätzlich per Schalter in `.env` abschalten.
3. **Additiv statt Umbau.** Neue Funktionen kommen in einen eigenen Ordner `kh/<funktion>/` (Backend und Frontend). Fertiger Code früherer Phasen wird nur für Fehlerbehebungen geändert, jeweils mit Test.
4. **Erweiterungspunkte einplanen.** Wo absehbar ist, dass spätere Phasen andocken (Hinweise in der Prüfansicht, Importwege, Anzeige von Mengen), baut die frühere Phase eine einfache Liste oder einen Einhängepunkt, in den spätere Phasen sich eintragen. Nur dort, wo dieser Plan es schon vorsieht, nichts auf Vorrat.
5. **Stabile Schnittstellen.** API-Routen, Funktionen und Datenformate früherer Phasen bleiben kompatibel. Datenbank-Migrationen sind nur additiv (neue Tabellen oder Spalten); Umbenennen oder Löschen eigener Spalten erst mit Migrationsweg und Backup.
6. **Alte Tests bleiben grün.** Die CI führt die Tests aller Phasen aus. Ein roter Test einer früheren Phase blockiert den Merge.
7. **Upgrade-Test.** Vor jedem Release: vorherigen Tag installieren, Daten anlegen, auf den neuen Tag aktualisieren, Daten prüfen.

### Phase 0 · Fork und Code-Rundgang

- [x] Mealies Code ins eigene Repo `gamingnet006/own-recipe-app` holen: Remote `upstream` auf Mealie setzen, neueste stabile Version zusammenführen (kein GitHub-Fork, damit das Repo privat bleiben kann).
- [x] Mealies `CLAUDE.md`, `README.md` und `.gitignore` unverändert übernehmen (erledigt: v3.29.0 eingespielt, `# KH`-Block angehängt; 30.10.2026 bestätigt: Claude Code lädt Mealies `CLAUDE.md` und unsere `.claude/CLAUDE.md` gemeinsam); unsere `.gitignore`-Zeilen als markierten `# KH`-Block anhängen; prüfen, dass Claude Code `.claude/CLAUDE.md` zusätzlich lädt (D17).
- [x] Fork lokal auf dem Mac in Docker bauen und starten, Mealies Tests laufen lassen (29.10.2026: Image gebaut, mit 2 CPUs/2 GB gesund nach ~33 s, ~222 MB RAM; Backend-pytest Exit 0, Frontend 602/602 Tests grün); die echten Befehle in `.claude/CLAUDE.md` unter „Befehle“ eintragen.
- [x] Einfache CI auf GitHub: Lint und Tests bei jedem Push (`kh-ci.yml` ruft Mealies Test-Workflows auf; erster Lauf 29.10.2026 grün: Frontend, Backend SQLite und Postgres; übrige Mealie-Workflows im Repo deaktiviert).
- [x] Code-Rundgang: Aufbau notieren (Backend, Frontend, Datenmodell für Rezept, Zutat und Schritt, Import, Parser, Skalierung, Kochmodus, Backups) in `docs/code-rundgang.md`.
- [x] Liste „behalten · umbauen · entfernen · neu“ und die Pfade für unsere `kh`-Ordner in `docs/code-rundgang.md`.
- [ ] Frühe Tests T6 und T8 (Abschnitt 12); die übrigen jeweils vor ihrer Phase.
- **Fertig wenn:** Der Fork läuft lokal, die Tests sind grün, CI läuft und Rundgang und Liste stehen.

### Phase 1 · Läuft bei der Familie (v0.0)

- [x] CI baut das amd64-Image pro Tag und veröffentlicht es in der GitHub Container Registry; das arm64-Image wird auf dem Mac nativ gebaut und mit einem Befehl pro Release dorthin geschoben, solange das Repo privat ist (D20). (30.10.2026: `.github/workflows/kh-release.yml` und `kh/ops/release.sh` angelegt, Tests grün. Release-Kandidat `v0.0-rc.1` veröffentlicht: `-amd64` aus der CI, `-arm64` vom Mac, Lauf 8:48 Minuten. Auf dem Mac per `update.sh` aus GHCR geladen, gestartet und wieder zurück gewechselt, Daten geprüft. 31.10.2026: Release `v0.0` veröffentlicht. Vor dem Hochladen hat die CI den Upgrade-Test von `rc.2-amd64` bestanden, das arm64-Image auf dem MacBook `upgrade_test.sh` von `rc.2-arm64` (2 Rezepte, Bild unverändert). Offen: Test auf dem Pi.)
- [ ] `docker-compose.yml` und `.env.example` (nur Platzhalter, keine echten Zugangsdaten); auf dem Pi starten. (29.10.2026: `kh/ops/docker-compose.yml` und `kh/ops/.env.example` angelegt, auf dem Mac mit 2 CPUs/2 GB gesund nach ~36 s, ~299 MB RAM; offen: Start auf dem Pi.)
- [x] `update.sh`: erst Backup, dann neue Version, Gesundheitsprüfung; bei Fehler altes Image und Datenbank zurück (D21). (30.10.2026: `kh/ops/update.sh <image>` macht Mealie-Backup, Datei-Schnappschuss der gestoppten Datenbank, Wechsel, prüft Gesundheit, laufendes Image und Rezeptzahl; bei Fehler kommen altes Image und Schnappschuss zurück. Mealies Wiederherstellen allein reicht dafür nicht, weil es eine laufende App mit derselben Datenbank-Version braucht. Tests in der CI; auf dem Mac geprüft: „läuft bereits“, Update hin und zurück, kaputte Version, die alle Rezepte löscht und abstürzt, sowie Rückfall, wenn der alte Image-Name inzwischen woanders hinzeigt.)
- [x] Upgrade-Test automatisch in der CI: vorheriges Release mit Testrezepten starten, aktualisieren, Rezepte und Bilder prüfen; ein Fehler blockiert das Release (D23). (30.10.2026: `kh/ops/upgrade_test.sh` mit selbst geschriebenen Testdaten in `kh/ops/testdata/`, eingebaut in `kh-release.yml`. Lokal geprüft: Upgrade `v0.0-rc.1` → aktueller Stand bestanden, kaputte Version richtig durchgefallen. In der CI beim Release-Kandidaten `v0.0-rc.2` bestanden: `rc.1-amd64` → `rc.2-amd64`, 2 Rezepte und Bild unverändert, erst danach veröffentlicht.)
- [x] Automatische Updates nur für stabile Releases, standardmäßig an, abschaltbar (D29). (30.10.2026: `kh/ops/auto_update.sh on|off|status|check|run` mit cron um 4 Uhr, auf macOS als LaunchAgent, weil macOS `crontab` über SSH sperrt; Release-Images tragen die Betriebsdateien unter `/app/kh-bundle`, `check_bundle.sh` prüft jedes Image vor dem Hochladen; `update.sh` erneuert nach dem Wechsel Backup-Dienst und Tunnel. Tests in der CI; auf dem MacBook echt geprüft: Versionsliste von GHCR, Herunterladen mit Wegwerf-Anmeldung, Auspacken aus einem Probe-Image, Upgrade-Test samt Backup-Dienst. 31.10.2026: auf dem Mac mini eingeschaltet (LaunchAgent, Lese-Schlüssel in der `.env`), Probelauf über launchd erfolgreich. Nach dem Release von `v0.0` meldet `auto_update.sh check` dort, dass es auf `v0.0-amd64` aktualisieren würde. Offen: der erste echte Lauf in der Nacht zum 1.11.) (1.11.2026: erster echter nächtlicher Lauf auf dem Mac mini um 04:02, auf `v0.0.2-amd64` aktualisiert, alle Rezepte da.)
- [x] Kurzanleitung „Installieren“ in der README für dieses Release. Darin auch: Anmeldung bei ghcr.io, solange die Images privat sind, und `kh/ops/auto_update.sh on` mit dem Lese-Schlüssel (`KH_REGISTRY_USER`, `KH_REGISTRY_TOKEN`) für automatische Updates (D29). Außerdem: die Ordner `data` und `backups` vor dem ersten Start anlegen (Colima unter macOS 12 kann sie nicht selbst anlegen), und Hintergrund-Jobs auf macOS brauchen `/usr/local/bin` im PATH. (31.10.2026: in `docs/kh/README.md` auf Deutsch und Englisch; `kh/ops/install.sh` fragt Backup-Ort (D32) und Adresse, schreibt die `.env`, startet und legt den Backup-Schlüssel an. Auf dem MacBook streng nach Anleitung in einen leeren Ordner installiert: Betriebsdateien aus dem Image, `install.sh`, Backup klappt. Der Test fand einen Fehler, behoben: `up --build backup` baute auch das Mealie-Image. Der Pi-Test folgt (D30).)
- [x] Nicht benötigte Mealie-Teile in Oberfläche und Routen ausblenden (Stufe 1 der Fork-Regeln). (31.10.2026: Teilen-Links standardmäßig aus (`KH_SHARE_LINKS`), Ankündigungen für neue Gruppen aus, Explore-Seiten gesperrt, solange Gruppe und Haushalt privat sind; `tunnel.sh on` geht nur noch mit privaten Gruppen und Haushalten online. Eigener Code in `mealie/kh/` und im Nuxt-Layer `frontend/kh/` (D26). Im Browser auf dem MacBook geprüft: Rezeptmenü ohne „Teilen“, mit `KH_SHARE_LINKS=true` wieder da, Download klappt. Beim Prüfen fiel auf: Gruppe und Haushalt der Familie waren öffentlich, neue Rezepte wären ohne Anmeldung lesbar gewesen. Über Mealies Einstellungen auf privat gestellt, Ankündigungen aus; von außen geprüft: 404.)
- [ ] Backup-Container über Mealies Backup-Schnittstelle (erstellen, an den zweiten Ort kopieren; `restore.sh` nutzt Mealies Wiederherstellen): täglich, Aufbewahrung, Push-Meldung an Uptime Kuma, Restore-Test-Skript. Admin-Zugang nur als Platzhalter in `.env.example` (D21). (29.10.2026: `kh/ops/backup/` mit `backup.sh`, `restore.sh`, Zeitplan per cron, Aufbewahrung, Uptime-Kuma-Meldung; Tests in der CI; auf dem Mac Backup und Wiederherstellen eines Testrezepts geprüft. 31.10.2026: Backup vom Mac mini auf dem MacBook wiederhergestellt, Rezepte, Konten und Gruppe stimmen überein; Push-Adressen aus Uptime Kuma dürfen mit der Beispiel-Abfrage eingefügt werden. `kh/ops/restore_test.sh` spielt ein Backup mit `restore.sh` in eine Wegwerf-Installation ein und vergleicht Rezepte und Dateien; auf MacBook und Mac mini bestanden. 31.10.2026: Kopie auf einen USB-Stick mit `kh/ops/backup_copy.sh`, wahlweise mit Passwort verschlüsselt (D32, D33); Tests in der CI, auch Ver- und Entschlüsseln mit echtem age im Backup-Image. Am Mac mini eingerichtet, erste Kopie geprüft. Meldungen an Uptime Kuma auf dem Mac mini eingerichtet und getestet: Backup und Stick-Kopie melden an einen Monitor, das Update an einen zweiten. Offen: Zeitplan für den Restore-Test.)
- [x] HTTPS und Tunnel für den Zugriff von unterwegs (gratis, ohne offene Ports; D14). Selbstregistrierung bleibt aus (`ALLOW_SIGNUP=false`, Mealie-Standard); der Tunnel-Anbieter steht in „Was geht wohin“ (D22). (30.10.2026: Cloudflare Tunnel als Dienst `tunnel` in `kh/ops/docker-compose.yml`, `kh/ops/tunnel.sh on|off|status` mit Sicherheitsprüfung, Tests in der CI. Auf dem Mac geprüft: Die Sperre greift beim Standard-Konto, ein ungültiger Schlüssel wird abgelehnt, „Beenden“ im Desktop-Skript schaltet den Tunnel mit ab. Tunnel in Cloudflare angelegt, Admin-E-Mail und -Passwort geändert; seit 30.10. läuft Küchenhelfer samt Tunnel auf dem Mac mini (D28), Probe-Backup dort ok. Route in Cloudflare angelegt: `https://kochbuch.example.org` antwortet über den Tunnel (HTTP 200, gültiges Zertifikat). Vom Handy über Mobilfunk erreichbar (30.10.2026). Der Umzug auf den Pi folgt mit der Pi-Aufgabe, D27.)
- [ ] Familienkonten anlegen, Beispielrezepte als Startdaten. (31.10.2026: keine Beispielrezepte, Konten per Einladungslink (D31); Anleitung in `docs/kh/familienkonten.md`. Auf der MacBook-Kopie geprüft: Registrierung per Link klappt trotz `ALLOW_SIGNUP=false`, jeder Link gilt einmal, eingeladene Konten haben keine Admin- oder Verwaltungsrechte. Offen: Konten der Familie anlegen.)
- [x] `THIRD_PARTY_NOTICES.md` und `CHANGELOG.md`. (30.10.2026: `docs/kh/CHANGELOG.md` angelegt, wegen D17 nicht im Hauptordner; `release.sh` verlangt pro Version einen Abschnitt. 31.10.2026: `docs/kh/THIRD_PARTY_NOTICES.md` mit Lizenzen, an der Quelle geprüft: GitHub und Paketangaben in den Images.)
- **Fertig wenn:** Die Familie trägt von unterwegs Rezepte ein, ein Backup ist auf einem zweiten Gerät wiederhergestellt und Release `v0.0` lässt sich nur mit der Kurzanleitung auf einem frischen Pi installieren.

### Phase 2 · Eingang, Prüfen, Duplikate (v0.1)

- [x] Entwürfe in einer eigenen `kh`-Tabelle samt Original; erst die Freigabe legt über Mealies vorhandenen Weg ein normales Rezept an und verknüpft das Original. Mealie selbst muss keine Entwürfe ausfiltern (D18, beantwortet T6). (31.10.2026: Tabelle `kh_drafts` auf eigenem Alembic-Zweig `kh`, Übernehmen über `RecipeService.create_one`, Herkunft über `recipe_id`; Backups stellen Entwürfe vollständig wieder her, 1.11.2026.)
- [x] KI-Anbindung über Mealies KI-Anbieter-Verwaltung (Ollama auf dem Mac oder eigener Key, D6, D25). (1.11.2026: Google Gemini mit Gratis-Schlüssel statt Ollama, D34, D35, D36; Probelauf vom iPhone über Tailscale ok.)
- [ ] Erweiterungspunkte für spätere Phasen: Liste der Prüfungen und Hinweise in der Prüfansicht, Liste der Importwege (Phasen-Regel 4). (Teilweise, Review 1.11.2026: Hinweise sind eine Liste mit `kind`, die Oberfläche zeigt neue Arten ohne Umbau. Prüfungen und Eingänge werden zu Listen, sobald die erste spätere Phase andockt.)
- [x] Eingang: Link (vorhandener Scraper), Text, Foto oder Screenshot, Ergebnis immer als Entwurf. (Mealies Import-Seiten führen auf den Eingang; im Probelauf 1.11.2026 Link, Text, Foto und Screenshot ok.)
- [x] Original mitspeichern: Foto, Beschreibung, Quelle, Autor, Datum, KI-Modell. (Originalfotos, Text oder Link, wer, wann und KI-Modell; am Rezept als Abzeichen mit „Original ansehen“.)
- [x] Prüfansicht wie im Mockup (Screen 2): Original und Ergebnis, Hinweise oben, Speichern, Verwerfen, Bearbeiten. (Am Handy untereinander, ab iPad-Breite nebeneinander; Portionen und Portionsangabe eintragbar.)
- [x] Duplikat-Check: normalisierter Link, Titel- und Zutaten-Ähnlichkeit; nur warnen, nie automatisch löschen. (Gleicher Link, ähnlicher Titel, gleiche Zutaten; beim Übernehmen erneut geprüft.)
- [x] Herkunfts-Badge in der Rezeptansicht.
- [x] Sicherheit beim Abrufen: private Adressbereiche sperren, Größe und Zeit begrenzen, KI-Antworten nur nach festem Schema, Ausgaben escapen. (Mealies sicherer Abruf, KI-Antworten nur nach Schema, Ausgaben maskiert, nur http(s)-Links klickbar.)
- **Fertig wenn:** Ein Foto eines handgeschriebenen Rezepts landet als Entwurf in der Prüfansicht, die Testfälle (ohne Video) ergeben prüfbare Entwürfe, nichts wird ohne Freigabe gespeichert und die Duplikat-Testfälle schlagen an. Danach Release v0.1. (1.11.2026: erfüllt. `v0.1` ist mit beiden Images veröffentlicht, Upgrade-Test von `v0.0.2` und CI auf SQLite und Postgres grün. Am selben Tag folgte `v0.1.1` (Teilen per Kurzbefehl, D37), Upgrade-Test von `v0.1` grün; der Mac mini geht in der Nacht auf den 2.11. von `v0.0.2` direkt auf `v0.1.1`.)
- **Danach** (Wünsche aus dem Probelauf, 1.11.2026):
  - [x] Design und Funktionen durchsehen: Vorschläge mit Mockups zum Abstimmen, bevor Code entsteht; nach `v0.1`, vor Phase 3. (1.11.2026: Look „Salbei“ gewählt, Leiste unten, eigene Rezeptseite; D38.)
  - [x] Oberfläche nach D38 umsetzen: `v0.1.2` Rahmen, `v0.1.3` Rezeptseite. (8.11.2026: beides ausgeliefert mit `v0.2`, ohne eigene Releases.)
  - [ ] Rezeptsprache in der App einstellbar (Admin-Einstellung statt `KH_RECIPE_LANGUAGE` in `.env`, D36).
  - [ ] Fremdsprachige Seiten mit Rezeptdaten übersetzen; kostet eine KI-Anfrage je Link.
  - [x] Zweiter KI-Anbieter als Ausweichweg, wenn das Gratis-Kontingent aufgebraucht ist (Spezifikation „Später“). (4.11.2026: durch die Prio-Liste mit beliebig vielen Anbietern und der Glocke, D39.)

### Phase 3 · Mengen (v0.2)

- [x] `parse_ingredient()` für deutsche Angaben (½, 1 1/2, Bereiche, EL, TL, Prise, Bund, Pck., Stück) mit Tests; ersetzt oder ergänzt Mealies Parser.
- [x] Mengen im Schritttext: Der Text bleibt unverändert; eine `kh`-Nebentabelle merkt sich Stelle, Zutat und optionalen Bruchteil, aufbauend auf Mealies `ingredient_references`. `link_quantities()` beim Import; Verknüpfen und Lösen in der Prüfansicht; nach einer Textänderung werden die Stellen neu geprüft (D19).
- [x] Portionsrechner mit drei Wegen (Portionen, „Ich habe nur …“, Backform) und einer einzigen Anzeige-Funktion `format_amount()` für alle Ansichten.
- [x] Zeiten bleiben fest; Hinweis bei Faktor über 2 oder unter 0,5.
- [x] Plausibilitäts-Warnungen in der Prüfansicht: Mengen, Zeiten, Temperaturen, Zutat ohne Schritt, umgerechnete Einheiten (nutzt den Parser).
- **Fertig wenn:** Die Mengen-Testfälle (Abschnitt 7) bestehen und die Plausibilitäts-Testfälle schlagen an.

### Phase 4 · Kochmodus (v0.3)

- [x] Zeiten im Schritttext erkennen und anklickbar machen (auch „20–30 Min.“ und „eine halbe Stunde“).
- [x] Mengen neben Zutaten im Schritttext: Nennt ein Schritt eine Zutat ohne Menge („die Butter schmelzen“), steht ihre Menge passend zum gewählten Faktor dabei, etwa „die Butter (200 g) schmelzen“. Der Text bleibt unverändert; die Darstellung wird vor dem Bau abgestimmt (D41).
- [x] Timer bei gesperrtem Handy nach dem Ergebnis von T1: Kurzbefehl mit echtem Uhr-Timer, Server-Timer mit Push, Bildschirm anlassen.
- [x] Große Tasten und Wischen für Weiter und Zurück (D42).
- [ ] Sprachbefehle mit Vosk im Browser, als `v0.3.1` nach T2 (D42).
- [x] Offline-Rezepte: die letzten 30 geöffneten (Web-App, dafür ist HTTPS nötig; steht seit Phase 1; D42).
- **Fertig wenn:** Auf dem iPhone klingelt ein Timer bei gesperrtem Handy, und die Tasten führen durch die Schritte; „weiter“ per Sprache folgt mit `v0.3.1`.

### Phase 5 · Familienkochbuch und Teilen (v0.4)

- [x] PDF: Rezeptkarte und Familienkochbuch mit Buch-Editor und Vorschau (Auswahl, Inhaltsverzeichnis, Systemschrift, nur eigene Fotos; D43).
- [x] Kurzbefehl für das Teilen-Menü mit einem widerrufbaren Token pro Gerät. (1.11.2026: vorgezogen in `v0.1.1`, D35, D37.)
- [x] Umzug: Anleitung für Mealies Migrationen, danach Duplikat-Scan.
- [x] Umluft-Umrechner (D43); Menü-Zeitplan später, sobald ihn jemand vermisst.
- **Fertig wenn:** Ein Link über das Teilen-Menü landet als Entwurf in der Prüfansicht und ein Kochbuch mit 10 Rezepten ist als PDF druckbar.

### Phase 6 · Nährwerte und Allergene (v0.5)

- [x] Nährwerte: BLS lokal (nach T5), Open Food Facts optional und später; Zuordnung bestätigen und merken; Standardgewichte; Anzeige „ca.“.
- [x] Allergen-Tags: feste Regeln für die 14 EU-Hauptallergene, KI nur als Vorschlag, Familienprofil als Warnung, Hinweis „ohne Gewähr“.
- [x] Austausch-Regeln: Standardliste plus eigene Regeln; danach Allergen-Check neu; als Variante speichern, nie das Original überschreiben.
- **Fertig wenn:** Jeder Allergen-Tag und Nährwert ist auf eine Zutat rückführbar und die Allergen-Testfälle (Abschnitt 7) bestehen.

### Phase 7 · Video, Bots und schwere KI (v0.6)

- [ ] Whisper-Dienst (OpenAI-kompatibel, lokal) nach T3.
- [ ] Eingang Video (Teil erledigt, 8.11.2026, P7.2; Rest ist P7.3 Whisper für eigene Dateien): Weg nach T4/D5 ohne Download: Videolinks werden nicht abgerufen, Beschreibung oder Screenshot machen den Entwurf, der Link bleibt Quelle; Mealies yt-dlp ist entfernt (8.11.2026, P7.2; ein Whisper-Weg für eigene Dateien ist P7.3).
- [x] Telegram-Bot (holt Nachrichten selbst ab, nur erlaubte IDs). (8.11.2026: P7.1 im Paket v0.5; Dienst `telegram` im Profil `telegram`, Tests mit aufgezeichnetem HTTP; Pi-Probelauf und Telegram-Probe von Hand stehen noch aus.)
- [ ] Profile `leicht`, `normal`, `stark`, `lokal` und Hardware-Test (1 Minute Audio messen, Profil vorschlagen).
- **Fertig wenn:** Ein Reel-Link über das Teilen-Menü oder Telegram landet als Entwurf in der Prüfansicht und das Profil `leicht` läuft auf dem Pi.

### Phase 8 · Betrieb und Veröffentlichung (v1.0)

- [ ] Neuer Name und Logo (nach T7); Mealie-Hinweis, Lizenz und Quellcode-Link in der Oberfläche.
- [ ] Erststart-Assistent (Hardware-Test, Profil, KI-Anbindung, Backup-Test) und Systemprüfung.
- [ ] Häkchen „Automatische Updates“ in den Admin-Einstellungen; schaltet `KH_AUTO_UPDATE` (D29).
- [ ] Nicht benötigte Mealie-Tabellen per Migration entfernen (Stufe 2 der Fork-Regeln).
- [ ] README mit „Was geht wohin“ (Abschnitt 8), Installationsanleitung Deutsch und Englisch, Wartungs-Checkliste.
- [ ] Rechts-Checkliste (Abschnitt 9), Lizenz-Scan, Name geprüft.
- [ ] Ein gemeinsamer Image-Tag für amd64 und arm64, sobald die CI beide Architekturen selbst baut (öffentliches Repo, D20).
- [ ] Release `v1.0`, Issue-Vorlagen.
- **Fertig wenn:** Eine fremde Person installiert es nur mit dem README auf einem frischen Raspberry Pi.

**Später:** Wochenplan und Einkaufsliste (in Mealie vorhanden, nur aufräumen) · Notizfeld „Nächstes Mal“ · Desktop-App.

---

## 6. Mengen: Portionen im Text und Nährwerte

Alle Mengen rechnen sich live mit, in der Zutatenliste und im Schritttext; Zeiten, Temperaturen und Formgrößen bleiben fest.

**Grundidee.** Zutaten stehen strukturiert da (Menge, Einheit, Zutat, Notiz). Mengen im Schritttext sind mit einer Zutat verknüpft, optional mit Bruchteil („die Hälfte davon“). Der Text selbst bleibt unverändert; die Verknüpfung (Stelle, Zutat, Bruchteil) liegt in einer `kh`-Nebentabelle (D19). Kein frei programmierbares Vorlagensystem; das ist einfacher und sicherer.

**Beim Import.** Die KI liefert Zutaten strukturiert und Schritte mit markierten Mengen. `link_quantities()` schlägt eine Verknüpfung vor, wo im Text eine Zutatenmenge ohne Verknüpfung steht („250 g Mehl“). In der Prüfansicht sind verknüpfte Mengen farbig, Antippen verknüpft oder löst. Zahlen ohne Verknüpfung bleiben fest.

| Weg | Eingabe | Faktor |
|---|---|---|
| Portionen | neue Portionszahl | neu ÷ Basis |
| „Ich habe nur …“ | Menge einer Zutat, z. B. 300 g Mehl | 300 ÷ 250 |
| Backform | alter und neuer Durchmesser, bei Rechteck Länge × Breite | Fläche neu ÷ Fläche alt (26 → 20 cm ergibt etwa 0,59) |

**Anzeige in einer Funktion `format_amount()`** (Web, Kochmodus, PDF, Einkaufsliste):

- Brüche statt Dezimalzahlen: ¼, ⅓, ½, ⅔, ¾.
- Stückware (Eier, Zwiebeln) auf halbe Stücke; bei 1½ Eiern der Hinweis „ein Ei verquirlen und die Hälfte nehmen“.
- Einheiten wechseln: 1000 g → 1 kg, 1000 ml → 1 l, 3 TL → 1 EL.
- Gramm ab 100 g auf 5 oder 10 runden.
- Bereiche („2–3 EL“) skalieren an beiden Enden.
- Fest bleiben Prise, „etwas“, „nach Geschmack“ und alle Zutaten mit Skalierungsart „fest“.

**Gespeichert** wird nur die Basis (Portionen oder Ertrag wie „Backform Ø 26 cm“). Der gewählte Faktor ist reine Ansicht und gilt auch für PDF und Einkaufsliste. Nährwerte pro Portion bleiben gleich, die Gesamtsumme ändert sich.

**Nährwerte, einfach erklärt**

1. Jede Zutatenzeile wird einem Eintrag der Nährwert-Datenbank zugeordnet („Mehl“ → „Weizenmehl Type 405“).
2. Die Menge wird in Gramm umgerechnet („2 EL Öl“ etwa 28 g, „1 Ei“ etwa 55 g, „500 ml Milch“ etwa 515 g).
3. Die Datenbank nennt Werte pro 100 g; daraus wird je Zutat gerechnet.
4. Alles wird addiert, durch die Portionen geteilt und als „ca.“ pro Portion angezeigt.

Schritt 1 und 2 brauchen Bestätigung: Die Zuordnung wird einmal in der Prüfansicht bestätigt und gemerkt, dazu kommt eine Tabelle mit Standardgewichten. Start einfach: zuerst nur Zutaten mit Gramm oder Milliliter, der Rest folgt.

---

## 7. Qualität und Tests

- **Testset** (eigener Testordner, Pfad nach dem Code-Rundgang): 20 selbst geschriebene Fälle mit Eingabe und erwartetem Ergebnis. Gemischt aus Webseite (lokale HTML-Datei mit JSON-LD), Text, selbst gemachtem Foto oder Screenshot, Transkript, Duplikat-Paaren (gleicher Link mit Zusatz, gleiches Rezept anders geschrieben), Fehlerfällen (Unsinn-Mengen) und Allergen-Fällen mit versteckten Zutaten (z. B. Worcestersauce enthält Fisch).
- **Mengen-Testfälle:** ½, 1 1/2, Bereiche, Stückware, Löffel, Einheitenwechsel, Platzhalter im Text, Faktor 0,5 / 2 / 3, Backform 26 → 20 cm, „ich habe nur 300 g Mehl“.
- **KI in Tests:** Tests nutzen aufgezeichnete KI-Antworten (selbst erzeugt, frei lizenziert) und prüfen Schema, Prüfansicht und Fehlerfälle; kein KI-Key in der CI. Echte Modellqualität wird getrennt gemessen (D23).
- **Echte Reels und Webseiten** nur privat testen, nie im öffentlichen Repo.
- **CI bei jedem Push:** Mealies Lint und Tests plus unsere Tests; Image-Build für amd64 und arm64.
- **Vor jedem Upstream-Abgleich und Update:** Testset, Backup, kurze Restore-Probe.
- **KI-Qualität (privat):** Anteil richtig erkannter Zutaten und Mengen vor der Prüfung, pro Modell notiert.
- **Pi-Probe:** am Ende jeder Phase auf dem echten Raspberry Pi installieren und durchklicken.

---

## 8. README-Vorlage: Was geht wohin, Profile

Im Profil „lokal“ verlässt nichts das Haus; alle anderen Wege sind einzeln abschaltbar.

| Funktion | Was wird gesendet | An wen | Profil „lokal“ |
|---|---|---|---|
| Link importieren | Seitenadresse | die jeweilige Webseite | gleich |
| Text oder Foto auslesen | Text oder Bild | lokale KI (Standard) oder Cloud-KI, nur mit eingetragenem Key | nur lokale KI |
| Video oder Audio umwandeln | Audio | lokales Whisper (Standard) | nur lokal |
| Zugriff von unterwegs | gesamter Verkehr zur Web-App; Cloudflare kann ihn lesen, weil HTTPS dort endet | Cloudflare (Tunnel `kochbuch.example.org`, D27) | Tunnel aus: nur Heimnetz oder eigenes VPN |
| Automatische Updates | Abruf der Versionsliste und der neuen Images, mit dem Lese-Schlüssel, solange das Repo privat ist; beim Erneuern des Backup-Dienstes das Alpine-Basisimage und Pakete | GitHub (ghcr.io), Docker Hub, Alpine-Paketspiegel (D29) | aus (`KH_AUTO_UPDATE=false`) |
| Teilen per Telegram | Link oder Screenshot | Telegram-Server | aus |
| Teilen per Kurzbefehl | Link | dein Küchenhelfer | gleich |
| Sprachbefehle | Mikrofon-Audio | nirgends, Vosk läuft im Browser | gleich |
| Nährwerte | Zutatennamen | BLS lokal; Open Food Facts online (optional) | nur BLS lokal |
| Backups | Daten | dein zweiter Speicherort, extern nur verschlüsselt | gleich |
| Benachrichtigungen | Kurztext | ntfy, SMTP oder Resend, je nach Wahl | ntfy oder SMTP im eigenen Netz |
| Timer-Push | Timer-Text | Apples Push-Dienst über die Web-App | Kurzbefehl statt Push |

| Profil | Gedacht für | Was läuft | Was nicht |
|---|---|---|---|
| leicht | Raspberry Pi, alter Mini | Text- und Screenshot-Import, Prüfansicht, Kochmodus; Videos nachts in der Warteschlange oder auf einem stärkeren Rechner | große lokale KI |
| normal | aktueller Mini-PC, Mac | zusätzlich kleines Whisper und kleine lokale KI | große Modelle |
| stark | Apple Silicon, Mini-PC mit viel RAM | großes Whisper und lokale KI | – |
| lokal | beliebig, kombinierbar | alles auf eigener Hardware, kein Telegram, keine Cloud-Keys | Cloud-Funktionen |

Der Hardware-Test beim ersten Start misst, wie lange 1 Minute Audio dauert, und schlägt ein Profil vor.

---

## 9. Rechts-Leitplanken

Kein Rechtsrat; vor der Veröffentlichung einmal juristisch prüfen lassen.

1. **Nur private Instanzen.** Keine fremden Rezepte, Texte oder Fotos hosten, öffentlich teilen oder im Repo ablegen; Quelle und Autor immer mitspeichern; Teilen-Links nur bewusst, standardmäßig aus.
2. **Kein Downloader im Repo.** yt-dlp nur als optionales Plug-in, vom Nutzer selbst installiert, standardmäßig aus, mit Warnhinweis. Hintergrund: Instagram [verbietet automatisiertes Sammeln ohne Erlaubnis](https://help.instagram.com/581066165581870) und [schränkt Konten bei Scraping ein](https://help.instagram.com/740480200552298); Apples [App-Store-Regel 5.2.3](https://developer.apple.com/app-store/review/guidelines/) untersagt Apps, die Medien von Drittquellen laden.
3. **Standardweg ohne Download:** Beschreibungstext einfügen oder Screenshot hochladen.
4. **Lizenzen.** Das ganze Projekt steht unter AGPL-3.0; Mealies Hinweise bleiben, der Quellcode-Link steht in der Oberfläche. `THIRD_PARTY_NOTICES.md` für jede Abhängigkeit; Server-Teile mit „source-available“-Lizenz meiden. [Open Food Facts](https://support.openfoodfacts.org/help/en-gb/12-api-data-reuse/94-are-there-conditions-to-use-the-api) verlangt Namensnennung und Share-Alike; die [BLS-Bedingungen](https://heise.de/-11123877) vor dem Einbinden lesen.
5. **Keys.** Nur eigene Keys der Nutzer, nie Keys aus dem Netz; keine Keys im Repo; Secret-Scan aktivieren.
6. **Datenschutz.** Keine Telemetrie; kein zentraler Server, jeder hostet selbst; die Tabelle in Abschnitt 8 nennt alles, was das Haus verlässt.
7. **Namen und Logos.** Kein TikTok, Instagram oder Mealie in Name oder Logo; Projektname auf Konflikte prüfen; Schriften nur mit freier Lizenz.
8. **Gesundheit.** Allergen-Tags und Nährwerte sind Hinweise ohne Gewähr, nie „garantiert frei von“.
9. **Tests und Doku** nur mit selbst geschriebenen oder frei lizenzierten Rezepten.
10. **KI-geschriebener Code.** Abhängigkeiten per Lizenz-Scan prüfen, keine großen Fremdblöcke übernehmen, Quelle im Kommentar nennen.

---

## 10. Kosten-Check

Stand 28.10.2026; Preise und Limits ändern sich, vor der Veröffentlichung neu prüfen.

| Baustein | Kosten | Haken |
|---|---|---|
| Küchenhelfer (Fork), Backup, Uptime Kuma | 0 € | nur Strom und eigene Hardware |
| Lokale KI (Ollama) und Whisper | 0 € | braucht Rechenleistung, darum Profile |
| Gratis-Cloud-KI (optional) | 0 € | Limits, Änderungen, teils Datennutzung; [OpenAIs Gratis-Stufe reicht für Mealie nicht](https://mealie.io/documentation/getting-started/installation/ai-providers/) |
| Benachrichtigungen | 0 € | ntfy und SMTP gratis; [Resend](https://www.resend.com/pricing.md) sendet nur von einer eigenen verifizierten Domain |
| Telegram-Bot | 0 € | Telegram-Konto nötig; der Bot [lädt nur Dateien bis 20 MB](https://core.telegram.org/bots/faq) |
| Nährwerte: BLS 4.0 | 0 € | [seit Dezember 2025 kostenfrei](https://heise.de/-11123877); Bedingungen prüfen |
| iPhone: Web-App und Kurzbefehl | 0 € | [Push nur für zum Home-Bildschirm hinzugefügte Web-Apps](https://firt.dev/notes/pwa-ios/) |
| GitHub (Repo, CI, Images) | 0 € | [arm64-Runner nur für öffentliche Repos kostenlos](https://github.blog/changelog/2025-08-07-arm64-hosted-runners-for-public-repositories-are-now-generally-available/); solange das Repo privat ist, arm64 auf dem Mac bauen (D20) |
| Cloudflare Tunnel | 0 € | Cloudflare sieht den Verkehr (Abschnitt 8) |
| Domain `example.org` (aus dem Toggly-Projekt) | 0 € bis 3.7.2027 (schon bezahlt) | danach Verlängerung (etwa 10 € im Jahr) oder Wechsel auf eine kostenlose Adresse, z. B. Tailscale Funnel |
| Docker Desktop (Mac) | privat 0 € | [in großen Firmen kostenpflichtig](https://docs.docker.com/subscription-billing/desktop-license.md); Podman als freie Alternative |
| iOS-App im Store, signierte Mac-App | 99 USD pro Jahr | [Mitgliedschaft nötig](https://developer.apple.com/support/compare-memberships); nicht geplant |

---

## 11. Risiken und Lösungen

| Risiko | Lösung | Phase |
|---|---|---|
| KI vertut sich (Mengen, erfundene Zutaten) | Prüfansicht mit Original, Plausibilitäts-Warnungen, nichts ungeprüft speichern | 2 |
| Reel-Import bricht (Plattformen ändern oder sperren) | Beschreibung und Screenshot als Standard, Download nur als Plug-in, „experimentell“ | 7 |
| Rezept steht nur im Bild oder Kommentar | Beschreibung und Screenshot zuerst auswerten | 2 |
| Duplikate schwer zu erkennen; [Mealie meldet doppelte Links nicht](https://github.com/mealie-recipes/mealie/discussions/3478) | Link normalisieren, Titel und Zutaten vergleichen, nur warnen | 2 |
| URL-Import: Zugriff aufs Heimnetz, eingeschleuste Anweisungen, Schadcode in der Anzeige | Private Adressbereiche sperren, Schema für KI-Antworten, escapen | 2 |
| [Mealies Parser verhaspelt sich teils, z. B. bei 1/3](https://www.github.com/mealie-recipes/mealie/issues/3318) | Eigener deutscher Parser mit Tests | 3 |
| Nährwerte nur geschätzt | Zuordnung bestätigen und merken, Standardgewichte, „ca.“ | 6 |
| Allergen-Tags falsch | Feste Regeln, KI nur Vorschlag, Bestätigung, „ohne Gewähr“ | 6 |
| [Timer auf einer mobilen Webseite nicht garantierbar](https://github.com/mealie-recipes/mealie/discussions/5356) | Kurzbefehl mit Uhr-Timer, Server-Timer mit Push, Bildschirm an; früh testen (T1) | 4 |
| [Browser-Spracherkennung läuft nicht in installierten Web-Apps](https://mobilexweb.com/ios-14.5/) | Vosk lokal im Browser, Tasten als Rückfall (T2) | 4 |
| Backup fehlt oder lässt sich nicht einspielen | Täglich auf zweiten Ort, Push-Meldung, Restore-Test vor jedem Update | 1 |
| Große fremde Codebasis | Code-Rundgang, Mealies `AGENTS.md`, erst Tests, dann Änderungen | 0 |
| Konflikte beim Upstream-Abgleich | Eigene `kh`-Ordner, `KH:`-Markierung, `cherry-pick`, Abgleich alle drei Monate | laufend |
| Mac und Pi verhalten sich unterschiedlich | Alles in Docker, Pi-Probe am Ende jeder Phase (Abschnitt in `.claude/CLAUDE.md`) | laufend |
| Pi zu langsam | Profile, Hardware-Test, Warteschlange, schwere Builds nur in der CI | 7, 8 |
| Teilen unterwegs braucht Erreichbarkeit und HTTPS | Tunnel oder VPN mit Gratis-Tarif, widerrufbarer Token pro Gerät, Telegram ohne offene Tür | 1, 5, 7 |
| Updates bei anderen gehen schief | `update.sh` mit Backup und Rückweg, Upgrade-Test vor jedem Release, Sicherheits-Hinweise von Mealie verfolgen | 1 |
| Zu viel auf einmal | Familie nutzt ab Phase 1, v0.1 nach Phase 2, Feature-Stopp nach v1.0 | laufend |
| Spätere Phase macht Früheres kaputt | Phasen-Regeln (Abschnitt 5): additiv, Erweiterungspunkte, alte Tests in der CI, Upgrade-Test | laufend |
| KI-geschriebener Code mit unklarer Herkunft | Lizenz-Scan, keine großen Fremdblöcke | laufend |
| Pflege bleibt an einer Person hängen | Wenige Bausteine, automatische Tests, monatlicher Update-Termin, gute Doku | laufend |
| Rechte-Ärger | Abschnitt 9, juristische Prüfung vor dem Release | 8 |

---

## 12. Frühe Tests

- [x] **T1 Timer:** Startet ein Kurzbefehl-Link bei gesperrtem iPhone einen klingelnden Uhr-Timer? Alternativ Server-Timer mit Push. (8.11.2026: ja. Der Link `shortcuts://run-shortcut?name=KH%20Timer&input=text&text=1` aus Safari startet den Uhr-Timer, und er klingelt bei gesperrtem iPhone. Damit kommt „Auf Uhr-Timer legen“ in `v0.3`, Push entfällt; D42.)
- [ ] **T2 Sprache:** Vosk mit deutschem Modell im Browser auf dem iPhone, mit Küchengeräuschen.
- [ ] **T3 Whisper-Tempo:** Wie lange dauert 1 Minute Audio auf MacBook, Raspberry Pi und gegebenenfalls Mini-PC?
- [ ] **T4 Instagram-Weg:** Beschreibung und Screenshot gegen Download, mit eigenen Beispielen.
- [x] **T5 BLS:** Nutzungsbedingungen lesen und die Einbindung in ein offenes Projekt klären. (8.11.2026: BLS 4.0 vom Max Rubner-Institut ist Open Data unter CC BY 4.0, Download ohne Anmeldung unter blsdb.de, 7.140 Lebensmittel mit deutschen Namen, 138 Nährstoffe je 100 g. Darf mit Namensnennung ins Repo und ins Image; Änderungen an den Daten kennzeichnen. Open Food Facts nur für Markenprodukte, online und mit 10 Suchen pro Minute.)
- [x] **T6 Entwurfs-Stufe:** beantwortet durch D18 (eigene `kh`-Tabelle, Mealies Datenmodell bleibt unverändert).
- [ ] **T7 Name:** Projektname auf Marken- und Namenskonflikte prüfen.
- [ ] **T8 Pi-Probe:** Offizielles Mealie-Image auf dem Raspberry Pi starten und Tempo sowie RAM notieren. Wartet auf den Pi (29.10.2026 nicht erreichbar); bis dahin Ersatzwert vom Mac mit 2 CPUs/2 GB: gesund nach ~33 s, ~222 MB RAM.

---

## 13. Start-Prompt für Claude Code

Im geklonten Fork (mit `PLAN.md` im Hauptordner und `.claude/CLAUDE.md`) einfügen:

```text
Lies .claude/CLAUDE.md und PLAN.md. Wir bauen den Küchenhelfer als Fork von Mealie.
Beginne mit Phase 0 und arbeite in kleinen Schritten:
1) Erkläre kurz, wie du den Fork lokal auf meinem Mac in Docker baust und startest,
   und trage die echten Befehle in .claude/CLAUDE.md unter „Befehle“ ein.
2) Lass Mealies Tests laufen und berichte das Ergebnis.
3) Mach den Code-Rundgang und schreibe docs/code-rundgang.md mit der Liste
   „behalten · entfernen · neu“ und den Pfaden für unsere kh-Ordner.
Ändere in Phase 0 noch keinen Mealie-Code. Frag nach, wenn etwas unklar ist,
und hake Erledigtes in PLAN.md ab.
```
