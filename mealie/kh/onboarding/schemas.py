"""KH: the data of first sign-in, welcome and confirm-e-mail links, and the admin switch (D53)."""

from pydantic import Field

from mealie.kh.accent import Accent
from mealie.kh.i18n.locale import Locale
from mealie.schema._mealie import MealieModel


class OnboardingStatus(MealieModel):
    """What a signed-in person still has to do before using the app."""

    must_change_password: bool
    needs_email: bool
    pending_email: str | None = None  # address a confirm link was sent to and that is not yet confirmed
    tour: bool = False  # the first-sign-in tour is still to be shown (D59)
    news_seen: str | None = None  # newest "Neu in Kochheft" version the person has seen, None: none yet (D69)
    intolerances_asked: bool = False  # "Verträgst du etwas nicht?" was answered or skipped (once per account)


class PasswordIn(MealieModel):
    password: str


class EmailIn(MealieModel):
    email: str


class TokenIn(MealieModel):
    token: str


class WelcomeIn(TokenIn):
    password: str


class WelcomeInfo(MealieModel):
    """Who a welcome link is for, shown on the page before the person chooses a password."""

    username: str
    full_name: str


class AccountSettingsOut(MealieModel):
    email_required: bool
    locale: Locale | None = None  # the installation's language from the first setup
    accent: Accent | None = None  # the installation's colour from the first setup


class AccountSettingsIn(MealieModel):
    email_required: bool | None = None  # None keeps the stored value
    locale: Locale | None = None  # None keeps the stored value
    accent: Accent | None = None  # None keeps the stored value


class InstallationLocale(MealieModel):
    """The installation's language alone, readable before anyone signs in (login page, first setup)."""

    locale: Locale | None = None


class InstallationAccent(MealieModel):
    """The installation's colour alone, readable before anyone signs in (login page, first setup)."""

    accent: Accent | None = None


class NewsSeenIn(MealieModel):
    version: str = Field(max_length=20)


class TourIn(MealieModel):
    tour: bool
