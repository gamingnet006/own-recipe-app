"""KH: the two mails of D53 (welcome with a link to choose a password, confirm e-mail), in German and English.
Built on Mealie's default HTML template, which escapes every value."""

from mealie.core.config import get_app_settings
from mealie.kh.features.settings import get_kh_settings
from mealie.services.email import EmailService
from mealie.services.email.email_service import EmailTemplate

TEXTS = {
    "de": {
        "welcome": {
            "subject": "Dein Kochheft-Konto",
            "header_text": "Willkommen bei Kochheft",
            "top": "Für dich wurde ein Konto angelegt. Benutzername: {username}. Adresse: {site}. "
            "Lege mit dem Knopf dein eigenes Passwort fest.",
            "bottom": "Der Link gilt {hours} Stunden. Falls du das Konto nicht erwartest, ignoriere diese Mail.",
            "button": "Eigenes Passwort festlegen",
            "path": "/willkommen",
        },
        "verify": {
            "subject": "Bestätige deine E-Mail-Adresse",
            "header_text": "E-Mail bestätigen",
            "top": "Bestätige mit dem Knopf, dass diese Adresse zu deinem Kochheft-Konto gehört.",
            "bottom": "Der Link gilt {hours} Stunden. Falls du das nicht angefordert hast, ignoriere diese Mail.",
            "button": "E-Mail bestätigen",
            "path": "/email-bestaetigen",
        },
    },
    "en": {
        "welcome": {
            "subject": "Your Kochheft account",
            "header_text": "Welcome to Kochheft",
            "top": "An account was created for you. Username: {username}. Address: {site}. "
            "Use the button to choose your own password.",
            "bottom": "The link is valid for {hours} hours. If you do not expect this account, ignore this mail.",
            "button": "Choose your password",
            "path": "/willkommen",
        },
        "verify": {
            "subject": "Confirm your e-mail address",
            "header_text": "Confirm e-mail",
            "top": "Use the button to confirm that this address belongs to your Kochheft account.",
            "bottom": "The link is valid for {hours} hours. If you did not ask for this, ignore this mail.",
            "button": "Confirm e-mail",
            "path": "/email-bestaetigen",
        },
    },
}


def pick_language(accept_language: str | None) -> str:
    """German when the browser asks for it first, else English."""
    return "de" if (accept_language or "").lower().startswith("de") else "en"


def send_account_mail(kind: str, address: str, token: str, accept_language: str | None, username: str = "") -> bool:
    """Sends the "welcome" or "verify" mail with the raw TOKEN in its link; False when mail sending is off."""
    text = TEXTS[pick_language(accept_language)][kind]
    site = get_app_settings().BASE_URL
    hours = get_kh_settings().account_link_hours
    template = EmailTemplate(
        subject=text["subject"],
        header_text=text["header_text"],
        message_top=text["top"].format(username=username, site=site),
        message_bottom=text["bottom"].format(hours=hours),
        button_link=f"{site}{text['path']}?token={token}",
        button_text=text["button"],
    )
    return EmailService(locale=accept_language).send_email(address, template)
