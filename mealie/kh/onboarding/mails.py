"""KH: the two mails of D53 (welcome with a link to choose a password, confirm e-mail), in the person's language
(texts in mealie/kh/i18n/messages.py). Built on Mealie's default HTML template, which escapes every value."""

from mealie.core.config import get_app_settings
from mealie.kh.features.settings import get_kh_settings
from mealie.kh.i18n.locale import Locale
from mealie.kh.i18n.messages import say
from mealie.services.email import EmailService
from mealie.services.email.email_service import EmailTemplate

PATHS = {"welcome": "/willkommen", "verify": "/email-bestaetigen"}


def send_account_mail(kind: str, address: str, token: str, locale: Locale, username: str = "") -> bool:
    """Sends the "welcome" or "verify" mail in LOCALE with the raw TOKEN in its link; False when mail sending is off."""
    site = get_app_settings().BASE_URL
    hours = get_kh_settings().account_link_hours
    template = EmailTemplate(
        subject=say(f"mail_{kind}_subject", locale),
        header_text=say(f"mail_{kind}_header", locale),
        message_top=say(f"mail_{kind}_top", locale, username=username, site=site),
        message_bottom=say(f"mail_{kind}_bottom", locale, hours=hours),
        button_link=f"{site}{PATHS[kind]}?token={token}",
        button_text=say(f"mail_{kind}_button", locale),
    )
    return EmailService(locale=locale).send_email(address, template)
