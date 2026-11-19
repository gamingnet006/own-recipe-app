# Rezepte als Text exportieren und Dateien importieren (D61, D62)

Stand 19.11.2026, vom Nutzer so abgestimmt.

## Warum

Rezepte sollen einfach aus Kochheft heraus (in Notizen, WhatsApp, als Datei, ein ganzes Kochbuch als Ordner) und
genauso einfach wieder hinein (Textdateien, ZIP-Ordner). Was Kochheft exportiert, liest es ohne KI wieder ein.

## D61 Export

- **Ein Rezept:** im Rezept-Menü (⋮) „Als Text teilen“. Fenster: „Für wie viele Portionen?“ (Plus/Minus, vorbelegt mit
  der gerade gewählten Portionenzahl; ohne Portionen im Rezept: Faktor ×1, ×2 …), Vorschau, Knöpfe **Teilen**
  (Teilen-Menü des Geräts; ohne eines: kopieren), **Kopieren**, **Als Datei** (`<Rezeptname>.txt`).
- **Ein Kochbuch:** in der Kochbuch-Ansicht „Als Textdateien exportieren“. Fenster: Portionen „wie im Rezept“ oder „für
  alle: N“, Haken **„Mit Fotos“** (an/aus). Ergebnis `<Kochbuch>.zip` mit Ordner `<Kochbuch>/`, darin je Rezept
  `<Rezeptname>.txt` und mit Haken das Foto daneben (`<Rezeptname>.webp`). Gleiche Namen bekommen „(2)“.
- **Textformat** (eine Funktion für beides): Titel; Zeile „Portionen: … · Zubereitung: … · Gesamt: …“; Leerzeile;
  „Zutaten:“ mit „- “-Zeilen und Abschnittsüberschriften; „Zubereitung:“ mit „1. “-Schritten; optional „Notizen:“;
  „Quelle: <URL>“; letzte Zeile „Exportiert aus Kochheft“. Mengen in Zutaten, Überschriften und Schritten rechnen mit.

## D62 Import von Dateien

- Im Eingang neben Link, Foto, Text die Quelle **Datei** (iPhone: Dateien-App).
- `.txt`/`.md`: ein Text-Entwurf. `.zip`: auf dem Server entpackt (Python `zipfile`, nichts auf die Platte); jede
  Text-Datei ein Entwurf, jedes Foto (jpg, png, webp, heic) ohne gleichnamige Text-Datei ein Foto-Entwurf; ein Foto mit
  gleichem Namen wie eine Text-Datei gehört zu diesem Rezept. Ordner sind egal; versteckte Dateien (`__MACOSX`, `._*`,
  `.DS_Store`) werden übergangen.
- Grenzen: höchstens 100 Entwürfe pro ZIP, 50 MB entpackt, einzelne Texte bis zur Entwurfs-Höchstlänge; was nicht
  passt oder nicht lesbar ist, nennt die Antwort.
- Texte im Kochheft-Exportformat werden ohne KI gelesen; andere Texte und Fotos liest wie bisher die KI.
- PDF vorerst nicht (bräuchte eine neue Bibliothek).

## Nicht-Ziele

Kein Mealie-JSON-Import über diesen Weg (Mealie hat eigenen Import), keine PDF, kein Export mehrerer Kochbücher auf
einmal.
