"""KH: which language the server speaks to a person: their account choice, the request's Accept-Language, the
installation's language from the first setup, then German (keeps existing installs German)."""

from typing import Literal, get_args

import sqlalchemy as sa
from pydantic import UUID4
from sqlalchemy.orm import Session

from mealie.kh.navigation.models import KhUserNavigation
from mealie.kh.onboarding.models import KhAccountSettings

Locale = Literal["de-DE", "en-US"]
LOCALES: tuple[str, ...] = get_args(Locale)
DEFAULT_LOCALE: Locale = "de-DE"
APP_NAMES: dict[Locale, str] = {"de-DE": "Kochheft", "en-US": "Cookbook"}  # the frontend key kh.app.name


def known_locale(value: str | None) -> Locale | None:
    """The value when it is one of the two supported locales, else None."""
    return value if value in LOCALES else None  # type: ignore[return-value]


def accept_language_locale(header: str | None) -> Locale | None:
    """The first German or English entry of an Accept-Language header (highest q first), None if neither."""
    ranked: list[tuple[float, int, str]] = []
    for position, part in enumerate((header or "").split(",")):
        tag, _, params = part.strip().partition(";")
        quality = 1.0
        if params.strip().startswith("q="):
            try:
                quality = float(params.strip()[2:])
            except ValueError:
                continue
        ranked.append((-quality, position, tag.strip().lower()))
    for _, _, tag in sorted(ranked):
        if tag.startswith("de"):
            return "de-DE"
        if tag.startswith("en"):
            return "en-US"
    return None


def installation_locale(session: Session) -> Locale | None:
    """The language chosen in the first setup, None while nobody chose one."""
    return known_locale(session.execute(sa.select(KhAccountSettings.locale)).scalars().first())


def installation_app_name(session: Session, configured: str) -> str:
    """The name the app gives itself on the home screen: "Cookbook" for an English installation, else the configured
    name (an own BRANDING_NAME is never replaced)."""
    if configured == APP_NAMES["de-DE"] and installation_locale(session) == "en-US":
        return APP_NAMES["en-US"]
    return configured


def person_locale(session: Session, user_id: UUID4 | None, accept_language: str | None) -> Locale:
    """The language to answer a person in: account choice, then Accept-Language, then the installation, then German."""
    chosen = None
    if user_id is not None:
        chosen = session.execute(
            sa.select(KhUserNavigation.locale).where(KhUserNavigation.user_id == user_id)
        ).scalar_one_or_none()
    return (
        known_locale(chosen)
        or accept_language_locale(accept_language)
        or installation_locale(session)
        or DEFAULT_LOCALE
    )
