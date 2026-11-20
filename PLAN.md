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
| D45 | Großes Update `v0.5` (8.11.2026, `docs/kh/specs/2026-11-08-v0.5-paket-design.md`): Phase 6 plus aus Phase 8 „Über Küchenhelfer“ mit Lizenz und Quellcode-Link, Häkchen „Automatische Updates“ (Brücke über `data/kh/auto_update.json`), Systemprüfung mit Erststart-Liste, „Was geht wohin“, Installations- und Wartungsanleitung, Rechts-Checkliste und Lizenz-Scan, Issue-Vorlagen; aus Phase 7 Telegram-Bot und Whisper als abschaltbare Zusatzmodule ohne Schlüssel im Repo, Video-Links nach D5 ohne Abruf, Profile mit Hardware-Test, Sprachbefehle als Test-Schalter (T2). Nicht dabei: Name und Logo (T7), Entfernen von Mealie-Tabellen, gemeinsamer Image-Tag, Ollama | beschlossen |
| D46 | Zusatzfunktionen (8.11.2026): Admin-Seite „Mehr → Zusatzfunktionen“ für den ganzen Haushalt; ausgeschaltet verschwindet die Funktion aus der Oberfläche, die Daten bleiben. Oben „Große Bereiche“ Einkaufsliste und Essensplaner (Vorschlag G1–G5 wie empfohlen: zwei große Karten plus Frage in der Erststart-Liste, nur ausblenden, Leiste dann mit drei Plätzen, gilt für den Haushalt, Standard beide an). Darunter an: Familienkochbuch, Doppelte Rezepte, Umluft-Klammer, Nährwerte, Allergene, Austausch und Varianten, Offline-Rezepte; aus: Uhr-Timer, öffentliche Teilen-Links, Telegram, Whisper, Sprachbefehle. Grundfunktionen (Eingang, Prüfansicht, Mengen, Kochmodus, Timer, Backups, Updates) bleiben immer an. Lokale KI (Ollama) wird nicht gebaut: nur ein Hinweis bei der KI-Einrichtung und eine als ungetestet markierte Anleitung `docs/kh/LOKALE-KI.md` | beschlossen |
| D47 | Das große Update aus D45 und D46 erscheint als `v1.0` statt `v0.5` (8.11.2026, Wunsch des Nutzers). Dazu kommen Name und Logo: 5 bis 10 Vorschläge mit grober Konfliktprüfung (T7) vor dem Release, nach der Wahl überall eingebaut. Schlüssel-Scan bis zur Veröffentlichung des Repos mit gitleaks in der CI. Der Pi-Test aus „Fertig wenn“ von Phase 8 bleibt offen, bis der Pi bereitsteht; ersatzweise eine frische Installation mit Pi-ähnlichen Grenzen | beschlossen |
| D48 | Zusatzfunktionen, Umsetzung (9.11.2026): gespeichert pro Haushalt (Tabelle `kh_household_addons`, `kh0007`; ohne Zeile gelten die Standardwerte, bei Altinstallationen ändert sich nichts), nur Admins ändern. Was der Host schon eingerichtet hat (Telegram-Token, Whisper-URL, Teilen-Links per Umgebung, Uhr-Kurzbefehl) startet an, die Umgebung bleibt die harte Obergrenze. Ausgeschaltet: eigene `/api/kh`-Endpunkte antworten 403, Mealies Einkaufslisten- und Essensplan-API bleibt unberührt (nur die Oberfläche blendet aus). Telegram-Bot meldet sich per Kopfzeile `X-KH-Via`, Aufnahmen gelten als Whisper-Funktion; Teilen-Links zusätzlich pro Haushalt geschlossen | beschlossen |
| D49 | Name `Kochheft` mit dem Logo aus Vorschlag 1 (Heft mit Löffel als Lesezeichen), Wahl des Nutzers am 9.11.2026. Umbenannt wird alles, was Nutzer sehen (App-Titel, Logo, Symbole, Texte, Anleitungen, Bot-Antworten); technische Namen bleiben, damit laufende Installationen und Updates weiter funktionieren (`kh`-Ordner, `KH_*`-Variablen, Compose-Projekt und Container `kuechenhelfer-*`, Image `own-recipe-app`, Repo-Name). Markenprüfung bei DPMA und TMview vor dem Release (T7) | beschlossen |
| D50 | Idee (10.11.2026), zurückgestellt: Den KI-Anbieter richtet ein Admin einmal für die ganze Installation ein, er gilt dann für alle, die Kochheft benutzen, und die Einstellung taucht sonst nirgends mehr auf. Heute gilt sie pro Gruppe (Mealie, D25), was bei einer Familie mit einer Gruppe praktisch dasselbe ist. Neu entscheiden, falls Kochheft einmal für mehrere Familien oder öffentlich betrieben wird | zurückgestellt |
| D52 | Haushalt wechseln (17.11.2026): Eine Person kann zwischen Haushalten umschalten, die der Admin freigibt, auch in anderen Gruppen. Umgesetzt als verbundene Konten (Tabelle `kh_account_links`): Für jeden weiteren Haushalt legt Kochheft ein eigenes Konto an, „Haushalt wechseln“ meldet per Tipp ohne Passwort dorthin um. Ein echter Wechsel von `household_id` scheidet aus, weil Rezepte, Einkaufslisten und Essenspläne ihren Haushalt über den Ersteller bekommen und mitwandern würden. Rechte kommen bei jedem Wechsel vom Hauptkonto, Unverträglichkeiten werden beim Anlegen einmal kopiert. Nur der Admin vergibt Freigaben. | beschlossen |
| D53 | Konten ohne E-Mail (18.11.2026): Der Admin legt Konten auch ohne E-Mail an; Kochheft trägt dann eine Platzhalter-Adresse `<hex>@no-email.invalid` ein, die die Oberfläche als „keine E-Mail“ zeigt, damit Mealies Kern unverändert bleibt. „Passwort zurücksetzen“ erscheint nur mit eingerichtetem Mail-Versand, sonst der Hinweis auf den Admin. Wer vom Admin angelegt wird, legt beim ersten Anmelden ein eigenes Passwort fest. Mit E-Mail und Mail-Versand kommt eine Willkommens-Mail mit einem Link zum Festlegen des Passworts, ohne Passwort im Klartext. Der Admin-Schalter „E-Mail-Adresse Pflicht“ (nur mit Mail-Versand) verlangt von Personen ohne bestätigte Adresse eine, die per Link bestätigt wird. Links gelten `KH_ACCOUNT_LINK_HOURS` (72) Stunden. Die Sperre beim ersten Anmelden sitzt nur in der Oberfläche. | beschlossen |
| D54 | Kommentare zurück (18.11.2026): Die Rezeptseite zeigt wieder Mealies Kommentare (D38 hatte sie ausgeblendet). Jede Person kann beliebig viele Kommentare schreiben, alle sehen sie. Abschalten lassen sie sich mit Mealies eigenen Schaltern pro Haushalt und pro Rezept, eine eigene Zusatzfunktion braucht es nicht. Nur in der eigenen Gruppe, nicht im Bearbeiten- und Kochmodus. | beschlossen |
| D55 | Neues Rezept direkt prüfen (18.11.2026): In der Vorschau eines Entwurfs tippt man auf Titel, Zutat oder Schritt und ändert ihn dort; eine Zutat wird neu gelesen, Schritt-Verknüpfungen folgen dem Text oder fallen weg. Darunter fragt „Wohin kommt das Rezept?“ nach Kategorien und Kochbuch; ein Kochbuch zählt, wenn sein Filter genau eine Kategorie ist, „+ Neu“ legt Kategorie oder Kochbuch an (nur mit Recht zum Organisieren). Ein Knopf „Übernehmen“ wie bisher. | beschlossen |
| D56 | Einkaufsliste weitergeben (19.11.2026): „Teilen“ öffnet das Teilen-Menü des Geräts mit den offenen Artikeln, eine Zeile pro Artikel, ohne Etiketten-Überschriften; ohne Teilen-Menü wird kopiert. Bring!s eigener Import liest nur öffentliche Rezeptseiten (schema.org) und nimmt keine Liste, deshalb keine eigene Bring!-Anbindung; ob Bring! geteilten Text annimmt, entscheidet Bring!. | beschlossen |
| D57 | Import aus dem Teilen-Menü (19.11.2026): Neben `recipe_import_url` nimmt `/r/create/url` auch `recipe_import_text`; der Text steht danach im Eingang bereit. Wer nicht angemeldet ist, meldet sich an und landet danach dort (Mealies Weiterleitung mit der ganzen Adresse). Kein Schlüssel nötig; der Kurzbefehl mit Geräteschlüssel (D37) bleibt für lange Texte. | beschlossen |
| D58 | Eigene Seitenleiste (19.11.2026): Jede Person blendet unter Mehr per Haken aus, was in ihrer Seitenleiste steht (nicht Rezepte und Mehr). Gespeichert pro Konto in `kh_user_navigation`, also auf allen Geräten gleich. Die Leiste unten am Handy bleibt. | beschlossen |
| D59 | Einführung beim ersten Anmelden (19.11.2026): Der Admin setzt beim Anlegen den Haken „Mit Einführung“ (Standard an). Nach den ersten Schritten zeigt die Startseite sechs kurze Karten; „Überspringen“ unten links. Unter Mehr jederzeit „Einführung ansehen“. Eine Karten-Folge statt eines Rundgangs mit Hervorhebungen, ohne neue Bibliothek. | beschlossen |
| D60 | Einkaufsliste mit Kacheln (19.11.2026): Eigene Seite `/einkauf` im Bring!-Stil auf Mealies Listen, pro Laden eine Liste (Ladenwahl setzt die Abteilungs-Reihenfolge), rote Kacheln für Offenes, „Zuletzt gekauft“, Katalog nach Abteilung aus Mealies Lebensmitteln plus Alltags-Artikeln; Details (Menge, Eigenschaften in der Notiz, Dringlichkeit in `extras.kh_urgency`) beim Aufschreiben. Mealies `/shopping-lists` leitet dorthin, außer mit `?klassisch=1`. Eigenes Manifest `/einkauf.webmanifest` und Android-Kurzbefehl für ein Symbol auf dem Home-Bildschirm. Entwurf: `docs/kh/specs/2026-11-19-einkaufsliste-design.md`. | beschlossen |
| D61 | Rezepte als Text (19.11.2026): „Als Text teilen“ im Rezeptmenü (Portionen wählbar; Teilen, Kopieren, `.txt`) und „Als Textdateien exportieren“ im Kochbuch (ZIP mit je einer `.txt` pro Rezept, optional Fotos daneben; keine neue Abhängigkeit, eigener ZIP-Schreiber ohne Kompression). Textformat: Titel, Info-Zeile, „Zutaten:“, „Zubereitung:“, optional „Notizen:“ und „Quelle:“, letzte Zeile „Exportiert aus Kochheft“; Mengen rechnen mit. Entwurf: `docs/kh/specs/2026-11-19-text-export-import-design.md`. | beschlossen |
| D62 | Import von Dateien (19.11.2026): Im Eingang die Quelle „Datei“ (`POST /api/kh/drafts/file`): `.txt`/`.md` ein Text-Entwurf, `.zip` im Speicher entpackt (Texte → Entwürfe, Foto mit gleichnamigem Text = dessen Titelbild, übrige Fotos → Foto-Entwürfe, versteckte Dateien ignoriert); Grenzen `KH_IMPORT_MAX_DRAFTS=100`, `KH_IMPORT_MAX_UNZIPPED_MB=50`. Texte im Kochheft-Format liest `mealie/kh/drafts/text_format.py` ohne KI; keine PDF. Ergänzt D61. | beschlossen |
| D63 | Einkaufsliste ohne Netz (19.11.2026): `/einkauf` öffnet auch ohne Empfang: Der letzte geladene Stand (Listen, Artikel, Foods, Abteilungen, Einheiten) liegt pro Nutzer im `localStorage` (`kh/app/lib/shopping-offline.ts`) und erscheint sofort, danach lädt die Seite neu. Ohne Netz oder bei einer Anfrage ohne Antwort gelten Abhaken, Zurücklegen, Kachel aufschreiben, Menge, Eigenschaften, Dringlichkeit und Notiz sofort auf dem Bildschirm und wandern in eine gespeicherte Warteschlange (zwei Änderungen am selben Artikel werden zusammengelegt, ein Entfernen streicht sie); ein Hinweis „Offline – Änderungen werden nachgeschickt“ erscheint. Kommt das Netz zurück (`online`-Ereignis oder nächste Aktualisierung), läuft die Warteschlange der Reihe nach mit dem Lesen-dann-Schreiben von `change()`; ein inzwischen gelöschter Artikel wird übersprungen, ein schon auf der Liste stehendes Food wird zusammengeführt. Das Ganze gilt nur bei eingeschaltetem Zusatz „Offline-Rezepte“ (`offline`); ausgeschaltet und beim Abmelden löscht `clearOfflineCaches()` auch die gespeicherten Listen. Die Seite selbst lädt über den Service Worker (Skripte vorab gespeichert, Navigation fällt auf die App-Hülle zurück). Nicht offline möglich: neue Artikelnamen tippen (der Server liest die Zeile), „Immer im Haus“ ändern, neuen Laden anlegen. | beschlossen |
| D64 | „Hey Siri, Milch auf die Einkaufsliste“ (19.11.2026): `POST /api/kh/shopping/add {text, list?}` für den angemeldeten Nutzer, auch mit API-Schlüssel wie beim Teilen-Kurzbefehl (D37). Der Text wird mit `parse_shopping_line` gelesen, an „und“ und Kommas in mehrere Artikel geteilt, Food und Einheit wie in `mealie/kh/shopping` angelegt und auf die Liste `list` (ohne Groß-/Kleinschreibung) oder die zuletzt geänderte Haushaltsliste geschrieben; ein offener Artikel bekommt die Menge dazu, ein abgehakter wird wieder offen. Antwort `{message}` auf Deutsch zum Vorlesen („Milch und Butter stehen auf der Liste Rewe.“); 404 ohne Liste, 422 ohne verstandenen Artikel, 403 bei ausgeschaltetem Einkaufs-Add-on. Kurzbefehl-Anleitung in der README. Code in `mealie/kh/shopping/voice.py`. | beschlossen |
| D65 | „Immer im Haus“ (19.11.2026): Mealie merkt sich pro Haushalt, welche Foods immer da sind (`households_to_ingredient_foods`, in der API `householdsWithIngredientFood` als Haushalts-Slugs); „Zur Einkaufsliste hinzufügen“ lässt solche Zutaten bereits ungehakt (der Dialog liest den Haushalt des Nutzers, der Dienst den der Liste, kein globales Flag; das alte Flag `on_hand` ist veraltet und wird nicht gelesen). Neu: `POST /api/kh/shopping/on-hand {foodId, onHand}` (`mealie/kh/shopping/on_hand.py`) setzt oder löscht die Verknüpfung des eigenen Haushalts für jedes Mitglied ohne Organisieren-Recht; fremde Gruppe 404, Zusatz „Einkaufsliste“ aus 403, andere Haushalte unberührt. In der Einkaufsliste: Schalter „Immer im Haus“ im Detailblatt, langes Drücken auf eine Katalog-Kachel öffnet ihn ebenfalls; solche Kacheln tragen ein kleines Haus und stehen am Ende ihrer Abteilung. | beschlossen |
| D66 | Ganze Woche auf die Einkaufsliste (19.11.2026): Geprüft: Mealies Wochenplaner (Menü ⋮ → „Alle zur Einkaufsliste hinzufügen“) legt alle Rezepte der angezeigten Tage mit ihren Portionen (Maßstab je Eintrag, gleiche Rezepte werden addiert) in einem Dialog auf eine wählbare Liste (also einen Laden aus D60) und lässt Zutaten unmarkiert, die der Haushalt als „immer im Haus“ führt. Es ist also kein Code nötig; die README beschreibt den Weg („Ganze Woche auf die Einkaufsliste“). Das Menü fehlt nur bei ausgeschaltetem Einkaufs-Add-on (D46). | beschlossen |
| D67 | „Oft gekocht“ und „Lange nicht gekocht“ (19.11.2026): Auf der Startseite über der Rezeptliste zwei waagerechte Reihen mit Mealies Rezeptkarten (leer = nicht gezeigt); `GET /api/kh/recipes/cooked` → `{often, longAgo}` mit je bis zu 8 Karten `{id, slug, name, image, count, lastMade}`. „Oft“: die Rezepte der Gruppe mit den meisten „gekocht“-Einträgen der letzten 365 Tage, mindestens 2. „Lange nicht“: Rezepte, die der Haushalt mindestens einmal gekocht hat und zuletzt vor mehr als 30 Tagen, das am längsten Zurückliegende zuerst. Ein „gekocht“-Eintrag ist ein Zeitleisten-Eintrag „… made this“/„… hat's gemacht“ (Vom Dialog „Ich hab's gemacht“, Typ Kommentar; nur deutsch und englisch erkannt) oder „recipe.made-this-…“ (vom Tagesplan, Typ Info). Code in `mealie/kh/cooked/`, `KhCookedRows.vue`. | beschlossen |
| D70 | „Was koche ich diese Woche?“ (19.11.2026): Im Essensplan (Zusatzfunktion „Essensplan“) öffnet „Woche vorschlagen“ ein Fenster mit einem Gericht je Tag ohne Abendessen (vergangene Tage nicht): Bild, Name, „Anderes“ (holt eines nach, ohne die gezeigten) und Haken. „Übernehmen“ legt Abendessen für die Haken an und fragt, ob alles auf die Einkaufsliste soll. `GET /api/kh/recipes/week-suggestion?days=7&exclude=<id>&seed=<n>` → Liste `{id, slug, name, image}`: zuerst Wünsche (D72, die längste zuerst), dann abwechselnd „oft“ und „lange nicht“ (der Dienst aus D67), dann nie gekochte Favoriten der Person, dann zufällige Rezepte der Gruppe; nie eines, das in den letzten 7 Tagen gekocht wurde, in den nächsten 14 Tagen geplant ist (Plan des Haushalts) oder in `exclude` steht. `seed` macht die Auswahl wiederholbar (Tests). Code in `mealie/kh/weeksuggestion/`, `KhWeekSuggestion.vue`. | beschlossen |
| D71 | Handy bleibt hochkant (19.11.2026): iOS ignoriert `orientation` im Manifest und kennt kein `screen.orientation.lock`. Auf Handys (Touch und kürzere Bildschirmseite unter 500 px, am Bildschirm gemessen, nicht am Fenster) deckt ein Hinweis „Bitte dreh dein Handy hochkant.“ die App ab, solange das Handy quer liegt, auch im Kochmodus. iPads (ab 744 px) und Computer sehen ihn nie, ein globales Manifest-`orientation` gibt es deshalb nicht. Auf Android in der installierten App wird zusätzlich `screen.orientation.lock('portrait')` versucht (Ablehnung ignoriert). Der Hinweis ist ein Client-Plugin (`kh-portrait.client.ts`, reines DOM, deckt jedes Layout ab); Entscheidung `isPhoneLandscape` in `lib/portrait.ts`; die Drehung des Symbols entfällt bei „weniger Bewegung“. | beschlossen |
| D72 | Wunschliste (19.11.2026): Auf der Rezeptseite „Wünsch ich mir“ (jede Person für sich) mit der Zeile „Anna und Opa wünschen sich das“. Im Essensplan ein Bereich „Wünsche“ (neben dem Plan ab 960 px, darüber einklappbar auf Handys; ohne Wünsche nicht gezeigt): Wunsch antippen, Tages-Chip der gezeigten Woche antippen, das Rezept wird als Abendessen eingeplant, der Wunsch ist weg. Tabelle `kh_recipe_wishes` (Migration kh0012, eindeutig je Haushalt, Rezept und Person). `GET /api/kh/wishes` → `[{recipe, people, since}]`, die längste zuerst; `PUT`/`DELETE /api/kh/wishes/{recipe_id}` (eigener Wunsch); `POST /api/kh/wishes/{recipe_id}/plan {date, entryType}` legt den Eintrag wie Mealies Anlegen an (mit Ereignis) und löscht die Wünsche. Ein Wunsch ist erfüllt (für alle gelöscht), sobald der Haushalt das Rezept für heute oder später eingeplant hat: beim Auflisten geprüft, auch bei Plänen über Mealies eigene Schnittstelle. Zusatzfunktion „Essensplan“ aus: 403. SQLite erzwingt das CASCADE nicht; Wünsche gelöschter Personen oder Rezepte werden deshalb beim Auflisten durch Inner Joins nicht gezeigt. | beschlossen |
| D73 | Wochenplan teilen (19.11.2026): Im Essensplan „Woche teilen“ schickt den gezeigten Zeitraum als Text („Essen diese Woche“, je Tag mit Einträgen eine Zeile „Mo 24.11.: Lasagne · Salat“, Tage ohne Einträge fehlen, am Ende die Adresse) ans Teilen-Menü, sonst in die Zwischenablage. Gleiche Hilfen wie der Rezepttext (D61), Text in `lib/week-text.ts`. | beschlossen |
| D74 | Kochmodus am iPad quer (19.11.2026): Ab 1024 px Breite im Querformat (iPad 11"/13" quer, Mac) zeigt der Kochmodus zwei Spalten: links die Zutaten in der gewählten Menge mit Häkchen (dieselben wie auf der Rezeptseite), die Zutaten des aktuellen Schritts hervorgehoben; rechts groß der Schritt mit Timern und Zurück/Weiter. Handy und Hochformat bleiben wie bisher. | beschlossen |
| D68 | Kochheft einrichten (19.11.2026): Seite `/aufs-handy` (Mehr → „Kochheft einrichten“), Gerät aus dem Browsernamen (iPhone, iPad auch als „Macintosh“ mit Touch, Android, Mac, anderer Computer; Umschalter „Gerät“), Karten mit 2 bis 5 Schritten und Haken „Erledigt“ (localStorage je Person): Home-Bildschirm oder Dock (bei laufender App schon erledigt), Einkaufsliste als eigenes Symbol (Link mit `target=_blank`), Schlüssel für Kurzbefehle (Mealies Token-Route, einmal gezeigt, nie gespeichert), Import-Kurzbefehl und Siri (Knopf bei gesetztem `KH_IMPORT_SHORTCUT_URL` / `KH_SIRI_SHORTCUT_URL`, sonst die Schritte; am Mac über iCloud-Sync), Uhr-Timer nur iOS. Frage auf neuen Geräten nach der Anmeldung (`kh-device-setup:<userId>`: Ja, Später = 7 Tage, Nein = nie; Handy, iPad, Computer nur in Safari, Chrome, Edge), genau ein Dialog auf der Startseite (`KhStartDialogs`: Einführung vor Neuigkeiten vor Geräte-Frage). Einführung um „Teilen“ und „Kochheft einrichten“ erweitert; Dialog-Rahmen `KhCards.vue` (Vollbild nur unter 600 px, sonst Karte höchstens 92 % der Fensterhöhe, Inhalt scrollt, Tasten bleiben unten). Reine Regeln in `lib/device-setup.ts`, `lib/start-dialog.ts`. | beschlossen |
| D69 | „Neu in Kochheft“ (19.11.2026): `lib/whats-new.ts` (Versionen, neueste zuerst, Karten mit Symbol, Schlüssel, optionalem Add-on und Knopf), `unseenNews` (neuer als `newsSeen`, höchstens die zwei neuesten Versionen, Karten ausgeschalteter Add-ons weg). Spalte `kh_user_onboarding.news_seen` (kh0011); `GET /api/kh/onboarding/me` liefert `newsSeen`, `POST /api/kh/onboarding/news-seen {version}` setzt es; vom Admin angelegte Personen starten mit `NEWS_VERSION` (`mealie/kh/onboarding/news.py`), sehen also die Einführung statt der Neuigkeiten. Ein pytest liest die erste Version aus `whats-new.ts` und vergleicht sie mit `NEWS_VERSION` (einfachster robuster Weg ohne gemeinsame Datei). Mehr → „Neuigkeiten“ zeigt alle Versionen. Pflicht vor jedem Release: Karten ergänzen (`.claude/CLAUDE.md`, Phasen-Regeln). | beschlossen |
| D75 | Mitteilungen (19.11.2026): Web Push (kein Store), `pywebpush` 2.5.0 (MPL-2.0, Lizenz-Scan besteht; bringt py-vapid, http-ece, aiohttp u. a.). VAPID-Schlüssel beim ersten Gebrauch in `<Daten>/kh/vapid.json` (0600), öffentlicher Teil unter `GET /api/kh/notifications/key`. Tabellen `kh_push_subscriptions`, `kh_notification_settings` (kh0013). API: `GET/PUT /settings`, `GET/POST/DELETE /subscriptions` (DELETE mit `?endpoint=`), `POST /test`. Ereignisse (nie an die auslösende Person, nur eigener Haushalt, nur mit Schalter): Essensplan (Hook in Mealies Anlegen und in `/api/kh/wishes/{id}/plan`, Bündel von 2 Minuten), Abend-Erinnerung (minütliche Aufgabe, einmal je Tag und Person, Hinweise aus Food-Label und Schritten, `hints.py`), Einkaufsliste (höchstens eine Mitteilung je Liste in 15 Minuten, Hooks in Mealies `create-bulk` und Siri-`/add`), Wünsche, Eingang (auch an die einreichende Person: sie wartet darauf), Neuigkeiten (einmal je `NEWS_VERSION`, Marke in `<Daten>/kh/news-pushed`). Versand im Hintergrund, 404/410 löscht das Gerät. Seite Mehr → „Mitteilungen“ (`/mitteilungen`), Handler `frontend/public/kh-push.js` über `importScripts` im Service Worker. Abweichungen: Texte der Mitteilungen nur auf Deutsch; Zutaten, die über „Auf die Einkaufsliste“ am Rezept kommen, lösen keine Mitteilung aus. | beschlossen |
| D76 | Abläufe vereinfacht (19.11.2026, auf Wunsch: weniger Tipps, klarer; Einkauf und Kochen siehe D77): **Essensplan:** Mealies englischer Umschalter „Weeks/Days“ ist weg (Wochenansicht), die Woche beginnt in deutschsprachigen Haushalten ohne eigene Wahl am Montag (`lib/week-start.ts`; Mealie speichert 0 = Sonntag auch für „nie gewählt“, deshalb kann ein deutscher Haushalt den Sonntag nicht mehr wählen), „Alle zur Einkaufsliste“ ist ein eigener Knopf neben „Woche vorschlagen“ und „Woche teilen“, Seitentitel und Menüeintrag heißen beide „Essensplan“ (`kh.nav.mealplan`). **Änderung an D38:** Die untere Leiste bekommt als fünften Platz „Woche“ (Kalender, Essensplan), solange die Zusatzfunktion „Essensplan“ an ist; ohne sie bleibt es bei vier (ohne Einkaufsliste drei); die Plätze schrumpfen auf 375 px. **Kochmodus** hat den ganzen Bildschirm: bei `cook=true` verschwinden Leiste, Seitenleiste, Menüknopf und „Abmelden“ (`use-kh-cook-screen.ts`). **Eingang:** wartende Entwürfe stehen oben, das Formular ist unter „Rezept hinzufügen“ eingeklappt (offen ohne Entwürfe oder bei geteiltem Link); der KI-Hinweis ist eine Zeile; „Kochheft einrichten“ statt „Anleitung“. **Ohne KI:** „Selbst eintippen“ (öffnet Mealies Namensformular, ein Vorausfüllen mit dem Entwurfstext gibt es dort nicht) statt „Neu versuchen“; wer die KI nicht verwalten darf, liest „Frag den Admin, eine KI einzurichten.“; fehlgeschlagene Entwürfe zählen nicht im Eingang-Zähler (`waitingCount`). **Entwurf prüfen:** „Übernehmen“ bleibt unten am Bildschirm stehen (über der Leiste, `--v-layout-bottom`), eine Zeile „Ergibt [12] [Muffins]“ schreibt Portionen und Menge gleich, den Text als Ergibt-Text, das Dublettenfenster bietet „Diesen Entwurf verwerfen“. **Mehr** in fünf Gruppen: Planen · Sammlung · Einstellungen (eine Zeile, Seite `/g/<Gruppe>/einstellungen` mit Profil, Daten, Zusatzfunktionen, Haushalten, Einladen, Mitteilungen, Ofen, Nährwerten, Timer und ab 840 px der Seitenleiste) · Hilfe (Einführung, Kochheft einrichten, Neuigkeiten, Über) · Konto (Sprache, Hell/Dunkel, Abmelden); nichts ist unerreichbar. **Wochenvorschlag** auf dem Handy: Vollbild, Tag als „Do 20.11.“ (`dayLabel`), kein Platz für fehlende Fotos, Rezeptlink im selben Tab. **Wörter:** eine Bezeichnung je Sache in den Kochheft-Texten (Eingang für den Ort, Entwurf für den Eintrag, „Mealie“ nur noch im Lizenzhinweis); ein Schlüssel in `kh/lang`, der einen Mealie-Schlüssel gleichen Namens trägt, wird von Mealies Datei überstimmt (beim Zusammenführen der Sprachen steht die Hauptanwendung nach der Schicht `kh`), deshalb ersetzen KH-Schlüssel Mealies Texte nur dort, wo Kochheft den Schlüssel selbst wählt; Mealies „Koch-Modus“-Knopf unter Zubereitung ist entfernt („Kochen starten“ bleibt). **Neuigkeiten 1.3:** sechs statt elf Karten. | beschlossen |
| D77 | Einkauf und Kochen vereinfacht (19.11.2026): Rezeptzutaten ohne Lebensmittel („ml Milch“ mit Menge 200) zeigen die Einheit unter dem Namen („200 ml“ unter „Milch“), gehören zur Kachel „Milch“ und werden beim Öffnen der Seite mit dem Lebensmittel verknüpft, wenn die Gruppe es kennt (`foodLink`; Notizen mit Menge oder fehlender Einheit bleiben). Eine getippte Menge ohne Einheit („2 Milch“) behält die Einheit des Artikels auf der Liste und öffnet kein Blatt, sondern zeigt kurz „Milch: 2 l“. Bei 2 bis 5 Läden stehen sie als Chips unter dem Titel; im Rezept-Fenster „Auf die Einkaufsliste“ steht der zuletzt benutzte Laden oben (`lastUsedFirst`, derselbe Speicherschlüssel wie die Kachelseite). Kochmodus: „Du brauchst“ schreibt die Menge zuerst („200 ml Milch“); auf dem letzten Schritt ist der grüne Knopf „Fertig – gekocht“ (öffnet „Gekocht“ ohne Autofokus, Knopf „Gekocht speichern“), daneben „Nur schließen“; nach dem Speichern verschwinden `cook` und `step` aus der Adresse (`useKhCook().finish`). Timer heißen „Schritt 3 · 20 Min“ statt des abgeschnittenen Schritttexts. |
| D78 | Konto löschen ohne Rezeptverlust (19.11.2026): Beim Löschen eines Kontos (Admin, `DELETE /api/admin/users/{id}?transferTo=`, und selbst, `POST /api/kh/account/delete`) gehen Rezepte, Einkaufslisten, Wochenplan-Einträge, Kommentare, „gekocht“-Einträge und Entwürfe an eine Person desselben Haushalts (Admin/Verwalter zuerst, sonst das älteste Konto, nie ein verbundenes Konto derselben Person); Favoriten, Bewertungen, Wünsche, Einstellungen, Schlüssel und Verbindungen werden gelöscht. Ohne Erben und mit Besitz: 409. Selbst löschen: Benutzername tippen, nicht für die letzte Admin-Person oder die letzte Person eines Haushalts, verbundene Konten gehen mit. Dienst `mealie/kh/accounts/removal.py`, `KhDeleteAccountDialog.vue`, keine Migration. |
| D79 | Einfache Ansicht (19.11.2026, beschlossen): pro Person (Spalte `simple` in `kh_user_navigation`, Migration kh0014, `GET/PUT /api/kh/navigation`, Admin: `PUT /api/kh/admin/navigation/{user_id}`) größere Schrift (112 %), Leiste und Seitenmenü nur Rezepte, Einkaufsliste, Woche, Mehr, Startseite ohne Filterreihe, Mehr mit „Mehr anzeigen“; Schalter unter Mehr → Konto. Nichts wird unerreichbar. |
| D80 | Saison (19.11.2026, beschlossen): Zusatz `season` (aus); Startseite zeigt, was in Deutschland Saison hat (eigene Liste `lib/season.ts`), und bis zu 8 passende Rezepte (`GET /api/kh/recipes/season?food=…`; der Kalender liegt nur im Frontend, das die Namen mitschickt). |
| D81 | Einkaufsliste per QR-Code und NFC (19.11.2026, beschlossen): auf `/aufs-handy` Abschnitt „Für die Küche“ mit druckbarem QR-Code (`uqr`), NFC-Sticker schreiben per Web NFC (Android Chrome) und Schritte für iPhone. |
| D82 | Notiz am Rezept (19.11.2026, beschlossen): eine Familiennotiz pro Rezept und Haushalt (`kh_recipe_notes`, Migration kh0015, `GET/PUT/DELETE /api/kh/recipes/{id}/note`, bis 2000 Zeichen), Kasten „Unsere Notiz“ am Rezept, Banner im Kochmodus, Textexport „Unsere Notiz:“ (D61/D62), beim Konto löschen an den Erben (D78). |
| D83 | Ersteinrichtung kennt Kochheft (19.11.2026, beschlossen): Mealies Assistent (`/admin/setup`) bekommt drei Schritte nach „KI“: Zusatzfunktionen (die drei Voreinstellungen als große Karten, darunter die Schalter von D46), Familie (Personen mit vorläufigem Passwort, Einführung D59, einfache Ansicht D79) und Prüfen (Backup, USB-Kopie, Updates, Zugang von unterwegs, Mail, KI aus der Systemprüfung). Deutsche Grunddaten werden nur angelegt, wo es noch keine gibt (die Abteilungen entstehen mit den Lebensmitteln). Zusammenfassung nennt die Kochheft-Wahl, Ende-Seite führt zu „Dieses Gerät einrichten“ und „Mitteilungen“. Wieder öffnen: Mehr → Einstellungen → Einrichtungs-Assistent (nur Admins), ohne Kontoschritt, geschrieben wird nur, was geändert wurde. Neu-Karte nur für Admins (`admin: true`). | beschlossen |
| D84 | Ein Teilen-Endpunkt und PDFs (19.11.2026): `POST /api/kh/drafts/share` (Formular `file`, `text`, `url`, gleiche Anmeldung und Prüfungen wie `POST /drafts`) entscheidet selbst, weil Kurzbefehle nicht nach dem Typ der Eingabe verzweigen können (`classify_share`, `mealie/kh/drafts/share.py`): Datei nach Inhalt (nicht Name) Foto (JPEG, PNG, WebP, GIF, HEIC) vor PDF vor ZIP/.txt/.md (D62), Web-Seiten und Web-Archive werden übergangen; danach genau eine Adresse mit höchstens 200 Zeichen Begleittext (Regel wie `readSharedImport`, D57) ein Link-Entwurf, sonst Text ein Text-Entwurf (die eine Adresse wird dann nicht gemerkt), sonst die erste Adresse; nichts Brauchbares 422; Videolinks nie geholt (D5). Antwort `{created, skipped}`. PDF mit `pypdf` 7.1.0 (BSD-3-Clause): Text der ersten `KH_PDF_MAX_PAGES` (20) Seiten ab 200 Zeichen ein Text-Entwurf, sonst die eingebetteten Seitenbilder (höchstens `KH_DRAFT_MAX_IMAGES`) ein Foto-Entwurf (pypdf kann nicht rendern); sonst übersprungen mit `pdf_unreadable`, `pdf_encrypted`, `unreadable`; auch im Datei-Import (D62) und in ZIPs. README: ein empfohlener Kurzbefehl „In Kochheft importieren“ statt D37 und D57 (der schlüssellose bleibt als Hinweis). Keine Migration. |
| D85 | Adresswechsel (20.11.2026, beschlossen): Kurzbefehle und Home-Bildschirm-Symbole enthalten die Adresse (BASE_URL). `mealie/kh/system/address.py` merkt sie in `<data>/kh/address.json` (`current`, `previous`, `changed_at`, `notified`); der 5-Minuten-Job (`send_address_change_once`) vergleicht sie, ein Platzhalter (localhost) zählt als nicht gesetzt. Admin: Zeile „Adresse geändert“ (gelb) 60 Tage lang in der Systemprüfung, sonst Hinweiszeile. Alle: einmal pro Person und Gerät die Karte „Neue Adresse“ (`KhStartDialogs`, Merker in localStorage nach `changed_at`, `address_changed_at` in `/api/kh/features`) und einmal Push (Schalter „Neuigkeiten“). Automatisch beim ersten Start nach dem Wechsel, kein Knopf; keine Migration. `/aufs-handy` nennt die BASE_URL. [x] |
| D86 | Antworten für den Kurzbefehl am Knopf (20.11.2026, beschlossen): In „Rezepte aus anderen Apps importieren“ und „Hey Siri, Auf die Einkaufsliste“ stehen unter „Kurzbefehl hinzufügen“ die beiden Antworten auf die Fragen des Geräts als Kopierfelder (`KhCopyField.vue`): „Adresse“ (BASE_URL) und „Dein Schlüssel“ (oder „Schlüssel erstellen“, nutzt `makeKey` der Karte „Schlüssel für Kurzbefehle“). Die Schlüssel (mehrere möglich, Namen „… (2)“) gelten für alle Karten der Seite und sind nirgends gespeichert. Nur Oberfläche, keine Migration. [x] |
| D87 | Laden beim Sprechen (20.11.2026, beschlossen): `POST /api/kh/shopping/add` erkennt am Textende „bei/für/auf/in/zu (die/der/den/dem) <Name>( Liste)“, wenn <Name> zu einer Liste des Haushalts passt (ohne Groß-/Kleinschreibung und ohne „Liste“; genauer Name vor eindeutigem Anfang wie „Rossmann“ für „Rossmann Innenstadt“), und nimmt diese Liste; der Rest wird zerlegt. Passt keine Liste („Kaffee für Gäste“), bleibt der Text. Das Feld `list` hat Vorrang, ohne Laden gilt die zuletzt geänderte Liste. Reine Funktion `split_store` in `mealie/kh/shopping/voice.py`. Ergänzt D64. | beschlossen |
| D51 | Seitenmenü ab 840 px (15.11.2026): Am Ende steht „Mehr“. Nur dort liegen die Zusatzfunktionen, Systemprüfung, Über und die Einstellungen für Umluft, Nährwerte und Uhr; ohne den Eintrag waren sie auf iPad quer und Computer nicht erreichbar. Ergänzt D38. | beschlossen |

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
- [x] Sprachbefehle mit Vosk im Browser als Test-Schalter „Sprachbefehle (Test)“ (Zusatzfunktion `voice`, standardmäßig aus; Modell im Image; Code: `KhCookVoice.vue`, `use-kh-voice.ts`, `lib/voice.ts`); ob es am iPhone klappt, zeigt T2 (D42, D45).
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

