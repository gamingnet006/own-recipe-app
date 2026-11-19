# Einkaufsliste mit Kacheln (D60)

Stand 19.11.2026, abgestimmt am klickbaren Entwurf (https://claude.ai/artifact/58S2cQ5vMGUsDJoZbxajb9).

## Warum

Die Familie kennt Bring!: Kacheln antippen statt tippen, pro Laden eine Liste, beim Aufschreiben gleich Menge und
Details. Mealies Einkaufsliste ist eine Textliste. Ein Abgleich mit Bring! scheidet aus (keine offizielle Schnittstelle).
Kochheft bekommt deshalb eine eigene Einkaufsseite im Bring!-Stil, ohne Bring!s Zeichnungen oder Farben.

## Ziele

- Pro Laden eine Liste (Rewe, Aldi, dm …), umschalten über ☰ oben links. Eine neue Liste fragt zuerst: welcher Laden?
  Die Wahl gibt den Namen und eine passende Reihenfolge der Abteilungen.
- Rote Kacheln oben: was noch fehlt; Dringendes zuerst. Antippen = gekauft, langes Drücken = Details.
- „Zuletzt gekauft“: Antippen setzt es wieder auf die Liste.
- Darunter alle Artikel nach Abteilung in der Reihenfolge des Ladens; Antippen schreibt auf und fragt sofort Menge,
  Eigenschaften (Bio, laktosefrei …), Dringend/Angebot/Wenn's passt und eine eigene Notiz.
- Suche filtert die Kacheln; ein unbekannter Name wird neu aufgeschrieben.
- Rezept → „Auf die Einkaufsliste“ funktioniert wie bisher; die Zutaten erscheinen als Kacheln mit „Aus dem Rezept …“.
- Ein eigenes Symbol auf dem Home-Bildschirm führt direkt in die Einkaufsliste.

## Nicht-Ziele

- Kein Abgleich mit Bring!, keine eigenen Listen-Tabellen: die Seite ist eine Ansicht auf Mealies Listen.
- Kein Umbau von Mealies Einkaufsseite; sie bleibt als „Klassische Ansicht“ erreichbar (Abteilungen sortieren, Rezepte
  der Liste, Aufräumen).

## Wege (abgewogen)

1. **Eigene Kochheft-Seite auf Mealies Listen (gewählt).** Neue Ansicht, Mealies Daten und Rezept-Funktion bleiben.
2. Mealies Seite umbauen: große Eingriffe in eine Mealie-Datei, Konflikte bei jedem Update.
3. Eigene Listen neben Mealies: Rezept-Zutaten und vorhandene Listen gingen verloren oder wären doppelt.

## Entscheidungen

- **Daten:** Laden = Mealie-Einkaufsliste. Gekauft = `checked`. Menge-Chip schreibt `quantity` und, wenn die Gruppe die
  Einheit kennt (g, kg, l, ml), `unit`, sonst in die Notiz. Eigenschaften sind Wörter in der Notiz, damit Teilen und
  klassische Ansicht sie zeigen. Dringlichkeit in `extras.kh_urgency` (`urgent`, `offer`, `whenever`): keine Migration.
- **Kacheln:** Mealies Lebensmittel der Gruppe mit ihrer Abteilung (Label) plus eine kleine Kochheft-Liste mit
  Alltags-Artikeln, die Mealies Rezept-Lebensmittel nicht kennt (Brot, Toilettenpapier …); diese werden als Artikel mit
  Notiz und Abteilung aufgeschrieben, nicht als neue Lebensmittel. Pro Abteilung erst die häufigsten Kacheln, „Alle
  zeigen“ für den Rest.
- **Bildchen:** Emojis; erst nach Name, sonst das Emoji der Abteilung, sonst der Anfangsbuchstabe.
- **Reihenfolge pro Laden:** Mealies Abteilungs-Reihenfolge der Liste (`updateLabelSettings`); die Ladenwahl setzt eine
  Vorlage (Supermarkt, Discounter, Drogerie, Markt/Bäcker), ändern geht in der klassischen Ansicht.
- **Adresse:** `/einkauf` (ohne Gruppe; Mealies Listen sind ohnehin dem Haushalt zugeordnet). Mealies `/shopping-lists`
  und `/shopping-lists/<id>` leiten dorthin, außer mit `?klassisch=1`. Der Navigationspunkt Einkaufsliste zeigt dorthin.
- **Home-Bildschirm:** Android: App-Verknüpfung im Manifest (`shortcuts`, langes Drücken aufs Kochheft-Symbol) .
  iPhone: `/einkauf` bringt ein eigenes Manifest (Name „Einkauf“, Start `/einkauf`), Safari → Teilen → „Zum
  Home-Bildschirm“ legt dann ein eigenes Symbol an; beim ersten Öffnen einmal anmelden (iOS trennt die Anmeldung pro
  Home-Bildschirm-App). Am echten iPhone zu prüfen.
- **Aktualität:** neu laden nach jeder Aktion, beim Zurückkommen in die App und alle 30 Sekunden, solange sichtbar.

## Dem Bauenden überlassen

Aufteilung in Komponenten, die genaue Emoji-Liste, die Abteilungs-Vorlagen im Detail, Wortlaut kleiner Hinweise.
