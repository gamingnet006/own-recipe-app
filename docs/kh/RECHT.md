# Rechts-Checkliste / Legal checklist – Kochheft

**Kein Rechtsrat.** Diese Liste hält fest, was wir aus PLAN.md Abschnitt 9 schon einhalten und was noch offen ist. Vor einer öffentlichen Veröffentlichung einmal juristisch prüfen lassen.
*No legal advice. This list records which points of PLAN.md section 9 are met and which are open. Have it reviewed by a lawyer before any public release.*

Stand: 8.11.2026 (v0.5). Status: **erfüllt**, **teilweise**, **offen**.

| # | Leitplanke | Stand | Was dazu gilt |
|---|---|---|---|
| 1 | Nur private Instanzen: keine fremden Rezepte hosten oder ins Repo legen; Quelle mitspeichern; Teilen-Links bewusst | teilweise | Im Repo liegen nur selbst geschriebene Testrezepte (Regel 9 in `.claude/CLAUDE.md`). Mealie speichert die Quelladresse; ob zusätzlich der Autor gespeichert wird, ist noch nicht geprüft. Öffentliche Gruppen und Haushalte sperrt `kh/ops/tunnel.sh on`. |
| 2 | Kein Downloader im Repo | erfüllt | Kochheft liefert keinen Downloader mit (D5). Seit v0.5 (P7.2) ist auch Mealies `yt-dlp` entfernt (nicht mehr in `pyproject.toml` und `uv.lock`); der Mealie-Weg zum Herunterladen von Videoaudio antwortet mit einem Fehler, und Mealies Importwege rufen Links zu Instagram, TikTok, YouTube und Facebook weder ab noch laden sie. Der Kochheft-Eingang (und Bot und Kurzbefehl) bauen den Entwurf aus Text oder Bild, der Link bleibt die Quelle. |
| 3 | Standardweg ohne Download: Beschreibung einfügen oder Screenshot hochladen | erfüllt (v0.5) | Videolinks zeigen den Hinweis „Videos lädt Kochheft nicht herunter“ und bieten Text- und Bildfeld an (P7.2, D5). |
| 4 | Lizenzen: AGPL-3.0, Mealies Hinweise bleiben, Quellcode-Link in der Oberfläche, `THIRD_PARTY_NOTICES.md`, keine „source-available“-Teile; Open Food Facts und BLS prüfen | erfüllt | Quellcode-Link unter „Mehr“. Jede eigene Abhängigkeit steht in `docs/kh/THIRD_PARTY_NOTICES.md`. `kh/ops/license_scan.sh` prüft alle Python- und npm-Pakete gegen eine Erlaubt-Liste und läuft in `kh-ci.yml` mit; Ausnahmen mit Grund in `kh/ops/license_exceptions.txt`. BLS 4.0 steht unter CC BY 4.0 und darf mitgeliefert werden (PLAN T5). Open Food Facts (Namensnennung, Share-Alike) ist nur optional und noch nicht eingebaut. |
| 5 | Keys: nur eigene, keine im Repo, Secret-Scan aktivieren | erfüllt | Keys liegen nur in `kh/ops/.env` und in der Datenbank; `.env` und `.secret` stehen in `.gitignore`, die Beispiele haben nur Platzhalter. gitleaks prüft in `kh-ci.yml` bei jedem Lauf die ganze Geschichte; bekannte Funde aus Mealies Geschichte stehen in `.gitleaksignore`. GitHubs eigenen Secret-Scan beim Veröffentlichen des Repos einschalten (für private Repos kostenpflichtig). |
| 6 | Datenschutz: keine Telemetrie, kein zentraler Server, die Tabelle nennt alles, was das Haus verlässt | erfüllt | Die Tabelle „Was geht wohin“ steht in `docs/kh/README.md` und wird mit jeder neuen Funktion ergänzt. Das Profil `lokal` sperrt Cloud-Wege. Mealies Versionsprüfung steht dort ebenfalls. |
| 7 | Namen und Logos: kein TikTok, Instagram oder Mealie in Name oder Logo; Projektname prüfen; freie Schriften | offen | „Kochheft“ (vormals Küchenhelfer, D49) ist als Name gewählt; die Markenprüfung bei DPMA und TMview steht vor einer Veröffentlichung noch aus (T7). Schriften stammen aus Mealies Frontend; eine Prüfung der Schriftlizenzen für Kochhefts eigene Oberfläche steht noch aus. |
| 8 | Gesundheit: Allergene und Nährwerte sind Hinweise ohne Gewähr, nie „garantiert frei von“ | erfüllt | Die Oberfläche schreibt „ohne Gewähr“ bei Allergenen und „ca.“ bei Nährwerten; es gibt keine Aussage „frei von“. |
| 9 | Tests und Doku nur mit selbst geschriebenen oder frei lizenzierten Rezepten | erfüllt | Testdaten in `kh/ops/testdata/` und in den Tests sind selbst geschrieben. Die README nennt keine fremden Rezepte. |
| 10 | KI-geschriebener Code: Abhängigkeiten per Lizenz-Scan, keine großen Fremdblöcke, Quelle im Kommentar | erfüllt | Der Lizenz-Scan läuft in der CI. Fremder Code wird nur mit Quelle im Kommentar übernommen (Code-Regel 3 und 5). |

## English summary

- Met: 5 (keys: gitleaks scans the whole history in CI), 2 (no downloader: yt-dlp removed in v0.5, video links are neither downloaded nor fetched), 3 (default way without download), 4 (licenses, scan in CI), 6 (privacy table), 8 (health notes), 9 (own test data), 10 (licence scan).
- Partly: 1.
- Open: 7 (name and fonts check before any release).

## Wie man die Liste pflegt

- Bei jedem Release die Spalte „Stand“ prüfen und ändern, was sich verändert hat.
- Neue Abhängigkeit: Lizenz prüfen, in `THIRD_PARTY_NOTICES.md` eintragen, dann `kh/ops/license_scan.sh all` laufen lassen.
- Meldet der Scan ein Paket, das nicht auf der Erlaubt-Liste steht: Lizenz im Quellcode des Pakets nachlesen. Ist sie in Ordnung, kommt das Paket mit Grund in `kh/ops/license_exceptions.txt`; sonst fliegt das Paket raus.