- [x] Whisper-Dienst (OpenAI-kompatibel, lokal) nach T3. (8.11.2026: P7.3 im Paket v0.5; Dienst `whisper` im Profil `whisper`, Image `ghcr.io/speaches-ai/speaches:0.8.3-cpu` (MIT, amd64 und arm64); eigene Audio- und Videodateien werden im Hintergrund transkribiert, Tests mit Fake-Transport; Pi-Probelauf steht noch aus.)
- [ ] Eingang Video (Teil erledigt, 8.11.2026, P7.2; Rest ist P7.3 Whisper für eigene Dateien): Weg nach T4/D5 ohne Download: Videolinks werden nicht abgerufen, Beschreibung oder Screenshot machen den Entwurf, der Link bleibt Quelle; Mealies yt-dlp ist entfernt (8.11.2026, P7.2; ein Whisper-Weg für eigene Dateien ist P7.3).
- [x] Telegram-Bot (holt Nachrichten selbst ab, nur erlaubte IDs). (8.11.2026: P7.1 im Paket v0.5; Dienst `telegram` im Profil `telegram`, Tests mit aufgezeichnetem HTTP; Pi-Probelauf und Telegram-Probe von Hand stehen noch aus.)
- [x] Profile `leicht`, `normal`, `stark`, `lokal` und Hardware-Test (1 Minute Audio messen, Profil vorschlagen). (8.11.2026: P7.4 im Paket v0.5; `KH_PROFILE` setzt das Whisper-Modell, `kh/ops/hardware_test.sh` misst und schlägt vor; Messung auf dem echten Pi steht noch aus.)
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

