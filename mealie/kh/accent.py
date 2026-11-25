"""KH: the ten accent colours (wave 2): the keys a person or the installation may choose, and the installation's colour
for the home-screen manifest. The colours themselves live in frontend/kh/app/lib/accent-colours.ts (a test keeps the
two in step)."""

from typing import Literal, get_args

import sqlalchemy as sa
from sqlalchemy.orm import Session

from mealie.kh.onboarding.models import KhAccountSettings

Accent = Literal["salbei", "waldgruen", "petrol", "blau", "indigo", "lila", "beere", "tomatenrot", "terrakotta", "senf"]
ACCENTS: tuple[str, ...] = get_args(Accent)

# The light primary of every colour, for the manifest's theme colour (the frontend table holds the same values)
LIGHT_PRIMARY: dict[str, str] = {
    "salbei": "#2F7A55",
    "waldgruen": "#207E47",
    "petrol": "#187986",
    "blau": "#236DC7",
    "indigo": "#4044BF",
    "lila": "#8946B9",
    "beere": "#C2387D",
    "tomatenrot": "#CA382B",
    "terrakotta": "#A85A38",
    "senf": "#8D6707",
}

# In a request, this value takes a person's own colour back to the installation's
FOLLOW_INSTALLATION = "installation"


def known_accent(value: str | None) -> Accent | None:
    """The value when it is one of the ten colours, else None."""
    return value if value in ACCENTS else None  # type: ignore[return-value]


def installation_accent(session: Session) -> Accent | None:
    """The colour the admin chose in the first setup, None while nobody chose one."""
    return known_accent(session.execute(sa.select(KhAccountSettings.accent)).scalars().first())


def manifest_theme_color(session: Session, configured: str) -> str:
    """The browser bar colour of the installed app: the installation's colour, unless a THEME_LIGHT_PRIMARY of the
    operator's own is configured (that is never replaced)."""
    chosen = installation_accent(session)
    if chosen and configured == LIGHT_PRIMARY["salbei"]:
        return LIGHT_PRIMARY[chosen]
    return configured
