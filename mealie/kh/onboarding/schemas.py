"""KH: the data of first sign-in, welcome and confirm-e-mail links, and the admin switch (D53)."""

from mealie.schema._mealie import MealieModel


class OnboardingStatus(MealieModel):
    """What a signed-in person still has to do before using the app."""

    must_change_password: bool
    needs_email: bool
    pending_email: str | None = None  # address a confirm link was sent to and that is not yet confirmed
    tour: bool = False  # the first-sign-in tour is still to be shown (D59)


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


class AccountSettingsIn(MealieModel):
    email_required: bool


class TourIn(MealieModel):
    tour: bool
