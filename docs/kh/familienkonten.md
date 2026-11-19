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

## Konto selbst anlegen, auch ohne E-Mail

Statt eines Einladungslinks kannst du ein Konto auch selbst anlegen: **Admin → Benutzer → Neu**.

- Die E-Mail ist freiwillig. Ohne sie meldet sich die Person mit dem Benutzernamen an.
- Gib der Person Benutzername und Startpasswort. Beim ersten Anmelden legt sie ein eigenes Passwort fest, erst dann geht es weiter.
- Hat sie ihr Passwort vergessen: Öffne unter **Admin → Benutzer** ihr Konto, tippe auf **Link zum Zurücksetzen erzeugen** und schick ihr den Link, z. B. per Messenger.

Mit eingerichtetem Mail-Versand (`KH_SMTP_*` in `kh/ops/.env`, Beispiel für Gmail in `kh/ops/.env.example`) gibt es mehr:

- Wer beim Anlegen eine E-Mail bekommt, erhält eine Willkommens-Mail mit einem Link zum Festlegen des Passworts. Ein Passwort steht nie in der Mail. Der Link gilt 72 Stunden (`KH_ACCOUNT_LINK_HOURS`).
- Auf der Anmeldeseite erscheint **Passwort zurücksetzen** wieder.
- Unter **Admin → Benutzer** lässt sich **E-Mail-Adresse Pflicht** einschalten. Dann gibt jede Person ohne bestätigte Adresse nach dem Anmelden eine an und bestätigt sie per Link. Admins sind davon ausgenommen, damit sich niemand aussperrt.

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

## Konto löschen

Wird ein Konto gelöscht, verschwinden die Rezepte der Person nicht: Rezepte, Einkaufslisten, Wochenplan-Einträge, Kommentare und „gekocht“-Einträge gehen an eine andere Person desselben Haushalts (Admins und Haushaltsverwalter zuerst, sonst das älteste Konto, nie ein verbundenes Konto derselben Person). Favoriten, Bewertungen, „Ich vertrage nicht“, Wünsche, Einstellungen, Schlüssel und Verbindungen werden gelöscht. Admins löschen unter **Admin → Benutzer** und wählen die Erbin oder den Erben; ist die Person allein im Haushalt, verschiebst du ihre Rezepte zuerst in einen anderen Haushalt. Jede Person löscht ihr eigenes Konto unter **Mehr → Konto**; die verbundenen Konten derselben Person gehen dabei mit, jedes mit der Erbin oder dem Erben seines Haushalts.
