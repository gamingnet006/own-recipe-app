"""KH: every sentence the server says to people (Siri and shortcut answers, push messages, refusals) in German and
English, in one table. `say` picks the language; the app calls itself "Kochheft" in German and "Cookbook" in English."""

from fastapi import Request
from pydantic import UUID4
from sqlalchemy.orm import Session

from mealie.kh.i18n.locale import DEFAULT_LOCALE, Locale, person_locale

MESSAGES: dict[str, dict[Locale, str]] = {
    # Siri shopping list
    "first_list_name": {"de-DE": "Einkaufsliste", "en-US": "Shopping list"},
    "no_article": {"de-DE": "Ich habe keinen Artikel verstanden.", "en-US": "I did not understand any item."},
    "no_such_list": {"de-DE": "Die Liste {name} gibt es nicht.", "en-US": "There is no list called {name}."},
    "and": {"de-DE": "und", "en-US": "and"},
    "on_list": {"de-DE": "auf der Liste {name}", "en-US": "on your {name} list"},
    "on_list_plain": {"de-DE": "auf der Liste {name}", "en-US": "on your {name}"},  # the name already says "list"
    "listed_one": {"de-DE": "{what} steht {where}.", "en-US": "{what} is {where}."},
    "listed_many": {"de-DE": "{what} stehen {where}.", "en-US": "{what} are {where}."},
    # web manifests (the names on the home screen)
    "manifest_shopping_name": {"de-DE": "Einkaufsliste", "en-US": "Shopping list"},
    "manifest_shopping_short": {"de-DE": "Einkauf", "en-US": "Shopping"},
    # refusals and reasons shown to people
    "name_mismatch": {"de-DE": "Der Benutzername stimmt nicht.", "en-US": "The username does not match."},
    "collection_own_household": {
        "de-DE": "Nur der eigene Haushalt kann diese Sammlung ändern",
        "en-US": "Only your own household can change this collection",
    },
    "recipe_not_yours": {"de-DE": "Dieses Rezept darfst du nicht ändern", "en-US": "You may not change this recipe"},
    "heir_same_household": {
        "de-DE": "Der Erbe muss im selben Haushalt wohnen.",
        "en-US": "The heir must live in the same household.",
    },
    "removal_alone": {
        "de-DE": "Diese Person ist allein im Haushalt. Wähle, wer die Rezepte übernimmt, "
        "oder verschiebe sie zuerst in einen anderen Haushalt.",
        "en-US": "This person is alone in the household. Choose who takes over the recipes, "
        "or move them to another household first.",
    },
    "removal_last_person": {
        "de-DE": "Du bist die letzte Person in diesem Haushalt. Bitte den Admin, dein Konto zu löschen.",
        "en-US": "You are the last person in this household. Ask the admin to delete your account.",
    },
    "removal_last_admin": {
        "de-DE": "Du bist die letzte Admin-Person. Mach zuerst jemand anderen zum Admin.",
        "en-US": "You are the last admin. Make someone else an admin first.",
    },
    "removal_no_heir": {
        "de-DE": "Dein Zugang im Haushalt „{household}“ hat dort niemanden, der die Rezepte übernimmt. "
        "Bitte den Admin, ihn zu löschen.",
        "en-US": "Your access in the household “{household}” has nobody there to take over the recipes. "
        "Ask the admin to delete it.",
    },
    "verify_cooldown": {
        "de-DE": "Die letzte Bestätigungsmail ist gerade erst unterwegs. Warte {seconds} Sekunden und versuche es "
        "dann noch einmal.",
        "en-US": "The last confirmation mail was only just sent. Wait {seconds} seconds and try again.",
    },
    # share shortcut
    "share_nothing_usable": {
        "de-DE": "Damit kann Kochheft nichts anfangen.",
        "en-US": "Cookbook cannot do anything with that.",
    },
    "share_failed": {"de-DE": "Das hat nicht geklappt: {reason}.", "en-US": "That did not work: {reason}."},
    "share_done_one": {"de-DE": "Ist im Eingang: {count} Entwurf", "en-US": "It is in the inbox: {count} draft"},
    "share_done_many": {"de-DE": "Ist im Eingang: {count} Entwürfe", "en-US": "It is in the inbox: {count} drafts"},
    "skip_other": {"de-DE": "Kochheft kann damit nichts anfangen", "en-US": "Cookbook cannot do anything with it"},
    "skip_too_large": {"de-DE": "zu groß", "en-US": "too large"},
    "skip_not_an_image": {"de-DE": "kein Foto", "en-US": "not a photo"},
    "skip_unreadable": {"de-DE": "nicht lesbar", "en-US": "not readable"},
    "skip_empty": {"de-DE": "leer", "en-US": "empty"},
    "skip_text_too_long": {"de-DE": "Text zu lang", "en-US": "text too long"},
    "skip_unsupported": {"de-DE": "Dateityp nicht unterstützt", "en-US": "file type not supported"},
    "skip_too_many": {"de-DE": "zu viele Dateien", "en-US": "too many files"},
    "skip_pdf_encrypted": {"de-DE": "PDF mit Passwort", "en-US": "PDF with a password"},
    "skip_pdf_unreadable": {
        "de-DE": "kein Text und kein Bild im PDF",
        "en-US": "no text and no image in the PDF",
    },
    "skip_pdf_too_slow": {"de-DE": "PDF zu aufwendig", "en-US": "PDF too elaborate"},
    # errors the shortcut routes answer with (speakable.py)
    "code_video_link": {
        "de-DE": "Videolinks lädt Kochheft nicht. Teile stattdessen den Text oder ein Foto.",
        "en-US": "Cookbook does not load video links. Share the text or a photo instead.",
    },
    "code_too_large": {"de-DE": "Die Datei ist zu groß.", "en-US": "The file is too large."},
    "code_text_too_long": {"de-DE": "Der Text ist zu lang.", "en-US": "The text is too long."},
    "code_not_an_image": {"de-DE": "Das ist kein Foto.", "en-US": "That is not a photo."},
    "code_unreadable": {"de-DE": "Die Datei lässt sich nicht lesen.", "en-US": "The file cannot be read."},
    "code_empty": {"de-DE": "Da ist nichts drin.", "en-US": "There is nothing in it."},
    "code_unsupported": {
        "de-DE": "Diesen Dateityp kann Kochheft nicht lesen.",
        "en-US": "Cookbook cannot read this file type.",
    },
    "code_too_many_images": {"de-DE": "Das sind zu viele Fotos.", "en-US": "That is too many photos."},
    "status_401": {
        "de-DE": "Du bist nicht angemeldet. Prüfe den API-Schlüssel im Kurzbefehl.",
        "en-US": "You are not signed in. Check the API key in the shortcut.",
    },
    "status_403": {"de-DE": "Das ist nicht erlaubt.", "en-US": "That is not allowed."},
    "status_404": {"de-DE": "Das gibt es nicht.", "en-US": "That does not exist."},
    "status_other": {"de-DE": "Das hat nicht geklappt.", "en-US": "That did not work."},
    # add-ons that are off
    "addon_off": {
        "de-DE": "{label} ist ausgeschaltet. Ein Admin kann sie unter Mehr → Zusatzfunktionen einschalten.",
        "en-US": "{label} is switched off. An admin can switch it on under More → Add-ons.",
    },
    "addon_books": {"de-DE": "Familienkochbuch", "en-US": "Family cookbook"},
    "addon_duplicates": {"de-DE": "Doppelte Rezepte", "en-US": "Duplicate recipes"},
    "addon_nutrition": {"de-DE": "Nährwerte", "en-US": "Nutrition"},
    "addon_allergens": {"de-DE": "Allergene", "en-US": "Allergens"},
    "addon_substitutions": {"de-DE": "Austausch und Varianten", "en-US": "Exchange and variants"},
    "addon_whisper": {"de-DE": "Audio und Video mit Whisper", "en-US": "Audio and video with Whisper"},
    "addon_telegram": {"de-DE": "Telegram-Bot", "en-US": "Telegram bot"},
    "addon_share_links": {"de-DE": "Öffentliche Teilen-Links", "en-US": "Public share links"},
    "addon_season": {"de-DE": "Saison", "en-US": "Season"},
    # Telegram bot
    "tg_draft_made": {"de-DE": "Entwurf angelegt{where}", "en-US": "Draft created{where}"},
    "tg_video_link": {
        "de-DE": "Videos lädt Kochheft nicht herunter. Füge die Beschreibung ein oder lade einen Screenshot hoch.",
        "en-US": "Cookbook does not download videos. Paste the description or upload a screenshot.",
    },
    "tg_no_source": {
        "de-DE": "Schick mir einen Link, einen Text oder ein Foto.",
        "en-US": "Send me a link, a text or a photo.",
    },
    "tg_several_sources": {
        "de-DE": "Nur eins auf einmal: ein Link, ein Text oder ein Foto.",
        "en-US": "Only one at a time: a link, a text or a photo.",
    },
    "tg_too_many_images": {"de-DE": "Zu viele Fotos auf einmal.", "en-US": "Too many photos at once."},
    "tg_too_large": {"de-DE": "Das Foto ist zu groß.", "en-US": "The photo is too large."},
    "tg_not_an_image": {"de-DE": "Das ist kein Foto.", "en-US": "That is not a photo."},
    "tg_text_too_long": {"de-DE": "Der Text ist zu lang.", "en-US": "The text is too long."},
    "tg_unknown_chat": {
        "de-DE": "Diese Chat-ID ist nicht freigeschaltet: {id}",
        "en-US": "This chat ID is not allowed: {id}",
    },
    "tg_bad_api_token": {
        "de-DE": "Der API-Token des Bots ist ungültig. Leg in Kochheft unter Profil → API-Tokens einen neuen an.",
        "en-US": "The bot's API token is invalid. Create a new one in Cookbook under Profile → API tokens.",
    },
    "tg_bot_off": {
        "de-DE": "Der Telegram-Bot ist in Kochheft ausgeschaltet. Ein Admin kann ihn unter Mehr → Zusatzfunktionen "
        "einschalten.",
        "en-US": "The Telegram bot is switched off in Cookbook. An admin can switch it on under More → Add-ons.",
    },
    "tg_down": {
        "de-DE": "Kochheft ist gerade nicht erreichbar. Versuch es gleich noch einmal.",
        "en-US": "Cookbook cannot be reached right now. Try again in a moment.",
    },
    "tg_rejected": {
        "de-DE": "Kochheft hat den Entwurf nicht angenommen (Fehler {status}).",
        "en-US": "Cookbook did not accept the draft (error {status}).",
    },
    "tg_photo_limit": {
        "de-DE": "Das Foto ist zu groß (höchstens {mb} MB).",
        "en-US": "The photo is too large (at most {mb} MB).",
    },
    "tg_photo_failed": {
        "de-DE": "Das Foto konnte nicht von Telegram geladen werden.",
        "en-US": "The photo could not be loaded from Telegram.",
    },
    # account mails (D53)
    "mail_welcome_subject": {"de-DE": "Dein Kochheft-Konto", "en-US": "Your Cookbook account"},
    "mail_welcome_header": {"de-DE": "Willkommen bei Kochheft", "en-US": "Welcome to Cookbook"},
    "mail_welcome_top": {
        "de-DE": "Für dich wurde ein Konto angelegt. Benutzername: {username}. Adresse: {site}. "
        "Lege mit dem Knopf dein eigenes Passwort fest.",
        "en-US": "An account was created for you. Username: {username}. Address: {site}. "
        "Use the button to choose your own password.",
    },
    "mail_welcome_bottom": {
        "de-DE": "Der Link gilt {hours} Stunden. Falls du das Konto nicht erwartest, ignoriere diese Mail.",
        "en-US": "The link is valid for {hours} hours. If you do not expect this account, ignore this mail.",
    },
    "mail_welcome_button": {"de-DE": "Eigenes Passwort festlegen", "en-US": "Choose your password"},
    "mail_verify_subject": {"de-DE": "Bestätige deine E-Mail-Adresse", "en-US": "Confirm your e-mail address"},
    "mail_verify_header": {"de-DE": "E-Mail bestätigen", "en-US": "Confirm e-mail"},
    "mail_verify_top": {
        "de-DE": "Bestätige mit dem Knopf, dass diese Adresse zu deinem Kochheft-Konto gehört.",
        "en-US": "Use the button to confirm that this address belongs to your Cookbook account.",
    },
    "mail_verify_bottom": {
        "de-DE": "Der Link gilt {hours} Stunden. Falls du das nicht angefordert hast, ignoriere diese Mail.",
        "en-US": "The link is valid for {hours} hours. If you did not ask for this, ignore this mail.",
    },
    "mail_verify_button": {"de-DE": "E-Mail bestätigen", "en-US": "Confirm e-mail"},
    # push messages
    "someone": {"de-DE": "Jemand", "en-US": "Someone"},
    "device_unknown": {"de-DE": "Gerät", "en-US": "Device"},
    "push_plan_title": {"de-DE": "Essensplan", "en-US": "Meal plan"},
    "push_plan_item": {"de-DE": "{recipe} für {day}", "en-US": "{recipe} for {day}"},
    "push_plan_one": {"de-DE": "{who} hat {item} eingeplant", "en-US": "{who} planned {item}"},
    "push_plan_many": {
        "de-DE": "{who} hat {count} Gerichte eingeplant: {items}",
        "en-US": "{who} planned {count} dishes: {items}",
    },
    "push_wish_title": {"de-DE": "Wunschliste", "en-US": "Wish list"},
    "push_wish": {"de-DE": "{who} wünscht sich {recipe}", "en-US": "{who} wishes for {recipe}"},
    "push_shopping_title": {"de-DE": "Einkaufsliste", "en-US": "Shopping list"},
    "push_shopping_list": {"de-DE": "die Einkaufsliste", "en-US": "the shopping list"},
    "push_shopping_one": {
        "de-DE": "{who} hat {item} auf {where} gesetzt",
        "en-US": "{who} put {item} on {where}",
    },
    "push_shopping_many": {
        "de-DE": "{who} hat {count} Sachen auf {where} gesetzt: {items}",
        "en-US": "{who} put {count} items on {where}: {items}",
    },
    "push_draft_title": {"de-DE": "Eingang", "en-US": "Inbox"},
    "push_draft": {"de-DE": "Zum Prüfen bereit: {name}", "en-US": "Ready to review: {name}"},
    "push_evening_title": {"de-DE": "Morgen: {dishes}", "en-US": "Tomorrow: {dishes}"},
    "push_thaw": {"de-DE": "Denk ans Auftauen: {foods}", "en-US": "Remember to thaw: {foods}"},
    "push_prepare": {"de-DE": "Am Vortag vorbereiten: {step}", "en-US": "Prepare the day before: {step}"},
    "push_news_title": {"de-DE": "Neu in Kochheft {version}", "en-US": "New in Cookbook {version}"},
    "push_news": {"de-DE": "Schau dir die Neuigkeiten an.", "en-US": "Take a look at what is new."},
    "push_address_title": {"de-DE": "Kochheft hat eine neue Adresse", "en-US": "Cookbook has a new address"},
    "push_address": {
        "de-DE": "Bitte Kurzbefehle und das Home-Bildschirm-Symbol neu einrichten.",
        "en-US": "Please set up the shortcuts and the home screen icon again.",
    },
    "push_test_title": {"de-DE": "Kochheft", "en-US": "Cookbook"},
    "push_test": {"de-DE": "Test von Kochheft", "en-US": "Test from Cookbook"},
}


def say(key: str, locale: Locale = DEFAULT_LOCALE, **values: object) -> str:
    """The sentence KEY in LOCALE with VALUES filled in."""
    return MESSAGES[key][locale].format(**values)


def request_locale(session: Session, user_id: UUID4 | None, request: Request) -> Locale:
    """The language to answer this request in. Remembered on the request, so the error handler of the shortcut
    routes (speakable.py) answers failures in the same language."""
    locale = person_locale(session, user_id, request.headers.get("accept-language"))
    request.state.kh_locale = locale
    return locale
