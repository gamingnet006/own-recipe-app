# Family accounts

Everyone in the family gets their own account without admin rights (D31). You invite them by link, and each person sets their own password. Nobody else knows it.

[Deutsch](familienkonten.md)

The labels below are the ones of the German interface; the English interface uses the matching English labels.

## For you: create an invite link

1. Open Kochheft at its outside address, `https://kochbuch.example.org`, and log in.
   - The link uses the address you are logged in at.
   - Created through `localhost` or the home network address, it does not work for the family.
2. Open your profile: `https://kochbuch.example.org/user/profile`.
3. Tap **Einladungslink erzeugen** (Get invite link).
   - The link appears right away.
   - Leave group and household as they are; there is only one of each.
4. Tap **Kopieren** (Copy) and send the link to the person, for example in a message.
   - The **Einladen** (Invite) button for e-mail does not help, because Kochheft sends no e-mails.

**One link per person.** Each link creates exactly one account. For the next person, open the dialog again; that creates a new link.

**Only create links you send right away.** A link stays valid until it is used. Anyone who gets hold of it can create an account in your household.

## For the family: create the account

1. Open the link you received.
2. Fill in **Kontoinformationen** (Account details): full name, user name, e-mail and the password twice.
   - Pick a long password.
   - After 5 wrong attempts the account is locked for 24 hours.
3. You can leave **Erweiterte Inhalte aktivieren** (Enable advanced content) switched off.
4. Tap **Weiter** (Next), then **Absenden** (Submit).
5. Log in and tick **Angemeldet bleiben** (Remember me). You then stay logged in for 30 days, even without opening the app.

## Several households

If a person belongs to two households, give them another one under **More → Household access**. They then switch under **More → Switch household**, without a second password. No second invite link is needed.

## Add it to the home screen

Kochheft then opens like an app.

- **iPhone and iPad (Safari):** share icon, then **Add to Home Screen**.
- **Android (Chrome):** menu ⋮, then **Add to Home screen**.

## What the family can do

Invited accounts can create, edit and search recipes, and use the meal plan and the shopping list.

They cannot:

- create new tags, categories, foods or units
- invite users
- change settings

They can use existing tags and categories.

**More rights for single accounts:** If someone should also create new tags and foods, give the account the matching right.

1. Open `https://kochbuch.example.org/admin/manage/users` and pick the account.
2. Tick **Benutzer kann Lebensmittel, Tags und Kategorien verwalten** (User can manage foods, tags and categories).

That is not an admin right.