### Wünsche nach v1.2 (gesammelt am 18.11.2026)

Erste Antwort auf „Was muss noch gemacht werden?“. In Arbeit für v1.3:

- [x] Konten ohne E-Mail, eigenes Passwort beim ersten Anmelden, Willkommens- und Bestätigungs-Mail (D53).
- [x] Kommentare unter jedem Rezept (D54).
- [x] Portionen: Überschriften wie „Zutaten für 6 Portionen“ rechnen mit, „2 Eigelbe“ und „2 Eiweiß“ wachsen mit den Eiern.
- [x] Neues Rezept prüfen: in der Vorschau auf Titel, Zutat oder Schritt tippen und gleich dort ändern, ein Knopf „Übernehmen“ (D55).
- [x] Neues Rezept prüfen: gleich fragen, in welche Kategorie und welches Kochbuch es kommt; „Nein“, eines aus der Liste oder unten „+ Neu“ (gehört zu D55).
- [x] Chefkoch-Import: Mengen und Zutaten in den Schritten (z. B. Milch) werden nicht erkannt.
- [x] Kochmodus: nach dem letzten Schritt beginnt er beim nächsten Mal wieder vorn statt am Ende.
- [x] Kochmodus: am Ende „Fertig“ und „Fertig, als gekocht markieren“, statt über das Drei-Punkte-Menü.

Ideen, umgesetzt am 19.11.2026 (D56–D59):

- [x] Einkaufsliste an eine andere App schicken (wie Bring!): wie das geht, ohne Abo und ohne fremde Konten, erst prüfen.
- [x] Teilen-Kurzbefehl „In Kochheft importieren“ aus jeder App (z. B. Notizen): öffnet Kochheft mit dem Text; wer nicht angemeldet ist, meldet sich an und landet danach automatisch beim Import.
- [x] Kurze Einführung beim ersten Anmelden: Der Admin setzt beim Anlegen eines Kontos den Haken „Mit Einführung“; die Person wird dann Schritt für Schritt durch die App geführt, unten links „Überspringen“.
- [x] Eigene Seitenleiste pro Person: unter Mehr bei jeder Funktion ein Haken „in der Seitenleiste“. Standard wie heute; ohne Haken steht die Funktion nur unter Mehr.

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
- [x] **T7 Name:** Projektname auf Marken- und Namenskonflikte prüfen. (9.11.2026: „Kochheft“; grobe Prüfung von Apps, Webseiten, GitHub und Domains ohne Konflikt, DPMAregister mit nationalen, Unions- und internationalen Marken sowie WIPO Global Brand Database ohne Treffer; D49.)
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
