"""KH: the add-ons page's data (D46)."""

from pydantic import ConfigDict

from mealie.schema._mealie import MealieModel


class AddonFlags(MealieModel):
    """One switch per add-on; the defaults are the ones of a fresh install (the host's own setup is added by
    service.default_flags). Switching one off hides it from the interface and closes its own endpoints."""

    model_config = ConfigDict(extra="forbid")  # a misspelled switch is an error, not silently dropped

    shopping: bool = True  # big area: the shopping list
    planner: bool = True  # big area: the meal planner
    books: bool = True  # family cookbook
    duplicates: bool = True
    oven: bool = True  # fan-oven bracket in step texts
    nutrition: bool = True
    allergens: bool = True
    substitutions: bool = True  # exchange and variants; only usable with allergens
    offline: bool = True
    clock: bool = True  # "put on the Clock" timer button
    season: bool = False  # start page row: what is in season now
    share_links: bool = False
    telegram: bool = False
    whisper: bool = False  # own audio and video recordings
    voice: bool = False  # voice commands (test)


class AddonsOut(MealieModel):
    """flags: what the admin chose; enabled: what is really in force; unavailable: add-ons the host does not offer
    (camelCase names), shown as "not set up"."""

    flags: AddonFlags
    enabled: AddonFlags
    unavailable: list[str]
