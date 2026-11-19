"""KH: the answer and request of a person's own side menu (D58) and simple view (D79)."""

from pydantic import field_validator

from mealie.schema._mealie import MealieModel

# The entries of the side menu a person may hide, in the menu's order (never recipes or More); the frontend's
# list in kh/app/composables/use-kh-navigation.ts holds the same keys.
HIDEABLE_ENTRIES = ("intake", "shopping", "mealplan", "cookbooks", "finder", "organizers", "timeline")


class NavigationSettings(MealieModel):
    """The hidden side-menu entries; stored without duplicates, in the menu's order. In a request, simple None keeps
    the stored switch, so a client that only knows the hidden list stays compatible."""

    hidden: list[str]
    simple: bool | None = None

    @field_validator("hidden")
    @classmethod
    def known_and_ordered(cls, value: list[str]) -> list[str]:
        unknown = [key for key in value if key not in HIDEABLE_ENTRIES]
        if unknown:
            raise ValueError(f"Unknown side menu entry: {', '.join(unknown)}")
        return [key for key in HIDEABLE_ENTRIES if key in value]


class SimpleView(MealieModel):
    """The simple-view switch alone, as the admin sets it for another person."""

    simple: bool
