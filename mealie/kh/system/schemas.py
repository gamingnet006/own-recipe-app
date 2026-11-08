"""KH: what the About, auto-update and system-check routes send and take."""

from mealie.schema._mealie import MealieModel


class AboutOut(MealieModel):
    version: str
    notices: str  # THIRD_PARTY_NOTICES.md as shipped in the image, empty when it is not there


class AutoUpdateIn(MealieModel):
    enabled: bool


class AutoUpdateOut(MealieModel):
    enabled: bool | None  # None: no file, KH_AUTO_UPDATE in .env decides
    status: str | None  # the last run, None before the first one


class CheckOut(MealieModel):
    key: str
    state: str  # ok | warn | bad | info
    value: str
