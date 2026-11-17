# Familienkonten

Jede Person in der Familie bekommt ein eigenes Konto ohne Admin-Rechte (D31). Du lädst sie per Link ein, und jede Person setzt ihr Passwort selbst. Niemand sonst kennt es.

[English](familienkonten.en.md)

## Für dich: Einladungslink erzeugen

1. Öffne Kochheft über die Adresse von unterwegs, also `https://kochbuch.example.org`, und melde dich an.
   - Der Link übernimmt die Adresse, über die du gerade angemeldet bist.
   - Erzeugst du ihn über `localhost` oder die Adresse im Heimnetz, funktioniert er bei der Familie nicht.
2. Öffne dein Profil: `https://kochbuch.example.org/user/profile`.
3. Tippe auf **Einladungslink erzeugen**.
   - Der Link erscheint sofort.
   - Gruppe und Haushalt kannst du so lassen, es gibt nur je einen.
4. Tippe auf **Kopieren** und schick den Link der Person, zum Beispiel per Nachricht.
   - Den Knopf **Einladen** für E-Mails kannst du nicht nehmen, weil Kochheft keine E-Mails verschickt.

**Ein Link für eine Person.** Jeder Link gilt für genau ein Konto. Für die nächste Person öffnest du den Dialog neu, dann entsteht ein neuer Link.

**Nur erzeugen, was du gleich verschickst.** Ein Link gilt, bis er benutzt ist. Wer ihn in die Hände bekommt, kann damit ein Konto in eurem Haushalt anlegen.

## Für die Familie: Konto anlegen

1. Öffne den Link, den du bekommen hast.
2. Fülle **Kontoinformationen** aus: Vollständiger Name, Benutzername, E-Mail und zweimal das Passwort.
   - Das Passwort sollte lang sein.
   - Nach 5 falschen Versuchen ist das Konto 24 Stunden gesperrt.
3. **Erweiterte Inhalte aktivieren** kannst du ausgeschaltet lassen.
4. Tippe auf **Weiter** und dann auf **Absenden**.
5. Melde dich an und setz dabei den Haken bei **Angemeldet bleiben**. Dann bleibst du 30 Tage angemeldet, auch wenn du die App nicht öffnest.

## Mehrere Haushalte

Gehört eine Person zu zwei Haushalten, gibst du ihr unter **Mehr → Haushalte freigeben** einen weiteren frei. Sie wechselt dann unter **Mehr → Haushalt wechseln**, ohne zweites Passwort. Ein zweiter Einladungslink ist dafür nicht nötig.

## Auf den Home-Bildschirm legen

Dann öffnet sich Kochheft wie eine App.

- **iPhone und iPad (Safari):** Teilen-Symbol, dann **Zum Home-Bildschirm**.
- **Android (Chrome):** Menü ⋮, dann **Zum Startbildschirm hinzufügen**.

## Was die Familie darf

Eingeladene Konten können Rezepte anlegen, ändern und suchen, den Wochenplan und die Einkaufsliste nutzen.

Nicht erlaubt sind:

- neue Schlagwörter, Kategorien, Lebensmittel oder Einheiten anlegen
- Benutzer einladen
- Einstellungen ändern

Vorhandene Schlagwörter und Kategorien können sie verwenden.

**Mehr Rechte für einzelne Konten:** Soll jemand auch neue Schlagwörter und Lebensmittel anlegen dürfen, gibst du dem Konto das passende Recht.

1. Öffne `https://kochbuch.example.org/admin/manage/users` und wähle das Konto.
2. Setze den Haken bei **Benutzer kann Lebensmittel, Tags und Kategorien verwalten**.

Das ist kein Admin-Recht.
